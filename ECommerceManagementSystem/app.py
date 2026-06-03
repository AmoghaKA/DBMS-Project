import os
import re
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation

import oracledb
from flask import Flask, flash, redirect, render_template, request, url_for


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ecommerce-management-system-secret")

ORACLE_USER = os.getenv("ORACLE_USER", "ecommerce_user")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "ecommerce_password")
ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost/XEPDB1")

PAYMENT_METHODS = ["Cash", "Card", "Bank Transfer", "Mobile Wallet"]
PAYMENT_STATUSES = ["Pending", "Completed", "Failed", "Refunded"]


def connect_db():
    return oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)


@contextmanager
def db_session(commit=False):
    connection = connect_db()
    cursor = connection.cursor()
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def rows_to_dicts(cursor):
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_all(sql, params=None):
    with db_session() as cursor:
        cursor.execute(sql, params or {})
        return rows_to_dicts(cursor)


def fetch_one(sql, params=None):
    with db_session() as cursor:
        cursor.execute(sql, params or {})
        row = cursor.fetchone()
        if not row:
            return None
        columns = [column[0].lower() for column in cursor.description]
        return dict(zip(columns, row))


def fetch_scalar(sql, params=None, default=None):
    result = fetch_one(sql, params)
    if not result:
        return default
    return next(iter(result.values()))


def currency(value):
    if value is None:
        return "0.00"
    try:
        return f"{Decimal(str(value)):.2f}"
    except Exception:
        return str(value)


app.jinja_env.filters["currency"] = currency


@app.errorhandler(oracledb.DatabaseError)
def handle_db_error(error):
    error_message = str(error)
    is_credentials_error = "ORA-01017" in error_message
    is_listener_error = any(code in error_message for code in ["ORA-12541", "ORA-12154", "ORA-12203", "ORA-12560", "NJS-511", "NJS-115"])
    is_missing_tables = any(code in error_message for code in ["ORA-00942", "ORA-02289"])
    
    return render_template(
        "db_error.html",
        error_message=error_message,
        is_credentials_error=is_credentials_error,
        is_listener_error=is_listener_error,
        is_missing_tables=is_missing_tables,
        oracle_user=ORACLE_USER,
        oracle_dsn=ORACLE_DSN
    ), 500


def validate_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def parse_int(value, field_name, minimum=None):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid whole number."
    if minimum is not None and parsed < minimum:
        return None, f"{field_name} must be at least {minimum}."
    return parsed, None


def parse_decimal(value, field_name, minimum=None):
    try:
        parsed = Decimal(str(value).strip())
    except (TypeError, InvalidOperation, ValueError):
        return None, f"{field_name} must be a valid number."
    if minimum is not None and parsed < minimum:
        return None, f"{field_name} must be at least {minimum}."
    return parsed, None


def recalculate_order_total(cursor, order_id):
    cursor.execute(
        """
        UPDATE orders
           SET total_amount = (
               SELECT NVL(SUM(subtotal), 0)
                 FROM order_item
                WHERE order_id = :order_id
           )
         WHERE order_id = :order_id
        """,
        {"order_id": order_id},
    )


def order_exists(order_id):
    return fetch_scalar("SELECT COUNT(*) AS total_count FROM orders WHERE order_id = :order_id", {"order_id": order_id}, 0) > 0


def category_exists(category_id):
    return fetch_scalar("SELECT COUNT(*) AS total_count FROM category WHERE category_id = :category_id", {"category_id": category_id}, 0) > 0


def customer_exists(customer_id):
    return fetch_scalar("SELECT COUNT(*) AS total_count FROM customer WHERE customer_id = :customer_id", {"customer_id": customer_id}, 0) > 0


def build_dashboard_data():
    return {
        "customers": fetch_scalar("SELECT COUNT(*) AS total_count FROM customer", default=0),
        "categories": fetch_scalar("SELECT COUNT(*) AS total_count FROM category", default=0),
        "products": fetch_scalar("SELECT COUNT(*) AS total_count FROM product", default=0),
        "orders": fetch_scalar("SELECT COUNT(*) AS total_count FROM orders", default=0),
        "payments": fetch_scalar("SELECT COUNT(*) AS total_count FROM payment", default=0),
    }


