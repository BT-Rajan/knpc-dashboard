CREATE DATABASE IF NOT EXISTS knpc_dashboard CHARACTER SET utf8mb4;
USE knpc_dashboard;

CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(40) NOT NULL,
    unit VARCHAR(40) DEFAULT 'USD/bbl',
    active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    name VARCHAR(120) NOT NULL,
    url VARCHAR(500) NOT NULL,
    source_type VARCHAR(20) NOT NULL DEFAULT 'css',
    value_selector VARCHAR(500) NOT NULL,
    news_selector VARCHAR(500),
    priority INT DEFAULT 1,
    active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    source_id INT,
    price_date DATE NOT NULL,
    price DOUBLE NOT NULL,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_item_price_date (item_id, price_date),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS news_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT,
    headline VARCHAR(500) NOT NULL,
    url VARCHAR(700),
    source VARCHAR(120),
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_headline_item (headline, item_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS scrape_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    item_code VARCHAR(40),
    source_name VARCHAR(120),
    status VARCHAR(20) NOT NULL,
    message TEXT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS scrape_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    frequency_minutes INT DEFAULT 30,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ai_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deepseek_api_key VARCHAR(200),
    claude_api_key VARCHAR(200),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
