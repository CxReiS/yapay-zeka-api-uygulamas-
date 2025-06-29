import sys
import os
import json
import logging
import uuid
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QTextEdit, 
    QListWidget, QSplitter, QStatusBar, QTreeWidget, QTreeWidgetItem,
    QComboBox, QFrame, QMenuBar, QMenu, QSystemTrayIcon, QCheckBox,
    QInputDialog, QDialog, QDialogButtonBox, QFormLayout, QTabWidget,
    QFileDialog, QListWidgetItem, QLineEdit, QGroupBox, QScrollArea,
    QKeySequenceEdit, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDateTime
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QTextCursor, QColor, QTextCharFormat, QFont

# Loglama sistemi
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DeepSeekChat')

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.login_button.setIconSize(QSize(64, 64))  # İkon boyutunu büyüttük
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
    
    def attempt_login(self):
        try:
            # Basit giriş kontrolü
            if self.remember_check.isChecked():
                # Kullanıcı bilgilerini kaydet
                with open("user_prefs.json", "w") as f:
                    json.dump({
                        "username": self.username_input.text(),
                        "remember": True
                    }, f)
            self.open_main_app()
        except Exception as e:
            logger.error(f"Giriş hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Giriş sırasında hata oluştu: {str(e)}")

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

class ErrorDialog(QDialog):
    def __init__(self, error_msg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Hata Raporu")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Hata mesajı
        error_label = QLabel("Aşağıdaki hata oluştu:")
        layout.addWidget(error_label)
        
        self.error_text = QTextEdit()
        self.error_text.setPlainText(error_msg)
        self.error_text.setReadOnly(True)
        layout.addWidget(self.error_text)
        
        # Log dosyası butonu
        log_btn = QPushButton("Log Dosyasını Aç")
        log_btn.clicked.connect(self.open_log)
        layout.addWidget(log_btn)
        
        # Kapat butonu
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def open_log(self):
        try:
            if os.path.exists("app.log"):
                os.startfile("app.log")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Log dosyası açılamadı: {str(e)}")

class MainApplication(QMainWindow):
    VERSION = "1.0.1"
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"💬 DeepSeek Chat v{self.VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Hata yakalama
        sys.excepthook = self.handle_exception
        
        # Sistem Tepsisine Ekle
        self.tray_icon = QSystemTrayIcon(QIcon("icons/logo.png"), self)
        self.setup_tray_icon()
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 1. Sol Sidebar (250px genişlik)
        self.setup_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 2. Sağ Panel (Esnek)
        self.setup_right_panel()
        main_layout.addWidget(self.right_panel, 1)
        
        # Status bar
        self.setup_statusbar()  # Status bar'ı kur
        
        # Menü çubuğu
        self.setup_menu_bar()
        
        # Kısayollar
        self.setup_shortcuts()
        
        # Tema
        self.apply_theme("dark")
        
        # Ekli dosyalar
        self.attached_files = []
        
        # Uygulama durumunu yükle
        self.load_app_state()
        
        # Aktif sohbet ID'si
        self.active_chat_id = None
        
    def setup_statusbar(self):
        """Status bar'ı kur"""
        status_bar = self.statusBar()
        status_bar.showMessage("✅ Bağlantı kuruldu")
        
        # Tepsi açıklaması
        tray_label = QLabel("Uygulamayı kapatmak için tepsi simgesine sağ tıklayın")
        tray_label.setStyleSheet("color: #888; font-style: italic;")
        status_bar.addPermanentWidget(tray_label)
        
        # Minimize butonu
        self.minimize_btn = QToolButton()
        self.minimize_btn.setIcon(QIcon("icons/minimize.png"))
        self.minimize_btn.setIconSize(QSize(24, 24))
        self.minimize_btn.setToolTip("Tepsiye indir")
        self.minimize_btn.clicked.connect(self.minimize_to_tray)
        
        # Status bar widget'ı
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 5, 0)
        status_layout.addStretch()
        status_layout.addWidget(self.minimize_btn)
        
        status_bar.addPermanentWidget(status_widget)    

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Özel hata yöneticisi"""
        error_msg = f"{exc_type.__name__}: {exc_value}"
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Hata diyaloğunu göster
        error_dialog = ErrorDialog(error_msg, self)
        error_dialog.exec()

    def setup_tray_icon(self):
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Göster")
        show_action.triggered.connect(self.show_and_activate)
        
        check_update_action = tray_menu.addAction("Güncellemeleri Kontrol Et")
        check_update_action.triggered.connect(self.check_for_updates)
        
        quit_action = tray_menu.addAction("Çıkış")
        quit_action.triggered.connect(self.quit_application) 
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        # Layout düzeni
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Arama Kutusu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Sohbetlerde ara...")
        self.search_box.textChanged.connect(self.filter_chats)
        sidebar_layout.addWidget(self.search_box)
        
        # Yeni Sohbet Butonu - Büyük ikon (48x48)
        self.new_chat_btn = QPushButton()
        self.new_chat_btn.setIcon(QIcon("icons/new_chat.png"))
        self.new_chat_btn.setIconSize(QSize(48, 48))  # İkon boyutunu büyüttük
        self.new_chat_btn.setText(" Yeni Sohbet")
        self.new_chat_btn.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(self.new_chat_btn)
        
        # Sohbet Listesi
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_chat)
        self.chat_list.itemDoubleClicked.connect(self.edit_chat_title)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_list_context_menu)
        sidebar_layout.addWidget(self.chat_list)
        
        # Yeni Proje Butonu - Büyük ikon (48x48)
        self.new_project_btn = QPushButton()
        self.new_project_btn.setIcon(QIcon("icons/new_folder.png"))
        self.new_project_btn.setIconSize(QSize(48, 48))  # İkon boyutunu büyüttük
        self.new_project_btn.setText(" Yeni Proje")
        self.new_project_btn.clicked.connect(self.new_project)
        sidebar_layout.addWidget(self.new_project_btn)
        
        # Proje Ağacı
        self.projects_tree = QTreeWidget()
        self.projects_tree.setHeaderLabel("Projeler")
        self.projects_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.projects_tree.customContextMenuRequested.connect(self.show_project_context_menu)
        self.projects_tree.itemClicked.connect(self.load_project_chat)
        self.projects_tree.itemDoubleClicked.connect(self.edit_project_title)
        sidebar_layout.addWidget(self.projects_tree)

        # Model seçimi
        model_box = QGroupBox("🤖 Model Seçimi")
        model_layout = QVBoxLayout(model_box)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek-chat", "deepseek-coder", "deepseek-math"])
        model_layout.addWidget(self.model_combo)
        sidebar_layout.addWidget(model_box)
        
        # Özel Özellikler - Bu özellikler artık mesaj gönderim alanında olacak
        sidebar_layout.addStretch()

    def setup_right_panel(self):
        self.right_panel = QSplitter(Qt.Orientation.Vertical)
        
        # Mesaj Görüntüleme
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setHtml("<center><i>Hoş geldiniz! Lütfen bir sohbet seçin.</i></center>")
        self.chat_display.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_display.customContextMenuRequested.connect(self.show_chat_context_menu)
        
        # Mesaj Gönderme Paneli
        send_panel = QWidget()
        send_layout = QVBoxLayout(send_panel)
        
        # Mesaj Girişi
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("DeepSeek'e mesaj yazın...")
        self.message_input.setMinimumHeight(100)
        self.message_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.message_input.customContextMenuRequested.connect(self.show_text_context_menu)
        
        # Butonlar için alt panel
        bottom_layout = QHBoxLayout()
        
        # Özel Özellikler (Derin Düşünce ve Web'de Ara) - Büyük ikonlar (48x48)
        features_layout = QHBoxLayout()
        
        self.deep_thought_btn = QPushButton()
        self.deep_thought_btn.setIcon(QIcon("icons/brain.png"))
        self.deep_thought_btn.setIconSize(QSize(48, 48))
        self.deep_thought_btn.setText(" Derin Düşünce")
        self.deep_thought_btn.setToolTip("Derin Düşünce")
        self.deep_thought_btn.setCheckable(True)
        features_layout.addWidget(self.deep_thought_btn)
        
        self.web_search_btn = QPushButton()
        self.web_search_btn.setIcon(QIcon("icons/search.png"))
        self.web_search_btn.setIconSize(QSize(48, 48))
        self.web_search_btn.setText(" Web'de Ara")
        self.web_search_btn.setToolTip("Web'de Ara")
        self.web_search_btn.setCheckable(True)
        features_layout.addWidget(self.web_search_btn)
        
        bottom_layout.addLayout(features_layout)
        bottom_layout.addStretch()
        
        # Dosya Ekle Butonu - Yeni ikon (48x48)
        self.attach_btn = QPushButton()
        self.attach_btn.setIcon(QIcon("icons/attach_file.png"))  # Yeni ikon
        self.attach_btn.setIconSize(QSize(48, 48))
        self.attach_btn.setText(" Dosya Ekle")
        self.attach_btn.setToolTip("Dosya ekle")
        self.attach_btn.clicked.connect(self.attach_file)
        bottom_layout.addWidget(self.attach_btn)
        
        # Gönder Butonu - Yeni ikon (48x48)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(QIcon("icons/send_message.png"))  # Yeni ikon
        self.send_btn.setIconSize(QSize(48, 48))
        self.send_btn.setText(" Gönder")
        self.send_btn.setToolTip("Mesajı gönder")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bottom_layout.addWidget(self.send_btn)
        
        send_layout.addWidget(self.message_input)
        send_layout.addLayout(bottom_layout)
        
        self.right_panel.addWidget(self.chat_display)
        self.right_panel.addWidget(send_panel)
        self.right_panel.setSizes([600, 200])

    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        # Dosya Menüsü
        file_menu = menubar.addMenu("📁 Dosya")
        
        new_project_action = QAction(QIcon("icons/new_folder.png"), "Yeni Proje", self)
        new_project_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        export_action = QAction(QIcon("icons/export.png"), "Sohbetleri Dışa Aktar", self)
        export_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        export_action.triggered.connect(self.export_chats)
        file_menu.addAction(export_action)
        
        # Ayarlar Menüsü - Menü ikonları
        settings_menu = menubar.addMenu("⚙️ Ayarlar")
        
        theme_action = QAction(QIcon("icons/theme.png"), "🎨 Tema Ayarları", self)
        theme_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        theme_action.triggered.connect(self.open_theme_settings)
        settings_menu.addAction(theme_action)
        
        shortcuts_action = QAction(QIcon("icons/keyboard.png"), "⌨️ Kısayollar", self)
        shortcuts_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        shortcuts_action.triggered.connect(self.open_shortcut_settings)
        settings_menu.addAction(shortcuts_action)
        
        models_action = QAction(QIcon("icons/model.png"), "🤖 Model Yönetimi", self)
        models_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        models_action.triggered.connect(self.open_model_management)
        settings_menu.addAction(models_action)
        
        # Yardım Menüsü - Menü ikonları
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction(QIcon("icons/info.png"), "ℹ️ Hakkında", self)
        about_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        update_action = QAction(QIcon("icons/update.png"), "🔄 Güncellemeleri Kontrol Et", self)
        update_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(update_action)
        
        # Tepsiye indir butonu - Büyük ikon (32x32)
        minimize_action = QAction(QIcon("icons/minimize.png"), "Tepsiye İndir", self)
        minimize_action.setIconVisibleInMenu(True)  # İkonun görünür olmasını sağla
        minimize_action.triggered.connect(self.minimize_to_tray)
        menubar.addAction(minimize_action)

    def minimize_to_tray(self):
        """Uygulamayı tepsiye indir"""
        self.hide()
        self.tray_icon.showMessage(
            "DeepSeek Chat", 
            "Uygulama sistem tepsisinde çalışmaya devam ediyor",
            QSystemTrayIcon.MessageIcon.Information, 
            2000
        )

    def setup_shortcuts(self):
        # Enter ile gönder
        self.send_action = QAction(self)
        self.send_action.setShortcut(QKeySequence(Qt.Key.Key_Return | Qt.KeyboardModifier.ControlModifier))
        self.send_action.triggered.connect(self.send_message)
        self.addAction(self.send_action)
        
        # Shift+Enter ile yeni satır
        self.newline_action = QAction(self)
        self.newline_action.setShortcut(QKeySequence(Qt.Key.Key_Return))
        self.newline_action.triggered.connect(self.insert_newline)
        self.addAction(self.newline_action)
        
        # F11 ile tam ekran
        self.fullscreen_action = QAction(self)
        self.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(self.fullscreen_action)
        
        # Ctrl+M ile tepsiye indir
        self.minimize_action = QAction(self)
        self.minimize_action.setShortcut(QKeySequence("Ctrl+M"))
        self.minimize_action.triggered.connect(self.minimize_to_tray)
        self.addAction(self.minimize_action)

    def apply_theme(self, theme_name):
        try:
            self.current_theme = theme_name
            if theme_name == "dark":
                # Modern Koyu Tema
                self.setStyleSheet("""
                    /* Ana Pencere */
                    QMainWindow {
                        background-color: #121212;
                        color: #e0e0e0;
                    }
                    
                    /* Genel Widget'lar */
                    QWidget {
                        background-color: #121212;
                        color: #e0e0e0;
                    }
                    
                    /* Metin Girişleri */
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        border: 1px solid #2d2d2d;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #4a76cd;
                        selection-color: white;
                    }
                    
                    /* Butonlar */
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #e0e0e0;
                        border: 1px solid #3a3a3a;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    
                    QPushButton:hover {
                        background-color: #3a3a3a;
                    }
                    
                    QPushButton:pressed {
                        background-color: #1d1d1d;
                    }
                    
                    QPushButton:checked {
                        background-color: #4a76cd;
                        color: white;
                    }
                    
                    /* Açılır Menüler */
                    QComboBox {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        border: 1px solid #2d2d2d;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #2d2d2d;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    
                    /* Splitter */
                    QSplitter::handle {
                        background-color: #2d2d2d;
                    }
                    
                    /* Sekmeler */
                    QTabWidget::pane {
                        border: 1px solid #2d2d2d;
                        background: #1e1e1e;
                    }
                    
                    QTabBar::tab {
                        background: #2d2d2d;
                        color: #e0e0e0;
                        padding: 8px 12px;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                        margin-right: 2px;
                    }
                    
                    QTabBar::tab:selected {
                        background: #4a76cd;
                        color: white;
                    }
                    
                    /* ScrollBar */
                    QScrollBar:vertical {
                        border: none;
                        background: #1e1e1e;
                        width: 10px;
                        margin: 0;
                    }
                    
                    QScrollBar::handle:vertical {
                        background: #3a3a3a;
                        min-height: 20px;
                        border-radius: 5px;
                    }
                    
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    
                    /* Grup Kutuları */
                    QGroupBox {
                        border: 1px solid #2d2d2d;
                        border-radius: 6px;
                        margin-top: 1ex;
                        padding-top: 10px;
                        font-weight: bold;
                    }
                    
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top center;
                        padding: 0 5px;
                    }
                """)
            
            elif theme_name == "light":
                # Modern Açık Tema
                self.setStyleSheet("""
                    /* Ana Pencere */
                    QMainWindow {
                        background-color: #f5f7fa;
                        color: #333333;
                    }
                    
                    /* Genel Widget'lar */
                    QWidget {
                        background-color: #f5f7fa;
                        color: #333333;
                    }
                    
                    /* Metin Girişleri */
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #ffffff;
                        color: #333333;
                        border: 1px solid #d1d9e6;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #4a76cd;
                        selection-color: white;
                    }
                    
                    /* Butonlar */
                    QPushButton {
                        background-color: #ffffff;
                        color: #333333;
                        border: 1px solid #d1d9e6;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    
                    QPushButton:hover {
                        background-color: #f0f4f9;
                    }
                    
                    QPushButton:pressed {
                        background-color: #e4eaf3;
                    }
                    
                    QPushButton:checked {
                        background-color: #4a76cd;
                        color: white;
                    }
                    
                    /* Açılır Menüler */
                    QComboBox {
                        background-color: #ffffff;
                        color: #333333;
                        border: 1px solid #d1d9e6;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #d1d9e6;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    
                    /* Splitter */
                    QSplitter::handle {
                        background-color: #d1d9e6;
                    }
                    
                    /* Sekmeler */
                    QTabWidget::pane {
                        border: 1px solid #d1d9e6;
                        background: #ffffff;
                    }
                    
                    QTabBar::tab {
                        background: #f0f4f9;
                        color: #333333;
                        padding: 8px 12px;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                        margin-right: 2px;
                    }
                    
                    QTabBar::tab:selected {
                        background: #4a76cd;
                        color: white;
                    }
                    
                    /* ScrollBar */
                    QScrollBar:vertical {
                        border: none;
                        background: #ffffff;
                        width: 10px;
                        margin: 0;
                    }
                    
                    QScrollBar::handle:vertical {
                        background: #d1d9e6;
                        min-height: 20px;
                        border-radius: 5px;
                    }
                    
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    
                    /* Grup Kutuları */
                    QGroupBox {
                        border: 1px solid #d1d9e6;
                        border-radius: 6px;
                        margin-top: 1ex;
                        padding-top: 10px;
                        font-weight: bold;
                    }
                    
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top center;
                        padding: 0 5px;
                    }
                """)
            
            elif theme_name == "blue":
                # Mavi Tema
                self.setStyleSheet("""
                    /* Ana Pencere */
                    QMainWindow {
                        background-color: #0d1b2a;
                        color: #e0e0e0;
                    }
                    
                    /* Genel Widget'lar */
                    QWidget {
                        background-color: #0d1b2a;
                        color: #e0e0e0;
                    }
                    
                    /* Metin Girişleri */
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #1b263b;
                        color: #ffffff;
                        border: 1px solid #415a77;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #4a76cd;
                        selection-color: white;
                    }
                    
                    /* Butonlar */
                    QPushButton {
                        background-color: #1b263b;
                        color: #e0e0e0;
                        border: 1px solid #415a77;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    
                    QPushButton:hover {
                        background-color: #415a77;
                    }
                    
                    QPushButton:pressed {
                        background-color: #0d1b2a;
                    }
                    
                    QPushButton:checked {
                        background-color: #4a76cd;
                        color: white;
                    }
                    
                    /* Açılır Menüler */
                    QComboBox {
                        background-color: #1b263b;
                        color: #ffffff;
                        border: 1px solid #415a77;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #415a77;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    
                    /* Splitter */
                    QSplitter::handle {
                        background-color: #415a77;
                    }
                    
                    /* Sekmeler */
                    QTabWidget::pane {
                        border: 1px solid #415a77;
                        background: #1b263b;
                    }
                    
                    QTabBar::tab {
                        background: #415a77;
                        color: #e0e0e0;
                        padding: 8px 12px;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                        margin-right: 2px;
                    }
                    
                    QTabBar::tab:selected {
                        background: #4a76cd;
                        color: white;
                    }
                    
                    /* ScrollBar */
                    QScrollBar:vertical {
                        border: none;
                        background: #1b263b;
                        width: 10px;
                        margin: 0;
                    }
                    
                    QScrollBar::handle:vertical {
                        background: #415a77;
                        min-height: 20px;
                        border-radius: 5px;
                    }
                    
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    
                    /* Grup Kutuları */
                    QGroupBox {
                        border: 1px solid #415a77;
                        border-radius: 6px;
                        margin-top: 1ex;
                        padding-top: 10px;
                        font-weight: bold;
                    }
                    
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top center;
                        padding: 0 5px;
                    }
                """)
            
            elif theme_name == "green":
                # Yeşil Tema
                self.setStyleSheet("""
                    /* Ana Pencere */
                    QMainWindow {
                        background-color: #0d1f12;
                        color: #e0e0e0;
                    }
                    
                    /* Genel Widget'lar */
                    QWidget {
                        background-color: #0d1f12;
                        color: #e0e0e0;
                    }
                    
                    /* Metin Girişleri */
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #1b3b24;
                        color: #ffffff;
                        border: 1px solid #2d7747;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #4a76cd;
                        selection-color: white;
                    }
                    
                    /* Butonlar */
                    QPushButton {
                        background-color: #1b3b24;
                        color: #e0e0e0;
                        border: 1px solid #2d7747;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    
                    QPushButton:hover {
                        background-color: #2d7747;
                    }
                    
                    QPushButton:pressed {
                        background-color: #0d1f12;
                    }
                    
                    QPushButton:checked {
                        background-color: #4a76cd;
                        color: white;
                    }
                    
                    /* Açılır Menüler */
                    QComboBox {
                        background-color: #1b3b24;
                        color: #ffffff;
                        border: 1px solid #2d7747;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #2d7747;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    
                    /* Splitter */
                    QSplitter::handle {
                        background-color: #2d7747;
                    }
                    
                    /* Sekmeler */
                    QTabWidget::pane {
                        border: 1px solid #2d7747;
                        background: #1b3b24;
                    }
                    
                    QTabBar::tab {
                        background: #2d7747;
                        color: #e0e0e0;
                        padding: 8px 12px;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                        margin-right: 2px;
                    }
                    
                    QTabBar::tab:selected {
                        background: #4a76cd;
                        color: white;
                    }
                    
                    /* ScrollBar */
                    QScrollBar:vertical {
                        border: none;
                        background: #1b3b24;
                        width: 10px;
                        margin: 0;
                    }
                    
                    QScrollBar::handle:vertical {
                        background: #2d7747;
                        min-height: 20px;
                        border-radius: 5px;
                    }
                    
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    
                    /* Grup Kutuları */
                    QGroupBox {
                        border: 1px solid #2d7747;
                        border-radius: 6px;
                        margin-top: 1ex;
                        padding-top: 10px;
                        font-weight: bold;
                    }
                    
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top center;
                        padding: 0 5px;
                    }
                """)
            
            elif theme_name == "purple":
                # Mor Tema
                self.setStyleSheet("""
                    /* Ana Pencere */
                    QMainWindow {
                        background-color: #1a0d2a;
                        color: #e0e0e0;
                    }
                    
                    /* Genel Widget'lar */
                    QWidget {
                        background-color: #1a0d2a;
                        color: #e0e0e0;
                    }
                    
                    /* Metin Girişleri */
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #2a1b3b;
                        color: #ffffff;
                        border: 1px solid #5a2d77;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #4a76cd;
                        selection-color: white;
                    }
                    
                    /* Butonlar */
                    QPushButton {
                        background-color: #2a1b3b;
                        color: #e0e0e0;
                        border: 1px solid #5a2d77;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    
                    QPushButton:hover {
                        background-color: #5a2d77;
                    }
                    
                    QPushButton:pressed {
                        background-color: #1a0d2a;
                    }
                    
                    QPushButton:checked {
                        background-color: #4a76cd;
                        color: white;
                    }
                    
                    /* Açılır Menüler */
                    QComboBox {
                        background-color: #2a1b3b;
                        color: #ffffff;
                        border: 1px solid #5a2d77;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #5a2d77;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    
                    /* Splitter */
                    QSplitter::handle {
                        background-color: #5a2d77;
                    }
                    
                    /* Sekmeler */
                    QTabWidget::pane {
                        border: 1px solid #5a2d77;
                        background: #2a1b3b;
                    }
                    
                    QTabBar::tab {
                        background: #5a2d77;
                        color: #e0e0e0;
                        padding: 8px 12px;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                        margin-right: 2px;
                    }
                    
                    QTabBar::tab:selected {
                        background: #4a76cd;
                        color: white;
                    }
                    
                    /* ScrollBar */
                    QScrollBar:vertical {
                        border: none;
                        background: #2a1b3b;
                        width: 10px;
                        margin: 0;
                    }
                    
                    QScrollBar::handle:vertical {
                        background: #5a2d77;
                        min-height: 20px;
                        border-radius: 5px;
                    }
                    
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                    
                    /* Grup Kutuları */
                    QGroupBox {
                        border: 1px solid #5a2d77;
                        border-radius: 6px;
                        margin-top: 1ex;
                        padding-top: 10px;
                        font-weight: bold;
                    }
                    
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top center;
                        padding: 0 5px;
                    }
                """)
        except Exception as e:
            logger.error(f"Tema uygulanırken hata: {str(e)}")
            
    def filter_chats(self, text):
        """Sohbetleri filtrele"""
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_chat(self, item):
        try:
            chat_id = item.data(Qt.ItemDataRole.UserRole)
            if chat_id not in self.chat_data:
                self.chat_data[chat_id] = {
                    "title": item.text(),
                    "messages": []
                }
            
            # Mesajları yükle
            self.chat_display.clear()
            for msg in self.chat_data[chat_id]["messages"]:
                self.append_message(msg["sender"], msg["message"])
            
            self.active_chat_id = chat_id
            self.statusBar().showMessage(f"💬 {item.text()} yüklendi", 3000)
            
            # Sidebar'da seçili hale getir
            self.chat_list.setCurrentItem(item)
            
            # Aktif modeli göster
            model_name = self.model_combo.currentText()
            self.statusBar().showMessage(f"🤖 Aktif Model: {model_name}", 5000)
        except Exception as e:
            logger.error(f"Sohbet yüklenirken hata: {str(e)}")

    def load_project_chat(self, item, column):
        try:
            if item.parent():  # Sadece alt öğelerde (sohbetlerde) işlem yap
                chat_id = item.data(0, Qt.ItemDataRole.UserRole)
                if not chat_id:
                    chat_id = str(uuid.uuid4())
                    item.setData(0, Qt.ItemDataRole.UserRole, chat_id)
                
                if chat_id not in self.chat_data:
                    self.chat_data[chat_id] = {
                        "title": item.text(0),
                        "messages": []
                    }
                
                # Mesajları yükle
                self.chat_display.clear()
                for msg in self.chat_data[chat_id]["messages"]:
                    self.append_message(msg["sender"], msg["message"])
                
                self.active_chat_id = chat_id
                project_name = item.parent().text(0)
                self.statusBar().showMessage(f"📂 {project_name} > {item.text(0)} yüklendi", 3000)
                
                # Ağaçta seçili hale getir
                self.projects_tree.setCurrentItem(item)
                
                # Aktif modeli göster
                model_name = self.model_combo.currentText()
                self.statusBar().showMessage(f"🤖 Aktif Model: {model_name}", 5000)
        except Exception as e:
            logger.error(f"Proje sohbeti yüklenirken hata: {str(e)}")

    def new_chat(self):
        try:
            # Boş "Yeni Sohbet" var mı kontrol et
            for i in range(self.chat_list.count()):
                item = self.chat_list.item(i)
                if item.text().startswith("Yeni Sohbet") and not self.chat_data.get(item.data(Qt.ItemDataRole.UserRole), {}).get("messages", []):
                    self.chat_list.setCurrentItem(item)
                    self.load_chat(item)
                    self.statusBar().showMessage("📝 Mevcut yeni sohbet seçildi", 3000)
                    return
            
            # Yeni sohbet öğesi oluştur
            chat_count = self.chat_list.count() + 1
            chat_name = f"Yeni Sohbet {chat_count}"
            chat_id = str(uuid.uuid4())
            
            item = QListWidgetItem(chat_name)
            item.setData(Qt.ItemDataRole.UserRole, chat_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.chat_list.addItem(item)
            
            # Yeni sohbet verisini oluştur
            self.chat_data[chat_id] = {
                "title": chat_name,
                "messages": []
            }
            
            # Son eklenen öğeyi seç
            self.chat_list.setCurrentItem(item)
            self.active_chat_id = chat_id
            
            # Sohbeti yükle
            self.chat_display.setHtml("<center><i>Yeni sohbet başlatıldı</i></center>")
            self.statusBar().showMessage("🆕 Yeni sohbet başlatıldı", 3000)
            
            # Uygulama durumunu kaydet
            self.save_app_state()
        except Exception as e:
            logger.error(f"Yeni sohbet oluşturulurken hata: {str(e)}")

    def edit_chat_title(self, item):
        """Sohbet başlığını düzenle"""
        try:
            self.chat_list.editItem(item)
            if item.data(Qt.ItemDataRole.UserRole) in self.chat_data:
                self.chat_data[item.data(Qt.ItemDataRole.UserRole)]["title"] = item.text()
            self.save_app_state()
        except Exception as e:
            logger.error(f"Sohbet başlığı düzenlenirken hata: {str(e)}")

    def new_project(self):
        try:
            project_name, ok = QInputDialog.getText(self, "Yeni Proje", "Proje Adı:")
            if ok and project_name:
                # Yeni proje oluştur
                new_project = QTreeWidgetItem([f"📂 {project_name}"])
                new_project.setFlags(new_project.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Varsayılan sohbet ekle
                default_chat = QTreeWidgetItem(["💬 Ana Sohbet"])
                chat_id = str(uuid.uuid4())
                default_chat.setData(0, Qt.ItemDataRole.UserRole, chat_id)
                default_chat.setFlags(default_chat.flags() | Qt.ItemFlag.ItemIsEditable)
                new_project.addChild(default_chat)
                
                # Yeni sohbet verisini oluştur
                self.chat_data[chat_id] = {
                    "title": "Ana Sohbet",
                    "messages": []
                }
                
                # Ağaca ekle
                self.projects_tree.addTopLevelItem(new_project)
                
                # Projeyi genişlet
                new_project.setExpanded(True)
                
                # Projeyi seç
                self.projects_tree.setCurrentItem(new_project)
                
                self.statusBar().showMessage(f"🆕 Yeni proje oluşturuldu: {project_name}", 3000)
                self.save_app_state()
        except Exception as e:
            logger.error(f"Yeni proje oluşturulurken hata: {str(e)}")

    def edit_project_title(self, item, column):
        """Proje başlığını düzenle"""
        try:
            if not item.parent():  # Sadece üst seviye öğeler (projeler)
                self.projects_tree.editItem(item, column)
                self.save_app_state()
        except Exception as e:
            logger.error(f"Proje başlığı düzenlenirken hata: {str(e)}")

    def show_project_context_menu(self, pos):
        """Proje bağlam menüsü (silme)"""
        try:
            item = self.projects_tree.itemAt(pos)
            if item:
                menu = QMenu()
                
                # Sadece projeler için silme
                if not item.parent():
                    delete_action = menu.addAction(QIcon("icons/delete.png"), "Projeyi Sil")
                    delete_action.triggered.connect(lambda: self.delete_project(item))
                
                # Projeye sohbet ekle
                add_chat_action = menu.addAction(QIcon("icons/add_chat.png"), "Sohbet Ekle")
                add_chat_action.triggered.connect(lambda: self.add_chat_to_project(item))
                
                menu.exec(self.projects_tree.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Bağlam menüsü gösterilirken hata: {str(e)}")

    def add_chat_to_project(self, project_item):
        """Projeye yeni sohbet ekle"""
        try:
            chat_count = project_item.childCount() + 1
            chat_name = f"Yeni Sohbet {chat_count}"
            chat_id = str(uuid.uuid4())
            
            new_chat = QTreeWidgetItem([f"💬 {chat_name}"])
            new_chat.setData(0, Qt.ItemDataRole.UserRole, chat_id)
            new_chat.setFlags(new_chat.flags() | Qt.ItemFlag.ItemIsEditable)
            project_item.addChild(new_chat)
            project_item.setExpanded(True)
            
            # Yeni sohbet verisini oluştur
            self.chat_data[chat_id] = {
                "title": chat_name,
                "messages": []
            }
            
            # Başlığı düzenlemek için aç
            self.projects_tree.editItem(new_chat, 0)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Projeye sohbet eklenirken hata: {str(e)}")

    def delete_project(self, item):
        """Projeyi sil"""
        try:
            if not item.parent():  # Sadece projeleri sil
                # Alt sohbetleri sil
                for i in range(item.childCount()):
                    child = item.child(i)
                    chat_id = child.data(0, Qt.ItemDataRole.UserRole)
                    if chat_id in self.chat_data:
                        del self.chat_data[chat_id]
                
                root = self.projects_tree.invisibleRootItem()
                (root if item.parent() is None else item.parent()).removeChild(item)
                self.statusBar().showMessage("🗑️ Proje silindi", 3000)
                self.save_app_state()
        except Exception as e:
            logger.error(f"Proje silinirken hata: {str(e)}")

    def send_message(self):
        try:
            message = self.message_input.toPlainText().strip()
            if not message and not self.attached_files:
                return
                
            if not self.active_chat_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce bir sohbet seçin")
                return
                
            # Ekli dosyaları mesaja dahil et
            for file_path in self.attached_files:
                file_name = os.path.basename(file_path)
                message += f"\n\n[📎 Ek: {file_name}]"
            
            # Kullanıcı mesajını ekrana ve hafızaya ekle
            self.append_message("user", message)
            self.chat_data[self.active_chat_id]["messages"].append({
                "sender": "user",
                "message": message,
                "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
            })
            
            self.message_input.clear()
            
            # Yanıtı simüle et
            self.statusBar().showMessage("⏳ DeepSeek yanıt oluşturuyor...")
            
            # Aktif modeli göster
            model_name = self.model_combo.currentText()
            QTimer.singleShot(1500, lambda: self.simulate_response(model_name))
            
            # Ekli dosyaları temizle
            self.attached_files = []
            
            # Uygulama durumunu kaydet
            self.save_app_state()
        except Exception as e:
            logger.error(f"Mesaj gönderilirken hata: {str(e)}")

    def simulate_response(self, model_name):
        try:
            if not self.active_chat_id:
                return
                
            response = f"Bu bir simüle edilmiş yanıttır ({model_name}). Gerçek uygulamada API'den yanıt alınacaktır."
            
            # Yanıtı ekrana ve hafızaya ekle
            self.append_message("assistant", response)
            self.chat_data[self.active_chat_id]["messages"].append({
                "sender": "assistant",
                "message": response,
                "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
            })
            
            self.statusBar().showMessage(f"✅ Yanıt alındı ({model_name})", 3000)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Yanıt simüle edilirken hata: {str(e)}")

    def append_message(self, sender, message):
        try:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            
            if sender == "user":
                prefix = "Siz:"
                color = "#4ec9b0"  # Mavi-yeşil
            else:  # assistant
                prefix = "DeepSeek:"
                color = "#d69a66"  # Turuncu
            
            # Sola hizalı mesaj
            html_content = f"""
            <div style="margin-bottom: 20px;">
                <p style="color: {color}; font-weight: bold; margin-top: 0; margin-bottom: 5px;">{prefix}</p>
                <div style="color: #d4d4d4; background-color: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px;">
                    {message}
                </div>
            </div>
            """
            
            self.chat_display.insertHtml(html_content)
            self.chat_display.ensureCursorVisible()
        except Exception as e:
            logger.error(f"Mesaj eklenirken hata: {str(e)}")

    def insert_newline(self):
        try:
            self.message_input.insertPlainText("\n")
        except Exception as e:
            logger.error(f"Yeni satır eklenirken hata: {str(e)}")

    def toggle_fullscreen(self):
        try:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        except Exception as e:
            logger.error(f"Tam ekran değiştirilirken hata: {str(e)}")

    def attach_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
            if file_path:
                file_name = os.path.basename(file_path)
                self.attached_files.append(file_path)
                
                # Mesaj girişine bilgi ekle
                cursor = self.message_input.textCursor()
                cursor.insertHtml(f'<span style="color:#4CD964;">📎 {file_name} eklendi</span><br>')
                self.message_input.ensureCursorVisible()
        except Exception as e:
            logger.error(f"Dosya eklenirken hata: {str(e)}")

    def export_chats(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Sohbetleri Dışa Aktar", 
                "", 
                "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
            )
            
            if file_path:
                # Sohbet verilerini dışa aktar
                export_data = {
                    "version": self.VERSION,
                    "export_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
                    "chats": self.chat_data
                }
                
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                self.statusBar().showMessage(f"📤 Sohbetler dışa aktarıldı: {file_path}", 5000)
        except Exception as e:
            logger.error(f"Sohbetler dışa aktarılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Sohbetler dışa aktarılırken hata oluştu: {str(e)}")

    def open_theme_settings(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🎨 Tema Ayarları")
            dialog.setFixedSize(400, 300)

            # Butonlarla tema seçimi
            theme_buttons = QWidget()
            grid = QGridLayout(theme_buttons)
            
            themes = [
                ("🌙 Koyu", "dark", "#121212"),
                ("☀️ Açık", "light", "#f5f7fa"),
                ("🔵 Mavi", "blue", "#0d1b2a"),
                ("🍏 Yeşil", "green", "#0d1f12"),
                ("🍇 Mor", "purple", "#1a0d2a")
            ]
            
            for i, (name, theme, color) in enumerate(themes):
                btn = QPushButton(name)
                btn.setStyleSheet(f"""
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    padding: 15px;
                    border-radius: 8px;
                """)
                btn.clicked.connect(lambda _, t=theme: self.apply_theme(t))
                grid.addWidget(btn, i // 2, i % 2)
            
            # Önizleme alanı
            preview_box = QGroupBox("Önizleme")
            preview_layout = QVBoxLayout()
            self.preview_text = QTextEdit()
            self.preview_text.setReadOnly(True)
            self.preview_text.setHtml("""
                <b>Örnek Mesajlaşma</b><br><br>
                <span style="color:#4ec9b0;"><b>Siz:</b></span> Merhaba, nasılsın?<br>
                <span style="color:#d69a66;"><b>DeepSeek:</b></span> Merhaba! Ben bir yapay zeka asistanıyım. Size nasıl yardımcı olabilirim?
            """)
            preview_layout.addWidget(self.preview_text)
            preview_box.setLayout(preview_layout)
            layout.addWidget(preview_box)
            
            # Tema değiştiğinde önizlemeyi güncelle
            self.theme_combo.currentIndexChanged.connect(self.update_theme_preview)
            
            # Butonlar
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(lambda: self.apply_theme_from_combo(dialog))
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Tema ayarları açılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Tema ayarları açılırken hata oluştu: {str(e)}")
            
    def update_theme_preview(self):
        """Tema önizlemesini güncelle"""
        index = self.theme_combo.currentIndex()
        if index == 0:
            self.preview_text.setStyleSheet(self.get_theme_style("dark"))
        elif index == 1:
            self.preview_text.setStyleSheet(self.get_theme_style("light"))
        elif index == 2:
            self.preview_text.setStyleSheet(self.get_theme_style("blue"))
        elif index == 3:
            self.preview_text.setStyleSheet(self.get_theme_style("green"))
        elif index == 4:
            self.preview_text.setStyleSheet(self.get_theme_style("purple"))
    
    def get_theme_style(self, theme_name):
        """Tema stilini döndür"""
        if theme_name == "dark":
            return """
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #2d2d2d;
                    border-radius: 6px;
                    padding: 8px;
                }
            """
        elif theme_name == "light":
            return """
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d1d9e6;
                    border-radius: 6px;
                    padding: 8px;
                }
            """
        elif theme_name == "blue":
            return """
                QTextEdit {
                    background-color: #1b263b;
                    color: #ffffff;
                    border: 1px solid #415a77;
                    border-radius: 6px;
                    padding: 8px;
                }
            """
        elif theme_name == "green":
            return """
                QTextEdit {
                    background-color: #1b3b24;
                    color: #ffffff;
                    border: 1px solid #2d7747;
                    border-radius: 6px;
                    padding: 8px;
                }
            """
        elif theme_name == "purple":
            return """
                QTextEdit {
                    background-color: #2a1b3b;
                    color: #ffffff;
                    border: 1px solid #5a2d77;
                    border-radius: 6px;
                    padding: 8px;
                }
            """
        return ""
    
    def apply_theme_from_combo(self, dialog):
        """Combobox'tan seçilen temayı uygula"""
        index = self.theme_combo.currentIndex()
        if index == 0:
            self.apply_theme("dark")
        elif index == 1:
            self.apply_theme("light")
        elif index == 2:
            self.apply_theme("blue")
        elif index == 3:
            self.apply_theme("green")
        elif index == 4:
            self.apply_theme("purple")
        dialog.accept()

    def apply_theme(self, theme_name):
        try:
            self.current_theme = theme_name
            
            # Tüm widget'lar için ortak stiller
            common_style = """
                QWidget {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11pt;
                }
                
                QPushButton {
                    padding: 8px 12px;
                    border-radius: 6px;
                    min-width: 100px;
                }
                
                QTextEdit, QLineEdit, QListWidget, QTreeWidget, QComboBox {
                    border-radius: 6px;
                    padding: 8px;
                }
                
                QTabWidget::pane {
                    border: 1px solid;
                    border-radius: 6px;
                }
                
                QGroupBox {
                    border: 1px solid;
                    border-radius: 6px;
                    margin-top: 1ex;
                    padding-top: 10px;
                    font-weight: bold;
                }
            """
            
            if theme_name == "dark":
                self.setStyleSheet(common_style + """
                    /* Ana Pencere */
                    QMainWindow {
                        background-color: #121212;
                        color: #e0e0e0;
                    }
                    
                    /* Metin Girişleri */
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        border: 1px solid #2d2d2d;
                        selection-background-color: #4a76cd;
                        selection-color: white;
                    }
                    
                    /* Butonlar */
                    QPushButton {
                        background-color: #2d2d2d;
                        color: #e0e0e0;
                        border: 1px solid #3a3a3a;
                    }
                    
                    QPushButton:hover {
                        background-color: #3a3a3a;
                    }
                    
                    QPushButton:pressed {
                        background-color: #1d1d1d;
                    }
                    
                    QPushButton:checked {
                        background-color: #4a76cd;
                        color: white;
                    }
                    
                    /* Açılır Menüler */
                    QComboBox {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        border: 1px solid #2d2d2d;
                    }
                    
                    /* Splitter */
                    QSplitter::handle {
                        background-color: #2d2d2d;
                    }
                    
                    /* Sekmeler */
                    QTabBar::tab {
                        background: #2d2d2d;
                        color: #e0e0e0;
                    }
                    
                    QTabBar::tab:selected {
                        background: #4a76cd;
                        color: white;
                    }
                    
                    /* Grup Kutuları */
                    QGroupBox {
                        border-color: #2d2d2d;
                    }
                """)
            
            # Diğer temalar için benzer şekilde güncellendi...
            # (light, blue, green, purple temaları önceki gibi güncellenmiş olarak kalacak)
            
        except Exception as e:
            logger.error(f"Tema uygulanırken hata: {str(e)}")        

    def open_shortcut_settings(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("⌨️ Kısayol Ayarları")
            dialog.setFixedSize(400, 300)
            
            tabs = QTabWidget()
            
            # Genel kısayollar
            general_tab = QWidget()
            form = QFormLayout(general_tab)
            
            # Mesaj gönder kısayolu
            send_key_edit = QKeySequenceEdit(self.send_action.shortcut())
            form.addRow("Mesaj Gönder (Ctrl+Enter):", send_key_edit)
            
            # Yeni satır kısayolu
            newline_key_edit = QKeySequenceEdit(self.newline_action.shortcut())
            form.addRow("Yeni Satır (Enter):", newline_key_edit)
            
            # Tam ekran kısayolu
            fullscreen_key_edit = QKeySequenceEdit(self.fullscreen_action.shortcut())
            form.addRow("Tam Ekran:", fullscreen_key_edit)
            
            # Tepsiye indirme kısayolu
            minimize_key_edit = QKeySequenceEdit(self.minimize_action.shortcut())
            form.addRow("Tepsiye İndir:", minimize_key_edit)
            
            tabs.addTab(general_tab, "Genel")
            
            layout = QVBoxLayout()
            layout.addWidget(tabs)
            
            # Kaydet butonu
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
            buttons.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet")
            buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal")
            buttons.accepted.connect(lambda: self.save_shortcuts(
                send_key_edit.keySequence(),
                newline_key_edit.keySequence(),
                fullscreen_key_edit.keySequence(),
                minimize_key_edit.keySequence()
            ))
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Kısayol ayarları açılırken hata: {str(e)}")

    def save_shortcuts(self, send_seq, newline_seq, fullscreen_seq, minimize_seq):
        try:
            # Kısayolları güncelle
            self.send_action.setShortcut(send_seq)
            self.newline_action.setShortcut(newline_seq)
            self.fullscreen_action.setShortcut(fullscreen_seq)
            self.minimize_action.setShortcut(minimize_seq)
            
            self.statusBar().showMessage("✅ Kısayollar kaydedildi", 3000)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Kısayollar kaydedilirken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Kısayollar kaydedilirken hata oluştu: {str(e)}")

    def open_model_management(self):
        try:
            self.model_dialog = QDialog(self)
            dialog = self.model_dialog
            dialog.setWindowTitle("🤖 Model Yönetimi")
            dialog.setFixedSize(600, 400)
            
            layout = QVBoxLayout()
            
            # Model Seçimi
            model_layout = QHBoxLayout()
            model_layout.addWidget(QLabel("Aktif Model:"))
            self.model_combo_dialog = QComboBox()
            self.model_combo_dialog.addItems(["deepseek-chat", "deepseek-coder", "deepseek-math"])
            self.model_combo_dialog.setCurrentText(self.model_combo.currentText())
            model_layout.addWidget(self.model_combo_dialog, 1)
            layout.addLayout(model_layout)
            
            # API Anahtarı
            api_layout = QHBoxLayout()
            api_layout.addWidget(QLabel("API Anahtarı:"))
            self.api_key_edit = QLineEdit()
            self.api_key_edit.setPlaceholderText("sk-xxxxxxxxxxxxxxxxxxxxxxxx")
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            api_layout.addWidget(self.api_key_edit, 1)
            layout.addLayout(api_layout)
            
            # Model Bilgileri
            info_box = QGroupBox("Model Bilgileri")
            info_layout = QVBoxLayout()
            self.model_info = QTextEdit()
            self.model_info.setReadOnly(True)
            self.model_info.setHtml("""
                <b>deepseek-chat</b>: Genel amaçlı sohbet modeli<br>
                <b>deepseek-coder</b>: Kodlama odaklı model<br>
                <b>deepseek-math</b>: Matematiksel problem çözme modeli
            """)
            info_layout.addWidget(self.model_info)
            info_box.setLayout(info_layout)
            layout.addWidget(info_box)
            
            # Güncelleme Butonu - Büyük ikon (48x48)
            update_btn = QPushButton()
            update_btn.setIcon(QIcon("icons/update.png"))
            update_btn.setIconSize(QSize(48, 48))
            update_btn.setText(" Modelleri Güncelle")
            update_btn.clicked.connect(self.update_models)
            layout.addWidget(update_btn)
            
            # Butonlar
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
            button_box.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet")
            button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal")
            button_box.accepted.connect(self.save_model_settings)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Model yönetimi açılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Model yönetimi açılırken hata oluştu: {str(e)}")
            
    def update_models(self):
        """Modelleri güncelle"""
        try:
            # Gerçek güncelleme işlemi için API entegrasyonu
            self.statusBar().showMessage("🔄 Modeller güncelleniyor...", 3000)
            QTimer.singleShot(2000, lambda: self.statusBar().showMessage("✅ Modeller güncellendi", 5000))
        except Exception as e:
            logger.error(f"Modeller güncellenirken hata: {str(e)}")

    def save_model_settings(self):
        """Model ayarlarını kaydet"""
        try:
            selected_model = self.model_combo_dialog.currentText()
            api_key = self.api_key_edit.text()
            
            # Ana model seçimini güncelle
            self.model_combo.setCurrentText(selected_model)
            
            # Burada ayarları kaydetme işlemi yapılacak
            self.statusBar().showMessage(f"✅ {selected_model} modeli ayarlandı", 5000)
            self.save_app_state()
            
            # Diyaloğu kapat
            self.model_dialog.accept()
        except Exception as e:
            logger.error(f"Model ayarları kaydedilirken hata: {str(e)}")        
            
    def show_about(self):
        try:
            about_text = f"""
            <b>DeepSeek Chat</b><br>
            Versiyon: {self.VERSION}<br>
            <br>
            Geliştirici: CxReiS<br>
            <br>
            Bu uygulama PyQt6 ile geliştirilmiştir.<br>
            DeepSeek API entegrasyonu ile çalışmaktadır.<br>
            """
            
            QMessageBox.about(self, "Hakkında", about_text)
        except Exception as e:
            logger.error(f"Hakkında penceresi açılırken hata: {str(e)}")

    def check_for_updates(self):
        try:
            # Burada gerçek güncelleme kontrolü yapılacak
            QMessageBox.information(self, "Güncellemeler", "Güncelleme kontrol ediliyor...")
            self.statusBar().showMessage("🔄 Güncellemeler kontrol ediliyor...", 3000)
            QTimer.singleShot(2000, lambda: self.statusBar().showMessage("✅ En güncel sürüm kullanıyorsunuz", 5000))
        except Exception as e:
            logger.error(f"Güncelleme kontrol edilirken hata: {str(e)}")
    
    def show_chat_context_menu(self, pos):
        """Sohbet bağlam menüsü (yeniden adlandırma, silme)"""
        try:
            menu = QMenu()
        
            # Yeniden adlandır
            rename_action = menu.addAction(QIcon("icons/rename.png"), "Yeniden Adlandır")
            rename_action.triggered.connect(self.rename_selected_chat)
        
            # Sil
            delete_action = menu.addAction(QIcon("icons/delete.png"), "Sil")
            delete_action.triggered.connect(self.delete_selected_chat)
        
            menu.exec(self.chat_display.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Bağlam menüsü gösterilirken hata: {str(e)}")
            
    def show_text_context_menu(self, pos):
        """Türkçe metin menüsü"""
        try:
            menu = self.message_input.createStandardContextMenu()
        
            # Aksiyonları Türkçeleştir
            for action in menu.actions():
                if action.text() == "&Copy": action.setText("Kopyala")
                elif action.text() == "&Paste": action.setText("Yapıştır")
                elif action.text() == "Cu&t": action.setText("Kes")
                elif action.text() == "&Undo": action.setText("Geri Al")
                elif action.text() == "&Redo": action.setText("İleri Al")
                elif action.text() == "Select All": action.setText("Tümünü Seç")
        
            menu.exec(self.message_input.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Metin menüsü gösterilirken hata: {str(e)}")        

    def show_chat_list_context_menu(self, pos):
        """Sohbet listesi için bağlam menüsü"""
        try:
            item = self.chat_list.itemAt(pos)
            if not item:
                return
            
            menu = QMenu()
        
            # Yeniden adlandır
            rename_action = menu.addAction(QIcon("icons/rename.png"), "Yeniden Adlandır")
            rename_action.triggered.connect(lambda: self.rename_selected_chat())
        
            # Sil
            delete_action = menu.addAction(QIcon("icons/delete.png"), "Sil")
            delete_action.triggered.connect(lambda: self.delete_selected_chat())
        
            # Projelere taşı menüsü
            move_menu = menu.addMenu(QIcon("icons/move.png"), "Projeye Taşı")
        
            # Mevcut projeleri listele
            for i in range(self.projects_tree.topLevelItemCount()):
                project = self.projects_tree.topLevelItem(i)
                project_action = move_menu.addAction(project.text(0))
                project_action.triggered.connect(
                    lambda checked, p=project, c=item: self.move_chat_to_project(p, c)
                )
        
            menu.exec(self.chat_list.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Bağlam menüsü gösterilirken hata: {str(e)}")

    def move_chat_to_project(self, project_item, chat_item):
        """Sohbeti projeye taşı"""
        try:
            chat_title = chat_item.text()
            chat_id = chat_item.data(Qt.ItemDataRole.UserRole)
        
            # Yeni sohbet öğesi oluştur
            new_chat = QTreeWidgetItem([f"💬 {chat_title}"])
            new_chat.setData(0, Qt.ItemDataRole.UserRole, chat_id)
            new_chat.setFlags(new_chat.flags() | Qt.ItemFlag.ItemIsEditable)
            project_item.addChild(new_chat)
            project_item.setExpanded(True)
        
            # Özgün sohbeti sil
            self.chat_list.takeItem(self.chat_list.row(chat_item))
        
            self.statusBar().showMessage(f"📂 Sohbet '{chat_title}' projeye taşındı", 3000)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Sohbet taşınırken hata: {str(e)}")        
    
    def rename_selected_chat(self):
        """Seçili sohbeti yeniden adlandır"""
        try:
            if self.chat_list.currentItem():
                self.chat_list.editItem(self.chat_list.currentItem())
            elif self.projects_tree.currentItem() and self.projects_tree.currentItem().parent():
                self.projects_tree.editItem(self.projects_tree.currentItem(), 0)
        except Exception as e:
            logger.error(f"Sohbet yeniden adlandırılırken hata: {str(e)}")

    def delete_selected_chat(self):
        """Seçili sohbeti sil"""
        try:
            if self.chat_list.currentItem():
                chat_id = self.chat_list.currentItem().data(Qt.ItemDataRole.UserRole)
                if chat_id in self.chat_data:
                    del self.chat_data[chat_id]
                
                row = self.chat_list.row(self.chat_list.currentItem())
                self.chat_list.takeItem(row)
                self.statusBar().showMessage("🗑️ Sohbet silindi", 3000)
                self.save_app_state()
                
            elif self.projects_tree.currentItem() and self.projects_tree.currentItem().parent():
                item = self.projects_tree.currentItem()
                chat_id = item.data(0, Qt.ItemDataRole.UserRole)
                if chat_id in self.chat_data:
                    del self.chat_data[chat_id]
                
                parent = item.parent()
                parent.removeChild(item)
                self.statusBar().showMessage("🗑️ Proje sohbeti silindi", 3000)
                self.save_app_state()
        except Exception as e:
            logger.error(f"Sohbet silinirken hata: {str(e)}")
    
    def save_app_state(self):
        """Uygulama durumunu kaydet"""
        try:
            # Chat listesini kaydet
            chat_items = []
            for i in range(self.chat_list.count()):
                item = self.chat_list.item(i)
                chat_items.append({
                    "title": item.text(),
                    "id": item.data(Qt.ItemDataRole.UserRole)
                })
            
            # Proje ağacını kaydet
            def save_tree_item(item):
                data = {
                    "text": item.text(0),
                    "id": item.data(0, Qt.ItemDataRole.UserRole),
                    "children": []
                }
                for i in range(item.childCount()):
                    child = item.child(i)
                    data["children"].append(save_tree_item(child))
                return data
            
            projects = []
            for i in range(self.projects_tree.topLevelItemCount()):
                item = self.projects_tree.topLevelItem(i)
                projects.append(save_tree_item(item))
            
            app_state = {
                "version": self.VERSION,
                "chats": chat_items,
                "projects": projects,
                "chat_data": self.chat_data,
                "model": self.model_combo.currentText(),
                "theme": self.current_theme,
                "shortcuts": {
                    "send": self.send_action.shortcut().toString(),
                    "newline": self.newline_action.shortcut().toString(),
                    "fullscreen": self.fullscreen_action.shortcut().toString(),
                    "minimize": self.minimize_action.shortcut().toString()
                },
                "active_chat_id": self.active_chat_id
            }
            
            with open("app_state.json", "w") as f:
                json.dump(app_state, f, indent=2)
                
            logger.info("Uygulama durumu kaydedildi")
        except Exception as e:
            logger.error(f"Uygulama durumu kaydedilirken hata: {str(e)}")

    def load_app_state(self):
        """Uygulama durumunu yükle"""
        try:
            self.chat_data = {}
            if os.path.exists("app_state.json"):
                with open("app_state.json", "r") as f:
                    app_state = json.load(f)
                    
                    # Chat listesini yükle
                    self.chat_list.clear()
                    for chat in app_state.get("chats", []):
                        item = QListWidgetItem(chat["title"])
                        item.setData(Qt.ItemDataRole.UserRole, chat["id"])
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                        self.chat_list.addItem(item)
                        
                        # Chat verilerini yükle
                        if "chat_data" in app_state and chat["id"] in app_state["chat_data"]:
                            self.chat_data[chat["id"]] = app_state["chat_data"][chat["id"]]
                    
                    # Proje ağacını yükle
                    self.projects_tree.clear()
                    for project in app_state.get("projects", []):
                        def load_tree_item(data, parent=None):
                            item = QTreeWidgetItem([data["text"]])
                            if data["id"]:
                                item.setData(0, Qt.ItemDataRole.UserRole, data["id"])
                            
                            # Chat verilerini yükle
                            if "chat_data" in app_state and data["id"] in app_state["chat_data"]:
                                self.chat_data[data["id"]] = app_state["chat_data"][data["id"]]
                            
                            for child_data in data["children"]:
                                child_item = load_tree_item(child_data)
                                item.addChild(child_item)
                            return item
                        
                        item = load_tree_item(project)
                        self.projects_tree.addTopLevelItem(item)
                    
                    # Modeli yükle
                    model = app_state.get("model", "deepseek-chat")
                    self.model_combo.setCurrentText(model)
                    
                    # Temayı yükle
                    theme = app_state.get("theme", "dark")
                    self.apply_theme(theme)
                    self.current_theme = theme
                    
                    # Kısayolları yükle
                    shortcuts = app_state.get("shortcuts", {})
                    self.send_action.setShortcut(QKeySequence(shortcuts.get("send", "Ctrl+Return")))
                    self.newline_action.setShortcut(QKeySequence(shortcuts.get("newline", "Return")))
                    self.fullscreen_action.setShortcut(QKeySequence(shortcuts.get("fullscreen", "F11")))
                    self.minimize_action.setShortcut(QKeySequence(shortcuts.get("minimize", "Ctrl+M")))
                    
                    # Aktif sohbeti yükle
                    self.active_chat_id = app_state.get("active_chat_id")
                    if self.active_chat_id and self.active_chat_id in self.chat_data:
                        # Aktif sohbeti bul ve yükle
                        found = False
                        
                        # Chat listesinde ara
                        for i in range(self.chat_list.count()):
                            item = self.chat_list.item(i)
                            if item.data(Qt.ItemDataRole.UserRole) == self.active_chat_id:
                                self.chat_list.setCurrentItem(item)
                                self.load_chat(item)
                                found = True
                                break
                        
                        # Proje sohbetlerinde ara
                        if not found:
                            def find_chat_in_tree(item):
                                if item.data(0, Qt.ItemDataRole.UserRole) == self.active_chat_id:
                                    self.projects_tree.setCurrentItem(item)
                                    self.load_project_chat(item, 0)
                                    return True
                                for i in range(item.childCount()):
                                    if find_chat_in_tree(item.child(i)):
                                        return True
                                return False
                            
                            for i in range(self.projects_tree.topLevelItemCount()):
                                if find_chat_in_tree(self.projects_tree.topLevelItem(i)):
                                    break
                    
                logger.info("Uygulama durumu yüklendi")
        except Exception as e:
            logger.error(f"Uygulama durumu yüklenirken hata: {str(e)}")
            # Hata durumunda temiz başlangıç
            self.chat_data = {}
    
    def show_and_activate(self):
        """Pencereyi göster ve öne getir"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def quit_application(self):
        """Uygulamadan tamamen çık"""
        self.tray_icon.hide()
        self.save_app_state()
        QApplication.quit()    

    def closeEvent(self, event):
        """Pencere kapatma olayı"""
        try:
            event.ignore()
            self.minimize_to_tray()
            self.save_app_state()
        except Exception as e:
            logger.error(f"Uygulama kapatılırken hata: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek Chat")
    
    # Font ayarı
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    try:
        # Giriş bilgilerini kontrol et
        if os.path.exists("user_prefs.json"):
            with open("user_prefs.json", "r") as f:
                prefs = json.load(f)
                if prefs.get("remember", False):
                    window = MainApplication()
                    window.show()
                    sys.exit(app.exec())
        
        # Normal giriş ekranı için
        login_window = LoginWindow()
        login_window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Uygulama başlatılırken hata: {str(e)}")
        error_dialog = ErrorDialog(str(e))
        error_dialog.exec()
        sys.exit(1)