@app.route("/")
def index():
    stats = build_dashboard_data()
    recent_orders = fetch_all(
        """
        SELECT o.order_id,
               TO_CHAR(o.order_date, 'YYYY-MM-DD') AS order_date,
               o.total_amount,
               c.name AS customer_name,
               NVL(p.payment_status, 'Unpaid') AS payment_status
          FROM orders o
          JOIN customer c ON c.customer_id = o.customer_id
     LEFT JOIN payment p ON p.order_id = o.order_id
      ORDER BY o.order_date DESC, o.order_id DESC
         FETCH FIRST 5 ROWS ONLY
        """
    )
    return render_template(
        "index.html",
        active_page="dashboard",
        page_title="Dashboard",
        stats=stats,
        recent_orders=recent_orders,
    )


@app.route("/customers", methods=["GET", "POST"])
def customers():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        errors = []
        if not name:
            errors.append("Customer name is required.")
        if not validate_email(email):
            errors.append("A valid email address is required.")
        if not phone:
            errors.append("Phone number is required.")
        if not address:
            errors.append("Address is required.")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("customers", edit_id=customer_id or None))

        try:
            with db_session(commit=True) as cursor:
                if customer_id:
                    cursor.execute(
                        """
                        UPDATE customer
                           SET name = :name,
                               email = :email,
                               phone = :phone,
                               address = :address
                         WHERE customer_id = :customer_id
                        """,
                        {
                            "customer_id": int(customer_id),
                            "name": name,
                            "email": email,
                            "phone": phone,
                            "address": address,
                        },
                    )
                    flash("Customer updated successfully.", "success")
                else:
                    cursor.execute(
                        """
                        INSERT INTO customer (customer_id, name, email, phone, address)
                        VALUES (customer_seq.NEXTVAL, :name, :email, :phone, :address)
                        """,
                        {"name": name, "email": email, "phone": phone, "address": address},
                    )
                    flash("Customer registered successfully.", "success")
        except oracledb.IntegrityError:
            flash("The email address already exists or the customer is referenced by orders.", "error")

        return redirect(url_for("customers"))

    edit_id = request.args.get("edit_id", type=int)
    customers_list = fetch_all(
        """
        SELECT customer_id, name, email, phone, address
          FROM customer
      ORDER BY customer_id DESC
        """
    )
    edit_customer = None
    if edit_id:
        edit_customer = fetch_one(
            """
            SELECT customer_id, name, email, phone, address
              FROM customer
             WHERE customer_id = :customer_id
            """,
            {"customer_id": edit_id},
        )
    return render_template(
        "customer.html",
        active_page="customers",
        page_title="Customer Management",
        customers=customers_list,
        edit_customer=edit_customer,
    )


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    if fetch_scalar("SELECT COUNT(*) AS total_count FROM orders WHERE customer_id = :customer_id", {"customer_id": customer_id}, 0) > 0:
        flash("Cannot delete a customer who already has orders.", "error")
        return redirect(url_for("customers"))

    with db_session(commit=True) as cursor:
        cursor.execute("DELETE FROM customer WHERE customer_id = :customer_id", {"customer_id": customer_id})

    flash("Customer deleted successfully.", "success")
    return redirect(url_for("customers"))


@app.route("/categories", methods=["GET", "POST"])
def categories():
    if request.method == "POST":
        category_id = request.form.get("category_id")
        category_name = request.form.get("category_name", "").strip()
        description = request.form.get("description", "").strip()

        if not category_name:
            flash("Category name is required.", "error")
            return redirect(url_for("categories", edit_id=category_id or None))

        try:
            with db_session(commit=True) as cursor:
                if category_id:
                    cursor.execute(
                        """
                        UPDATE category
                           SET category_name = :category_name,
                               description = :description
                         WHERE category_id = :category_id
                        """,
                        {
                            "category_id": int(category_id),
                            "category_name": category_name,
                            "description": description,
                        },
                    )
                    flash("Category updated successfully.", "success")
                else:
                    cursor.execute(
                        """
                        INSERT INTO category (category_id, category_name, description)
                        VALUES (category_seq.NEXTVAL, :category_name, :description)
                        """,
                        {"category_name": category_name, "description": description},
                    )
                    flash("Category added successfully.", "success")
        except oracledb.IntegrityError:
            flash("Category name already exists or the category is still referenced by products.", "error")

        return redirect(url_for("categories"))

    edit_id = request.args.get("edit_id", type=int)
    categories_list = fetch_all(
        """
        SELECT category_id, category_name, description
          FROM category
      ORDER BY category_id DESC
        """
    )
    edit_category = None
    if edit_id:
        edit_category = fetch_one(
            """
            SELECT category_id, category_name, description
              FROM category
             WHERE category_id = :category_id
            """,
            {"category_id": edit_id},
        )
    return render_template(
        "category.html",
        active_page="categories",
        page_title="Category Management",
        categories=categories_list,
        edit_category=edit_category,
    )


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    if fetch_scalar("SELECT COUNT(*) AS total_count FROM product WHERE category_id = :category_id", {"category_id": category_id}, 0) > 0:
        flash("Cannot delete a category that has products.", "error")
        return redirect(url_for("categories"))

    with db_session(commit=True) as cursor:
        cursor.execute("DELETE FROM category WHERE category_id = :category_id", {"category_id": category_id})

    flash("Category deleted successfully.", "success")
    return redirect(url_for("categories"))


