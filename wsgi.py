#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем приложение
from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=False) 