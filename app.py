import sys
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QStatusBar, QMenuBar, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QKeySequence

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='w'
)
logger = logging.getLogger('DeepSeekChat.app')

class DeepSeekChatApp(QMainWindow):
    def __init__(self, user_manager, email_verifier):
        super().__init__()
        print("DEBUG: Uygulama başlatılıyor")
        
        self.user_manager = user_manager
        self.email_verifier = email_verifier
        
        # StatusBar ve temel ayarlar
        self.statusBar().showMessage("🟢 Uygulama başlatıldı")
        self.setWindowTitle("DeepSeek Chat")
        self.setGeometry(100, 100, 800, 600)
        
        # Temel arayüzü oluştur
        self.setup_basic_ui()
        
        # Tam ekran kısayolları
        self.setup_shortcuts()
        
        print("DEBUG: Uygulama başlatma tamamlandı")

    def setup_basic_ui(self):
        """Temel arayüz bileşenlerini oluşturur"""
        # Merkez widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Düzen
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Örnek etiket
        label = QLabel("DeepSeek Chat Uygulaması\nLütfen giriş yapın")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # Örnek buton
        btn = QPushButton("Giriş Yap")
        btn.clicked.connect(self.show_login)
        layout.addWidget(btn)

    def setup_shortcuts(self):
        """Kısayolları ayarlar"""
        # F11 - Tam ekran
        self.full_screen_shortcut = QAction(self)
        self.full_screen_shortcut.setShortcut(QKeySequence("F11"))
        self.full_screen_shortcut.triggered.connect(self.toggle_full_screen)
        self.addAction(self.full_screen_shortcut)
        
        # ESC - Tam ekrandan çık
        self.escape_shortcut = QAction(self)
        self.escape_shortcut.setShortcut(QKeySequence("Esc"))
        self.escape_shortcut.triggered.connect(self.exit_full_screen)
        self.addAction(self.escape_shortcut)

    def show_login(self):
        """Giriş ekranını göster"""
        print("DEBUG: Giriş ekranı açılıyor")
        self.statusBar().showMessage("🔑 Giriş ekranı açılıyor...")

    def toggle_full_screen(self):
        """F11 ile tam ekran modunu aç/kapat"""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("↕️ Pencere modu", 2000)
        else:
            self.showFullScreen()
            self.statusBar().showMessage("🔳 Tam ekran modu", 2000)
    
    def exit_full_screen(self):
        """ESC ile tam ekran modundan çık"""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("↕️ Pencere moduna geçildi", 2000)

if __name__ == "__main__":
    print("=== app.py TEST ===")
    from user_manager import UserManager
    from email_verifier import EmailVerifier
    
    app = QApplication(sys.argv)
    window = DeepSeekChatApp(UserManager(), EmailVerifier())
    window.show()
    sys.exit(app.exec())