@app.route("/products", methods=["GET", "POST"])
def products():
    categories_list = fetch_all("SELECT category_id, category_name FROM category ORDER BY category_name")

    if request.method == "POST":
        product_id = request.form.get("product_id")
        product_name = request.form.get("product_name", "").strip()
        price_raw = request.form.get("price", "").strip()
        stock_raw = request.form.get("stock", "").strip()
        category_id_raw = request.form.get("category_id")

        errors = []
        if not product_name:
            errors.append("Product name is required.")

        price, error = parse_decimal(price_raw, "Price", Decimal("0"))
        if error:
            errors.append(error)

        stock, error = parse_int(stock_raw, "Stock", 0)
        if error:
            errors.append(error)

        category_id, error = parse_int(category_id_raw, "Category", 1)
        if error:
            errors.append(error)
        elif not category_exists(category_id):
            errors.append("Selected category does not exist.")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("products", edit_id=product_id or None))

        try:
            with db_session(commit=True) as cursor:
                if product_id:
                    cursor.execute(
                        """
                        UPDATE product
                           SET product_name = :product_name,
                               price = :price,
                               stock = :stock,
                               category_id = :category_id
                         WHERE product_id = :product_id
                        """,
                        {
                            "product_id": int(product_id),
                            "product_name": product_name,
                            "price": price,
                            "stock": stock,
                            "category_id": category_id,
                        },
                    )
                    flash("Product updated successfully.", "success")
                else:
                    cursor.execute(
                        """
                        INSERT INTO product (product_id, product_name, price, stock, category_id)
                        VALUES (product_seq.NEXTVAL, :product_name, :price, :stock, :category_id)
                        """,
                        {
                            "product_name": product_name,
                            "price": price,
                            "stock": stock,
                            "category_id": category_id,
                        },
                    )
                    flash("Product added successfully.", "success")
        except oracledb.IntegrityError:
            flash("Unable to save the product because of a database constraint.", "error")

        return redirect(url_for("products"))

    edit_id = request.args.get("edit_id", type=int)
    products_list = fetch_all(
        """
        SELECT p.product_id,
               p.product_name,
               p.price,
               p.stock,
               p.category_id,
               c.category_name
          FROM product p
          JOIN category c ON c.category_id = p.category_id
      ORDER BY p.product_id DESC
        """
    )
    edit_product = None
    if edit_id:
        edit_product = fetch_one(
            """
            SELECT product_id, product_name, price, stock, category_id
              FROM product
             WHERE product_id = :product_id
            """,
            {"product_id": edit_id},
        )
    return render_template(
        "product.html",
        active_page="products",
        page_title="Product Management",
        products=products_list,
        categories=categories_list,
        edit_product=edit_product,
    )


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    if fetch_scalar("SELECT COUNT(*) AS total_count FROM order_item WHERE product_id = :product_id", {"product_id": product_id}, 0) > 0:
        flash("Cannot delete a product that is already part of an order.", "error")
        return redirect(url_for("products"))

    with db_session(commit=True) as cursor:
        cursor.execute("DELETE FROM product WHERE product_id = :product_id", {"product_id": product_id})

    flash("Product deleted successfully.", "success")
    return redirect(url_for("products"))


