-- Создание базы данных
CREATE DATABASE IF NOT EXISTS accounting_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE accounting_system;

-- Таблица сотрудников
CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    telegram VARCHAR(50),
    salary_percent DECIMAL(5,2) DEFAULT 10.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Таблица аккаунтов
CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform ENUM('bybit', 'htx', 'bliss', 'gate') NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    employee_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
);

-- Таблица отчетов
CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_date DATE NOT NULL,
    shift_type ENUM('morning', 'evening') NOT NULL,
    dokidka_amount DECIMAL(10,2) DEFAULT 0.00,
    internal_transfer_amount DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Таблица балансов аккаунтов
CREATE TABLE account_balances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_id INT NOT NULL,
    account_id INT NOT NULL,
    start_balance DECIMAL(10,2) DEFAULT 0.00,
    end_balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

-- Вставка тестовых данных
INSERT INTO employees (name, telegram, salary_percent) VALUES
('Иван Иванов', '@ivan_trader', 12.5),
('Мария Петрова', '@maria_crypto', 10.0),
('Алексей Сидоров', '@alex_arbitrage', 15.0);

INSERT INTO accounts (platform, account_name, employee_id) VALUES
('bybit', 'Main Account', 1),
('htx', 'Trading Account', 1),
('bliss', 'Arbitrage Account', 2),
('gate', 'Secondary Account', 2),
('bybit', 'Pro Account', 3);

INSERT INTO reports (employee_id, shift_date, shift_type, dokidka_amount, internal_transfer_amount) VALUES
(1, '2024-01-15', 'morning', 100.50, 50.00),
(2, '2024-01-15', 'evening', 75.25, 25.00),
(3, '2024-01-16', 'morning', 200.00, 100.00);

INSERT INTO account_balances (report_id, account_id, start_balance, end_balance) VALUES
(1, 1, 1000.00, 1150.50),
(1, 2, 500.00, 525.00),
(2, 3, 800.00, 875.25),
(2, 4, 300.00, 325.00),
(3, 5, 1500.00, 1700.00);

-- Создание индексов для оптимизации
CREATE INDEX idx_reports_date ON reports(shift_date);
CREATE INDEX idx_reports_employee ON reports(employee_id);
CREATE INDEX idx_accounts_platform ON accounts(platform);
CREATE INDEX idx_balances_report ON account_balances(report_id);
CREATE INDEX idx_balances_account ON account_balances(account_id); 