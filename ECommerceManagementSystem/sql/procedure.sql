CREATE OR REPLACE PROCEDURE sp_get_order_summary (
    p_order_id IN NUMBER,
    p_result OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_result FOR
        SELECT
            o.order_id,
            TO_CHAR(o.order_date, 'YYYY-MM-DD') AS order_date,
            o.total_amount,
            c.customer_id,
            c.name AS customer_name,
            c.email,
            c.phone,
            c.address,
            p.product_id,
            p.product_name,
            p.price,
            oi.quantity,
            oi.subtotal,
            pay.payment_id,
            pay.payment_method,
            pay.amount AS payment_amount,
            pay.payment_status
        FROM orders o
        JOIN customer c
            ON c.customer_id = o.customer_id
        JOIN order_item oi
            ON oi.order_id = o.order_id
        JOIN product p
            ON p.product_id = oi.product_id
        LEFT JOIN payment pay
            ON pay.order_id = o.order_id
        WHERE o.order_id = p_order_id
        ORDER BY oi.order_item_id;
END;
/