@app.route("/orders", methods=["GET"])
def orders():
    orders_list = fetch_all(
        """
        SELECT o.order_id,
               TO_CHAR(o.order_date, 'YYYY-MM-DD') AS order_date,
               o.total_amount,
               c.customer_id,
               c.name AS customer_name,
               NVL(p.payment_status, 'Unpaid') AS payment_status,
               COUNT(oi.order_item_id) AS item_count
          FROM orders o
          JOIN customer c ON c.customer_id = o.customer_id
     LEFT JOIN order_item oi ON oi.order_id = o.order_id
     LEFT JOIN payment p ON p.order_id = o.order_id
      GROUP BY o.order_id, o.order_date, o.total_amount, c.customer_id, c.name, p.payment_status
      ORDER BY o.order_date DESC, o.order_id DESC
        """
    )
    customers_list = fetch_all("SELECT customer_id, name FROM customer ORDER BY name")
    products_list = fetch_all(
        """
        SELECT p.product_id,
               p.product_name,
               p.price,
               p.stock,
               c.category_name
          FROM product p
          JOIN category c ON c.category_id = p.category_id
      ORDER BY p.product_name
        """
    )

    selected_order_id = request.args.get("order_id", type=int)
    if selected_order_id is None and orders_list:
        selected_order_id = orders_list[0]["order_id"]

    selected_order = None
    selected_items = []
    if selected_order_id and order_exists(selected_order_id):
        selected_order = fetch_one(
            """
            SELECT o.order_id,
                   TO_CHAR(o.order_date, 'YYYY-MM-DD') AS order_date,
                   o.total_amount,
                   c.customer_id,
                   c.name AS customer_name,
                   c.email,
                   c.phone,
                   c.address,
                   NVL(p.payment_status, 'Pending') AS payment_status,
                   NVL(p.payment_method, 'N/A') AS payment_method,
                   NVL(p.amount, 0) AS payment_amount
              FROM orders o
              JOIN customer c ON c.customer_id = o.customer_id
         LEFT JOIN payment p ON p.order_id = o.order_id
             WHERE o.order_id = :order_id
            """,
            {"order_id": selected_order_id},
        )
        selected_items = fetch_all(
            """
            SELECT oi.order_item_id,
                   oi.order_id,
                   oi.product_id,
                   pr.product_name,
                   pr.price,
                   oi.quantity,
                   oi.subtotal,
                   c.category_name,
                   pr.stock
              FROM order_item oi
              JOIN product pr ON pr.product_id = oi.product_id
              JOIN category c ON c.category_id = pr.category_id
             WHERE oi.order_id = :order_id
          ORDER BY oi.order_item_id
            """,
            {"order_id": selected_order_id},
        )

    return render_template(
        "order.html",
        active_page="orders",
        page_title="Order Management",
        orders=orders_list,
        customers=customers_list,
        products=products_list,
        selected_order=selected_order,
        selected_items=selected_items,
        selected_order_id=selected_order_id,
        payment_methods=PAYMENT_METHODS,
    )


