CREATE OR REPLACE TRIGGER trg_update_stock_on_order
AFTER INSERT ON order_item
FOR EACH ROW
BEGIN
    UPDATE product
    SET stock = stock - :NEW.quantity
    WHERE product_id = :NEW.product_id;
END;
/
