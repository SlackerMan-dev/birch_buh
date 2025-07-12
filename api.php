<?php
// Подключаем конфигурацию
require_once 'config.php';

// Подключение к базе данных
$pdo = getDbConnection();

// Проверка авторизации
if (!isAuthorized()) {
    die(json_encode(['error' => 'Не авторизован']));
}

// Получение данных запроса
$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

header('Content-Type: application/json');

try {
    switch ($action) {
        case 'dashboard':
            getDashboardData();
            break;
        case 'employees':
            if ($method === 'GET') {
                getEmployees();
            } elseif ($method === 'POST') {
                addEmployee();
            }
            break;
        case 'accounts':
            if ($method === 'GET') {
                getAccounts();
            } elseif ($method === 'POST') {
                addAccount();
            }
            break;
        case 'reports':
            if ($method === 'GET') {
                getReports();
            } elseif ($method === 'POST') {
                addReport();
            }
            break;
        case 'platform_balances':
            getPlatformBalances();
            break;
        default:
            echo json_encode(['error' => 'Неизвестное действие']);
    }
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
}

function getDashboardData() {
    global $pdo;
    
    // Общая прибыль
    $stmt = $pdo->query("
        SELECT 
            SUM(ab.end_balance - ab.start_balance) as total_profit,
            COUNT(DISTINCT r.id) as total_reports,
            COUNT(DISTINCT e.id) as active_employees,
            COUNT(DISTINCT a.id) as total_accounts
        FROM account_balances ab
        JOIN reports r ON ab.report_id = r.id
        JOIN employees e ON r.employee_id = e.id AND e.is_active = 1
        JOIN accounts a ON ab.account_id = a.id AND a.is_active = 1
    ");
    
    $data = $stmt->fetch(PDO::FETCH_ASSOC);
    
    echo json_encode([
        'total_profit' => round($data['total_profit'] ?? 0, 2),
        'total_reports' => $data['total_reports'] ?? 0,
        'active_employees' => $data['active_employees'] ?? 0,
        'total_accounts' => $data['total_accounts'] ?? 0
    ]);
}

function getEmployees() {
    global $pdo;
    
    $stmt = $pdo->query("
        SELECT 
            e.*,
            COUNT(r.id) as reports_count,
            SUM(ab.end_balance - ab.start_balance) as total_profit
        FROM employees e
        LEFT JOIN reports r ON e.id = r.employee_id
        LEFT JOIN account_balances ab ON r.id = ab.report_id
        WHERE e.is_active = 1
        GROUP BY e.id
        ORDER BY e.name
    ");
    
    $employees = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($employees);
}

function addEmployee() {
    global $pdo;
    
    $input = json_decode(file_get_contents('php://input'), true);
    
    $stmt = $pdo->prepare("
        INSERT INTO employees (name, telegram, salary_percent) 
        VALUES (?, ?, ?)
    ");
    
    $stmt->execute([
        $input['name'],
        $input['telegram'] ?? null,
        $input['salary_percent'] ?? 10.0
    ]);
    
    echo json_encode(['success' => true, 'id' => $pdo->lastInsertId()]);
}

function getAccounts() {
    global $pdo;
    
    $stmt = $pdo->query("
        SELECT 
            a.*,
            e.name as employee_name,
            COUNT(ab.id) as balance_records
        FROM accounts a
        LEFT JOIN employees e ON a.employee_id = e.id
        LEFT JOIN account_balances ab ON a.id = ab.account_id
        WHERE a.is_active = 1
        GROUP BY a.id
        ORDER BY a.platform, a.account_name
    ");
    
    $accounts = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($accounts);
}

function addAccount() {
    global $pdo;
    
    $input = json_decode(file_get_contents('php://input'), true);
    
    $stmt = $pdo->prepare("
        INSERT INTO accounts (platform, account_name, employee_id) 
        VALUES (?, ?, ?)
    ");
    
    $stmt->execute([
        $input['platform'],
        $input['account_name'],
        $input['employee_id'] ?: null
    ]);
    
    echo json_encode(['success' => true, 'id' => $pdo->lastInsertId()]);
}

function getReports() {
    global $pdo;
    
    $stmt = $pdo->query("
        SELECT 
            r.*,
            e.name as employee_name,
            SUM(ab.end_balance - ab.start_balance) as profit,
            COUNT(ab.id) as accounts_count
        FROM reports r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN account_balances ab ON r.id = ab.report_id
        GROUP BY r.id
        ORDER BY r.shift_date DESC, r.id DESC
        LIMIT 50
    ");
    
    $reports = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode($reports);
}

function addReport() {
    global $pdo;
    
    $input = json_decode(file_get_contents('php://input'), true);
    
    $pdo->beginTransaction();
    
    try {
        // Добавляем отчет
        $stmt = $pdo->prepare("
            INSERT INTO reports (employee_id, shift_date, shift_type, dokidka_amount, internal_transfer_amount) 
            VALUES (?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $input['employee_id'],
            $input['shift_date'],
            $input['shift_type'],
            $input['dokidka_amount'] ?? 0,
            $input['internal_transfer_amount'] ?? 0
        ]);
        
        $reportId = $pdo->lastInsertId();
        
        // Добавляем балансы аккаунтов (если есть)
        if (!empty($input['account_balances'])) {
            $stmt = $pdo->prepare("
                INSERT INTO account_balances (report_id, account_id, start_balance, end_balance) 
                VALUES (?, ?, ?, ?)
            ");
            
            foreach ($input['account_balances'] as $balance) {
                $stmt->execute([
                    $reportId,
                    $balance['account_id'],
                    $balance['start_balance'] ?? 0,
                    $balance['end_balance'] ?? 0
                ]);
            }
        }
        
        $pdo->commit();
        echo json_encode(['success' => true, 'id' => $reportId]);
        
    } catch (Exception $e) {
        $pdo->rollback();
        throw $e;
    }
}

function getPlatformBalances() {
    global $pdo;
    
    $stmt = $pdo->query("
        SELECT 
            a.platform,
            a.account_name,
            e.name as employee_name,
            ab.end_balance,
            r.shift_date,
            ROW_NUMBER() OVER (PARTITION BY a.id ORDER BY r.shift_date DESC, r.id DESC) as rn
        FROM accounts a
        LEFT JOIN account_balances ab ON a.id = ab.account_id
        LEFT JOIN reports r ON ab.report_id = r.id
        LEFT JOIN employees e ON a.employee_id = e.id
        WHERE a.is_active = 1
    ");
    
    $allBalances = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Группируем по платформам и берем только последние балансы
    $platformBalances = [];
    foreach ($allBalances as $balance) {
        if ($balance['rn'] == 1) { // Только последний баланс для каждого аккаунта
            $platform = $balance['platform'];
            if (!isset($platformBalances[$platform])) {
                $platformBalances[$platform] = [
                    'platform' => $platform,
                    'accounts' => [],
                    'total_balance' => 0
                ];
            }
            
            $accountBalance = $balance['end_balance'] ?? 0;
            $platformBalances[$platform]['accounts'][] = [
                'account_name' => $balance['account_name'],
                'employee_name' => $balance['employee_name'],
                'balance' => $accountBalance,
                'last_update' => $balance['shift_date']
            ];
            
            $platformBalances[$platform]['total_balance'] += $accountBalance;
        }
    }
    
    echo json_encode(array_values($platformBalances));
}
?> 