@app.route("/orders/create", methods=["POST"])
def create_order():
    customer_id_raw = request.form.get("customer_id")
    customer_id, error = parse_int(customer_id_raw, "Customer", 1)
    if error:
        flash(error, "error")
        return redirect(url_for("orders"))
    if not customer_exists(customer_id):
        flash("Selected customer does not exist.", "error")
        return redirect(url_for("orders"))

    with db_session(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO orders (order_id, order_date, total_amount, customer_id)
            VALUES (order_seq.NEXTVAL, SYSDATE, 0, :customer_id)
            """,
            {"customer_id": customer_id},
        )
        cursor.execute("SELECT order_seq.CURRVAL AS order_id FROM dual")
        new_order_id = int(cursor.fetchone()[0])

    flash("Order created successfully.", "success")
    return redirect(url_for("orders", order_id=new_order_id))


@app.route("/orders/<int:order_id>/items", methods=["POST"])
def add_order_item(order_id):
    if not order_exists(order_id):
        flash("The selected order does not exist.", "error")
        return redirect(url_for("orders"))

    product_id_raw = request.form.get("product_id")
    quantity_raw = request.form.get("quantity")
    product_id, error = parse_int(product_id_raw, "Product", 1)
    if error:
        flash(error, "error")
        return redirect(url_for("orders", order_id=order_id))
    quantity, error = parse_int(quantity_raw, "Quantity", 1)
    if error:
        flash(error, "error")
        return redirect(url_for("orders", order_id=order_id))

    try:
        with db_session(commit=True) as cursor:
            cursor.execute(
                """
                SELECT price, stock
                  FROM product
                 WHERE product_id = :product_id
                 FOR UPDATE
                """,
                {"product_id": product_id},
            )
            product_row = cursor.fetchone()
            if not product_row:
                flash("Selected product does not exist.", "error")
                return redirect(url_for("orders", order_id=order_id))

            price, stock = product_row
            cursor.execute(
                """
                SELECT order_item_id, quantity
                  FROM order_item
                 WHERE order_id = :order_id
                   AND product_id = :product_id
                """,
                {"order_id": order_id, "product_id": product_id},
            )
            existing_item = cursor.fetchone()

            if existing_item:
                current_quantity = int(existing_item[1])
                new_quantity = current_quantity + quantity
                if stock < quantity:
                    flash("Not enough stock to add the requested quantity.", "error")
                    return redirect(url_for("orders", order_id=order_id))

                cursor.execute(
                    """
                    UPDATE order_item
                       SET quantity = :quantity,
                           subtotal = :subtotal
                     WHERE order_item_id = :order_item_id
                    """,
                    {
                        "quantity": new_quantity,
                        "subtotal": Decimal(str(price)) * Decimal(new_quantity),
                        "order_item_id": existing_item[0],
                    },
                )
                cursor.execute(
                    """
                    UPDATE product
                       SET stock = stock - :quantity
                     WHERE product_id = :product_id
                    """,
                    {"quantity": quantity, "product_id": product_id},
                )
            else:
                if stock < quantity:
                    flash("Not enough stock to place this item on the order.", "error")
                    return redirect(url_for("orders", order_id=order_id))

                cursor.execute(
                    """
                    INSERT INTO order_item (order_item_id, order_id, product_id, quantity, subtotal)
                    VALUES (order_item_seq.NEXTVAL, :order_id, :product_id, :quantity, :subtotal)
                    """,
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "quantity": quantity,
                        "subtotal": Decimal(str(price)) * Decimal(quantity),
                    },
                )

            recalculate_order_total(cursor, order_id)
    except oracledb.Error:
        flash("Unable to add the product to the order.", "error")
        return redirect(url_for("orders", order_id=order_id))

    flash("Product added to order successfully.", "success")
    return redirect(url_for("orders", order_id=order_id))


@app.route("/order-items/<int:item_id>/update", methods=["POST"])
def update_order_item(item_id):
    quantity_raw = request.form.get("quantity")
    quantity, error = parse_int(quantity_raw, "Quantity", 1)
    if error:
        flash(error, "error")
        return redirect(url_for("orders"))

    with db_session(commit=True) as cursor:
        cursor.execute(
            """
            SELECT oi.order_id,
                   oi.product_id,
                   oi.quantity,
                   p.price,
                   p.stock
              FROM order_item oi
              JOIN product p ON p.product_id = oi.product_id
             WHERE oi.order_item_id = :item_id
             FOR UPDATE
            """,
            {"item_id": item_id},
        )
        row = cursor.fetchone()
        if not row:
            flash("Order item not found.", "error")
            return redirect(url_for("orders"))

        order_id, product_id, current_quantity, price, stock = row
        current_quantity = int(current_quantity)
        delta = quantity - current_quantity

        if delta > 0 and stock < delta:
            flash("Not enough stock to increase the quantity.", "error")
            return redirect(url_for("orders", order_id=order_id))

        if delta > 0:
            cursor.execute(
                "UPDATE product SET stock = stock - :delta WHERE product_id = :product_id",
                {"delta": delta, "product_id": product_id},
            )
        elif delta < 0:
            cursor.execute(
                "UPDATE product SET stock = stock + :delta WHERE product_id = :product_id",
                {"delta": abs(delta), "product_id": product_id},
            )

        cursor.execute(
            """
            UPDATE order_item
               SET quantity = :quantity,
                   subtotal = :subtotal
             WHERE order_item_id = :item_id
            """,
            {"quantity": quantity, "subtotal": Decimal(str(price)) * Decimal(quantity), "item_id": item_id},
        )
        recalculate_order_total(cursor, order_id)

    flash("Order item quantity updated successfully.", "success")
    return redirect(url_for("orders", order_id=order_id))


@app.route("/order-items/<int:item_id>/delete", methods=["POST"])
def delete_order_item(item_id):
    with db_session(commit=True) as cursor:
        cursor.execute(
            """
            SELECT order_id, product_id, quantity
              FROM order_item
             WHERE order_item_id = :item_id
             FOR UPDATE
            """,
            {"item_id": item_id},
        )
        row = cursor.fetchone()
        if not row:
            flash("Order item not found.", "error")
            return redirect(url_for("orders"))

        order_id, product_id, quantity = row
        cursor.execute(
            "UPDATE product SET stock = stock + :quantity WHERE product_id = :product_id",
            {"quantity": int(quantity), "product_id": product_id},
        )
        cursor.execute("DELETE FROM order_item WHERE order_item_id = :item_id", {"item_id": item_id})
        recalculate_order_total(cursor, order_id)

    flash("Order item removed successfully.", "success")
    return redirect(url_for("orders", order_id=order_id))


@app.route("/orders/<int:order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    if not order_exists(order_id):
        flash("The selected order does not exist.", "error")
        return redirect(url_for("orders"))

    items = fetch_all(
        "SELECT product_id, quantity FROM order_item WHERE order_id = :order_id",
        {"order_id": order_id},
    )

    with db_session(commit=True) as cursor:
        for item in items:
            cursor.execute(
                "UPDATE product SET stock = stock + :quantity WHERE product_id = :product_id",
                {"quantity": int(item["quantity"]), "product_id": item["product_id"]},
            )
        cursor.execute("DELETE FROM payment WHERE order_id = :order_id", {"order_id": order_id})
        cursor.execute("DELETE FROM orders WHERE order_id = :order_id", {"order_id": order_id})

    flash("Order cancelled successfully.", "success")
    return redirect(url_for("orders"))


@app.route("/payments", methods=["GET"])
def payments():
    payments_list = fetch_all(
        """
        SELECT p.payment_id,
               p.order_id,
               o.total_amount,
               c.name AS customer_name,
               p.payment_method,
               p.amount,
               p.payment_status
          FROM payment p
          JOIN orders o ON o.order_id = p.order_id
          JOIN customer c ON c.customer_id = o.customer_id
      ORDER BY p.payment_id DESC
        """
    )
    orders_list = fetch_all(
        """
        SELECT o.order_id,
               o.total_amount,
               c.name AS customer_name,
               NVL(p.payment_status, 'Unpaid') AS payment_status
          FROM orders o
          JOIN customer c ON c.customer_id = o.customer_id
     LEFT JOIN payment p ON p.order_id = o.order_id
      ORDER BY o.order_id DESC
        """
    )
    selected_order_id = request.args.get("order_id", type=int)
    selected_order = None
    if selected_order_id and order_exists(selected_order_id):
        selected_order = fetch_one(
            """
            SELECT o.order_id,
                   o.total_amount,
                   c.name AS customer_name,
                   c.email,
                   c.phone,
                   NVL(p.payment_method, 'Cash') AS payment_method,
                   NVL(p.payment_status, 'Pending') AS payment_status,
                   NVL(p.amount, o.total_amount) AS amount
              FROM orders o
              JOIN customer c ON c.customer_id = o.customer_id
         LEFT JOIN payment p ON p.order_id = o.order_id
             WHERE o.order_id = :order_id
            """,
            {"order_id": selected_order_id},
        )
    elif orders_list:
        selected_order = orders_list[0]
        selected_order_id = selected_order["order_id"]

    return render_template(
        "payment.html",
        active_page="payments",
        page_title="Payment Management",
        payments=payments_list,
        orders=orders_list,
        selected_order=selected_order,
        payment_methods=PAYMENT_METHODS,
        payment_statuses=PAYMENT_STATUSES,
    )


@app.route("/payments/make", methods=["POST"])
def make_payment():
    order_id_raw = request.form.get("order_id")
    payment_method = request.form.get("payment_method", "").strip()
    payment_status = request.form.get("payment_status", "").strip()

    order_id, error = parse_int(order_id_raw, "Order", 1)
    if error:
        flash(error, "error")
        return redirect(url_for("payments"))
    if not order_exists(order_id):
        flash("Selected order does not exist.", "error")
        return redirect(url_for("payments"))
    if payment_method not in PAYMENT_METHODS:
        flash("Please choose a valid payment method.", "error")
        return redirect(url_for("payments", order_id=order_id))
    if payment_status not in PAYMENT_STATUSES:
        flash("Please choose a valid payment status.", "error")
        return redirect(url_for("payments", order_id=order_id))

    total_amount = fetch_scalar("SELECT total_amount FROM orders WHERE order_id = :order_id", {"order_id": order_id}, Decimal("0"))

    with db_session(commit=True) as cursor:
        cursor.execute("SELECT payment_id FROM payment WHERE order_id = :order_id", {"order_id": order_id})
        existing_payment = cursor.fetchone()
        if existing_payment:
            cursor.execute(
                """
                UPDATE payment
                   SET payment_method = :payment_method,
                       amount = :amount,
                       payment_status = :payment_status
                 WHERE order_id = :order_id
                """,
                {
                    "payment_method": payment_method,
                    "amount": total_amount,
                    "payment_status": payment_status,
                    "order_id": order_id,
                },
            )
        else:
            cursor.execute(
                """
                INSERT INTO payment (payment_id, order_id, payment_method, amount, payment_status)
                VALUES (payment_seq.NEXTVAL, :order_id, :payment_method, :amount, :payment_status)
                """,
                {
                    "order_id": order_id,
                    "payment_method": payment_method,
                    "amount": total_amount,
                    "payment_status": payment_status,
                },
            )

    flash("Payment saved successfully.", "success")
    return redirect(url_for("payments", order_id=order_id))


@app.route("/orders/<int:order_id>/summary")
def order_summary(order_id):
    if not order_exists(order_id):
        flash("The selected order does not exist.", "error")
        return redirect(url_for("orders"))

    summary = None
    items = []

    try:
        # Call the stored procedure sp_get_order_summary
        connection = connect_db()
        cursor = connection.cursor()
        ref_cursor = connection.cursor()
        
        cursor.callproc("sp_get_order_summary", [order_id, ref_cursor])
        
        columns = [col[0].lower() for col in ref_cursor.description]
        results = [dict(zip(columns, row)) for row in ref_cursor.fetchall()]
        
        ref_cursor.close()
        cursor.close()
        connection.close()

        if results:
            first = results[0]
            summary = {
                "order_id": first["order_id"],
                "order_date": first["order_date"],
                "total_amount": first["total_amount"],
                "customer_id": first["customer_id"],
                "customer_name": first["customer_name"],
                "email": first["email"],
                "phone": first["phone"],
                "address": first["address"],
                "payment_method": first.get("payment_method") or "N/A",
                "payment_status": first.get("payment_status") or "Pending",
                "payment_amount": first.get("payment_amount") or 0,
            }
            for r in results:
                if r.get("product_name"):
                    items.append({
                        "product_name": r["product_name"],
                        "category_name": r.get("category_name") or "General",
                        "price": r["price"],
                        "quantity": r["quantity"],
                        "subtotal": r["subtotal"]
                    })
    except Exception:
        # Fallback to standard SQL queries if stored procedure fails or is not compiled
        pass

    # If results is empty or stored procedure fails, fetch using queries as fallback
    if not summary:
        summary = fetch_one(
            """
            SELECT o.order_id,
                   TO_CHAR(o.order_date, 'YYYY-MM-DD') AS order_date,
                   o.total_amount,
                   c.customer_id,
                   c.name AS customer_name,
                   c.email,
                   c.phone,
                   c.address,
                   NVL(p.payment_method, 'N/A') AS payment_method,
                   NVL(p.payment_status, 'Pending') AS payment_status,
                   NVL(p.amount, 0) AS payment_amount
              FROM orders o
              JOIN customer c ON c.customer_id = o.customer_id
         LEFT JOIN payment p ON p.order_id = o.order_id
             WHERE o.order_id = :order_id
            """,
            {"order_id": order_id},
        )
        items = fetch_all(
            """
            SELECT oi.order_item_id,
                   pr.product_name,
                   c.category_name,
                   pr.price,
                   oi.quantity,
                   oi.subtotal
              FROM order_item oi
              JOIN product pr ON pr.product_id = oi.product_id
              JOIN category c ON c.category_id = pr.category_id
             WHERE oi.order_id = :order_id
          ORDER BY oi.order_item_id
            """,
            {"order_id": order_id},
        )

    return render_template(
        "order_summary.html",
        active_page="orders",
        page_title="Order Summary",
        summary=summary,
        items=items,
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
