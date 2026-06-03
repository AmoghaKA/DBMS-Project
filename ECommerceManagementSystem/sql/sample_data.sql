INSERT INTO customer (customer_id, name, email, phone, address)
VALUES (customer_seq.NEXTVAL, 'Aarav Sharma', 'aarav@example.com', '9876543210', '12 Lake Road, Delhi');

INSERT INTO customer (customer_id, name, email, phone, address)
VALUES (customer_seq.NEXTVAL, 'Priya Singh', 'priya@example.com', '9988776655', '44 Park Street, Mumbai');

INSERT INTO category (category_id, category_name, description)
VALUES (category_seq.NEXTVAL, 'Electronics', 'Phones, laptops and gadgets');

INSERT INTO category (category_id, category_name, description)
VALUES (category_seq.NEXTVAL, 'Fashion', 'Clothing and accessories');

INSERT INTO category (category_id, category_name, description)
VALUES (category_seq.NEXTVAL, 'Home Appliances', 'Kitchen and household essentials');

INSERT INTO product (product_id, product_name, price, stock, category_id)
VALUES (product_seq.NEXTVAL, 'Smartphone X', 39999.00, 50, 1);

INSERT INTO product (product_id, product_name, price, stock, category_id)
VALUES (product_seq.NEXTVAL, 'Wireless Headphones', 4999.00, 75, 1);

INSERT INTO product (product_id, product_name, price, stock, category_id)
VALUES (product_seq.NEXTVAL, 'Cotton Jacket', 2599.00, 40, 2);

INSERT INTO product (product_id, product_name, price, stock, category_id)
VALUES (product_seq.NEXTVAL, 'Air Fryer', 8999.00, 25, 3);

INSERT INTO orders (order_id, order_date, total_amount, customer_id)
VALUES (order_seq.NEXTVAL, SYSDATE, 0, 1);

INSERT INTO order_item (order_item_id, order_id, product_id, quantity, subtotal)
VALUES (order_item_seq.NEXTVAL, 1, 1, 1, 39999.00);

INSERT INTO order_item (order_item_id, order_id, product_id, quantity, subtotal)
VALUES (order_item_seq.NEXTVAL, 1, 2, 2, 9998.00);

UPDATE orders
SET total_amount = (
    SELECT NVL(SUM(subtotal), 0)
    FROM order_item
    WHERE order_id = 1
)
WHERE order_id = 1;

INSERT INTO payment (payment_id, order_id, payment_method, amount, payment_status)
VALUES (payment_seq.NEXTVAL, 1, 'Credit Card', 49997.00, 'Completed');

COMMIT;
