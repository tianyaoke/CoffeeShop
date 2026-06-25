CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    username VARCHAR(20)NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS coffee_items(
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(8,2) NOT NULL CHECK (price >=0),
    category VARCHAR(50),
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS orders(
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN('pending', 'confirmed', 'ready', 'completed', 'cancelled')),
    total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >=0),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS order_items(
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    item_id INT REFERENCES coffee_items(item_id) ON DELETE SET NULL,
    item_name VARCHAR(100) NOT NULL,
    unit_price NUMERIC(8,2) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0)
);
INSERT INTO coffee_items (name, description, price, category, image_url, is_available)
VALUES
  ('Cappuccino', 'Rich espresso topped with smooth steamed milk foam.', 250.00, 'coffee', 'images/cappuccino.jpg', TRUE),
  ('Iced Latte', 'Cool, creamy, and refreshing coffee served over ice.', 280.00, 'coffee', 'images/iced-latte.jpg', TRUE),
  ('Americano', 'Simple black coffee with a bold taste.', 200.00, 'coffee', 'images/americano.jpg', TRUE),
  ('Milkshake', 'Sweet and creamy milkshake served chilled.', 300.00, 'beverages', 'images/milkshake.jpg', TRUE),
  ('Mojito', 'Refreshing mint and lime drink served cold.', 280.00, 'beverages', 'images/mojito.jpg', TRUE),
  ('Hot Chocolate', 'Warm chocolate drink with a smooth creamy taste.', 250.00, 'beverages', 'images/hot-chocolate.jpg', TRUE),
  ('Croissant', 'Freshly baked, soft inside, and golden outside.', 220.00, 'pastry', 'images/croissant.jpg', TRUE),
  ('Chocolate Muffin', 'Soft muffin with rich chocolate flavor.', 180.00, 'pastry', 'images/chocolate-muffin.jpg', TRUE),
  ('Chicken Sandwich', 'Fresh sandwich with chicken and vegetables.', 350.00, 'snacks', 'images/chicken-sandwich.jpg', TRUE),
  ('Cinnamon Roll', 'Sweet rolled pastry with cinnamon and icing.', 250.00, 'pastry', 'images/cinnamon-roll.jpg', TRUE),
  ('Garlic Bread', 'Toasted bread with garlic butter and herbs.', 180.00, 'snacks', 'images/garlic-bread.jpg', TRUE),
  ('Chicken Pie', 'Flaky pastry filled with warm seasoned chicken.', 300.00, 'snacks', 'images/chicken-pie.jpg', TRUE);

ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'customer';
UPDATE users SET role = 'admin' WHERE email = 'admin@dailybrew.com';

-- Standardize categories to match frontend filters
UPDATE coffee_items SET category = 'coffee' WHERE LOWER(category) IN ('coffee', 'hot coffee', 'cold coffee');
UPDATE coffee_items SET category = 'beverages' WHERE LOWER(category) IN ('beverages', 'drinks', 'cold drinks');
UPDATE coffee_items SET category = 'pastry' WHERE LOWER(category) IN ('pastry', 'pastries', 'bakery');
UPDATE coffee_items SET category = 'snacks' WHERE LOWER(category) IN ('snacks', 'snack', 'food');

-- Prepend path syntax matching your database image format layout if missing
UPDATE coffee_items 
SET image_url = 'images/' || image_url 
WHERE image_url NOT LIKE 'images/%';

-- Remove any default constraint that might be forcing 'customer'
ALTER TABLE users ALTER COLUMN role DROP DEFAULT;

-- Now, officially update your specific admin account
UPDATE users SET role = 'admin' WHERE email = 'admin@dailybrew.com';

-- Double check that it actually took
SELECT email, role FROM users WHERE email = 'admin@dailybrew.com';

UPDATE users SET role = 'customer' WHERE role IS NULL;
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'customer';