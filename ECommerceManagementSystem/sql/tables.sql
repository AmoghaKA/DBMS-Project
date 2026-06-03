BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE payment CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE order_item CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE orders CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE product CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE category CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE customer CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

CREATE TABLE customer (
    customer_id NUMBER PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    email VARCHAR2(150) NOT NULL,
    phone VARCHAR2(20) NOT NULL,
    address VARCHAR2(255) NOT NULL,
    CONSTRAINT uq_customer_email UNIQUE (email)
);

CREATE TABLE category (
    category_id NUMBER PRIMARY KEY,
    category_name VARCHAR2(100) NOT NULL,
    description VARCHAR2(255),
    CONSTRAINT uq_category_name UNIQUE (category_name)
);

CREATE TABLE product (
    product_id NUMBER PRIMARY KEY,
    product_name VARCHAR2(150) NOT NULL,
    price NUMBER(12,2) NOT NULL,
    stock NUMBER NOT NULL,
    category_id NUMBER,
    CONSTRAINT fk_product_category FOREIGN KEY (category_id)
        REFERENCES category (category_id)
        ON DELETE SET NULL,
    CONSTRAINT chk_product_price CHECK (price >= 0),
    CONSTRAINT chk_product_stock CHECK (stock >= 0)
);

CREATE TABLE orders (
    order_id NUMBER PRIMARY KEY,
    order_date DATE DEFAULT SYSDATE NOT NULL,
    total_amount NUMBER(12,2) DEFAULT 0 NOT NULL,
    customer_id NUMBER NOT NULL,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customer (customer_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_orders_total CHECK (total_amount >= 0)
);

CREATE TABLE order_item (
    order_item_id NUMBER PRIMARY KEY,
    order_id NUMBER NOT NULL,
    product_id NUMBER NOT NULL,
    quantity NUMBER NOT NULL,
    subtotal NUMBER(12,2) NOT NULL,
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_order_item_product FOREIGN KEY (product_id)
        REFERENCES product (product_id),
    CONSTRAINT uq_order_item UNIQUE (order_id, product_id),
    CONSTRAINT chk_order_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_item_subtotal CHECK (subtotal >= 0)
);

CREATE TABLE payment (
    payment_id NUMBER PRIMARY KEY,
    order_id NUMBER NOT NULL,
    payment_method VARCHAR2(50) NOT NULL,
    amount NUMBER(12,2) NOT NULL,
    payment_status VARCHAR2(20) NOT NULL,
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_payment_order UNIQUE (order_id),
    CONSTRAINT chk_payment_amount CHECK (amount >= 0),
    CONSTRAINT chk_payment_status CHECK (payment_status IN ('Pending', 'Completed', 'Failed', 'Refunded'))
);
