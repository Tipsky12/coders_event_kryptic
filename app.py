import os
from datetime import date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
import mysql.connector as sql

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "nfsu_inventory_super_secret_key_2026"

# Database Configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "passwd": "tiger"
}
DB_NAME = "school_inventory"

# Items Configuration from trial.py
# table name : (item code prefix, item name, category, storage location)
ITEMS = {
    "racquet":        ("RAQ", "Racquet",        "Sports",      "Sports Room - Shelf A"),
    "ball":           ("BAL", "Ball",           "Sports",      "Sports Room - Shelf B"),
    "drawing_board":  ("DRB", "Drawing Board",  "Educational", "Art Room - Rack 1"),
    "stationery_set": ("STS", "Stationery Set", "Educational", "Art Room - Rack 2"),
    "chair":          ("CHR", "Chair",          "Events",      "Event Store - Section 1"),
    "event_table":    ("TBL", "Table",          "Events",      "Event Store - Section 2"),
}
QTY = 10
ISSUE_DAYS = 15
ADMIN_NAME = "admin"
ADMIN_MAIL = "inventory.admin@nfsu.ac.in"
DEFAULT_PASSWORD = "tiger"

SAMPLE_ISSUES = [
    ("racquet",       "RAQ01", 20),
    ("ball",          "BAL02", 18),
    ("drawing_board", "DRB03", 25),
    ("chair",         "CHR04", 5),
]

PREFIX_TO_TABLE = {info[0]: tbl for tbl, info in ITEMS.items()}


def get_db_connection():
    """Connects to MySQL server and selects school_inventory database."""
    con = sql.connect(**DB_CONFIG, database=DB_NAME)
    return con


def init_db():
    """Initializes database schema and seed data."""
    try:
        # Initial connection without database
        con = sql.connect(**DB_CONFIG)
        cur = con.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cur.execute(f"USE {DB_NAME}")

        # Master inventory table
        cur.execute("""CREATE TABLE IF NOT EXISTS inventory(
                        item_code   VARCHAR(5) PRIMARY KEY,
                        name        VARCHAR(30) NOT NULL,
                        category    VARCHAR(15) NOT NULL,
                        qty         INT NOT NULL,
                        no_avail    INT NOT NULL)""")

        # Item piece tables
        for tbl in ITEMS:
            cur.execute(f"""CREATE TABLE IF NOT EXISTS {tbl}(
                            item_code        VARCHAR(8) PRIMARY KEY,
                            name             VARCHAR(30) NOT NULL,
                            item_condition   VARCHAR(10) DEFAULT 'Perfect',
                            status           VARCHAR(10) DEFAULT 'Available',
                            issuer_name      VARCHAR(40),
                            mail_id          VARCHAR(50),
                            date_of_issue    DATE,
                            return_date      DATE,
                            storage_location VARCHAR(40))""")

            try:
                cur.execute(f"ALTER TABLE {tbl} ADD COLUMN mail_id VARCHAR(50) AFTER issuer_name")
            except sql.Error:
                pass

        # Seed inventory rows
        for tbl, (code, name, cat, loc) in ITEMS.items():
            cur.execute("INSERT IGNORE INTO inventory VALUES(%s,%s,%s,%s,%s)",
                        (code, name, cat, QTY, QTY))

        # Seed individual pieces
        for tbl, (code, name, cat, loc) in ITEMS.items():
            for i in range(1, QTY + 1):
                piece = code + str(i).zfill(2)
                cur.execute(f"""INSERT IGNORE INTO {tbl}
                                (item_code, name, item_condition, status, storage_location)
                                VALUES(%s,%s,'Perfect','Available',%s)""",
                            (piece, name, loc))

        con.commit()

        # Seed sample issues if not already set
        for tbl, piece, days_ago in SAMPLE_ISSUES:
            issued_on = date.today() - timedelta(days=days_ago)
            due = issued_on + timedelta(days=ISSUE_DAYS)
            cur.execute(f"""UPDATE {tbl} SET status='Issued', issuer_name=%s, mail_id=%s,
                            date_of_issue=%s, return_date=%s
                            WHERE item_code=%s AND status='Available'
                            AND item_condition<>'Damaged'""",
                        (ADMIN_NAME, ADMIN_MAIL, issued_on, due, piece))

        con.commit()

        # Refresh availability for all
        for tbl in ITEMS:
            code = ITEMS[tbl][0]
            cur.execute(f"""SELECT COUNT(*) FROM {tbl}
                            WHERE status='Available' AND item_condition<>'Damaged'""")
            avail = cur.fetchone()[0]
            cur.execute("UPDATE inventory SET no_avail=%s WHERE item_code=%s", (avail, code))

        con.commit()
        cur.close()
        con.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error during database initialization: {e}")


