import os
import re
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase


def validate_email(email: str) -> bool:
    """E-posta adresinin geçerli olup olmadığını kontrol eder."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def get_available_fonts():
    """Sistemde bulunan yazı tiplerini döndürür."""
    app = QApplication.instance() or QApplication([])
    return QFontDatabase().families()


def format_file_size(size_bytes: int) -> str:
    """Bayt cinsinden verilen dosya boyutunu okunabilir formata dönüştürür."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def create_safe_filename(name: str) -> str:
    """Dosya sistemine güvenli olacak şekilde bir ad üretir."""
    return re.sub(r'[\\/*?:"<>|]', '', name).strip()


def get_file_icon(file_path: str) -> str:
    """Dosya uzantısına göre bir emoji ikonu döndürür."""
    extension = os.path.splitext(file_path)[1].lower()
    icons = {
        '.txt': '📝', '.py': '🐍', '.js': '📜', '.html': '🌐',
        '.css': '🎨', '.json': '📋', '.pdf': '📄', '.doc': '📄',
        '.docx': '📄', '.md': '📘'
    }
    return icons.get(extension, '📄')

