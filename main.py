import sys

import os

import json

import logging

import uuid

import requests

import time

import re

from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QWidget, QLineEdit, QLabel,
    QTextEdit, QListWidget, QSplitter, QVBoxLayout, QPushButton,
    QStatusBar, QTreeWidget, QTreeWidgetItem, QComboBox, QFrame, QMenuBar,
    QMenu, QSystemTrayIcon, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QTabWidget, QFileDialog, QListWidgetItem, QGroupBox,
    QScrollArea, QKeySequenceEdit, QToolButton, QSizePolicy, QGridLayout,
    QFontComboBox, QSlider, QMessageBox, QCheckBox, QListView,
    QAbstractScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, QSize, QDateTime, QEvent
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QTextCursor, QColor, QTextCharFormat, QFont, QPixmap, QFontMetrics
)

from login_window import LoginWindow
from user_manager import UserManager
from worker_thread import WorkerThread
from chat_database import ChatDatabase
from utils.error_dialog import ErrorDialog
from utils.font_manager import apply_font_settings
from utils import validate_email, format_file_size, create_safe_filename

# Log dosyasını yönet
MAX_LOG_LINES = 1000
LOG_META_FILE = "log_meta.json"

def manage_log_file(max_lines: int = MAX_LOG_LINES):
    """app.log dosyasını sınırlar ve kapatma sayısına göre temizler"""
    try:
        count = 0
        if os.path.exists(LOG_META_FILE):
            with open(LOG_META_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = data.get("close_count", 0)

        if count >= 2:
            if os.path.exists("app.log"):
                os.remove("app.log")
            count = 0
        elif os.path.exists("app.log"):
            with open("app.log", "r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
            if line_count >= max_lines:
                os.remove("app.log")
                count = 0

        with open(LOG_META_FILE, "w", encoding="utf-8") as f:
            json.dump({"close_count": count}, f)
    except Exception:
        pass

def increment_log_counter():
    try:
        count = 0
        if os.path.exists(LOG_META_FILE):
            with open(LOG_META_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = data.get("close_count", 0)
        count += 1
        with open(LOG_META_FILE, "w", encoding="utf-8") as f:
            json.dump({"close_count": count}, f)
    except Exception:
        pass

manage_log_file()

# Loglama sistemini başlat

logging.basicConfig(

    filename='app.log',

    level=logging.DEBUG,

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

)

logger = logging.getLogger("DeepSeekChat")



class MainApplication(QMainWindow):

    VERSION = "1.0.2"

    def __init__(self):
        """Ana uygulamanın tüm arayüz, değişken ve ayarlarını başlatır"""
        super().__init__()

        # 🧠 Sistemsel değişkenler
        self.current_project = None
        self.chat_data = {}
        self.db = ChatDatabase()
        self.projects_data = []
        self.project_context = {}
        self.model_mapping = {
            "deepseek-chat": "deepseek/deepseek-r1:free",
            "deepseek-coder": "deepseek/deepseek-coder:33b",
            "deepseek-math": "deepseek/deepseek-math:7b",
            "gemma-2b": "http://localhost:11434/v1"
        }

        self.projeler = []
        self.proje_widgetleri = {}

        # 🎨 Görsel yapılandırma
        self.setWindowTitle(f"\U0001F4AC DeepSeek Chat v{self.VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        self.current_theme = "dark"
        self.font_family = "Segoe UI"
        self.font_size = 12
        self.label_bold = True
        self.italic_subtitles = False

        # 🧱 Arayüz kurulum
        self.setup_ui()
        self.setup_sidebar()

        # 👥 Sohbet başlat
        if not os.path.exists("app_state.json"):
            chat_name = "Yeni Sohbet"
            chat_id = self.create_chat(chat_name)
            if chat_id:
                self.active_chat_id = chat_id
                self.statusBar().showMessage("🆕 Yeni sohbet başlatıldı", 3000)

        # 💾 Mevcut sohbet ve mesajları (SQLite'tan) yükle
        chats = self.db.load_chats()
        if hasattr(self, "active_chat_id"):
            messages = self.db.load_messages(self.active_chat_id)

        # 🛑 Genel hata yakalama sistemi
        sys.excepthook = self.handle_exception

        # 🖼️ Sistem tepsisi (ikon)
        pixmap = QPixmap("icons/logo.png")
        scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.tray_icon = QSystemTrayIcon(QIcon(scaled), self)
        self.setup_tray_icon()

        # 🔲 Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 🔹 Sol panel (sidebar)
        main_layout.addWidget(self.sidebar)

        # 🔹 Sağ panel (chat ekranı ve giriş alanı)
        self.setup_right_panel()
        if hasattr(self, "chat_display"):
            self.chat_display.setHtml("<center><i>Merhaba, size nasıl yardımcı olabilirim?</i></center>")
            main_layout.addWidget(self.right_panel, 1)

        # 📌 Status bar
        self.setup_statusbar()

        # ☰ Menü çubuğu ve minimize butonu
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

        # ⌨️ Kısayollar
        self.setup_shortcuts()

        # 📎 Ekli dosya ve model kontrol değişkenleri
        self.attached_files = []
        self.custom_models = []
        self.pending_message = ""
        self.sending = False

        # 💾 Uygulama durumu ve font ayarları
        self.load_app_state()
        self.apply_font_settings()

        # ✨ Tema uygulama
        self.apply_theme(self.current_theme)

        # 🌐 API bağlantısı
        self.api_key = None
        self.api_base_url = "https://openrouter.ai/api/v1"
        self.load_api_key()

        logger.info("Ana uygulama başlatıldı")

    def create_chat(self, name="Yeni Sohbet"):
        if any(chat["title"] == name for chat in self.chat_data.values()):
            logger.warning(f"Bu isimde bir sohbet zaten var: {name}")
            return None

        chat_id = str(uuid.uuid4())
        self.chat_data[chat_id] = {
            "title": name,
            "messages": []
        }
        return chat_id           
        
    def apply_font_settings(self):
        """Font ayarlarını uygular"""
        try:
            from utils.font_manager import apply_font_settings
            apply_font_settings(self)
        except Exception as e:
            logger.error(f"Font ayarları uygulanırken hata: {str(e)}")  
        
    def setup_ui(self):

        # UI kurulumu burada yapılır
        pass    

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
                        item.setSizeHint(QSize(25, 4))
                        self.chat_list.addItem(item)

                        if "chat_data" in app_state and chat["id"] in app_state["chat_data"]:
                            self.chat_data[chat["id"]] = app_state["chat_data"][chat["id"]]
                            self.chat_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
                            self.chat_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

                    # Proje ağacını yükle
                    self.projects_tree.clear()
                    for project in app_state.get("projects", []):
                        def load_tree_item(data, parent=None):
                            item = QTreeWidgetItem([data["text"]])
                            if data["id"]:
                                item.setData(0, Qt.ItemDataRole.UserRole, data["id"])

                            if "chat_data" in app_state and data["id"] in app_state["chat_data"]:
                                self.chat_data[data["id"]] = app_state["chat_data"][data["id"]]

                            for child_data in data.get("children", []):
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

                    # Font ayarları
                    self.font_family = app_state.get("font_family", "Arial")
                    self.font_size = app_state.get("font_size", 16)
                    self.label_bold = app_state.get("label_bold", True)
                    self.italic_subtitles = app_state.get("italic_subtitles", False)
                    self.apply_font_settings()

                    # Proje bağlamı
                    self.project_context = app_state.get("project_context", {})

                    # Kısayollar
                    shortcuts = app_state.get("shortcuts", {})
                    self.send_action.setShortcut(QKeySequence(shortcuts.get("send", "Ctrl+Return")))
                    self.newline_action.setShortcut(QKeySequence(shortcuts.get("newline", "Return")))
                    self.fullscreen_action.setShortcut(QKeySequence(shortcuts.get("fullscreen", "F11")))
                    self.minimize_action.setShortcut(QKeySequence(shortcuts.get("minimize", "Ctrl+M")))

                    # Aktif sohbet
                    self.active_chat_id = app_state.get("active_chat_id")
                    if self.active_chat_id and self.active_chat_id in self.chat_data:
                        found = False
                        for i in range(self.chat_list.count()):
                            item = self.chat_list.item(i)
                            if item.data(Qt.ItemDataRole.UserRole) == self.active_chat_id:
                                self.chat_list.setCurrentItem(item)
                                self.load_chat(item)
                                found = True
                                break

                        if not found:
                            def find_in_projects(item):
                                for i in range(item.childCount()):
                                    child = item.child(i)
                                    if child.data(0, Qt.ItemDataRole.UserRole) == self.active_chat_id:
                                        self.projects_tree.setCurrentItem(child)
                                        self.load_project_chat(child, 0)
                                        return True
                                return False

                            for i in range(self.projects_tree.topLevelItemCount()):
                                if find_in_projects(self.projects_tree.topLevelItem(i)):
                                    break

        except Exception as e:
            logger.error(f"Durum yüklenirken hata: {str(e)}")

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
        
    def setup_statusbar(self):
        """Status bar'ı kur"""
        status_bar = self.statusBar()
        status_bar.showMessage("✅ Bağlantı kuruldu")
                  
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
        
        # Yeni eklemeler
        self.chat_list.setResizeMode(QListView.ResizeMode.Adjust)  # Boyut ayarlama modu
        self.chat_list.setUniformItemSizes(False)  # Uniform olmayan boyutlar
        self.chat_list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)  # İçeriğe göre ayarla
        self.chat_list.itemChanged.connect(self.handle_chat_title_changed)
        # Font ölçümleri için
        self.font_metrics = QFontMetrics(self.font())
        self.chat_list.setWordWrap(False)
        
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
        self.projects_tree.itemClicked.connect(self.load_project_chat)
        self.projects_tree.itemDoubleClicked.connect(self.rename_project_or_chat)
        self.projects_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.projects_tree.customContextMenuRequested.connect(self.show_projects_context_menu)
        self.projects_tree.itemChanged.connect(self.handle_project_item_changed)
        self.projects_tree.setAcceptDrops(True)
        self.projects_tree.viewport().setAcceptDrops(True)
        self.projects_tree.dragEnterEvent = self.project_drag_enter
        self.projects_tree.dropEvent = self.project_drop_event
        self.projects_tree.setDragEnabled(True)
        self.projects_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
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
        
    def rename_project_or_chat(self, item, column):
        """Projeyi veya sohbeti çift tıklayınca yeniden adlandırma"""
        self.projects_tree.editItem(item, column)
    
    def show_projects_context_menu(self, position):
        item = self.projects_tree.itemAt(position)
        if not item:
            return
        menu = QMenu()
        rename_action = menu.addAction("Yeniden Adlandır")
        action = menu.exec(self.projects_tree.viewport().mapToGlobal(position))
        if action == rename_action:
            self.projects_tree.editItem(item, 0)

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
        self.project_tab = QWidget()
        project_layout = QVBoxLayout(self.project_tab)
        self.project_instructions = QTextEdit()
        self.project_instructions.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_instructions.customContextMenuRequested.connect(self.show_text_context_menu)
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
        self.project_tab_index = self.context_tabs.addTab(self.project_tab, "📂 Proje Bağlamı")
        self.context_tabs.setTabVisible(self.project_tab_index, False)

        # Mesaj Gönderme Paneli
        send_panel = QWidget()
        send_layout = QVBoxLayout(send_panel)
        self.right_panel.addWidget(self.context_tabs)
        self.right_panel.addWidget(send_panel)
        self.right_panel.setSizes([600, 200])
        
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
        self.deep_thought_btn.setObjectName("deep_thought_btn")
        self.deep_thought_btn.setIcon(QIcon("icons/brain.png"))
        self.deep_thought_btn.setIconSize(QSize(48, 48))
        self.deep_thought_btn.setText(" Derin Düşünce")
        self.deep_thought_btn.setToolTip("Derin Düşünce")
        self.deep_thought_btn.setCheckable(True)
        features_layout.addWidget(self.deep_thought_btn)
        self.web_search_btn = QPushButton()
        self.web_search_btn.setObjectName("web_search_btn")
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
        self.attach_btn.setObjectName("attach_btn")
        self.attach_btn.setIcon(QIcon("icons/attach_file.png"))
        self.attach_btn.setIconSize(QSize(48, 48))
        self.attach_btn.setText(" Dosya Ekle")
        self.attach_btn.setToolTip("Dosya ekle")
        self.attach_btn.clicked.connect(self.attach_file)
        bottom_layout.addWidget(self.attach_btn)
 
         # Gönder Butonu - Yeni ikon (48x48)
        self.send_btn = QPushButton()
        self.send_btn.setObjectName("send_btn")
        self.send_btn.setIcon(QIcon("icons/send_message.png"))
        self.send_btn.setIconSize(QSize(48, 48))
        self.send_btn.setText(" Gönder")
        self.send_btn.setToolTip("Mesajı gönder")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        bottom_layout.addWidget(self.send_btn)
        send_layout.addWidget(self.message_input)
        send_layout.addLayout(bottom_layout)
            
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

            # Uzak API kullanımı
            self.remote_api_check = QCheckBox("OpenRouter API Kullan")
            self.remote_api_check.setChecked(False)
            self.remote_api_check.setEnabled(False)
            self.remote_api_check.toggled.connect(self.toggle_remote_api_usage)
            layout.addWidget(self.remote_api_check)

            # API Anahtarı
            api_layout = QHBoxLayout()
            api_layout.addWidget(QLabel("🔑 OpenRouter API Anahtarı:"))
            self.api_key_edit = QLineEdit()
            self.api_key_edit.setPlaceholderText("sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx")
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_key_edit.setEnabled(False)
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

            # Gizlilik filtresi
            privacy_layout = QHBoxLayout()
            self.no_logging_toggle = QCheckBox("Sadece kayıt tutmayan modeller")
            self.no_logging_toggle.setEnabled(True)
            privacy_layout.addWidget(self.no_logging_toggle)
            layout.addLayout(privacy_layout)

            # Model listesi
            model_id_layout = QHBoxLayout()
            model_id_layout.addWidget(QLabel("🆔 Model ID:"))
            self.model_combo_dialog = QComboBox()
            self.model_combo_dialog.setEditable(False)
            model_id_layout.addWidget(self.model_combo_dialog, 1)
            layout.addLayout(model_id_layout)

            # Yeni model ekleme
            add_layout = QHBoxLayout()
            self.new_model_edit = QLineEdit()
            self.new_model_edit.setPlaceholderText("yeni model id")
            add_btn = QPushButton("Ekle")
            add_btn.clicked.connect(self.add_custom_model)
            remove_btn = QPushButton("Sil")
            remove_btn.clicked.connect(self.remove_custom_model)
            add_layout.addWidget(self.new_model_edit, 1)
            add_layout.addWidget(add_btn)
            add_layout.addWidget(remove_btn)
            layout.addLayout(add_layout)

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
            btn_layout = QHBoxLayout()
            self.fetch_models_btn = QPushButton("Çağır")
            self.fetch_models_btn.setEnabled(True)
            self.fetch_models_btn.clicked.connect(self.fetch_models)
            save_btn = QPushButton("Kaydet")
            save_btn.clicked.connect(self.save_model_settings)
            btn_layout.addWidget(self.fetch_models_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(save_btn)
            layout.addLayout(btn_layout)

            dialog.setLayout(layout)

            # Başlangıçta yerleşik modelleri göster
            self.populate_model_list()
            self.toggle_remote_api_usage(True)
            QMessageBox.information(self, "Bilgi", "Bu özellik sadece uzaktan API ile çalışır.")
            dialog.exec()
        except Exception as e:
            logger.error(f"Model yönetimi açılırken hata: {str(e)}")

    def save_model_settings(self):
        """Model ayarlarını kaydet"""
        try:
            api_key = self.api_key_edit.text().strip()
            model_id = self.model_combo_dialog.currentText().strip()
            self.save_api_key(api_key, model_id, self.remote_api_check.isChecked())
            self.save_custom_models()
            if self.model_combo.findText(model_id) == -1:
                self.model_combo.addItem(model_id)
            self.model_combo.setCurrentText(model_id)
            if hasattr(self, "model_dialog"):
                self.model_dialog.accept()
            self.update_model_combo()
        except Exception as e:
            logger.error(f"Model ayarları kaydedilirken hata: {str(e)}")

    def add_custom_model(self):
        mid = self.new_model_edit.text().strip()
        if not mid:
            return
        if mid not in self.custom_models:
            self.custom_models.append(mid)
            self.model_combo_dialog.addItem(mid)
        idx = self.model_combo_dialog.findText(mid)
        if idx >= 0:
            self.model_combo_dialog.setCurrentIndex(idx)
        self.new_model_edit.clear()

    def remove_custom_model(self):
        mid = self.model_combo_dialog.currentText().strip()
        if mid in self.custom_models:
            self.custom_models.remove(mid)
            idx = self.model_combo_dialog.currentIndex()
            self.model_combo_dialog.removeItem(idx)
            
    def populate_model_list(self):
        """Model dropdown'larını temizle ve güncel modellerle doldur."""
        try:
            # Varsayılan modeller
            default_models = ["deepseek-chat", "deepseek-coder", "deepseek-math"]

            # Eğer custom_models tanımlı değilse boş liste yap
            self.custom_models = getattr(self, "custom_models", [])

            all_models = default_models + self.custom_models

            # Ana ekranda model seçimi
            if hasattr(self, "model_combo"):
                self.model_combo.clear()
                self.model_combo.addItems(all_models)

            # Model ayarları penceresinde model seçimi
            if hasattr(self, "model_combo_dialog"):
                self.model_combo_dialog.clear()
                self.model_combo_dialog.addItems(all_models)

        except Exception as e:
            logger.error(f"Model listesi yüklenirken hata: {str(e)}")
            
    def update_model_combo(self):
        """Seçilen modeli tüm dropdown'lara uygula"""
        try:
            model_id = self.model_combo_dialog.currentText().strip()

            if hasattr(self, "model_combo") and model_id:
                # Eğer ana model listesinde yoksa, ekle
                if self.model_combo.findText(model_id) == -1:
                    self.model_combo.addItem(model_id)
                self.model_combo.setCurrentText(model_id)

            self.statusBar().showMessage(f"🤖 Aktif model güncellendi: {model_id}", 3000)

        except Exception as e:
            logger.error(f"Model güncellenirken hata: {str(e)}")
        
            
    def toggle_remote_api_usage(self, enabled):
        """Uzak API alanlarını devre dışı bırak"""
        self.remote_enabled = False
        self.api_key_edit.setEnabled(False)
        self.fetch_models_btn.setEnabled(False)
        self.update_model_combo()

    def fetch_models(self):
        """OpenRouter'dan model listesini çağır"""
        try:
            QMessageBox.information(self, "Bilgi", "Uzak API devre dışı.")
        except Exception as e:
            logger.error(f"Modeller alınırken hata: {str(e)}")
            QMessageBox.warning(self, "Hata", "Modeller alınamadı, varsayılanlar gösteriliyor")
            self.populate_model_list()

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
        
    def open_theme_settings(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🎨 Tema Ayarları")
            dialog.setFixedSize(400, 300)

            layout = QVBoxLayout()

            # Tema butonları
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
                btn.setObjectName(f"btn_theme_{theme_key}")
                btn.clicked.connect(lambda _, t=theme_key: self.apply_theme(t))
                grid.addWidget(btn, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1

            layout.addWidget(theme_buttons)

            # "Kaydet" yazan ama Close işlevi gören buton
            save_btn = QPushButton("Kaydet")
            save_btn.clicked.connect(dialog.accept)

            btn_box = QDialogButtonBox()
            btn_box.addButton(save_btn, QDialogButtonBox.ButtonRole.RejectRole)
            layout.addWidget(btn_box)

            dialog.setLayout(layout)
            dialog.exec()

        except Exception as e:
            logger.error(f"Tema ayarları açılırken hata: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Tema ayarları açılırken hata oluştu:\n{str(e)}")
            
    def add_project_file(self):
        """Projeye dosya ekle"""
        try:
            if not self.current_project or "name" not in self.current_project:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce bir proje seçin.")
                return
            # Proje seçili mi kontrol et
            if not self.current_project:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce bir proje seçin.")
                return

            file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
            if file_path:
                # 'dosyalar' anahtarı yoksa oluştur
                if 'dosyalar' not in self.current_project:
                    self.current_project['dosyalar'] = []

                if file_path not in self.current_project['dosyalar']:
                    self.current_project['dosyalar'].append(file_path)

                    file_size = os.path.getsize(file_path)
                    size_text = format_file_size(file_size)
                    self.project_files_list.addItem(f"📎 {os.path.basename(file_path)} ({size_text})")

                    self.save_app_state()

        except Exception as e:
            logger.error(f"Projeye dosya eklenirken hata: {str(e)}")

    def remove_project_file(self):

        """Projeden dosya kaldır"""

        try:

            selected_item = self.project_files_list.currentItem()

            if selected_item:

                file_name = selected_item.text().split("📎 ")[1].split(" (")[0]

                for file_path in self.current_project['dosyalar']:

                    if os.path.basename(file_path) == file_name:

                        self.current_project['dosyalar'].remove(file_path)

                        break

                self.project_files_list.takeItem(self.project_files_list.row(selected_item))

                self.save_app_state()

        except Exception as e:

            logger.error(f"Projeden dosya kaldırılırken hata: {str(e)}")



    def refresh_attachments_list(self):
        """Ekli dosya listesini yenile"""
        self.attachments_list.clear()
        for file_path in self.attached_files:
            file_name = os.path.basename(file_path)
            file_widget = QWidget()
            layout = QHBoxLayout(file_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            metrics = QFontMetrics(self.font())
            list_item = QListWidgetItem(elided)
            max_width = self.project_files_list.viewport().width() - 60
            elided = self.font_metrics.elidedText(file_display_name, Qt.TextElideMode.ElideRight, max_width)
            list_item.setToolTip(file_display_name)
            label = QLabel(f"📎 {elided}")
            label.setToolTip(file_name)
            layout.addWidget(label)
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(20, 20)
            remove_btn.setObjectName("remove_button")
            remove_btn.clicked.connect(lambda _, p=file_path: self.remove_attached_file(p))
            layout.addWidget(remove_btn)
            item = QListWidgetItem()
            item.setSizeHint(file_widget.sizeHint())
            self.attachments_list.addItem(item)
            self.attachments_list.setItemWidget(item, file_widget)    
            
    def minimize_to_tray(self):

        """Uygulamayı tepsiye indir"""

        self.hide()

        self.tray_icon.showMessage(

            "DeepSeek Chat", 

            "Uygulama sistem tepsisinde çalışmaya devam ediyor",

            QSystemTrayIcon.MessageIcon.Information, 

            2000

        )

          

    def check_for_updates(self):

        try:

            # Burada gerçek güncelleme kontrolü yapılacak

            QMessageBox.information(self, "Güncellemeler", "Güncelleme kontrol ediliyor...")

            self.statusBar().showMessage("🔄 Güncellemeler kontrol ediliyor...", 3000)

        except Exception as e:

            logger.error(f"Güncelleme kontrol edilirken hata: {str(e)}")

    

    def eventFilter(self, source, event):

        if source is self.message_input and event.type() == QEvent.Type.KeyPress:

            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):

                    self.send_message()

                    return True

        return super().eventFilter(source, event)

    

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
            project_name = project.text(0).lower()
            project_visible = text in project_name
            for j in range(project.childCount()):
                chat_item = project.child(j)
                chat_text = chat_item.text(0).lower()
                if text in chat_text or text in project_name:
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

                project_item = item.parent()

                project_id = project_item.data(0, Qt.ItemDataRole.UserRole)

                self.current_project = self.get_project_by_id(project_id)

                

                

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
            
    def get_project_by_id(self, project_id):
        """ID'ye göre projeyi bul"""

        for project in self.projects_data:

            if project['id'] == project_id:

                return project

        return None

        

    def load_projects(self):

        """projects.json içinden projeleri ve ağaç görünümünü yükler"""

        try:

            if os.path.exists("projects.json"):

                with open("projects.json", "r", encoding="utf-8") as f:

                    self.projeler = json.load(f)



                    if self.projeler:

                        self.current_project = self.projeler[0]



                    # Ağaç yapısını temizle ve yeniden yükle

                    self.projects_tree.clear()

                    for proje in self.projeler:

                        item = QTreeWidgetItem([f"📂 {proje['name']}"])

                        item.setData(0, Qt.ItemDataRole.UserRole, proje['id'])

                        self.projects_tree.addTopLevelItem(item)

        except Exception as e:

            logger.error(f"Projeler yüklenirken hata: {str(e)}")

            

    def load_project(self, project_id):
        """Seçilen projeyi yükler"""
        self.current_project = self.get_project_by_id(project_id)

        if not self.current_project:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir proje seçin.")
            return

    def load_project_context(self, current, previous):
        """Sol ağaçtaki proje seçildiğinde bağlam (talimat + dosya) verilerini yükler"""
        if not current or current.parent():
            self.context_tabs.setTabVisible(self.project_tab_index, False)
            return  # Sadece üst düzey proje öğelerinde çalış

        self.context_tabs.setTabVisible(self.project_tab_index, True)
        self.context_tabs.setCurrentIndex(self.project_tab_index)


        pid = id(current)



        if pid not in self.project_context:

            self.project_context[pid] = {"instructions": "", "files": []}



        ctx = self.project_context[pid]

        self.project_instructions.setText(ctx["instructions"])

        self.project_files_list.clear()



        for f in ctx["files"]:
            self.project_files_list.addItem(f)

    def save_project_context(self):
        """Seçili projenin bağlam bilgilerini kaydet"""
        try:
            item = self.projects_tree.currentItem()
            if not item or item.parent():
                return
            pid = id(item)
            self.project_context[pid] = {
                "instructions": self.project_instructions.toPlainText(),
                "files": [self.project_files_list.item(i).text() for i in range(self.project_files_list.count())],
            }
        except Exception as e:
            logger.error(f"Proje bağlamı kaydedilirken hata: {str(e)}")

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

            existing_names = {self.chat_list.item(i).text() for i in range(self.chat_list.count())}
            index = 1
            while f"Yeni Sohbet {index}" in existing_names:
                index += 1
            chat_name = f"Yeni Sohbet {index}" if index > 1 else "Yeni Sohbet"
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

        """Sohbet başlığını düzenleme moduna al"""

        try:

            chat_id = item.data(Qt.ItemDataRole.UserRole)

            if chat_id in self.chat_data:

                # Düzenleme öncesi orijinal başlığı yükle

                original_title = self.chat_data[chat_id]["title"]

                item.setText(original_title)

                

            self.chat_list.editItem(item)
            QTimer.singleShot(0, self._expand_editor_widget)
        except Exception as e:

            logger.error(f"Sohbet başlığı düzenlenirken hata: {str(e)}")

            

    def update_chat_title(self, chat_id, new_title):

        """Sohbet başlığını günceller ve panele sığacak şekilde formatlar"""

        # Maksimum uzunluk sınırı (opsiyonel)

        if len(new_title) > 100:

            new_title = new_title[:97] + "..."

        

        # QListWidget'ta güncelleme

        for i in range(self.chat_list.count()):

            item = self.chat_list.item(i)

            if item.data(Qt.ItemDataRole.UserRole) == chat_id:

                # Font ölçümleriyle doğru boyutu hesapla

                text_width = self.font_metrics.horizontalAdvance(new_title) + 30  # 30px padding

                

                # Minimum ve maksimum genişlik sınırları

                min_width = 100  # Minimum genişlik

                max_width = self.chat_list.width() - 20  # Panel genişliğine göre

                

                # Genişliği sınırla

                item_width = max(min_width, min(text_width, max_width))

                

                # Boyutu ayarla
                item.setSizeHint(QSize(self.chat_list.width() - 30, 36))  # Sabit boy
                
                # Metni kısalt ve tooltip ekle
                elided_text = self.font_metrics.elidedText(
                    new_title, 
                    Qt.TextElideMode.ElideRight, 
                    item_width - 10  # 10px kenar boşluğu
                )
                item.setText(elided_text)
                if isinstance(item, QListWidgetItem):
                    elided = self.font_metrics.elidedText(new_title, Qt.TextElideMode.ElideRight, self.chat_list.width() - 30)
                    item.setText(elided)
                    item.setToolTip(new_title)
                else:
                    item.setToolTip(0, new_title)
                break
        item.setSizeHint(QSize(self.chat_list.width() - 30, 36))
        self.chat_list.updateGeometries()

        # Proje ağacında güncelleme
        def update_tree(item):
            
            if item.data(0, Qt.ItemDataRole.UserRole) == chat_id:
                max_width = self.projects_tree.width() - 20
                elided = self.font_metrics.elidedText(new_title, Qt.TextElideMode.ElideRight, max_width)
                item.setText(0, f"💬 {elided}")
                item.setToolTip(0, new_title)
                return True
            
            for j in range(item.childCount()):
                child = item.child(j)
                if update_tree(child):
                    return True
        
        for i in range(self.projects_tree.topLevelItemCount()):
            update_tree(self.projects_tree.topLevelItem(i))
        
        if chat_id in self.chat_data:
            self.chat_data[chat_id]["title"] = new_title
            self.save_app_state()  

    def resizeEvent(self, event):
        """Pencere yeniden boyutlandırıldığında chat listesini güncelle"""
        super().resizeEvent(event)
        self.update_chat_list_titles()

    def update_chat_list_titles(self):

        """Tüm chat başlıklarını yeniden boyutlandır"""

        for i in range(self.chat_list.count()):

            item = self.chat_list.item(i)

            chat_id = item.data(Qt.ItemDataRole.UserRole)

            if chat_id in self.chat_data:

                title = self.chat_data[chat_id]["title"]

                self.update_chat_title(chat_id, title)  



    def handle_chat_title_changed(self, item):
        """Başlık değiştiğinde güncellemeleri yap"""
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id in self.chat_data:
            new_title = item.text().strip()
            if not new_title:
                new_title = self.chat_data[chat_id]["title"]
                item.setText(new_title)
            else:
                existing = {self.chat_list.item(i).text() for i in range(self.chat_list.count()) if self.chat_list.item(i) != item}
                if new_title in existing:
                    QMessageBox.warning(self, "Uyarı", "Bu isimde bir sohbet zaten var")
                    item.setText(self.chat_data[chat_id]["title"])
                    return
            self.update_chat_title(chat_id, new_title)

    def handle_project_item_changed(self, item, column):
        """Proje veya sohbet adı değiştiğinde hizala"""
        if not item.parent():
            name = item.text(0).replace("📂 ", "").strip()
            if not name:
                name = item.toolTip(0) or "Proje"
                item.setText(0, f"📂 {name}")
            else:
                existing = {self.projects_tree.topLevelItem(i).text(0).replace("📂 ", "") for i in range(self.projects_tree.topLevelItemCount()) if self.projects_tree.topLevelItem(i) != item}
                if name in existing:
                    QMessageBox.warning(self, "Uyarı", "Bu isimde bir proje zaten var")
                    item.setText(0, item.toolTip(0) or "Proje")
                    return
            max_width = self.projects_tree.width() - 20
            elided = self.font_metrics.elidedText(name, Qt.TextElideMode.ElideRight, max_width)
            item.setText(0, f"📂 {elided}")
            item.setToolTip(name)
        else:
            chat_id = item.data(0, Qt.ItemDataRole.UserRole)
            if chat_id in self.chat_data:
                title = item.text(0).replace("💬 ", "").strip()
                if not title:
                    title = self.chat_data[chat_id]["title"]
                    item.setText(0, f"💬 {title}")
                self.update_chat_title(chat_id, title)

    def _expand_editor_widget(self):
        """Edit kutusunu genişletir"""
        for editor in self.findChildren(QLineEdit):
            if editor.objectName() != "chat_editor":
                width = max(self.chat_list.width(), self.projects_tree.width()) - 20
                editor.setMinimumWidth(self.chat_list.width() - 20)
                editor.setObjectName("chat_editor")
                editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                editor.customContextMenuRequested.connect(lambda pos, e=editor: self.show_editor_context_menu(e, pos))
           

    def new_project(self):
        try:
            project_name, ok = QInputDialog.getText(self, "Yeni Proje", "Proje Adı:")
            if ok and project_name:
                names = {self.projects_tree.topLevelItem(i).text(0).replace("📂 ", "") for i in range(self.projects_tree.topLevelItemCount())}
                if project_name in names:
                    QMessageBox.warning(self, "Uyarı", "Bu isimde bir proje zaten var")
                    return
                project_id = str(uuid.uuid4())
                self.projects_data.append({
                    "id": project_id,
                    "name": project_name,
                    "chats": [],
                    "instructions": "",

                    "files": []

                })

                # Yeni proje oluştur
                new_project = QTreeWidgetItem([f"📂 {project_name}"])
                new_project.setData(0, Qt.ItemDataRole.UserRole, project_id)
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
                QTimer.singleShot(0, self._expand_editor_widget)
                if item.parent():
                    chat_id = item.data(0, Qt.ItemDataRole.UserRole)
                    if chat_id and chat_id in self.chat_data:
                        self.chat_data[chat_id]["title"] = item.text(0).replace("💬 ", "")
                self.save_app_state()

        

        except Exception as e:

            logger.error(f"Proje başlığı düzenlenirken hata: {str(e)}")



    def change_theme(self, theme_name):

        """Kullanıcı tema değiştirdiğinde çağrılır"""

        self.apply_theme(theme_name)

        self.current_theme = theme_name

        self.save_app_state()

    

    def apply_theme(self, theme_name):

        """Tema uygula - CSS hatalarına karşı korumalı"""

        try:

            css_files = [

                "styles/base.css",

                "styles/layout.css",

                "styles/components.css",

                "styles/remove_button.css",

                "styles/chat_editor.css",

                "styles/deep_thought_btn.css",

                "styles/web_search_btn.css",

                "styles/project_title.css",

                "styles/chat_message.css",

                f"styles/{theme_name}_theme.css",

            ]
            combined_css = ""
            for css_file in css_files:
                if os.path.exists(css_file):
                    with open(css_file, "r", encoding="utf-8") as f:
                        combined_css += f.read() + "\n"

            weight = "bold" if self.label_bold else "normal"

            style_italic = "italic" if self.italic_subtitles else "normal"

            combined_css += (

                f".chat-message .message-text {{ font-family: {self.font_family}; font-size: {self.font_size}px; }}\n"

                f".chat-message .sender {{ font-weight: {weight}; font-style: {style_italic}; }}\n"

            )



            self.setStyleSheet(combined_css)

        except Exception as e:

            logger.error(f"Tema yüklenirken hata: {str(e)}")

            

    def apply_button_styles(self):

        """Özel buton stillerini uygular"""

        # Tema dosyasında zaten tanımlı, ekstra bir şey yapmaya gerek yok

        pass

        

    

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
                    rename_action = menu.addAction(QIcon("icons/rename.png"), "Yeniden Adlandır")
                    rename_action.triggered.connect(lambda: self.projects_tree.editItem(item, 0))
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
                    move_root_action = menu.addAction(QIcon("icons/move.png"), "Ana Listeye Taşı")
                    move_root_action.triggered.connect(lambda: self.move_to_main_chat_list(item))
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

            

    def show_and_activate(self):

        """Pencereyi göster ve öne getir"""

        self.show()

        self.raise_()

        self.activateWindow()

        

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

            menu.exec(self.chat_list.mapToGlobal(pos))

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

            

    def project_drag_enter(self, event):

        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):

            event.acceptProposedAction()



    def project_drop_event(self, event):
        item = self.projects_tree.itemAt(event.position().toPoint())
        source = event.source()
        if source == self.projects_tree:
            chat_item = self.projects_tree.currentItem()
        else:
            chat_item = self.chat_list.currentItem()

        if chat_item:
            if item and not item.parent():
                self.move_chat_to_project(item, chat_item)
                event.acceptProposedAction()
            elif not item:
                self.move_to_main_chat_list(chat_item)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    

    def rename_selected_chat(self):

        """Seçili sohbeti yeniden adlandır"""

        try:

            if self.chat_list.currentItem():
                self.chat_list.editItem(self.chat_list.currentItem())
                QTimer.singleShot(0, self._expand_editor_widget)
            elif self.projects_tree.currentItem() and self.projects_tree.currentItem().parent():
                self.projects_tree.editItem(self.projects_tree.currentItem(), 0)
                QTimer.singleShot(0, self._expand_editor_widget)
        except Exception as e:

            logger.error(f"Sohbet yeniden adlandırılırken hata: {str(e)}")



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

    def show_editor_context_menu(self, editor, pos):
        menu = editor.createStandardContextMenu()
        self.translate_context_menu(menu)
        menu.exec(editor.mapToGlobal(pos))
    

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
            QTimer.singleShot(0, self._expand_editor_widget)
            self.save_app_state()

        except Exception as e:
            logger.error(f"Projeye sohbet eklenirken hata: {str(e)}")

    def move_chat_to_project(self, project_item, chat_item):
        """Sohbeti projeye taşır"""
        try:
            if isinstance(chat_item, QTreeWidgetItem):
                chat_id = chat_item.data(0, Qt.ItemDataRole.UserRole)
            else:
                chat_id = chat_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(chat_item, QTreeWidgetItem):
                title = chat_item.text(0)
                if chat_item.parent():
                    chat_item.parent().removeChild(chat_item)
            else:
                title = chat_item.text()
                row = self.chat_list.row(chat_item)
                self.chat_list.takeItem(row)
            new_item = QTreeWidgetItem([f"💬 {title if not title.startswith('💬 ') else title[2:].strip()}"])
            new_item.setData(0, Qt.ItemDataRole.UserRole, chat_id)
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
            project_item.addChild(new_item)
            project_item.setExpanded(True)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Sohbet projeye taşınırken hata: {str(e)}")

    def move_to_main_chat_list(self, chat_item):
        """Projeden ana sohbet listesine taşır"""
        try:
            if isinstance(chat_item, QTreeWidgetItem):
                chat_id = chat_item.data(0, Qt.ItemDataRole.UserRole)
            else:
                chat_id = chat_item.data(Qt.ItemDataRole.UserRole)
            title = chat_item.text(0) if isinstance(chat_item, QTreeWidgetItem) else chat_item.text()
            if isinstance(chat_item, QTreeWidgetItem) and chat_item.parent():
                chat_item.parent().removeChild(chat_item)

            new_item = QListWidgetItem(title if not title.startswith("💬 ") else title.replace("💬 ", ""))
            new_item.setData(Qt.ItemDataRole.UserRole, chat_id)
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.chat_list.addItem(new_item)
            self.save_app_state()
        except Exception as e:
            logger.error(f"Sohbet ana listeye taşınırken hata: {str(e)}")
            

    def export_chats(self):
        default_name = create_safe_filename(self.chat_data[self.active_chat_id]["title"])
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Sohbetleri Dışa Aktar", default_name, "JSON Dosyaları (*.json)"
        )
        try:
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.chat_data.get(self.active_chat_id, {}), f, indent=2, ensure_ascii=False)
                self.statusBar().showMessage("💾 Sohbet dışa aktarıldı", 3000)
        except Exception as e:
            logger.error(f"Sohbet dışa aktarılırken hata: {str(e)}")

    def export_selected_chat(self):
        """Seçili sohbeti dışa aktar"""
        try:
            item = self.chat_list.currentItem()
            if not item and self.projects_tree.currentItem():
                tree_item = self.projects_tree.currentItem()
                if tree_item.parent():
                    item = tree_item
            if not item:
                return
            chat_id = item.data(Qt.ItemDataRole.UserRole) if isinstance(item, QListWidgetItem) else item.data(0, Qt.ItemDataRole.UserRole)
            if not chat_id:
                return
            default_name = create_safe_filename(self.chat_data[chat_id]["title"])
            file_path, _ = QFileDialog.getSaveFileName(self, "Sohbeti Dışa Aktar", default_name, "JSON Dosyaları (*.json)")
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n" + "="*60 + "\n")
                    f.write(f"SOHBET: {self.chat_data[chat_id]['title']}\n")
                    f.write("="*60 + "\n")
                    for msg in self.chat_data[chat_id]["messages"]:
                        role = "Siz" if msg["sender"] == "user" else "Asistan"
                        f.write(f"{role}: {msg['message']}\n\n")
                self.statusBar().showMessage("💾 Sohbet dışa aktarıldı", 3000)
        except Exception as e:
            logger.error(f"Seçili sohbet dışa aktarılırken hata: {str(e)}")
            
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

            

    def quit_application(self):
        """Uygulamadan tamamen çık"""
        self.tray_icon.hide()
        self.save_app_state()
        QApplication.quit()

    def closeEvent(self, event):
        """Pencere kapatılırken durumu kaydet"""
        try:
            if hasattr(self, "worker") and self.worker.isRunning():
                self.worker.quit()
                self.worker.wait()
        except Exception as e:
            logger.error(f"Thread durdurulurken hata: {e}")
        event.accept()
    
    def load_api_key(self):

        """Kayıtlı API anahtarını yükle"""

        try:

            if os.path.exists("api_config.json"):

                with open("api_config.json", "r") as f:

                    config = json.load(f)

                    self.api_key = config.get("api_key")

        

        except Exception as e:

            logger.error(f"API anahtarı yüklenirken hata: {str(e)}")

    

    def save_api_key(self, model_name=None, api_key=None, source=None):
        try:
            if api_key:
                self.api_key = api_key
            if model_name:
                if hasattr(self, "model_combo"):
                    self.model_combo.setCurrentText(model_name)
            self.save_app_state()
            logger.info("API anahtarı ve model güncellendi.")
        except Exception as e:
            logger.error(f"Model ayarları kaydedilirken hata: {e}")

        def get_response_from_openrouter(self, model_name):
            """Local Ollama (gemma-2b) ve OpenRouter API'sinden yanıt al"""
            try:
                user_message = self.input_field.toPlainText()

                if model_name == "gemma-2b":
                    # ✅ Yerel model, API key yok
                    url = "http://localhost:11434/v1/chat/completions"
                    headers = {"Content-Type": "application/json"}
                    data = {
                        "model": "gemma:2b",
                        "messages": [
                            {"role": "user", "content": user_message}
                        ],
                        "stream": False
                    }

                else:
                    # ✅ OpenRouter için API key gerekli
                    url = self.api_base_url + "/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": self.model_mapping.get(model_name, model_name),
                        "messages": [
                            {"role": "user", "content": user_message}
                        ],
                        "stream": False
                    }

                response = requests.post(url, headers=headers, json=data)
                response_data = response.json()

                if response.status_code == 200 and "choices" in response_data:
                    assistant_reply = response_data["choices"][0]["message"]["content"]

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
                    QTimer.singleShot(1500, lambda: self.simulate_response(model_name))

            except Exception as e:
                logger.error(f"API isteği sırasında hata: {str(e)}")
                self.statusBar().showMessage(f"❌ İstek hatası: {str(e)}", 5000)
                QTimer.singleShot(1500, lambda: self.simulate_response(model_name))
                
    def save_custom_models(self):
        logger.info("Custom modeller kaydedildi (şimdilik boş)")            
        
    def send_message(self):
        try:
            # Gönderme devam ediyorsa iptal et
            if hasattr(self, "worker") and self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait()

            self.worker = WorkerThread(
                conversation_history=history,
                model=self.model_mapping.get(model_name, "gemma:2b"),
                endpoint="http://localhost:11434/api/generate"
            )
            self.worker.terminate()
            self.sending = False
            if self.chat_data[self.active_chat_id]["messages"]:
                self.chat_data[self.active_chat_id]["messages"].pop()
            self.chat_display.clear()
            for msg in self.chat_data[self.active_chat_id]["messages"]:
                self.append_message(msg["sender"], msg["message"])
            self.message_input.setPlainText(self.pending_message)
            self.send_btn.setText(" Gönder")
            self.send_btn.setIcon(QIcon("icons/send_message.png"))
            self.message_input.setReadOnly(False)
            self.statusBar().showMessage("Gönderim iptal edildi", 3000)
            return

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

            self.pending_message = message
            self.message_input.clear()
            

            # Aktif modeli al

            model_name = self.model_combo.currentText()

            

            # API iş parçacığı
            self.worker = WorkerThread(
                "demo-key",
                [{"role": msg['sender'], "content": msg['message']} for msg in self.chat_data[self.active_chat_id]["messages"]],
                model_name
            )
            self.worker.thinking_updated.connect(self.handle_thinking_update)
            self.worker.response_received.connect(lambda reply, t: self.handle_api_response(reply, model_name))
            self.worker.error_occurred.connect(lambda err: self.handle_api_error(err, model_name))
            self.worker.start()
            self.statusBar().showMessage("⏳ DeepSeek yanıt oluşturuyor...")
            self.send_btn.setText(" Durdur")
            self.send_btn.setIcon(QIcon("icons/update.png"))
            self.message_input.setReadOnly(True)
            self.sending = True
            if self.api_key:
                history = []
                for msg in self.chat_data[self.active_chat_id]["messages"]:
                    role = "user" if msg["sender"] == "user" else "assistant"
                    history.append({"role": role, "content": msg["message"]})
                # Önceki worker thread varsa durdur
                if hasattr(self, "worker") and self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait()
                self.worker = WorkerThread(
                    history,
                    model=self.model_mapping.get(model_name, "deepseek/deepseek-r1:free"),
                    endpoint="http://localhost:11434/api/generate" if "gemma" in model_name else "https://openrouter.ai/api/v1/chat/completions"
                )
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
        """Sohbet ekranına mesaj ekler"""
        try:
            if sender == "assistant" and not any(m["sender"] == "assistant" for m in self.chat_data[self.active_chat_id]["messages"]):
                self.chat_display.append("<i>Merhaba, size nasil yardimci olabilirim?</i><br>")
            msg_class = "user" if sender == "user" else "assistant"
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            spacer = "&nbsp;&nbsp;&nbsp;&nbsp;"
            prefix = "Siz:" if sender == "user" else "DeepSeek:"
            html_content = (
                f"<div class='chat-message {msg_class}'>"
                f"{spacer}<span class='sender'>{prefix}</span> "
                f"<span class='message-text'>{message}</span>"
                f"</div><br>"
            )
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



            files, _ = QFileDialog.getOpenFileNames(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
            valid_extensions = ['.txt', '.py', '.js', '.html', '.css', '.json', '.pdf', '.doc', '.docx', '.md']
            for file_path in files:
                if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
                    QMessageBox.warning(self, "Desteklenmeyen Dosya", "Seçilen dosya tipi desteklenmiyor. Lütfen metin tabanlı dosyalar ekleyin.")
                    continue

                file_name = os.path.basename(file_path)
                self.attached_files.append(file_path)

                file_widget = QWidget()
                layout = QHBoxLayout(file_widget)
                layout.setContentsMargins(0, 0, 0, 0)
                metrics = QFontMetrics(self.font())
                max_width = self.attachments_list.width() - 60
                elided = metrics.elidedText(file_name, Qt.TextElideMode.ElideMiddle, max_width)
                label = QLabel(f"📎 {elided}")
                label.setToolTip(file_name)
                layout.addWidget(label)
                remove_btn = QPushButton("✕")
                remove_btn.setFixedSize(20, 20)
                remove_btn.setObjectName("remove_button")
                remove_btn.clicked.connect(lambda _, p=file_path: self.remove_attached_file(p))
                layout.addWidget(remove_btn)

                item = QListWidgetItem()
                item.setSizeHint(file_widget.sizeHint())
                self.attachments_list.addItem(item)
                self.attachments_list.setItemWidget(item, file_widget)
            self.refresh_attachments_list()
        except Exception as e:

            logger.error(f"Dosya eklenirken hata: {str(e)}")



    def remove_attached_file(self, file_path):

        if file_path in self.attached_files:

            self.attached_files.remove(file_path)

            self.refresh_attachments_list()

            

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Özel hata yöneticisi"""
        error_msg = f"{exc_type.__name__}: {exc_value}"
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Hata diyaloğunu göster
        error_dialog = ErrorDialog(error_msg, self)
        error_dialog.exec()
    
    def handle_api_response(self, reply, model_name):
        try:
            self.append_message("assistant", reply)
            self.chat_data[self.active_chat_id]["messages"].append({
                "sender": "assistant",
                "message": reply,
                "timestamp": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
            })
            self.send_btn.setText(" Gönder")
            self.send_btn.setIcon(QIcon("icons/send_message.png"))
            self.message_input.setReadOnly(False)
            self.sending = False
        except Exception as e:
            logger.error(f"API yanıtı işlenirken hata: {str(e)}")

    def handle_thinking_update(self, text):
        """Düşünme adımlarını durum çubuğunda göster"""
        self.statusBar().showMessage(text)

    def handle_api_error(self, err, model_name):
        """API hatası olduğunda çağrılır"""
        message = err
        if "Ağ hatası" in err or "Connection refused" in err:
            message = "Model henüz yüklenmedi"
        self.statusBar().showMessage(message, 5000)
        self.send_btn.setText(" Gönder")
        self.send_btn.setIcon(QIcon("icons/send_message.png"))
        self.message_input.setReadOnly(False)
        self.sending = False

    def simulate_response(self, model_name):
        """API başarısız olduğunda basit bir yanıt simüle eder"""
        try:
            reply = f"(Sim) {model_name} cevabı hazır değil. Model henüz yüklenmedi."
            self.handle_api_response(reply, model_name)
        except Exception as e:
            logger.error(f"Simülasyon yanıtı oluşturulurken hata: {str(e)}")


if __name__ == "__main__":

    try:

        app = QApplication(sys.argv)

        app.setApplicationName("DeepSeek Chat")

        

        # Font ayarı

        font = app.font()

        font.setPointSize(10)

        app.setFont(font)

        

        # Pencereyi belirle

        window = None

        

        user_manager = UserManager()

        

         # Giriş bilgilerini kontrol et

        if os.path.exists("user_prefs.json"):

            with open("user_prefs.json", "r") as f:

                prefs = json.load(f)

                if prefs.get("remember", False):

                    window = MainApplication()

                    window.show()

                else:

                    window = LoginWindow(user_manager)

                    window.show()
        else:
            window = LoginWindow(user_manager)
            window.show()

        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Uygulama başlatılırken hata: {str(e)}")
        error_dialog = ErrorDialog(str(e))
        error_dialog.exec()
        sys.exit(1)