def update_no_avail(con, tbl):
    """Updates the available item count in the inventory master table."""
    cur = con.cursor()
    code = ITEMS[tbl][0]
    cur.execute(f"""SELECT COUNT(*) FROM {tbl}
                    WHERE status='Available' AND item_condition<>'Damaged'""")
    avail = cur.fetchone()[0]
    cur.execute("UPDATE inventory SET no_avail=%s WHERE item_code=%s", (avail, code))
    con.commit()
    cur.close()


def find_table_for_piece(piece_code):
    """Determines table name from piece code (e.g. RAQ01 -> racquet)."""
    piece = piece_code.strip().upper()
    for prefix, tbl in PREFIX_TO_TABLE.items():
        if piece.startswith(prefix):
            return tbl
    return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


# ----------------- ROUTES ----------------- #

@app.route("/styling.css")
def serve_styling_css():
    return send_from_directory("static", "styling.css")


@app.route("/dashboardstyle.css")
def serve_dashboardstyle_css():
    return send_from_directory("static", "dashboardstyle.css")


@app.route("/")
@app.route("/login")
@app.route("/login.html")
def login_page():
    if 'user' in session:
        return redirect(url_for('dashboard_page'))
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email.endswith("@nfsu.ac.in") or len(email) <= len("@nfsu.ac.in"):
        return jsonify({"success": False, "message": "Email must end with @nfsu.ac.in"}), 400

    if password != DEFAULT_PASSWORD:
        return jsonify({"success": False, "message": "Incorrect email or password."}), 401

    session['user'] = email
    return jsonify({"success": True, "user": email})


@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))


@app.route("/dashboard")
@app.route("/dashboard.html")
@login_required
def dashboard_page():
    return render_template("dashboard.html", user=session.get('user'))


@app.route("/inventory")
@app.route("/inventory.html")
@login_required
def inventory_page():
    con = get_db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM inventory")
    rows = cur.fetchall()
    cur.close()
    con.close()

    # Attach table key to each row for easy linking
    code_to_key = {info[0]: key for key, info in ITEMS.items()}
    for r in rows:
        r['tbl_key'] = code_to_key.get(r['item_code'], 'racquet')

    return render_template("inventory.html", inventory=rows)


@app.route("/items")
@app.route("/items.html")
@login_required
def items_page():
    selected_item = request.args.get("item", "racquet")
    if selected_item not in ITEMS:
        selected_item = "racquet"

    con = get_db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute(f"SELECT * FROM {selected_item} ORDER BY item_code ASC")
    pieces = cur.fetchall()
    cur.close()
    con.close()

    return render_template("items.html",
                           items_dict=ITEMS,
                           selected_item=selected_item,
                           pieces=pieces)


