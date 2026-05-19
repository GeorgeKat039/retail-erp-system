-- =========================
-- STORES
-- =========================
INSERT INTO stores (store_name, store_location) VALUES
('Athens Central', 'Athens'),
('Piraeus Store', 'Piraeus'),
('Thessaloniki Center', 'Thessaloniki'),
('Patras Store', 'Patras');

-- =========================
-- USERS
-- =========================
INSERT INTO users (store_id, username, password, role) VALUES
(1, 'manager_athens', '1234', 'manager'),
(1, 'assistant_athens', '1234', 'assistant'),
(2, 'manager_piraeus', '1234', 'manager'),
(2, 'assistant_piraeus', '1234', 'assistant'),
(3, 'manager_thess', '1234', 'manager'),
(4, 'manager_patras', '1234', 'manager');

-- =========================
-- PRODUCTS
-- =========================
INSERT INTO products (product_name, product_category, product_price) VALUES
('Milk 1L', 'Dairy', 1.20),
('Bread White', 'Bakery', 0.80),
('Eggs 12pcs', 'Dairy', 2.50),
('Coca Cola 1.5L', 'Beverages', 1.50),
('Orange Juice', 'Beverages', 2.00),
('Cheese Feta', 'Dairy', 5.00),
('Chicken Breast', 'Meat', 6.50),
('Pasta', 'Grocery', 1.10),
('Rice', 'Grocery', 1.30),
('Apples', 'Fruits', 2.20);

-- =========================
-- WAREHOUSE STOCK
-- =========================
INSERT INTO warehouse_stock (product_id, quantity) VALUES
(1, 500),
(2, 600),
(3, 400),
(4, 800),
(5, 300),
(6, 200),
(7, 250),
(8, 700),
(9, 650),
(10, 450);

-- =========================
-- STORE STOCK
-- =========================
INSERT INTO store_stock (store_id, product_id, quantity) VALUES
(1, 1, 50),
(1, 2, 70),
(1, 3, 30),
(2, 1, 40),
(2, 4, 60),
(2, 5, 20),
(3, 2, 80),
(3, 6, 25),
(3, 7, 15),
(4, 8, 90),
(4, 9, 100),
(4, 10, 60);

-- =========================
-- ORDERS
-- =========================
INSERT INTO orders (store_id, order_date, order_status) VALUES
(1, '2026-04-01', 'draft'),
(2, '2026-04-01', 'submitted'),
(3, '2026-04-02', 'draft');

-- =========================
-- ORDER ITEMS
-- =========================
INSERT INTO order_items (order_id, product_id, quantity) VALUES
(1, 1, 20),
(1, 2, 30),
(2, 4, 50),
(2, 5, 40),
(3, 6, 10),
(3, 7, 15);