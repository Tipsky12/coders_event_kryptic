# School Inventory and Access Portal

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A web-based inventory and equipment loan management system developed for academic and institutional facilities. The platform provides administrators with centralized oversight across equipment categories, piece-level tracking, loan issuance with automated return deadlines, condition inspections upon check-in, and real-time overdue detection.

---

## Features

- **Domain-Restricted Authentication**
  - Restricts login access exclusively to authorized institutional email domains (`@nfsu.ac.in`).
  - Session-based authorization controls access to all protected administrative endpoints.

- **Centralized Inventory Oversight**
  - Departmental categorization across Sports, Educational, and Event resources.
  - Automatic calculation of available versus total stock based on active loans and equipment condition.

- **Granular Piece-Level Tracking**
  - Unique piece identifiers (such as `RAQ01`, `BAL03`, `CHR05`) associated with specific physical storage locations.
  - Per-piece condition tracking (`Perfect` or `Damaged`) and status tracking (`Available` or `Issued`).

- **Automated Loan Issuance**
  - Records borrower details and sets a standardized 15-day loan period from the date of issue.
  - Automatically attributes loan transactions to the currently authenticated administrative account.

- **Check-In and Condition Triage**
  - Evaluates equipment condition upon return.
  - Damaged items are quarantined from available inventory counts until serviced or repaired.

- **Real-Time Overdue Detection**
  - Automatically identifies overdue items using SQL date-difference calculations (`DATEDIFF`).
  - Displays dynamic alert counts and late-day tallies directly on the administrative dashboard.

- **Responsive User Interface**
  - Structured card-based layout with custom CSS.
  - Native support for system dark and light display modes.

---

## System Architecture

```
                    +---------------------------+
                    |    Client Browser         |
                    +-------------+-------------+
                                  |
                                  | HTTP / JSON Requests
                                  v
                    +-------------+-------------+
                    |    Flask Application      |
                    |    (app.py)               |
                    |  - Session Authentication |
                    |  - Business Logic Rules   |
                    |  - Jinja2 Template Engine |
                    +-------------+-------------+
                                  |
                                  | MySQL Protocol (IPv4)
                                  v
+---------------------------------+---------------------------------+
|                  MySQL Database (school_inventory)                |
|                                                                   |
|  inventory         Master summary table (quantities & categories) |
|  racquet           Sports equipment piece records                 |
|  ball              Sports balls piece records                     |
|  drawing_board     Educational drafting board records             |
|  stationery_set    Educational stationery pack records            |
|  chair             Event seating records                          |
|  event_table       Event table records                            |
+-------------------------------------------------------------------+
```

---

## Directory Structure

```
.
├── app.py                   # Flask server, route controllers, and database initialization
├── trial.py                 # Original CLI utility script for inventory operations
├── requirements.txt         # Python project dependencies
├── .gitignore               # Git ignored file patterns
├── README.md                # Project documentation
│
├── static/                  # Static web assets
│   ├── styling.css          # Stylesheet for authentication and standalone form layouts
│   └── dashboardstyle.css   # Stylesheet for dashboard, tables, badges, and tiles
│
└── templates/               # Jinja2 HTML templates
    ├── login.html           # Authentication portal
    ├── dashboard.html       # Primary management dashboard
    ├── inventory.html       # Master inventory stock overview table
    ├── items.html           # Detailed piece-level breakdown table
    ├── issue.html           # Equipment loan issuance form
    └── return.html          # Equipment check-in and condition form
```

---

## Technology Stack

- **Backend Framework**: Python 3, Flask 3.x
- **Database Engine**: MySQL Server 8.x via `mysql-connector-python`
- **Frontend**: HTML5, CSS3, JavaScript (ES6 Fetch API)
- **Session Management**: Flask Server-Side Session Storage

---

## Installation and Setup

### Prerequisites

Ensure the following software packages are installed on the host system:
- Python 3.10 or higher
- MySQL Server 8.0 or higher (active on port `3306`)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/school-inventory-portal.git
cd school-inventory-portal
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Database Configuration

Database connection settings are defined in `app.py`:

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "passwd": "tiger"  # Set to your MySQL password if different
}
DB_NAME = "school_inventory"
```

The application features automated database provisioning. When `app.py` is executed, the `init_db()` routine will automatically:
1. Create the `school_inventory` database schema if not present.
2. Create the master `inventory` summary table and all individual equipment tables.
3. Seed default stock entries (10 units per equipment type).
4. Populate demonstration records for overdue and active loan testing.

---

## Running the Application

Start the Flask application server:

```bash
python app.py
```

Once initialized, open a web browser and navigate to:

```
http://127.0.0.1:5000
```

### Default Credentials

| Field | Value |
| :--- | :--- |
| **Email** | `inventory.admin@nfsu.ac.in` *(or any `@nfsu.ac.in` email address)* |
| **Password** | `tiger` |

---

## Equipment Specifications

| Prefix | Equipment Name | Department Category | Assigned Storage Location |
| :--- | :--- | :--- | :--- |
| `RAQ` | Racquet | Sports | Sports Room - Shelf A |
| `BAL` | Ball | Sports | Sports Room - Shelf B |
| `DRB` | Drawing Board | Educational | Art Room - Rack 1 |
| `STS` | Stationery Set | Educational | Art Room - Rack 2 |
| `CHR` | Chair | Events | Event Store - Section 1 |
| `TBL` | Table | Events | Event Store - Section 2 |

---

## Operational Workflows

1. **Authentication**: Sign in using an approved `@nfsu.ac.in` email and password.
2. **Dashboard Review**: Review real-time overdue notices and access primary management modules.
3. **Equipment Issuance**: Navigate to the Issue section, input the equipment piece code, and provide the borrower's name. The issuing administrator's account is automatically recorded.
4. **Equipment Return**: Access the Return section, enter the piece code, and assign the verified physical condition (`Perfect` or `Damaged`).
5. **Inventory Inspection**: View the master inventory counts or inspect individual pieces with location and loan metadata.

---

## License

This project is distributed under the terms of the [MIT License](LICENSE).
