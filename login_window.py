from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget, QMessageBox, QCheckBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize
import json
import os
import logging
from main import MainApplication
from user_manager import UserManager

logger = logging.getLogger('DeepSeekChat.login_window')

class LoginWindow(QMainWindow):
    def __init__(self):
        """Giriş penceresini oluşturur"""
        super().__init__()
        self.user_manager = user_manager
        self.setWindowTitle("🔐 DeepSeek Chat - Giriş")
        self.setFixedSize(450, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setPixmap(QIcon("icons/logo.png").pixmap(128, 128))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)
        
        # Giriş alanları
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Email")
        self.username_input.returnPressed.connect(self.attempt_login)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.attempt_login)
        
        # "Beni Hatırla" seçeneği
        self.remember_check = QCheckBox("Beni hatırla")
        self.remember_check.setChecked(True)
        
        # Giriş butonu
        self.login_button = QPushButton()
        self.login_button.setIcon(QIcon("icons/login.png"))
        self.login_button.setIconSize(QSize(64, 64))
        self.login_button.setText(" Giriş Yap")
        self.login_button.clicked.connect(self.attempt_login)
        
        # Otomatik giriş butonu
        self.skip_login_button = QPushButton("Geçici Olarak Atla")
        self.skip_login_button.clicked.connect(self.skip_login)
        
        # Layout
        layout.addWidget(self.logo_label)
        layout.addWidget(QLabel("Kullanıcı Adı:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Şifre:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.remember_check)
        layout.addWidget(self.login_button)
        layout.addWidget(self.skip_login_button)
        
    def load_user_prefs(self):
        """Kayıtlı kullanıcı adını yükle"""
        try:
            if os.path.exists("user_prefs.json"):
                with open("user_prefs.json", "r") as f:
                    prefs = json.load(f)
                    if prefs.get("remember"):
                        self.username_input.setText(prefs.get("username", ""))
                        self.remember_check.setChecked(True)
        except Exception as e:
            logger.error(f"Kullanıcı ayarları yüklenemedi: {str(e)}")    
            
    def apply_font_settings(self):
        """Font ayarlarını uygular"""
        try:
            from utils.font_manager import apply_font_settings
            apply_font_settings(self)
        except Exception as e:
            logger.error(f"Font ayarları uygulanırken hata: {str(e)}")   
            
    def attempt_login(self):
        try:
            email = self.username_input.text()
            password = self.password_input.text()

            success, message = self.user_manager.authenticate(email, password)

            if success:
                # Beni hatırla seçiliyse bilgileri kaydet
                if self.remember_check.isChecked():
                    with open("user_prefs.json", "w") as f:
                        json.dump({
                            "username": email,
                            "remember": True
                        }, f)
                self.open_main_app()
            else:
                QMessageBox.warning(self, "Giriş Başarısız", message)

        except Exception as e:
            logger.error(f"Giriş hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Giriş sırasında hata oluştu:\n{str(e)}")

    def skip_login(self):
        try:
            self.open_main_app()
        except Exception as e:
            logger.error(f"Giriş atlama hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Uygulama açılırken hata oluştu: {str(e)}")

    def open_main_app(self):
        self.main_app = MainApplication()
        self.main_app.show()
        self.close()
        
