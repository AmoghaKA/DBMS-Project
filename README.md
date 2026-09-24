# 🛒 E-Commerce Management System

> A full-stack **E-Commerce Management System** built with **Python Flask** and **Oracle Database**, featuring database-driven CRUD operations, order management, automated inventory updates, stored procedures, and a responsive dark-mode glassmorphic interface.

---

## 📌 Overview

The **E-Commerce Management System** is a full-stack web application designed to manage the core operations of an e-commerce platform.

The system provides dedicated modules for:

* 👥 Customer management
* 🗂️ Category management
* 📦 Product & inventory management
* 🛒 Order and order-item management
* 💳 Payment transaction management
* 🧾 Invoice generation
* 📊 Dashboard analytics

The application uses **Flask** as the backend framework and **Oracle Database (XE / 21c)** as the relational database. Database-side functionality such as **sequences, triggers, stored procedures, constraints, and relational integrity** is used to demonstrate practical Oracle database concepts.

---

## ✨ Key Features

### 📊 Dashboard

* Overview of customers, products, and orders
* Recent activity information
* Quick access to major system modules

### 👥 Customer Management

* Add new customers
* View registered customers
* Update customer information
* Delete customer records
* Instant client-side search/filtering

### 🗂️ Category Management

* Create product categories
* View existing categories
* Update category information
* Delete categories

### 📦 Product & Inventory Management

* Add and manage products
* Associate products with categories
* Track product prices and stock
* Highlight low-stock products
* Automatically update inventory after purchases

### 🛒 Order Management

* Create and manage customer orders
* Add multiple products to an order
* Dynamically calculate item subtotals
* Calculate order totals
* Cancel orders
* Automatically update product stock during checkout

### 💳 Payment Management

* Record payment transactions
* View payment history
* Associate payments with orders

### 🧾 Invoice / Order Summary

* Generate printable order invoices
* Retrieve invoice details through an Oracle stored procedure
* Display customer, product, quantity, price, and order-total information

---

# 🏗️ System Architecture

The project follows a simple full-stack architecture:

```text
┌─────────────────────────────┐
│       Client / Browser      │
│      HTML + CSS + JS        │
└──────────────┬──────────────┘
               │
               │ HTTP Requests
               ▼
┌─────────────────────────────┐
│        Flask Backend        │
│        Python + Jinja2      │
│                             │
│  • Routing                  │
│  • CRUD Operations          │
│  • Business Logic           │
│  • Database Connectivity    │
└──────────────┬──────────────┘
               │
               │ python-oracledb
               ▼
┌─────────────────────────────┐
│       Oracle Database       │
│          XE / 21c           │
│                             │
│  • Tables                   │
│  • PK / FK Constraints      │
│  • Sequences                │
│  • Triggers                 │
│  • Stored Procedures        │
│  • Relational Integrity     │
└─────────────────────────────┘
```

---

# 📂 Project Structure

```text
ECommerceManagementSystem/
│
├── app.py
├── requirements.txt
├── README.md
│
├── sql/
│   ├── tables.sql
│   ├── sequences.sql
│   ├── trigger.sql
│   ├── procedure.sql
│   └── sample_data.sql
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── script.js
│
└── templates/
    ├── base.html
    ├── index.html
    ├── customer.html
    ├── category.html
    ├── product.html
    ├── order.html
    ├── payment.html
    └── order_summary.html
```

---

# 🧰 Technology Stack

| Layer           | Technology                          |
| --------------- | ----------------------------------- |
| Frontend        | HTML5, CSS3, JavaScript             |
| UI              | Responsive Dark Glassmorphic Design |
| Templating      | Jinja2                              |
| Backend         | Python + Flask                      |
| Database        | Oracle XE / Oracle Database 21c     |
| Database Driver | `oracledb`                          |
| Database Tools  | Oracle SQL Developer                |
| Environment     | Python Virtual Environment          |

---

# 🗄️ Database Design

The project demonstrates several important Oracle Database concepts.

### 🔑 Primary & Foreign Keys

Tables are connected using relational keys to maintain data consistency between entities such as:

```text
Customer
   │
   ▼
 Order
   │
   ├──────────► Payment
   │
   ▼
Order Item
   │
   ▼
Product
   │
   ▼
Category
```

### 🔢 Sequences

Oracle sequences are used to generate unique identifiers for entities instead of relying on application-side ID generation.

Examples include:

```text
customer_seq
category_seq
product_seq
order_seq
payment_seq
```

### ⚡ Trigger

The project includes the database trigger:

```text
trg_update_stock_on_order
```

