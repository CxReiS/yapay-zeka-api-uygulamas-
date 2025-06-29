import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QRect

def create_icon(text, color_hex, size=128):
    """Büyük ve profesyonel ikon oluşturma"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    # Gradient arkaplan
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor(color_hex).lighter(120))
    gradient.setColorAt(1, QColor(color_hex).darker(120))
    painter.setBrush(QBrush(gradient))
    
    # Yuvarlatılmış dikdörtgen çiz
    rect = QRect(2, 2, size-4, size-4)
    painter.drawRoundedRect(rect, size/4, size/4)
    
    # İkon metni
    painter.setPen(QColor(Qt.GlobalColor.white))
    font = QFont("Segoe UI", size//3 if len(text) < 3 else size//4)
    font.setBold(True)
    painter.setFont(font)
    
    # Metin gölgesi
    painter.setPen(QColor(0, 0, 0, 150))
    painter.drawText(rect.adjusted(2, 2, 2, 2), Qt.AlignmentFlag.AlignCenter, text)
    
    # Ana metin
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    
    painter.end()
    return pixmap

def generate_all_icons():
    """Tüm ikonları oluştur ve kaydet"""
    icons = {
        "logo": ("AI", "#4A90E2"),
        "new_chat": ("💬", "#4CD964"),
        "new_folder": ("📁", "#FF9500"),
        "login": ("🔑", "#5856D6"),
        "attach_file": ("📤", "#007AFF"),
        "send_message": ("✉️", "#34C759"),
        "brain": ("🧠", "#AF52DE"),
        "search": ("🔍", "#5AC8FA"),
        "delete": ("🗑", "#FF3B30"),
        "rename": ("✏", "#007AFF"),
        "move": ("➡", "#FFCC00"),
        "minimize": ("⬇", "#8E8E93"),
        "update": ("🔄", "#5AC8FA"),
        "export": ("📤", "#4CD964"),
        "theme": ("🎨", "#FF9500"),
        "keyboard": ("⌨", "#5AC8FA"),
        "model": ("🤖", "#AF52DE"),
        "info": ("ℹ", "#007AFF"),
    }

    # icons klasörü yoksa oluştur
    if not os.path.exists("icons"):
        os.makedirs("icons")
        print("icons klasörü oluşturuldu")

    for name, (text, color) in icons.items():
        icon_path = f"icons/{name}.png"
        pixmap = create_icon(text, color, 128)
        pixmap.save(icon_path)
        print(f"İkon oluşturuldu: {icon_path}")

if __name__ == "__main__":
    app = QApplication([])
    generate_all_icons()
    print("Tüm ikonlar başarıyla oluşturuldu!")