<?php
// Подключаем конфигурацию
require_once 'config.php';

// Подключение к базе данных
$pdo = getDbConnection();

// Проверка авторизации
$isAuthorized = isAuthorized();

// Обработка авторизации
if (isset($_POST['action']) && $_POST['action'] === 'login') {
    if (login($_POST['password'])) {
        $isAuthorized = true;
    }
}

if (isset($_POST['action']) && $_POST['action'] === 'logout') {
    logout();
    $isAuthorized = false;
}
?>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Таблица бухгалтерии</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .login-form {
            padding: 50px;
            text-align: center;
        }

        .login-form input {
            padding: 15px;
            font-size: 18px;
            border: 2px solid #ddd;
            border-radius: 10px;
            margin: 10px;
            width: 300px;
        }

        .login-form button {
            padding: 15px 30px;
            font-size: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            margin: 10px;
        }

        .login-form button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .nav-tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }

        .nav-tab {
            padding: 20px 30px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }

        .nav-tab:hover {
            background: #e9ecef;
            color: #333;
        }

        .nav-tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            background: white;
        }

        .tab-content {
            display: none;
            padding: 30px;
        }

        .tab-content.active {
            display: block;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }

        .card h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-danger {
            background: #dc3545;
            color: white;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }

        .table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }

        .table tr:hover {
            background: #f8f9fa;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }

        .stat-card h3 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .stat-card p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
        }

        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Таблица бухгалтерии</h1>
            <p>Система учета арбитражных операций</p>
            <?php if ($isAuthorized): ?>
                <form method="POST" style="display: inline;">
                    <input type="hidden" name="action" value="logout">
                    <button type="submit" class="logout-btn">Выйти</button>
                </form>
            <?php endif; ?>
        </div>

        <?php if (!$isAuthorized): ?>
            <div class="login-form">
                <h2>Вход в систему</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="login">
                    <div>
                        <input type="password" name="password" placeholder="Введите пароль" required>
                    </div>
                    <div>
                        <button type="submit">Войти</button>
                    </div>
                </form>
            </div>
        <?php else: ?>
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showTab('dashboard')">📊 Дашборд</button>
                <button class="nav-tab" onclick="showTab('reports')">📋 Отчеты</button>
                <button class="nav-tab" onclick="showTab('employees')">👥 Сотрудники</button>
                <button class="nav-tab" onclick="showTab('accounts')">💳 Аккаунты</button>
                <button class="nav-tab" onclick="showTab('settings')">⚙️ Настройки</button>
            </div>

            <div id="dashboard" class="tab-content active">
                <h2>📊 Дашборд</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3 id="total-profit">0</h3>
                        <p>Общая прибыль (USDT)</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="total-reports">0</h3>
                        <p>Всего отчетов</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="active-employees">0</h3>
                        <p>Активных сотрудников</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="total-accounts">0</h3>
                        <p>Всего аккаунтов</p>
                    </div>
                </div>
            </div>

            <div id="reports" class="tab-content">
                <h2>📋 Отчеты</h2>
                <div class="card">
                    <h3>Добавить новый отчет</h3>
                    <form id="report-form">
                        <div class="form-group">
                            <label>Сотрудник</label>
                            <select class="form-control" name="employee_id" required>
                                <option value="">Выберите сотрудника</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Дата смены</label>
                            <input type="date" class="form-control" name="shift_date" required>
                        </div>
                        <div class="form-group">
                            <label>Тип смены</label>
                            <select class="form-control" name="shift_type" required>
                                <option value="">Выберите тип</option>
                                <option value="morning">Утренняя</option>
                                <option value="evening">Вечерняя</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Сумма докидки (USDT)</label>
                            <input type="number" step="0.01" class="form-control" name="dokidka_amount" value="0">
                        </div>
                        <div class="form-group">
                            <label>Внутренний перевод (USDT)</label>
                            <input type="number" step="0.01" class="form-control" name="internal_transfer" value="0">
                        </div>
                        <button type="submit" class="btn btn-primary">Добавить отчет</button>
                    </form>
                </div>

                <div class="card">
                    <h3>Список отчетов</h3>
                    <table class="table" id="reports-table">
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Сотрудник</th>
                                <th>Смена</th>
                                <th>Прибыль</th>
                                <th>Докидка</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="employees" class="tab-content">
                <h2>👥 Сотрудники</h2>
                <div class="card">
                    <h3>Добавить сотрудника</h3>
                    <form id="employee-form">
                        <div class="form-group">
                            <label>Имя сотрудника</label>
                            <input type="text" class="form-control" name="name" required>
                        </div>
                        <div class="form-group">
                            <label>Telegram</label>
                            <input type="text" class="form-control" name="telegram">
                        </div>
                        <div class="form-group">
                            <label>Процент зарплаты (%)</label>
                            <input type="number" step="0.1" class="form-control" name="salary_percent" value="10">
                        </div>
                        <button type="submit" class="btn btn-primary">Добавить сотрудника</button>
                    </form>
                </div>

                <div class="card">
                    <h3>Список сотрудников</h3>
                    <table class="table" id="employees-table">
                        <thead>
                            <tr>
                                <th>Имя</th>
                                <th>Telegram</th>
                                <th>Процент</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="accounts" class="tab-content">
                <h2>💳 Аккаунты</h2>
                <div class="card">
                    <h3>Добавить аккаунт</h3>
                    <form id="account-form">
                        <div class="form-group">
                            <label>Платформа</label>
                            <select class="form-control" name="platform" required>
                                <option value="">Выберите платформу</option>
                                <option value="bybit">Bybit</option>
                                <option value="htx">HTX</option>
                                <option value="bliss">Bliss</option>
                                <option value="gate">Gate</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Название аккаунта</label>
                            <input type="text" class="form-control" name="account_name" required>
                        </div>
                        <div class="form-group">
                            <label>Сотрудник</label>
                            <select class="form-control" name="employee_id">
                                <option value="">Не привязан</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary">Добавить аккаунт</button>
                    </form>
                </div>

                <div class="card">
                    <h3>Список аккаунтов</h3>
                    <table class="table" id="accounts-table">
                        <thead>
                            <tr>
                                <th>Платформа</th>
                                <th>Название</th>
                                <th>Сотрудник</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="settings" class="tab-content">
                <h2>⚙️ Настройки</h2>
                <div class="card">
                    <h3>Настройки системы</h3>
                    <p>Здесь будут настройки системы</p>
                </div>
            </div>
        <?php endif; ?>
    </div>

    <script>
        function showTab(tabName) {
            // Скрыть все табы
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Убрать активный класс с кнопок
            const buttons = document.querySelectorAll('.nav-tab');
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // Показать нужный таб
            document.getElementById(tabName).classList.add('active');
            
            // Активировать кнопку
            event.target.classList.add('active');
        }

        // Загрузка данных при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            if (document.querySelector('.nav-tabs')) {
                loadDashboardData();
                loadEmployees();
                loadAccounts();
                loadReports();
            }
        });

        async function apiRequest(action, method = 'GET', data = null) {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            try {
                const response = await fetch(`api.php?action=${action}`, options);
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                return { error: 'Ошибка сети' };
            }
        }

        async function loadDashboardData() {
            const data = await apiRequest('dashboard');
            if (!data.error) {
                document.getElementById('total-profit').textContent = data.total_profit;
                document.getElementById('total-reports').textContent = data.total_reports;
                document.getElementById('active-employees').textContent = data.active_employees;
                document.getElementById('total-accounts').textContent = data.total_accounts;
            }
        }

        async function loadEmployees() {
            const employees = await apiRequest('employees');
            if (!employees.error) {
                updateEmployeesTable(employees);
                updateEmployeeSelects(employees);
            }
        }

        function updateEmployeesTable(employees) {
            const tbody = document.querySelector('#employees-table tbody');
            tbody.innerHTML = '';
            
            employees.forEach(employee => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${employee.name}</td>
                    <td>${employee.telegram || '-'}</td>
                    <td>${employee.salary_percent}%</td>
                    <td><span class="badge badge-success">Активен</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editEmployee(${employee.id})">Редактировать</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteEmployee(${employee.id})">Удалить</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function updateEmployeeSelects(employees) {
            const selects = document.querySelectorAll('select[name="employee_id"]');
            selects.forEach(select => {
                // Сохраняем текущее значение
                const currentValue = select.value;
                
                // Очищаем опции, кроме первой
                while (select.children.length > 1) {
                    select.removeChild(select.lastChild);
                }
                
                // Добавляем сотрудников
                employees.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.id;
                    option.textContent = employee.name;
                    select.appendChild(option);
                });
                
                // Восстанавливаем значение
                select.value = currentValue;
            });
        }

        async function loadAccounts() {
            const accounts = await apiRequest('accounts');
            if (!accounts.error) {
                updateAccountsTable(accounts);
            }
        }

        function updateAccountsTable(accounts) {
            const tbody = document.querySelector('#accounts-table tbody');
            tbody.innerHTML = '';
            
            accounts.forEach(account => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><span class="badge badge-${getPlatformColor(account.platform)}">${account.platform.toUpperCase()}</span></td>
                    <td>${account.account_name}</td>
                    <td>${account.employee_name || 'Не привязан'}</td>
                    <td><span class="badge badge-success">Активен</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editAccount(${account.id})">Редактировать</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteAccount(${account.id})">Удалить</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function getPlatformColor(platform) {
            const colors = {
                'bybit': 'primary',
                'htx': 'success',
                'bliss': 'warning',
                'gate': 'info'
            };
            return colors[platform] || 'secondary';
        }

        async function loadReports() {
            const reports = await apiRequest('reports');
            if (!reports.error) {
                updateReportsTable(reports);
            }
        }

        function updateReportsTable(reports) {
            const tbody = document.querySelector('#reports-table tbody');
            tbody.innerHTML = '';
            
            reports.forEach(report => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(report.shift_date)}</td>
                    <td>${report.employee_name}</td>
                    <td><span class="badge badge-${report.shift_type === 'morning' ? 'warning' : 'info'}">${report.shift_type === 'morning' ? 'Утренняя' : 'Вечерняя'}</span></td>
                    <td class="${report.profit >= 0 ? 'text-success' : 'text-danger'}">${report.profit ? report.profit.toFixed(2) : '0.00'} USDT</td>
                    <td>${report.dokidka_amount ? report.dokidka_amount.toFixed(2) : '0.00'} USDT</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="viewReport(${report.id})">Просмотр</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteReport(${report.id})">Удалить</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU');
        }

        // Обработчики форм
        document.getElementById('employee-form')?.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            const result = await apiRequest('employees', 'POST', data);
            
            if (result.success) {
                showAlert('Сотрудник успешно добавлен!', 'success');
                this.reset();
                loadEmployees();
                loadDashboardData();
            } else {
                showAlert(result.error || 'Ошибка при добавлении сотрудника', 'error');
            }
        });

        document.getElementById('account-form')?.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            const result = await apiRequest('accounts', 'POST', data);
            
            if (result.success) {
                showAlert('Аккаунт успешно добавлен!', 'success');
                this.reset();
                loadAccounts();
                loadDashboardData();
            } else {
                showAlert(result.error || 'Ошибка при добавлении аккаунта', 'error');
            }
        });

        document.getElementById('report-form')?.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            const result = await apiRequest('reports', 'POST', data);
            
            if (result.success) {
                showAlert('Отчет успешно добавлен!', 'success');
                this.reset();
                loadReports();
                loadDashboardData();
            } else {
                showAlert(result.error || 'Ошибка при добавлении отчета', 'error');
            }
        });

        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'error'}`;
            alertDiv.textContent = message;
            
            // Добавляем в начало контейнера
            const container = document.querySelector('.container');
            container.insertBefore(alertDiv, container.firstChild);
            
            // Удаляем через 5 секунд
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }

        // Заглушки для функций редактирования/удаления
        function editEmployee(id) {
            showAlert('Функция редактирования в разработке', 'info');
        }

        function deleteEmployee(id) {
            if (confirm('Вы уверены, что хотите удалить этого сотрудника?')) {
                showAlert('Функция удаления в разработке', 'info');
            }
        }

        function editAccount(id) {
            showAlert('Функция редактирования в разработке', 'info');
        }

        function deleteAccount(id) {
            if (confirm('Вы уверены, что хотите удалить этот аккаунт?')) {
                showAlert('Функция удаления в разработке', 'info');
            }
        }

        function viewReport(id) {
            showAlert('Функция просмотра отчета в разработке', 'info');
        }

        function deleteReport(id) {
            if (confirm('Вы уверены, что хотите удалить этот отчет?')) {
                showAlert('Функция удаления в разработке', 'info');
            }
        }
    </script>
</body>
</html> 