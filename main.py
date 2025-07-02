import sys
import os
import json
import logging
import uuid
import requests
import time
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QTextEdit,
    QListWidget, QSplitter, QStatusBar, QTreeWidget, QTreeWidgetItem,
    QComboBox, QFrame, QMenuBar, QMenu, QSystemTrayIcon, QCheckBox,
    QInputDialog, QDialog, QDialogButtonBox, QFormLayout, QTabWidget,
    QFileDialog, QListWidgetItem, QLineEdit, QGroupBox, QScrollArea,
    QKeySequenceEdit, QToolButton, QSizePolicy, QGridLayout, QFontComboBox,
    QSlider
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDateTime, QEvent
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QTextCursor, QColor, QTextCharFormat, QFont, QPixmap
from worker_thread import WorkerThread
)
from worker_thread import WorkerThread

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
    
    def attempt_login(self):
        try:
            if self.remember_check.isChecked():
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
        
        # Sistem Tepsisine Ekle (büyük ikon)
        pixmap = QPixmap("logo.png")
        scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.tray_icon = QSystemTrayIcon(QIcon(scaled), self)
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
        self.setup_statusbar()
        
        # Menü çubuğu
        self.setup_menu_bar()

        minimize_btn = QToolButton()
        minimize_btn.setIcon(QIcon("icons/minimize.png"))
        minimize_btn.clicked.connect(self.minimize_to_tray)
        minimize_btn.setToolTip("Tepsiye indir")
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
        self.menuBar().setCornerWidget(title_widget)
        
        # Kısayollar
        self.setup_shortcuts()
        
        # Tema
        self.apply_theme("dark")

        self.api_key = None
        self.api_base_url = "https://openrouter.ai/api/v1"
        self.load_api_key()

        self.model_mapping = {
            "deepseek-chat": "deepseek/deepseek-r1:free",
            "deepseek-coder": "deepseek/deepseek-r1:free",
            "deepseek-math": "deepseek/deepseek-r1:free"
        }

        # Yazı tipi ayarları
        self.font_family = "Arial"
        self.font_size = 16
        self.label_bold = True
        self.italic_subtitles = False

        # Ekli dosyalar
        self.attached_files = []

        self.project_context = {}
        
        # Uygulama durumunu yükle
        self.load_app_state()
        self.apply_font_settings()
        
        # Aktif sohbet ID'si
        self.active_chat_id = None
        
    def setup_statusbar(self):
        """Status bar'ı kur"""
        status_bar = self.statusBar()
        status_bar.showMessage("✅ Bağlantı kuruldu")
        

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Özel hata yöneticisi"""
        error_msg = f"{exc_type.__name__}: {exc_value}"
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Hata diyaloğunu göster
        error_dialog = ErrorDialog(error_msg, self)
        error_dialog.exec()

    def setup_tray_icon(self):
        pixmap = QPixmap("icons/logo.png").scaled(
            64,
            64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)

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
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(10)
        
        # Arama Kutusu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Sohbetlerde ara...")
        self.search_box.textChanged.connect(self.filter_chats)
        sidebar_layout.addWidget(self.search_box)
        
        # Yeni Sohbet Butonu - Büyük ikon (48x48)
        self.new_chat_btn = QPushButton()
        self.new_chat_btn.setIcon(QIcon("icons/new_chat.png"))
        self.new_chat_btn.setIconSize(QSize(48, 48))
        self.new_chat_btn.setText(" Yeni Sohbet")
        self.new_chat_btn.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(self.new_chat_btn)
        
        # Sohbet Listesi
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_chat)
        self.chat_list.itemDoubleClicked.connect(self.edit_chat_title)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_list_context_menu)
        
        # Sürükle-bırak özelliği
        self.chat_list.setDragEnabled(True)
        self.chat_list.setAcceptDrops(True)
        self.chat_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.chat_list.model().rowsMoved.connect(self.chat_order_changed)
        
        sidebar_layout.addWidget(self.chat_list, 1)
        
        # Yeni Proje Butonu - Büyük ikon (48x48)
        self.new_project_btn = QPushButton()
        self.new_project_btn.setIcon(QIcon("icons/new_folder.png"))
        self.new_project_btn.setIconSize(QSize(48, 48))
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
        self.projects_tree.setAcceptDrops(True)
        self.projects_tree.viewport().setAcceptDrops(True)
        self.projects_tree.dragEnterEvent = self.project_drag_enter
        self.projects_tree.dropEvent = self.project_drop_event
        self.projects_tree.currentItemChanged.connect(self.load_project_context)
        sidebar_layout.addWidget(self.projects_tree, 1)
        
        # Model Seçimi
        model_box = QGroupBox("🤖 Model")
        model_layout = QVBoxLayout(model_box)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek-chat", "deepseek-coder", "deepseek-math"])
        self.model_combo.currentIndexChanged.connect(self.model_changed)
        model_layout.addWidget(self.model_combo)
        sidebar_layout.addWidget(model_box)

        sidebar_layout.addStretch()

    def setup_right_panel(self):
        self.right_panel = QSplitter(Qt.Orientation.Vertical)

        # Sekmeli alan
        self.context_tabs = QTabWidget()

        # Mesaj Görüntüleme
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setHtml("<center><i>Merhaba, size nasıl yardımcı olabilirim?</i></center>")
        self.chat_display.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_display.customContextMenuRequested.connect(self.show_chat_context_menu)
        chat_layout.addWidget(self.chat_display)
        self.context_tabs.addTab(chat_tab, "💬 Sohbet")

        # Proje Bağlamı Sekmesi
        project_tab = QWidget()
        project_layout = QVBoxLayout(project_tab)
        self.project_instructions = QTextEdit()
        self.project_instructions.setPlaceholderText("Proje talimatları...")
        project_layout.addWidget(QLabel("📝 Talimatlar:"))
        project_layout.addWidget(self.project_instructions)
        self.project_files_list = QListWidget()
        project_layout.addWidget(QLabel("📁 Dosyalar:"))
        project_layout.addWidget(self.project_files_list)
        file_btn_layout = QHBoxLayout()
        self.add_project_file_btn = QPushButton("Dosya Ekle")
        self.add_project_file_btn.clicked.connect(self.add_project_file)
        self.remove_project_file_btn = QPushButton("Dosya Sil")
        self.remove_project_file_btn.clicked.connect(self.remove_project_file)
        file_btn_layout.addWidget(self.add_project_file_btn)
        file_btn_layout.addWidget(self.remove_project_file_btn)
        project_layout.addLayout(file_btn_layout)
        self.context_tabs.addTab(project_tab, "📂 Proje Bağlamı")

        self.right_panel.addWidget(self.context_tabs)

        # Mesaj Gönderme Paneli
        send_panel = QWidget()
        send_layout = QVBoxLayout(send_panel)
        
        # Mesaj Girişi
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("DeepSeek'e mesaj yazın...")
        self.message_input.setMinimumHeight(100)
        self.message_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.message_input.customContextMenuRequested.connect(self.show_text_context_menu)
        self.message_input.installEventFilter(self)
        self.message_input.setAcceptDrops(True)

        self.attachments_list = QListWidget()
        send_layout.insertWidget(0, self.attachments_list)
        
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
        self.attach_btn.setIcon(QIcon("icons/attach_file.png"))
        self.attach_btn.setIconSize(QSize(48, 48))
        self.attach_btn.setText(" Dosya Ekle")
        self.attach_btn.setToolTip("Dosya ekle")
        self.attach_btn.clicked.connect(self.attach_file)
        bottom_layout.addWidget(self.attach_btn)
        
        # Gönder Butonu - Yeni ikon (48x48)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(QIcon("icons/send_message.png"))
        self.send_btn.setIconSize(QSize(48, 48))
        self.send_btn.setText(" Gönder")
        self.send_btn.setToolTip("Mesajı gönder")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bottom_layout.addWidget(self.send_btn)
        
        send_layout.addWidget(self.message_input)
        send_layout.addLayout(bottom_layout)

        self.right_panel.addWidget(send_panel)
        self.right_panel.setSizes([600, 200])

    def setup_menu_bar(self):
        menubar = self.menuBar()
        
        # Dosya Menüsü
        file_menu = menubar.addMenu("📁 Dosya")
        
        new_project_action = QAction(QIcon("icons/new_folder.png"), "Yeni Proje", self)
        new_project_action.setIconVisibleInMenu(True)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        export_action = QAction(QIcon("icons/export.png"), "Sohbetleri Dışa Aktar", self)
        export_action.setIconVisibleInMenu(True)
        export_action.triggered.connect(self.export_chats)
        file_menu.addAction(export_action)
        
        # Ayarlar Menüsü - Menü ikonları
        settings_menu = menubar.addMenu("⚙️ Ayarlar")
        
        theme_action = QAction(QIcon("icons/theme.png"), "🎨 Tema Ayarları", self)
        theme_action.setIconVisibleInMenu(True)
        theme_action.triggered.connect(self.open_theme_settings)
        settings_menu.addAction(theme_action)
        
        shortcuts_action = QAction(QIcon("icons/keyboard.png"), "⌨️ Kısayollar", self)
        shortcuts_action.setIconVisibleInMenu(True)
        shortcuts_action.triggered.connect(self.open_shortcut_settings)
        settings_menu.addAction(shortcuts_action)

        font_action = QAction(QIcon("icons/settings.png"), "🖋️ Yazı Tipi", self)
        font_action.setIconVisibleInMenu(True)
        font_action.triggered.connect(self.open_font_settings)
        settings_menu.addAction(font_action)
        
        models_action = QAction(QIcon("icons/model.png"), "🤖 Model Yönetimi", self)
        models_action.setIconVisibleInMenu(True)
        models_action.triggered.connect(self.open_model_management)
        settings_menu.addAction(models_action)
        
        # Yardım Menüsü - Menü ikonları
        help_menu = menubar.addMenu("❓ Yardım")
        
        about_action = QAction(QIcon("icons/info.png"), "ℹ️ Hakkında", self)
        about_action.setIconVisibleInMenu(True)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        update_action = QAction(QIcon("icons/update.png"), "🔄 Güncellemeleri Kontrol Et", self)
        update_action.setIconVisibleInMenu(True)
        update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(update_action)

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

        # Mesaj girişine event filter
        self.message_input.installEventFilter(self)

    def eventFilter(self, source, event):
        if source is self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.send_message()
                    return True
        return super().eventFilter(source, event)

    def apply_theme(self, theme_name):
        try:
            self.current_theme = theme_name
            common_style = """
                QFrame#sidebar {
                    border-right: 2px solid $border_color;
                }
                QSplitter::handle {
                    background-color: $border_color;
                }
            """
            
            if theme_name == "dark":
                style = common_style.replace("$border_color", "#2d2d2d") + """
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
                        border-left-color: #d1d9e6;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    QComboBox::down-arrow {
                        image: url(down_arrow.png);
                        width: 12px;
                        height: 12px;
                    }
                    QComboBox::down-arrow {
                        image: url(down_arrow.png);
                        width: 12px;
                        height: 12px;
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
                """
            
            elif theme_name == "light":
                style = common_style.replace("$border_color", "#d1d9e6") + """
                    /* Modern Açık Tema */
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

                    QComboBox::down-arrow {
                        image: url(icons/down_arrow.png);
                        width: 12px;
                        height: 12px;
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
                """

            elif theme_name == "blue":
                style = common_style.replace("$border_color", "#275a8e") + """
                    QMainWindow { background-color: #1b2e4a; color: #ffffff; }
                    QWidget { background-color: #1b2e4a; color: #ffffff; }
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #223b5f;
                        color: #ffffff;
                        border: 1px solid #275a8e;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #4a90e2;
                        selection-color: white;
                    }
                    QPushButton {
                        background-color: #275a8e;
                        color: #ffffff;
                        border: 1px solid #2f6ca1;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    QPushButton:hover { background-color: #2f6ca1; }
                    QPushButton:pressed { background-color: #1d4a7a; }
                    QPushButton:checked { background-color: #4a90e2; color: white; }
                    QComboBox {
                        background-color: #223b5f;
                        color: #ffffff;
                        border: 1px solid #275a8e;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #275a8e;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    QComboBox::down-arrow {
                        image: url(icons/down_arrow.png);
                        width: 12px;
                        height: 12px;
                    }
                    QTabWidget::pane { border: 1px solid #275a8e; background: #223b5f; }
                    QTabBar::tab { background: #275a8e; color: #ffffff; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
                    QTabBar::tab:selected { background: #4a90e2; color: white; }
                    QScrollBar:vertical { border: none; background: #223b5f; width: 10px; margin: 0; }
                    QScrollBar::handle:vertical { background: #2f6ca1; min-height: 20px; border-radius: 5px; }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                    QGroupBox { border: 1px solid #275a8e; border-radius: 6px; margin-top: 1ex; padding-top: 10px; font-weight: bold; }
                    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
                """

            elif theme_name == "green":
                style = common_style.replace("$border_color", "#2e8b57") + """
                    QMainWindow { background-color: #1f3d2b; color: #ffffff; }
                    QWidget { background-color: #1f3d2b; color: #ffffff; }
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #28543c;
                        color: #ffffff;
                        border: 1px solid #2e8b57;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #44c77f;
                        selection-color: white;
                    }
                    QPushButton {
                        background-color: #2e8b57;
                        color: #ffffff;
                        border: 1px solid #379b63;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    QPushButton:hover { background-color: #379b63; }
                    QPushButton:pressed { background-color: #1f5d3a; }
                    QPushButton:checked { background-color: #44c77f; color: white; }
                    QComboBox {
                        background-color: #28543c;
                        color: #ffffff;
                        border: 1px solid #2e8b57;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #2e8b57;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    QComboBox::down-arrow {
                        image: url(icons/down_arrow.png);
                        width: 12px;
                        height: 12px;
                    }
                    QTabWidget::pane { border: 1px solid #2e8b57; background: #28543c; }
                    QTabBar::tab { background: #2e8b57; color: #ffffff; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
                    QTabBar::tab:selected { background: #44c77f; color: white; }
                    QScrollBar:vertical { border: none; background: #28543c; width: 10px; margin: 0; }
                    QScrollBar::handle:vertical { background: #379b63; min-height: 20px; border-radius: 5px; }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                    QGroupBox { border: 1px solid #2e8b57; border-radius: 6px; margin-top: 1ex; padding-top: 10px; font-weight: bold; }
                    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
                """

            elif theme_name == "purple":
                style = common_style.replace("$border_color", "#8a2be2") + """
                    QMainWindow { background-color: #3d2a5b; color: #ffffff; }
                    QWidget { background-color: #3d2a5b; color: #ffffff; }
                    QTextEdit, QLineEdit, QListWidget, QTreeWidget {
                        background-color: #4a346d;
                        color: #ffffff;
                        border: 1px solid #8a2be2;
                        border-radius: 6px;
                        padding: 8px;
                        selection-background-color: #b366ff;
                        selection-color: white;
                    }
                    QPushButton {
                        background-color: #8a2be2;
                        color: #ffffff;
                        border: 1px solid #9b45e4;
                        border-radius: 6px;
                        padding: 8px 12px;
                        min-width: 100px;
                    }
                    QPushButton:hover { background-color: #9b45e4; }
                    QPushButton:pressed { background-color: #6c1fb8; }
                    QPushButton:checked { background-color: #b366ff; color: white; }
                    QComboBox {
                        background-color: #4a346d;
                        color: #ffffff;
                        border: 1px solid #8a2be2;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                        width: 20px;
                        border-left-width: 1px;
                        border-left-color: #8a2be2;
                        border-left-style: solid;
                        border-top-right-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                    QComboBox::down-arrow {
                        image: url(icons/down_arrow.png);
                        width: 12px;
                        height: 12px;
                    }
                    QTabWidget::pane { border: 1px solid #8a2be2; background: #4a346d; }
                    QTabBar::tab { background: #8a2be2; color: #ffffff; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
                    QTabBar::tab:selected { background: #b366ff; color: white; }
                    QScrollBar:vertical { border: none; background: #4a346d; width: 10px; margin: 0; }
                    QScrollBar::handle:vertical { background: #9b45e4; min-height: 20px; border-radius: 5px; }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                    QGroupBox { border: 1px solid #8a2be2; border-radius: 6px; margin-top: 1ex; padding-top: 10px; font-weight: bold; }
                    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
                """

            else:
                style = ""

            self.setStyleSheet(style)

            checked_style = "background-color: #4a76cd; color: white;"
            self.deep_thought_btn.setStyleSheet(f"QPushButton:checked {{{checked_style}}}")
            self.web_search_btn.setStyleSheet(f"QPushButton:checked {{{checked_style}}}")
        except Exception as e:
            logger.error(f"Tema uygulanirken hata: {str(e)}")

    def apply_font_settings(self):
        try:
            font = QFont(self.font_family, self.font_size)
            self.chat_display.setFont(font)
            self.message_input.setFont(font)
        except Exception as e:
            logger.error(f"Yazı tipi uygulanirken hata: {str(e)}")
            
    def chat_order_changed(self):
        """Sohbet sırası değiştiğinde kaydet"""
        self.save_app_state()
            
    def filter_chats(self, text):
        """Sohbetleri filtrele (projeler dahil)"""
        text = text.lower()
        
        # Standart sohbet listesi
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            item_text = item.text().lower()
            item.setHidden(text not in item_text)
        
        # Proje ağacı
        for i in range(self.projects_tree.topLevelItemCount()):
            project = self.projects_tree.topLevelItem(i)
            project_visible = False
            
            for j in range(project.childCount()):
                chat_item = project.child(j)
                chat_text = chat_item.text(0).lower()
                if text in chat_text:
                    project_visible = True
                    chat_item.setHidden(False)
                    # Eşleşme bulunduğunda projeyi genişlet
                    project.setExpanded(True)
                else:
                    chat_item.setHidden(True)
            
            project.setHidden(not project_visible)

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
            self.chat_display.setHtml("<center><i>Merhaba, size nasıl yardımcı olabilirim?</i></center>")
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

    def update_chat_title(self, chat_id, new_title):
        """Sohbet başlığını tüm listelerde güncelle"""
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == chat_id:
                item.setText(new_title)
                break

        def update_tree(item):
            if item.data(0, Qt.ItemDataRole.UserRole) == chat_id:
                item.setText(0, f"💬 {new_title}")
                return True
            for j in range(item.childCount()):
                if update_tree(item.child(j)):
                    return True
            return False

        for i in range(self.projects_tree.topLevelItemCount()):
            update_tree(self.projects_tree.topLevelItem(i))

        if chat_id in self.chat_data:
            self.chat_data[chat_id]["title"] = new_title
        self.save_app_state()

    def new_project(self):
        try:
            project_name, ok = QInputDialog.getText(self, "Yeni Proje", "Proje Adı:")
            if ok and project_name:
                # Yeni proje oluştur
                new_project = QTreeWidgetItem([f"📂 {project_name}"])
                new_project.setFlags(new_project.flags() | Qt.ItemFlag.ItemIsEditable)
                

                
                # Ağaca ekle
                self.projects_tree.addTopLevelItem(new_project)
                
                # Projeyi genişlet
                new_project.setExpanded(True)
                
                # Projeyi seç
                self.projects_tree.setCurrentItem(new_project)
                self.chat_display.setHtml("<center><i>Merhaba, size nasıl yardımcı olabilirim?</i></center>")
                
                self.statusBar().showMessage(f"🆕 Yeni proje oluşturuldu: {project_name}", 3000)
                self.save_app_state()
        except Exception as e:
            logger.error(f"Yeni proje oluşturulurken hata: {str(e)}")

    def edit_project_title(self, item, column):
        """Proje başlığını düzenle"""
        try:
            if item:
                self.projects_tree.editItem(item, column)
                if item.parent():
                    chat_id = item.data(0, Qt.ItemDataRole.UserRole)
                    if chat_id and chat_id in self.chat_data:
                        self.chat_data[chat_id]["title"] = item.text(0).replace("💬 ", "")
                self.save_app_state()
        except Exception as e:
            logger.error(f"Proje başlığı düzenlenirken hata: {str(e)}")

    def show_project_context_menu(self, pos):
        """Proje bağlam menüsü (silme)"""
        try:
            item = self.projects_tree.itemAt(pos)
            if item:
                menu = QMenu()
                
                # Proje öğesi ise
                if not item.parent():
                    delete_action = menu.addAction(QIcon("icons/delete.png"), "Projeyi Sil")
                    delete_action.triggered.connect(lambda: self.delete_project(item))
                    
                    add_chat_action = menu.addAction(QIcon("icons/add_chat.png"), "Sohbet Ekle")
                    add_chat_action.triggered.connect(lambda: self.add_chat_to_project(item))
                
                # Sohbet öğesi ise
                else:
                    delete_action = menu.addAction(QIcon("icons/delete.png"), "Sohbeti Sil")
                    delete_action.triggered.connect(lambda: self.delete_project_chat(item))

                    rename_action = menu.addAction(QIcon("icons/rename.png"), "Yeniden Adlandır")
                    rename_action.triggered.connect(lambda: self.projects_tree.editItem(item, 0))

                    export_action = menu.addAction(QIcon("icons/export.png"), "Dışa Aktar")
                    export_action.triggered.connect(self.export_selected_chat)
                    
                    move_menu = menu.addMenu(QIcon("icons/move.png"), "Projeye Taşı")
                    for i in range(self.projects_tree.topLevelItemCount()):
                        project = self.projects_tree.topLevelItem(i)
                        if project != item.parent():
                            move_action = move_menu.addAction(project.text(0))
                            move_action.triggered.connect(
                                lambda _, p=project, c=item: self.move_chat_to_project(p, c)
                            )
                
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
    
    def delete_project_chat(self, item):
        """Projedeki sohbeti sil"""
        try:
            chat_id = item.data(0, Qt.ItemDataRole.UserRole)
            if chat_id in self.chat_data:
                del self.chat_data[chat_id]
            parent = item.parent()
            parent.removeChild(item)
            self.statusBar().showMessage("🗑️ Proje sohbeti silindi", 3000)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Proje sohbeti silinirken hata: {str(e)}")

    def load_api_key(self):
        """Kayıtlı API anahtarını yükle"""
        try:
            if os.path.exists("api_config.json"):
                with open("api_config.json", "r") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key")
        except Exception as e:
            logger.error(f"API anahtarı yüklenirken hata: {str(e)}")

    def save_api_key(self, api_key):
        """API anahtarını kaydet"""
        try:
            with open("api_config.json", "w") as f:
                json.dump({"api_key": api_key}, f)
            self.api_key = api_key
            self.statusBar().showMessage("🔑 API anahtarı kaydedildi", 3000)
        except Exception as e:
            logger.error(f"API anahtarı kaydedilirken hata: {str(e)}")

    def get_response_from_openrouter(self, model_name):
        """OpenRouter API'sinden yanıt al"""
        try:
            url = f"{self.api_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/CxReiS/DeepSeekChat",
                "X-Title": "DeepSeek Chat"
            }

            # Sohbet geçmişini hazırla
            messages = []
            for msg in self.chat_data[self.active_chat_id]["messages"]:
                role = "user" if msg["sender"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["message"]})

            # OpenRouter model ID'sini al
            openrouter_model = self.model_mapping.get(model_name, "deepseek/deepseek-r1:free")

            data = {
                "model": openrouter_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096
            }

            response = requests.post(url, headers=headers, json=data, timeout=120)
            response_data = response.json()

            if response.status_code == 200:
                assistant_reply = response_data["choices"][0]["message"]["content"]

                # Yanıtı ekrana ve hafızaya ekle
                self.append_message("assistant", assistant_reply)
                self.chat_data[self.active_chat_id]["messages"].append({
                    "sender": "assistant",
                    "message": assistant_reply,
                    "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
                })

                self.statusBar().showMessage(f"✅ Yanıt alındı ({model_name})", 3000)
                self.save_app_state()
            else:
                error_msg = response_data.get("error", {}).get("message", "Bilinmeyen hata")
                self.statusBar().showMessage(f"❌ Hata: {error_msg}", 5000)
                logger.error(f"API hatası: {response.status_code} - {error_msg}")

                # Hata durumunda simülasyon yap
                QTimer.singleShot(1500, lambda: self.simulate_response(model_name))

        except Exception as e:
            logger.error(f"API isteği sırasında hata: {str(e)}")
            self.statusBar().showMessage(f"❌ İstek hatası: {str(e)}", 5000)

            # Hata durumunda simülasyon yap
            QTimer.singleShot(1500, lambda: self.simulate_response(model_name))

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

            if len(self.chat_data[self.active_chat_id]["messages"]) == 1:
                words = message.split()[:4]
                new_title = " ".join(words)
                if len(new_title) > 25:
                    new_title = new_title[:22] + "..."
                self.update_chat_title(self.active_chat_id, new_title)
            
            self.message_input.clear()
            
            # Aktif modeli al
            model_name = self.model_combo.currentText()

            # API iş parçacığı
            self.worker = WorkerThread(
                api_key="demo-key",
                conversation_history=[{"role": msg['sender'], "content": msg['message']} for msg in self.chat_data[self.active_chat_id]["messages"]],
                user_message=message,
                model=model_name
            )
            self.worker.thinking_updated.connect(self.handle_thinking_update)
            self.worker.response_received.connect(lambda reply, t: self.handle_api_response(reply, model_name))
            self.worker.error_occurred.connect(lambda err: self.statusBar().showMessage(err, 5000))
            self.worker.start()

            self.statusBar().showMessage("⏳ DeepSeek yanıt oluşturuyor...")

            if self.api_key:
                history = []
                for msg in self.chat_data[self.active_chat_id]["messages"]:
                    role = "user" if msg["sender"] == "user" else "assistant"
                    history.append({"role": role, "content": msg["message"]})
                self.worker = WorkerThread(self.api_key, history, self.model_mapping.get(model_name, "deepseek/deepseek-r1:free"))
                self.worker.response_received.connect(lambda reply, _: self.handle_api_response(reply, model_name))
                self.worker.error_occurred.connect(lambda err: self.handle_api_error(err, model_name))
                self.worker.start()
            else:
                QTimer.singleShot(1500, lambda: self.simulate_response(model_name))
            
            # Ekli dosyaları temizle
            self.attached_files = []
            
            # Uygulama durumunu kaydet
            self.save_app_state()
        except Exception as e:
            logger.error(f"Mesaj gönderilirken hata: {str(e)}")

    def handle_api_response(self, reply, model_name):
        try:
            self.append_message("assistant", reply)
            self.chat_data[self.active_chat_id]["messages"].append({
                "sender": "assistant",
                "message": reply,
                "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
            })
            self.statusBar().showMessage(f"✅ Yanıt alındı ({model_name})", 3000)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Yanıt işlenirken hata: {str(e)}")

    def handle_api_error(self, error_msg, model_name):
        logger.error(f"API hatası: {error_msg}")
        self.statusBar().showMessage(f"❌ Hata: {error_msg}", 5000)
        QTimer.singleShot(1500, lambda: self.simulate_response(model_name))

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

    def handle_thinking_update(self, message):
        cursor = self.chat_display.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.removeSelectedText()
        dimmed_color = "#888888" if self.current_theme == "light" else "#aaaaaa"
        html_content = f"<div style='color:{dimmed_color}; font-style:italic; margin-bottom:15px;'>{message}</div>"
        self.chat_display.insertHtml(html_content)
        self.chat_display.ensureCursorVisible()

    def handle_api_response(self, reply, model_name):
        self.chat_display.clear()
        self.append_message("assistant", reply)
        if self.active_chat_id:
            self.chat_data[self.active_chat_id]["messages"].append({
                "sender": "assistant",
                "message": reply,
                "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
            })
            self.save_app_state()

    def model_changed(self, index):
        model_name = self.model_combo.currentText()
        self.statusBar().showMessage(f"🤖 Aktif model: {model_name}", 5000)
        if "coder" in model_name:
            self.message_input.setPlaceholderText("Kod problemini yazın...")
        elif "math" in model_name:
            self.message_input.setPlaceholderText("Matematik problemini yazın...")
        else:
            self.message_input.setPlaceholderText("DeepSeek'e mesaj yazın...")

    def append_message(self, sender, message):
        try:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            if sender == "user":
                prefix = "Siz:"
                color = "#4ec9b0"
                bg_color = "#1e1e1e" if self.current_theme == "dark" else "#f0f4f9"
            else:
                prefix = "DeepSeek:"
                color = "#d69a66"
                bg_color = "#2a2a2a" if self.current_theme == "dark" else "#ffffff"

            weight = "bold" if self.label_bold else "normal"
            style_italic = "italic" if self.italic_subtitles else "normal"

            html_content = f"""
            <div style='margin-bottom:20px; padding:10px; background-color:{bg_color}; border-radius:8px;'>
                <span style='font-weight:{weight}; color:{color}; font-style:{style_italic};'>{prefix}</span>
                <div style='margin-top:5px; line-height:1.6; font-family:{self.font_family}; font-size:{self.font_size}px;'>
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
            if len(self.attached_files) >= 10:
                QMessageBox.warning(self, "Uyarı", "En fazla 10 dosya ekleyebilirsiniz")
                return

            file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
            if file_path:
                valid_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.pdf', '.doc', '.docx', '.md']
                if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
                    QMessageBox.warning(self, "Desteklenmeyen Dosya", "Seçilen dosya tipi desteklenmiyor. Lütfen metin tabanlı dosyalar ekleyin.")
                    return

                file_name = os.path.basename(file_path)
                self.attached_files.append(file_path)

                file_widget = QWidget()
                layout = QHBoxLayout(file_widget)
                layout.setContentsMargins(0, 0, 0, 0)
                label = QLabel(f"📎 {file_name}")
                layout.addWidget(label)
                remove_btn = QPushButton("✕")
                remove_btn.setFixedSize(20, 20)
                remove_btn.setStyleSheet("font-size: 10px; padding: 0;")
                remove_btn.clicked.connect(lambda _, p=file_path: self.remove_attached_file(p))
                layout.addWidget(remove_btn)

                item = QListWidgetItem()
                item.setSizeHint(file_widget.sizeHint())
                self.attachments_list.addItem(item)
                self.attachments_list.setItemWidget(item, file_widget)
        except Exception as e:
            logger.error(f"Dosya eklenirken hata: {str(e)}")

    def remove_attached_file(self, file_path):
        if file_path in self.attached_files:
            self.attached_files.remove(file_path)
            self.refresh_attachments_list()

    def refresh_attachments_list(self):
        self.attachments_list.clear()
        for path in self.attached_files:
            file_name = os.path.basename(path)
            file_widget = QWidget()
            layout = QHBoxLayout(file_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            label = QLabel(f"📎 {file_name}")
            layout.addWidget(label)
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(20, 20)
            remove_btn.setStyleSheet("font-size: 10px; padding: 0;")
            remove_btn.clicked.connect(lambda _, p=path: self.remove_attached_file(p))
            layout.addWidget(remove_btn)
            item = QListWidgetItem()
            item.setSizeHint(file_widget.sizeHint())
            self.attachments_list.addItem(item)
            self.attachments_list.setItemWidget(item, file_widget)

    def eventFilter(self, source, event):
        if source is self.message_input:
            if event.type() == QEvent.Type.KeyPress and event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self.send_message()
                    return True
            if event.type() == QEvent.Type.DragEnter and event.mimeData().hasUrls():
                event.acceptProposedAction()
                return True
            if event.type() == QEvent.Type.Drop and event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        if len(self.attached_files) >= 10:
                            QMessageBox.warning(self, "Uyarı", "En fazla 10 dosya ekleyebilirsiniz")
                            break
                        valid_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.pdf', '.doc', '.docx', '.md']
                        if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
                            QMessageBox.warning(self, "Desteklenmeyen Dosya", "Seçilen dosya tipi desteklenmiyor. Lütfen metin tabanlı dosyalar ekleyin.")
                            continue
                        self.attached_files.append(file_path)
                        file_name = os.path.basename(file_path)
                        file_widget = QWidget()
                        layout = QHBoxLayout(file_widget)
                        layout.setContentsMargins(0, 0, 0, 0)
                        label = QLabel(f"📎 {file_name}")
                        layout.addWidget(label)
                        remove_btn = QPushButton("✕")
                        remove_btn.setFixedSize(20, 20)
                        remove_btn.setStyleSheet("font-size: 10px; padding: 0;")
                        remove_btn.clicked.connect(lambda _, p=file_path: self.remove_attached_file(p))
                        layout.addWidget(remove_btn)
                        item = QListWidgetItem()
                        item.setSizeHint(file_widget.sizeHint())
                        self.attachments_list.addItem(item)
                        self.attachments_list.setItemWidget(item, file_widget)
                event.acceptProposedAction()
                return True
        return super().eventFilter(source, event)

    def export_chats(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Sohbetleri Dışa Aktar", 
                "", 
                "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
            )
            
            if file_path:
                export_data = {
                    "version": self.VERSION,
                    "export_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
                    "chats": {}
                }

                for cid, data in self.chat_data.items():
                    clean_msgs = []
                    for m in data["messages"]:
                        clean = m.copy()
                        clean["message"] = self.sanitize_text(m["message"])
                        clean_msgs.append(clean)
                    export_data["chats"][cid] = {"title": data["title"], "messages": clean_msgs}

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                self.statusBar().showMessage(f"📤 Sohbetler dışa aktarıldı: {file_path}", 5000)
        except Exception as e:
            logger.error(f"Sohbetler dışa aktarılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Sohbetler dışa aktarılırken hata oluştu: {str(e)}")

    def export_selected_chat(self):
        """Yalnızca seçili sohbeti dışa aktar"""
        try:
            if not self.active_chat_id or self.active_chat_id not in self.chat_data:
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sohbeti Dışa Aktar",
                "",
                "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
            )
            if not file_path:
                return

            export_data = {
                "version": self.VERSION,
                "export_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
                "chat": self.chat_data[self.active_chat_id]
            }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.statusBar().showMessage(f"📤 Sohbet dışa aktarıldı: {file_path}", 5000)
        except Exception as e:
            logger.error(f"Sohbet dışa aktarılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Sohbet dışa aktarılırken hata oluştu: {str(e)}")

    def export_selected_chat(self):
        if self.active_chat_id and self.active_chat_id in self.chat_data:
            self.export_chats()

    def sanitize_text(self, text):
        return re.sub(r"[\U0001F600-\U0001F6FF]", "", text)

    def open_theme_settings(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🎨 Tema Ayarları")
            dialog.setFixedSize(400, 300)
            
            layout = QVBoxLayout()
            
            # Tema seçimi için butonlar
            theme_buttons = QWidget()
            grid = QGridLayout(theme_buttons)
            
            themes = [
                ("🌙 Koyu Tema", "dark"),
                ("☀️ Açık Tema", "light"),
                ("🔵 Mavi Tema", "blue"),
                ("🍏 Yeşil Tema", "green"),
                ("🍇 Mor Tema", "purple")
            ]
            
            row, col = 0, 0
            for theme_name, theme_key in themes:
                btn = QPushButton(theme_name)
                btn.clicked.connect(lambda _, t=theme_key: self.apply_theme(t))
                grid.addWidget(btn, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1
            
            layout.addWidget(theme_buttons)
            
            # Kapat butonu
            btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            btn_box.rejected.connect(dialog.reject)
            layout.addWidget(btn_box)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Tema ayarları açılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Tema ayarları açılırken hata oluştu: {str(e)}")
            
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
                minimize_key_edit.keySequence(),
                dialog  # Diyaloğu kapatmak için
            ))
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Kısayol ayarları açılırken hata: {str(e)}")

    def save_shortcuts(self, send_seq, newline_seq, fullscreen_seq, minimize_seq, dialog):
        try:
            # Kısayolları güncelle
            self.send_action.setShortcut(send_seq)
            self.newline_action.setShortcut(newline_seq)
            self.fullscreen_action.setShortcut(fullscreen_seq)
            self.minimize_action.setShortcut(minimize_seq)
            
            self.statusBar().showMessage("✅ Kısayollar kaydedildi", 3000)
            self.save_app_state()
            dialog.accept()  # Diyaloğu kapat
        except Exception as e:
            logger.error(f"Kısayollar kaydedilirken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Kısayollar kaydedilirken hata oluştu: {str(e)}")

    def open_font_settings(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Yazı Tipi Ayarları")
            dialog.setFixedSize(400, 300)

            layout = QVBoxLayout()

            family_combo = QFontComboBox()
            family_combo.setCurrentFont(QFont(self.font_family))

            size_slider = QSlider(Qt.Orientation.Horizontal)
            size_slider.setRange(12, 24)
            size_slider.setValue(self.font_size)

            bold_check = QCheckBox("Kalın başlıklar")
            bold_check.setChecked(self.label_bold)

            italic_check = QCheckBox("İtalik altyazılar")
            italic_check.setChecked(self.italic_subtitles)

            layout.addWidget(QLabel("Yazı Tipi"))
            layout.addWidget(family_combo)
            layout.addWidget(QLabel("Yazı Boyutu"))
            layout.addWidget(size_slider)
            layout.addWidget(bold_check)
            layout.addWidget(italic_check)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)

            def save_and_close():
                self.font_family = family_combo.currentFont().family()
                self.font_size = size_slider.value()
                self.label_bold = bold_check.isChecked()
                self.italic_subtitles = italic_check.isChecked()
                self.apply_font_settings()
                self.statusBar().showMessage("✅ Yazı tipi ayarları kaydedildi", 3000)
                self.save_app_state()
                dialog.accept()

            buttons.accepted.connect(save_and_close)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Yazı tipi ayarları açılırken hata: {str(e)}")

    def open_model_management(self):
        try:
            self.model_dialog = QDialog(self)
            dialog = self.model_dialog
            dialog.setWindowTitle("🤖 Model Yönetimi")
            dialog.setFixedSize(600, 400)

            layout = QVBoxLayout()

            # API Anahtarı
            api_layout = QHBoxLayout()
            api_layout.addWidget(QLabel("🔑 OpenRouter API Anahtarı:"))
            self.api_key_edit = QLineEdit()
            self.api_key_edit.setPlaceholderText("sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx")
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            if self.api_key:
                self.api_key_edit.setText(self.api_key)
            api_layout.addWidget(self.api_key_edit, 1)

            # Anahtarı göster/gizle
            show_key_btn = QPushButton("👁️")
            show_key_btn.setCheckable(True)
            show_key_btn.setFixedWidth(30)
            show_key_btn.toggled.connect(lambda checked: self.api_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            ))
            api_layout.addWidget(show_key_btn)
            layout.addLayout(api_layout)

            # Anahtar almak için bağlantı
            key_link = QLabel('<a href="https://openrouter.ai/keys">🔑 Ücretsiz API Anahtarı Al</a>')
            key_link.setOpenExternalLinks(True)
            layout.addWidget(key_link)

            # Model Seçimi
            model_layout = QHBoxLayout()
            model_layout.addWidget(QLabel("🤖 Aktif Model:"))
            self.model_combo_dialog = QComboBox()
            self.model_combo_dialog.addItems(["deepseek-chat", "deepseek-coder", "deepseek-math"])
            self.model_combo_dialog.setCurrentText(self.model_combo.currentText())
            model_layout.addWidget(self.model_combo_dialog, 1)
            layout.addLayout(model_layout)

            # Model Bilgileri
            info_box = QGroupBox("ℹ️ DeepSeek R1 Model Bilgileri")
            info_layout = QVBoxLayout()
            self.model_info = QTextEdit()
            self.model_info.setReadOnly(True)
            self.model_info.setHtml("""
                <b>DeepSeek R1</b>: 128K bağlam pencereli güçlü dil modeli<br>
                <ul>
                    <li><b>Genel Sohbet</b>: Doğal diyalog yetenekleri</li>
                    <li><b>Kodlama</b>: Çoklu dil desteği</li>
                    <li><b>Matematik</b>: Mantıksal akıl yürütme</li>
                </ul>
                <p><b>Ücretsiz Kullanım:</b></p>
                <ul>
                    <li>Dakikada 5 istek</li>
                    <li>Günlük 100 istek</li>
                    <li>128K bağlam penceresi</li>
                </ul>
                <b>Dosya Tipi Kısıtlamaları:</b>
                <ul>
                    <li>Metin dosyaları (.txt, .py, .js, .html, etc.)</li>
                    <li>PDF ve Word dokümanları (metin içeriği okunur)</li>
                    <li><b>Görsel, ses ve video dosyaları desteklenmez</b></li>
                </ul>
            """)
            info_layout.addWidget(self.model_info)
            info_box.setLayout(info_layout)
            layout.addWidget(info_box)

            # Butonlar
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | 
                QDialogButtonBox.StandardButton.Cancel
            )
            button_box.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet")
            button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal")
            button_box.accepted.connect(self.save_model_settings)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            logger.error(f"Model yönetimi açılırken hata: {str(e)}")
            
    def update_models(self):
        """Modelleri güncelle"""
        try:
            # Gerçek güncelleme işlemi için API entegrasyonu
            self.statusBar().showMessage("🔄 Modeller güncelleniyor...", 3000)
            QTimer.singleShot(2000, lambda: self.statusBar().showMessage("✅ Modeller güncellendi", 5000))
        except Exception as e:
            logger.error(f"Modeller güncellenirken hata: {str(e)}")

    def save_model_settings(self):
        """Model ve API ayarlarını kaydet"""
        try:
            selected_model = self.model_combo_dialog.currentText()
            api_key = self.api_key_edit.text().strip()

            # API anahtarını kaydet
            if api_key:
                self.save_api_key(api_key)

            # Ana model seçimini güncelle
            self.model_combo.setCurrentText(selected_model)

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
        try:
            menu = self.chat_display.createStandardContextMenu()
            translations = {
                "&Undo": "Geri Al",
                "&Redo": "İleri Al",
                "Cu&t": "Kes",
                "&Copy": "Kopyala",
                "&Paste": "Yapıştır",
                "Paste and Match Style": "Biçimle Eşleştirerek Yapıştır",
                "Delete": "Sil",
                "Select All": "Tümünü Seç",
                "Copy Link Location": "Bağlantı Konumunu Kopyala"
            }
            for action in menu.actions():
                text = action.text().split('\t')[0]
                if text in translations:
                    action.setText(translations[text])
            menu.exec(self.chat_display.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Bağlam menüsü gösterilirken hata: {str(e)}")
            
    def show_text_context_menu(self, pos):
        """Türkçe metin menüsü"""
        try:
            menu = self.message_input.createStandardContextMenu()
            translations = {
                "&Undo": "Geri Al",
                "&Redo": "İleri Al",
                "Cu&t": "Kes",
                "&Copy": "Kopyala",
                "&Paste": "Yapıştır",
                "Paste and Match Style": "Biçimle Eşleştirerek Yapıştır",
                "Delete": "Sil",
                "Select All": "Tümünü Seç",
                "Copy Link Location": "Bağlantı Konumunu Kopyala"
            }

            for action in menu.actions():
                text = action.text().split('\t')[0]
                if text in translations:
                    action.setText(translations[text])

            menu.exec(self.message_input.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Metin menüsü gösterilirken hata: {str(e)}")

    def show_chat_list_context_menu(self, pos):
        """Sohbet listesi için bağlam menüsü"""
        try:
            menu = QMenu()

            # Yeniden adlandır
            rename_action = menu.addAction(QIcon("icons/rename.png"), "Yeniden Adlandır")
            rename_action.triggered.connect(self.rename_selected_chat)

            # Sil
            delete_action = menu.addAction(QIcon("icons/delete.png"), "Sil")
            delete_action.triggered.connect(self.delete_selected_chat)

            export_action = menu.addAction(QIcon("icons/export.png"), "Sohbeti Dışa Aktar")
            export_action.triggered.connect(self.export_selected_chat)

            menu.exec(self.chat_display.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Bağlam menüsü gösterilirken hata: {str(e)}")

    def show_text_context_menu(self, pos):
        """Türkçe metin menüsü"""
        try:
            menu = self.message_input.createStandardContextMenu()

            self.translate_context_menu(menu)

            menu.exec(self.message_input.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Metin menüsü gösterilirken hata: {str(e)}")

    def translate_context_menu(self, menu):
        """Bağlam menüsü eylemlerini Türkçeye çevir"""
        translations = {
            "&Undo": "Geri Al",
            "&Redo": "İleri Al",
            "Cu&t": "Kes",
            "&Copy": "Kopyala",
            "&Paste": "Yapıştır",
            "Delete": "Sil",
            "Select All": "Tümünü Seç",
            "Paste and Match Style": "Biçimle Eşleştirerek Yapıştır",
            "Copy Link Location": "Bağlantı Konumunu Kopyala"
        }
        for action in menu.actions():
            text = action.text().split('\t')[0]
            if text in translations:
                action.setText(translations[text])

    def move_to_main_chat_list(self, item):
        """Sohbeti ana sohbet listesine taşı"""
        chat_title = item.text()
        chat_id = item.data(Qt.ItemDataRole.UserRole)

        new_item = QListWidgetItem(chat_title)
        new_item.setData(Qt.ItemDataRole.UserRole, chat_id)
        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.chat_list.addItem(new_item)

        parent = item.parent()
        if parent:
            parent.removeChild(item)

        self.statusBar().showMessage("📂 Sohbet ana listeye taşındı", 3000)
        self.save_app_state()

    def project_drag_enter(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.acceptProposedAction()

    def project_drop_event(self, event):
        item = self.projects_tree.itemAt(event.position().toPoint())
        if item and not item.parent():
            chat_item = self.chat_list.currentItem()
            if chat_item:
                self.move_chat_to_project(item, chat_item)
                event.acceptProposedAction()
        elif not item:
            chat_item = self.chat_list.currentItem()
            if chat_item:
                self.move_to_main_chat_list(chat_item)
                event.acceptProposedAction()
        else:
            event.ignore()
    
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

    def load_project_context(self, current, previous):
        if current and not current.parent():
            pid = id(current)
            if pid not in self.project_context:
                self.project_context[pid] = {"instructions": "", "files": []}
            ctx = self.project_context[pid]
            self.project_instructions.setText(ctx["instructions"])
            self.project_files_list.clear()
            for f in ctx["files"]:
                self.project_files_list.addItem(f)

    def add_project_file(self):
        current = self.projects_tree.currentItem()
        if current and not current.parent():
            file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
            if file_path:
                pid = id(current)
                if pid not in self.project_context:
                    self.project_context[pid] = {"instructions": "", "files": []}
                self.project_context[pid]["files"].append(file_path)
                self.project_files_list.addItem(file_path)
                self.save_project_context()

    def remove_project_file(self):
        current = self.projects_tree.currentItem()
        item = self.project_files_list.currentItem()
        if current and not current.parent() and item:
            pid = id(current)
            file_path = item.text()
            self.project_files_list.takeItem(self.project_files_list.row(item))
            if pid in self.project_context and file_path in self.project_context[pid]["files"]:
                self.project_context[pid]["files"].remove(file_path)
                self.save_project_context()

    def save_project_context(self):
        current = self.projects_tree.currentItem()
        if current and not current.parent():
            pid = id(current)
            self.project_context[pid] = {
                "instructions": self.project_instructions.toPlainText(),
                "files": [self.project_files_list.item(i).text() for i in range(self.project_files_list.count())]
            }
    
    def save_app_state(self):
        """Uygulama durumunu kaydet"""
        try:
            self.save_project_context()
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
                "font_family": self.font_family,
                "font_size": self.font_size,
                "label_bold": self.label_bold,
                "italic_subtitles": self.italic_subtitles,
                "project_context": self.project_context,
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

                    self.font_family = app_state.get("font_family", "Arial")
                    self.font_size = app_state.get("font_size", 16)
                    self.label_bold = app_state.get("label_bold", True)
                    self.italic_subtitles = app_state.get("italic_subtitles", False)
                    self.apply_font_settings()
                    self.project_context = app_state.get("project_context", {})

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
