E-Commerce Management System (Full-Stack Oracle + Flask)
A complete full-stack E-Commerce Management System using Python Flask as the backend framework and Oracle Database (XE / 21c) as the relational database storage. Styled with a premium responsive dark-mode glassmorphic theme.

🏗️ Project Architecture & Folder Structure
ECommerceManagementSystem/
├── app.py                  # Main Flask backend application & DB Connection utility
├── requirements.txt        # Python dependency manifest
├── README.md               # Setup & instructions documentation
├── sql/                    # Oracle Database scripts
│   ├── tables.sql          # Table definitions with PKs, FKs, and constraints
│   ├── sequences.sql       # Sequences for Auto-Incrementing Primary Keys
│   ├── trigger.sql         # Trigger updating product stock post purchase
│   ├── procedure.sql       # Stored Procedure executing JOIN queries for order invoice summaries
│   └── sample_data.sql     # Seed script for initial setup
├── static/
│   ├── css/
│   │   └── style.css       # Custom modern CSS styling (Dark Glassmorphic)
│   └── js/
│       └── script.js       # Client side validations, subtotals, delete prompt & search filter
└── templates/              # Jinja2 HTML Layout templates
    ├── base.html           # Main Admin application shell & sidebar navbar
    ├── index.html          # Main metrics dashboard
    ├── customer.html       # Customer CRUD Workspace
    ├── category.html       # Category CRUD Workspace
    ├── product.html        # Product CRUD Workspace
    ├── order.html          # Dynamic split-screen Orders desk & Item management desk
    ├── payment.html        # Transactions log & Payment recorders
    └── order_summary.html  # Printable invoice receipt (loads from sp_get_order_summary)
🛠️ Setup & Installation
1. Install Oracle Database Express Edition (XE) / Oracle 21c
Download the Oracle Database XE installer from the Oracle Database XE Downloads Page matching your OS (e.g. Windows x64).
Run the installer and set a password for the administrative accounts (SYS, SYSTEM, PDBADMIN).
Complete installation. By default, the database will start a local listener on port 1521.
2. Configure Oracle SQL Developer
Download Oracle SQL Developer from the SQL Developer Download Page. Extract it.
Run sqldeveloper.exe.
Create a connection using the system admin account:
Connection Name: SYSTEM_Local
Username: system
Password: [The password you set during installation]
Hostname: localhost
Port: 1521
SID: xe (or Service Name XEPDB1 depending on version; Oracle 21c XE usually runs inside the pluggable container service XEPDB1 or FREEPDB1).
3. Create the Database User
Open SQL Developer, connect as system, and run the following script to create a dedicated user for this project:

-- Alter session to enable container user creation (if using pluggable databases)
ALTER SESSION SET "_ORACLE_SCRIPT"=true;

-- Create user
CREATE USER ecommerce_user IDENTIFIED BY ecommerce_password;

-- Grant permissions
GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE SEQUENCE, CREATE TRIGGER, CREATE PROCEDURE TO ecommerce_user;
ALTER USER ecommerce_user QUOTA UNLIMITED ON USERS;
📂 Compile & Run SQL Scripts
Connect as ecommerce_user in SQL Developer (using Service Name XEPDB1 or FREEPDB1 depending on version) and compile the scripts in the sql/ folder in the following exact order:

sequences.sql: Creates sequence counters (customer_seq, category_seq, etc.) to simulate auto-increments.
tables.sql: Generates table schemas with relational keys, check limits, unique indices, and cascade delete constraints.
trigger.sql: Compiles trg_update_stock_on_order to decrement product stock automatically on checkout.
procedure.sql: Compiles the stored procedure sp_get_order_summary containing Oracle JOIN subqueries.
sample_data.sql: Seeds sample data for testing.
🐍 Configure Python Flask Application
1. Set up Environment
Ensure you have Python 3.9+ installed. Open a terminal inside the project directory:

# Create a virtual environment
python -m venv venv

# Activate virtual environment (Windows Powershell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Windows CMD)
.\venv\Scripts\activate.bat
2. Install Dependencies
pip install -r requirements.txt
(Uses the thin-client driver oracledb which connects natively to Oracle Database without needing client library installations).

3. Setup Environment Variables
If your Oracle connection credentials differ from the defaults, set the following environment variables (or let them fallback):

ORACLE_USER (Default: ecommerce_user)
ORACLE_PASSWORD (Default: ecommerce_password)
ORACLE_DSN (Default: localhost/XEPDB1 or localhost/FREEPDB1)
FLASK_SECRET_KEY (Default: ecommerce-management-system-secret)
For Windows Powershell:

$env:ORACLE_USER="ecommerce_user"
$env:ORACLE_PASSWORD="ecommerce_password"
$env:ORACLE_DSN="localhost/XEPDB1"
🚀 Run the Flask App
Start the webserver:

python app.py
Open a browser and navigate to: http://127.0.0.1:5000

📸 Project Screenshots Placeholders
Below are outlines of the application modules for testing:

Dashboard: Metrics panel showing card counts of Customers, Products, and Orders, along with a "Recent Activity" table.
Customer Desk: Complete registered directory list. Displays instant table text searches.
Products Catalog: Shows items inventory with low stock highlights.
Order Workspace: Dual-pane workspace allowing real-time order-item checkout and cancellations.
Invoice / Receipt: Page generated directly by executing sp_get_order_summary within the database.
