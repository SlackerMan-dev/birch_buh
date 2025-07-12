from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from decimal import Decimal
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func, text
from utils import (
    find_prev_balance,
    calculate_report_profit,
    calculate_account_last_balance,
    group_reports_by_day_net_profit
)
import re

# Опциональный импорт pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

app = Flask(__name__)

# Конфигурация для Timeweb
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Настройки базы данных MySQL для Timeweb
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'your_database_name')
DB_USER = os.environ.get('DB_USER', 'your_username')
DB_PASS = os.environ.get('DB_PASS', 'your_password')

# Формируем строку подключения к MySQL
DATABASE_URL = f"mysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'webp', 'pdf', 'txt'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file):
    """Дополнительная проверка размера файла"""
    if file and hasattr(file, 'content_length') and file.content_length:
        return file.content_length <= app.config['MAX_CONTENT_LENGTH']
    return True

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- КОНСТАНТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
PLATFORMS = ['bybit', 'htx', 'bliss', 'gate']
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Blalala2')

def validate_admin_password(data):
    """Проверяет пароль администратора"""
    if not data or not data.get('password'):
        return False
    return data['password'] == ADMIN_PASSWORD

def convert_to_moscow_time(datetime_obj, platform):
    """
    Конвертирует время из часового пояса платформы в московское время
    """
    if not datetime_obj:
        return datetime_obj
    
    timezone_offsets = {
        'bybit': 3,
        'htx': -5,
        'bliss': 3,
        'gate': 0
    }
    
    offset_hours = timezone_offsets.get(platform.lower(), 0)
    
    if offset_hours != 0:
        datetime_obj = datetime_obj + timedelta(hours=offset_hours)
    
    return datetime_obj

# Импортируем остальные функции из оригинального app.py
# (здесь будет весь остальной код из app.py, но адаптированный для MySQL)

# Модели базы данных (адаптированные для MySQL)
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    telegram = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    salary_percent = db.Column(db.Float, nullable=True)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    platform = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class ShiftReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)
    total_requests = db.Column(db.Integer, default=0)
    balances_json = db.Column(db.Text, nullable=False, default='{}')
    scam_amount = db.Column(db.Numeric(15, 2), default=0)
    scam_comment = db.Column(db.Text, default='')
    scam_personal = db.Column(db.Boolean, default=False)
    dokidka_amount = db.Column(db.Numeric(15, 2), default=0)
    internal_transfer_amount = db.Column(db.Numeric(15, 2), default=0)
    dokidka_comment = db.Column(db.Text, default='')
    internal_transfer_comment = db.Column(db.Text, default='')
    bybit_file = db.Column(db.String(255), default=None)
    htx_file = db.Column(db.String(255), default=None)
    bliss_file = db.Column(db.String(255), default=None)
    start_photo = db.Column(db.String(255), default=None)
    end_photo = db.Column(db.String(255), default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bybit_requests = db.Column(db.Integer, default=0)
    htx_requests = db.Column(db.Integer, default=0)
    bliss_requests = db.Column(db.Integer, default=0)
    bybit_first_trade = db.Column(db.String(100), default='')
    bybit_last_trade = db.Column(db.String(100), default='')
    htx_first_trade = db.Column(db.String(100), default='')
    htx_last_trade = db.Column(db.String(100), default='')
    bliss_first_trade = db.Column(db.String(100), default='')
    bliss_last_trade = db.Column(db.String(100), default='')
    gate_first_trade = db.Column(db.String(100), default='')
    gate_last_trade = db.Column(db.String(100), default='')
    appeal_amount = db.Column(db.Numeric(15, 2), default=0)
    appeal_comment = db.Column(db.Text, default='')
    appeal_deducted = db.Column(db.Boolean, default=False)
    shift_start_time = db.Column(db.DateTime, default=None)
    shift_end_time = db.Column(db.DateTime, default=None)

class OrderDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_report_id = db.Column(db.Integer, db.ForeignKey('shift_report.id'), nullable=False)
    order_id = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    price = db.Column(db.Numeric(15, 8), nullable=False)
    total_usdt = db.Column(db.Numeric(15, 2), nullable=False)
    fees_usdt = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(20), nullable=False)
    executed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InitialBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0)

class AccountBalanceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Numeric(15, 2), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    employee_name = db.Column(db.String(100), nullable=True)
    balance_type = db.Column(db.String(10), nullable=False, default='end')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), nullable=False, unique=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False, default='bybit')
    account_name = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    side = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(15, 8), nullable=False)
    price = db.Column(db.Numeric(15, 8), nullable=False)
    total_usdt = db.Column(db.Numeric(15, 2), nullable=False)
    fees_usdt = db.Column(db.Numeric(15, 2), default=0)
    status = db.Column(db.String(20), nullable=False)
    executed_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    employee = db.relationship('Employee', backref='orders')

class EmployeeScamHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    shift_report_id = db.Column(db.Integer, db.ForeignKey('shift_report.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    comment = db.Column(db.Text, default='')
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee = db.relationship('Employee', backref='scam_history')
    shift_report = db.relationship('ShiftReport', backref='scam_history')

class SalarySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    base_percent = db.Column(db.Integer, nullable=False, default=30)
    min_requests_per_day = db.Column(db.Integer, nullable=False, default=50)
    bonus_percent = db.Column(db.Integer, nullable=False, default=5)
    bonus_requests_threshold = db.Column(db.Integer, nullable=False, default=70)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Здесь будут все остальные функции из оригинального app.py
# (маршруты, функции парсинга и т.д.)

@app.route('/')
def index():
    return render_template('index.html')

# Добавьте здесь все остальные маршруты из оригинального app.py

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=8000) 