@app.route("/issue", methods=["GET", "POST"])
@app.route("/issue.html", methods=["GET", "POST"])
@login_required
def issue_page():
    error = None
    success = None
    prefill_piece = request.args.get("piece", "").upper()

    logged_in_user = session.get('user', ADMIN_MAIL)

    if request.method == "POST":
        piece = request.form.get("piece_code", "").strip().upper()
        issuer_name = request.form.get("issuer_name", "").strip()
        mail_id = logged_in_user.strip().lower()

        tbl = find_table_for_piece(piece)
        if not tbl:
            error = f"Invalid piece code '{piece}'. Prefix not recognized."
        elif not issuer_name:
            error = "Issuer name is required."
        else:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute(f"SELECT status, item_condition FROM {tbl} WHERE item_code=%s", (piece,))
            row = cur.fetchone()

            if row is None:
                error = f"Piece '{piece}' does not exist."
            elif row[0] == "Issued":
                error = f"Piece '{piece}' is already issued."
            elif row[1] == "Damaged":
                error = f"Piece '{piece}' is marked Damaged and cannot be issued."
            else:
                today = date.today()
                due = today + timedelta(days=ISSUE_DAYS)
                cur.execute(f"""UPDATE {tbl} SET status='Issued', issuer_name=%s, mail_id=%s,
                                date_of_issue=%s, return_date=%s WHERE item_code=%s""",
                            (issuer_name, mail_id, today, due, piece))
                con.commit()
                update_no_avail(con, tbl)
                success = f"Piece '{piece}' successfully issued to {issuer_name} ({mail_id}). Return on or before {due}."
                prefill_piece = ""

            cur.close()
            con.close()

    return render_template("issue.html",
                           error=error,
                           success=success,
                           prefill_piece=prefill_piece,
                           logged_in_user=logged_in_user)


@app.route("/return", methods=["GET", "POST"])
@app.route("/return.html", methods=["GET", "POST"])
@login_required
def return_page():
    error = None
    success = None
    prefill_piece = request.args.get("piece", "").upper()

    if request.method == "POST":
        piece = request.form.get("piece_code", "").strip().upper()
        condition = request.form.get("item_condition", "Perfect").capitalize()

        if condition not in ("Perfect", "Damaged"):
            condition = "Perfect"

        tbl = find_table_for_piece(piece)
        if not tbl:
            error = f"Invalid piece code '{piece}'. Prefix not recognized."
        else:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute(f"SELECT status FROM {tbl} WHERE item_code=%s", (piece,))
            row = cur.fetchone()

            if row is None:
                error = f"Piece '{piece}' does not exist."
            elif row[0] == "Available":
                error = f"Piece '{piece}' was not issued (currently Available)."
            else:
                cur.execute(f"""UPDATE {tbl} SET status='Available', item_condition=%s,
                                issuer_name=NULL, mail_id=NULL, date_of_issue=NULL,
                                return_date=NULL WHERE item_code=%s""", (condition, piece))
                con.commit()
                update_no_avail(con, tbl)
                if condition == "Damaged":
                    success = f"Piece '{piece}' returned and marked as Damaged (not counted as available)."
                else:
                    success = f"Piece '{piece}' successfully returned in Perfect condition."
                prefill_piece = ""

            cur.close()
            con.close()

    return render_template("return.html", error=error, success=success, prefill_piece=prefill_piece)


@app.route("/api/overdue")
@login_required
def api_overdue():
    con = get_db_connection()
    cur = con.cursor(dictionary=True)
    overdue_list = []

    for tbl in ITEMS:
        cur.execute(f"""SELECT item_code, name, issuer_name, mail_id,
                               DATE_FORMAT(date_of_issue, '%Y-%m-%d') as date_of_issue,
                               DATE_FORMAT(return_date, '%Y-%m-%d') as return_date,
                               DATEDIFF(CURDATE(), return_date) as days_late
                        FROM {tbl}
                        WHERE status='Issued' AND return_date < CURDATE()
                        ORDER BY days_late DESC""")
        rows = cur.fetchall()
        overdue_list.extend(rows)

    cur.close()
    con.close()
    return jsonify({"items": overdue_list})


if __name__ == "__main__":
    init_db()
    print("Starting Flask server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
