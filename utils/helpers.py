import os
import re
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

def validate_email(email):
    """E-posta adresini doğrular"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def get_available_fonts():
    """Sistemdeki mevcut fontları listeler"""
    app = QApplication.instance() or QApplication([])
    return QFontDatabase().families()

def format_file_size(size_bytes):
    """Dosya boyutunu insan okuyabileceği formata çevirir"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def create_safe_filename(name):
    """Güvenli dosya adı oluşturur"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_file_icon(file_path):
    """Dosya türüne göre ikon döndürür"""
    extension = os.path.splitext(file_path)[1].lower()
    icons = {
        '.txt': '📝', '.py': '🐍', '.js': '📜', '.html': '🌐',
        '.css': '🎨', '.json': '📋', '.pdf': '📄', '.doc': '📄',
        '.docx': '📄', '.md': '📘'
    }
    return icons.get(extension, '📄')