Its purpose is to automatically decrement the available product stock when an order is processed.

This keeps inventory updates within the database layer and helps maintain consistency.

### 🧠 Stored Procedure

The project includes:

```text
sp_get_order_summary
```

The procedure performs the required database-side joins and retrieves the information required to generate an order invoice/summary.

This demonstrates the use of **Oracle stored procedures and JOIN-based queries** from the Flask application.

---

# ⚙️ Installation & Setup

## 1. Install Oracle Database

Install **Oracle Database XE / Oracle Database 21c** according to your operating system.

During installation, configure the administrative passwords for accounts such as:

```text
SYS
SYSTEM
PDBADMIN
```

Oracle typically uses port:

```text
1521
```

> The exact service name depends on the Oracle version and configuration. Common examples include `XEPDB1` and `FREEPDB1`.

---

## 2. Install Oracle SQL Developer

Install and launch **Oracle SQL Developer**.

Create a connection using an administrative account.

Example:

```text
Connection Name : SYSTEM_Local
Username        : system
Password        : <your Oracle password>
Hostname        : localhost
Port            : 1521
Service Name    : XEPDB1
```

> Use the service name configured by your Oracle installation. For Oracle XE versions, this may differ.

---

# 👤 3. Create the Application Database User

Connect to Oracle using the `SYSTEM` account and execute:

```sql
ALTER SESSION SET "_ORACLE_SCRIPT" = true;

CREATE USER ecommerce_user
IDENTIFIED BY ecommerce_password;

GRANT CONNECT,
      RESOURCE,
      CREATE VIEW,
      CREATE SEQUENCE,
      CREATE TRIGGER,
      CREATE PROCEDURE
TO ecommerce_user;

ALTER USER ecommerce_user
QUOTA UNLIMITED ON USERS;
```

This creates a dedicated database user for the application instead of running the application using the Oracle administrator account.

---

# 🗃️ 4. Initialize the Database

Connect to Oracle as:

```text
Username: ecommerce_user
```

Run the SQL scripts in the following order:

### Step 1 — Sequences

```text
sql/sequences.sql
```

Creates sequence counters used for generating primary keys.

### Step 2 — Tables

```text
sql/tables.sql
```

Creates the database tables along with:

* Primary keys
* Foreign keys
* Unique constraints
* Check constraints
* Referential integrity rules

### Step 3 — Trigger

```text
sql/trigger.sql
```

Creates the inventory-management trigger:

```text
trg_update_stock_on_order
```

### Step 4 — Stored Procedure

```text
sql/procedure.sql
```

Creates:

```text
sp_get_order_summary
```

for retrieving order invoice information.

### Step 5 — Sample Data

```text
sql/sample_data.sql
```

Populates the database with initial sample records for testing.

---

# 🐍 5. Configure the Flask Application

## Create a Virtual Environment

From the project directory:

### Windows PowerShell

```powershell
python -m venv venv

.\venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
python -m venv venv

.\venv\Scripts\activate.bat
```

---

## Install Dependencies

Once the virtual environment is activated:

```bash
pip install -r requirements.txt
```

The project uses the modern **`oracledb` Python driver**, allowing the Flask application to communicate with Oracle Database.

---

# 🔐 6. Configure Environment Variables

The application can be configured using environment variables.

| Variable           | Purpose                    | Default              |
| ------------------ | -------------------------- | -------------------- |
| `ORACLE_USER`      | Oracle database username   | `ecommerce_user`     |
| `ORACLE_PASSWORD`  | Oracle database password   | `ecommerce_password` |
| `ORACLE_DSN`       | Oracle connection string   | `localhost/XEPDB1`   |
| `FLASK_SECRET_KEY` | Flask session/security key | Project default      |

### Windows PowerShell Example

```powershell
$env:ORACLE_USER="ecommerce_user"
$env:ORACLE_PASSWORD="ecommerce_password"
$env:ORACLE_DSN="localhost/XEPDB1"
$env:FLASK_SECRET_KEY="your-secret-key"
```

> ⚠️ **Security Note:** Do not commit real database credentials or secret keys to GitHub. Use environment variables or a `.env` file that is excluded through `.gitignore`.

---

# 🚀 7. Run the Application

Start the Flask development server:

```bash
python app.py
```

Once the server starts, open:

```text
http://127.0.0.1:5000
```

The application dashboard should now be accessible through your browser.

---

# 🖥️ Application Modules

## 📊 Dashboard

Displays high-level metrics such as:

* Total customers
* Total products
* Total orders
* Recent activity

---

