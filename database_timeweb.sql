-- Миграция с SQLite на MySQL для Timeweb
-- Создание таблиц для системы бухгалтерии арбитража

-- Таблица сотрудников
CREATE TABLE employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    telegram VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    salary_percent FLOAT
);

-- Таблица аккаунтов
CREATE TABLE account (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    platform VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица отчетов о сменах
CREATE TABLE shift_report (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) NOT NULL,
    total_requests INT DEFAULT 0,
    balances_json TEXT NOT NULL,
    scam_amount DECIMAL(15,2) DEFAULT 0,
    scam_comment TEXT,
    scam_personal BOOLEAN DEFAULT FALSE,
    dokidka_amount DECIMAL(15,2) DEFAULT 0,
    internal_transfer_amount DECIMAL(15,2) DEFAULT 0,
    dokidka_comment TEXT,
    internal_transfer_comment TEXT,
    bybit_file VARCHAR(255),
    htx_file VARCHAR(255),
    bliss_file VARCHAR(255),
    start_photo VARCHAR(255),
    end_photo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    bybit_requests INT DEFAULT 0,
    htx_requests INT DEFAULT 0,
    bliss_requests INT DEFAULT 0,
    bybit_first_trade VARCHAR(100) DEFAULT '',
    bybit_last_trade VARCHAR(100) DEFAULT '',
    htx_first_trade VARCHAR(100) DEFAULT '',
    htx_last_trade VARCHAR(100) DEFAULT '',
    bliss_first_trade VARCHAR(100) DEFAULT '',
    bliss_last_trade VARCHAR(100) DEFAULT '',
    gate_first_trade VARCHAR(100) DEFAULT '',
    gate_last_trade VARCHAR(100) DEFAULT '',
    appeal_amount DECIMAL(15,2) DEFAULT 0,
    appeal_comment TEXT,
    appeal_deducted BOOLEAN DEFAULT FALSE,
    shift_start_time DATETIME,
    shift_end_time DATETIME,
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица деталей ордеров
CREATE TABLE order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_report_id INT NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    total_usdt DECIMAL(15,2) NOT NULL,
    fees_usdt DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    executed_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shift_report_id) REFERENCES shift_report(id)
);

-- Таблица начальных балансов
CREATE TABLE initial_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    balance DECIMAL(15,2) NOT NULL DEFAULT 0
);

-- Таблица истории балансов аккаунтов
CREATE TABLE account_balance_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    account_name VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) NOT NULL,
    balance DECIMAL(15,2) NOT NULL,
    employee_id INT,
    employee_name VARCHAR(100),
    balance_type VARCHAR(10) NOT NULL DEFAULT 'end',
    FOREIGN KEY (account_id) REFERENCES account(id),
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица ордеров
CREATE TABLE `order` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL UNIQUE,
    employee_id INT NOT NULL,
    platform VARCHAR(20) NOT NULL DEFAULT 'bybit',
    account_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,8) NOT NULL,
    total_usdt DECIMAL(15,2) NOT NULL,
    fees_usdt DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    executed_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- Таблица истории скамов сотрудников
CREATE TABLE employee_scam_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_report_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    comment TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee(id),
    FOREIGN KEY (shift_report_id) REFERENCES shift_report(id)
);

-- Таблица настроек зарплаты
CREATE TABLE salary_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    base_percent INT NOT NULL DEFAULT 30,
    min_requests_per_day INT NOT NULL DEFAULT 50,
    bonus_percent INT NOT NULL DEFAULT 5,
    bonus_requests_threshold INT NOT NULL DEFAULT 70,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX idx_shift_report_employee_date ON shift_report(employee_id, shift_date);
CREATE INDEX idx_order_employee_platform ON `order`(employee_id, platform);
CREATE INDEX idx_order_executed_at ON `order`(executed_at);
CREATE INDEX idx_account_balance_history_date ON account_balance_history(shift_date);
