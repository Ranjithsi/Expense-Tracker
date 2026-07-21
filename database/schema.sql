-- ============================================================
-- Expense Tracker - MySQL Database Schema
-- ============================================================
-- Run:  mysql -u root -p < database/schema.sql
-- (Or let SQLAlchemy's db.create_all() generate these tables
--  automatically the first time app.py is run.)
-- ============================================================

CREATE DATABASE IF NOT EXISTS expense_tracker
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE expense_tracker;

-- ------------------------------------------------------------
-- users
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(120),
  monthly_budget DECIMAL(12,2) DEFAULT 0,
  dark_mode BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- categories  (global defaults have user_id = NULL)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  type VARCHAR(10) NOT NULL,          -- 'income' or 'expense'
  icon VARCHAR(50) DEFAULT 'bi-tag',
  is_default BOOLEAN DEFAULT TRUE,
  user_id INT NULL,
  UNIQUE KEY uq_category_name_type_user (name, type, user_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- income
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS income (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  category_id INT NOT NULL,
  title VARCHAR(120) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  date DATE NOT NULL,
  notes VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- expenses
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  category_id INT NOT NULL,
  title VARCHAR(120) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  date DATE NOT NULL,
  notes VARCHAR(255),
  receipt_image VARCHAR(255),
  is_recurring BOOLEAN DEFAULT FALSE,
  recurring_frequency VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Seed default categories (global, user_id = NULL)
-- ------------------------------------------------------------
INSERT IGNORE INTO categories (name, type, icon, is_default, user_id) VALUES
  ('Food', 'expense', 'bi-cup-hot', TRUE, NULL),
  ('Transport', 'expense', 'bi-bus-front', TRUE, NULL),
  ('Shopping', 'expense', 'bi-bag', TRUE, NULL),
  ('Bills', 'expense', 'bi-receipt', TRUE, NULL),
  ('Entertainment', 'expense', 'bi-film', TRUE, NULL),
  ('Healthcare', 'expense', 'bi-heart-pulse', TRUE, NULL),
  ('Education', 'expense', 'bi-book', TRUE, NULL),
  ('Others', 'expense', 'bi-three-dots', TRUE, NULL),
  ('Salary', 'income', 'bi-cash-stack', TRUE, NULL),
  ('Freelance', 'income', 'bi-laptop', TRUE, NULL),
  ('Business', 'income', 'bi-briefcase', TRUE, NULL),
  ('Investment', 'income', 'bi-graph-up-arrow', TRUE, NULL),
  ('Gift', 'income', 'bi-gift', TRUE, NULL),
  ('Others', 'income', 'bi-three-dots', TRUE, NULL);