## 👥 Customer Desk

Provides a complete customer directory with:

* Customer records
* CRUD operations
* Instant table search/filtering

---

## 📦 Product Catalog

Provides inventory management functionality including:

* Product listing
* Category association
* Price information
* Stock information
* Low-stock indicators

---

## 🛒 Order Workspace

A dynamic order-management interface featuring:

* Customer selection
* Product selection
* Order-item management
* Quantity handling
* Automatic subtotal calculations
* Order total calculation
* Checkout
* Order cancellation

---

## 💳 Payment Transactions

Provides a centralized view of payment records and allows payment information to be recorded against orders.

---

## 🧾 Invoice / Receipt

Generates a printable order summary by executing:

```text
sp_get_order_summary
```

The resulting invoice contains the relevant customer, order, product, quantity, pricing, and total information.

---

# 🎨 UI & Frontend

The application uses a responsive **dark glassmorphic design** with:

* Glass-effect cards
* Responsive layouts
* Modern navigation/sidebar
* Interactive tables
* Form validation
* Search/filter functionality
* Dynamic order calculations
* Confirmation prompts

Client-side functionality is implemented in:

```text
static/js/script.js
```

while the application's styling is maintained in:

```text
static/css/style.css
```

---

# 🧪 Testing the Application

After starting the application, a typical testing flow is:

```text
1. Open Dashboard
       ↓
2. Create / View Categories
       ↓
3. Create / View Products
       ↓
4. Add Customers
       ↓
5. Create an Order
       ↓
6. Add Order Items
       ↓
7. Checkout
       ↓
8. Verify Product Stock
       ↓
9. Record Payment
       ↓
10. Generate Invoice
```

This flow allows the complete relationship between customers, products, orders, inventory, payments, and invoices to be tested.

---

# 📸 Screenshots

Add application screenshots here to showcase the major modules.

### Dashboard

```text
[ Add Dashboard Screenshot ]
```

### Customer Management

```text
[ Add Customer Desk Screenshot ]
```

### Product Catalog

```text
[ Add Product Catalog Screenshot ]
```

### Order Management

```text
[ Add Order Workspace Screenshot ]
```

### Invoice

```text
[ Add Invoice Screenshot ]
```

> 💡 **Tip:** For a polished GitHub repository, place screenshots inside a `docs/images/` directory.

Example:

```text
docs/
└── images/
    ├── dashboard.png
    ├── customers.png
    ├── products.png
    ├── orders.png
    └── invoice.png
```

Then reference them using:

```markdown
![Dashboard](docs/images/dashboard.png)
```

---

# 📚 Concepts Demonstrated

This project demonstrates practical implementation of:

* Full-stack web application development
* Flask routing and backend logic
* Jinja2 templating
* CRUD operations
* Relational database design
* Primary & foreign keys
* Database constraints
* Oracle sequences
* Oracle triggers
* Oracle stored procedures
* SQL JOIN operations
* Inventory management
* Transaction management
* Client-side JavaScript
* Form validation
* Environment-based configuration
* Responsive UI development

---

# 🔮 Future Enhancements

The project can be extended with features such as:

* 🔐 Authentication & role-based authorization
* 📈 Advanced sales analytics
* 📊 Interactive charts and reports
* 🔎 Advanced product filtering
* 🛍️ Shopping cart functionality
* 📦 Order status tracking
* 📧 Email notifications
* 💰 Discount and coupon management
* 📱 Improved mobile-first experience
* 🧾 PDF invoice generation
* 🐳 Docker-based deployment
* ☁️ Cloud deployment
* 🔒 Improved production security

---

# 👨‍💻 Project Purpose

This project was developed as a practical demonstration of integrating a **Python-based web application with an enterprise relational database system**.

The primary focus is on applying database-management concepts such as **relational modeling, constraints, sequences, triggers, stored procedures, and SQL joins** within a functional full-stack application.

---

## ⭐ Project Highlights

| Component      | Technology                               |
| -------------- | ---------------------------------------- |
| Frontend       | HTML + CSS + JavaScript + Jinja2         |
| Backend        | Python + Flask                           |
| Database       | Oracle XE / Oracle 21c                   |
| DB Driver      | `python-oracledb`                        |
| Architecture   | Full-Stack Web Application               |
| UI             | Responsive Dark Glassmorphic Design      |
| Database Logic | Sequences + Triggers + Stored Procedures |

---

## 📄 License

This project is intended for **academic and educational purposes**.

If you plan to publish or distribute the project, add an appropriate open-source license such as the **MIT License** according to your requirements.
