import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QSize
from utils import format_file_size


class ProjectView(QWidget):
    """Projeye ait sohbetleri ve dosyaları gösteren bileşen."""

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data or {}
        self.main_app = parent
        self._build_ui()
        self.refresh_view()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.title_label = QLabel()
        self.title_label.setObjectName("project_title")
        layout.addWidget(self.title_label)

        self.new_chat_btn = QPushButton("💬 Yeni Sohbet")
        self.new_chat_btn.setIconSize(QSize(24, 24))
        self.new_chat_btn.clicked.connect(self.new_chat)
        layout.addWidget(self.new_chat_btn)

        layout.addWidget(QLabel("Proje Sohbetleri:"))
        self.chat_list = QListWidget()
        self.chat_list.itemDoubleClicked.connect(self.load_chat)
        layout.addWidget(self.chat_list)

        tools_group = QGroupBox("🛠️ Araçlar")
        tools_layout = QVBoxLayout(tools_group)

        self.add_file_btn = QPushButton("📎 Dosya Ekle")
        self.add_file_btn.clicked.connect(self.add_file)
        tools_layout.addWidget(self.add_file_btn)

        self.file_list = QListWidget()
        tools_layout.addWidget(self.file_list)

        tools_layout.addWidget(QLabel("📝 Talimatlar:"))
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("Proje talimatları...")
        tools_layout.addWidget(self.instructions_edit)

        layout.addWidget(tools_group)

    def refresh_view(self):
        self.title_label.setText(f"📂 {self.project_data.get('name', 'Yeni Proje')}")

        self.chat_list.clear()
        for chat in self.project_data.get('chats', []):
            item = QListWidgetItem(f"💬 {chat.get('title')}")
            item.setData(Qt.ItemDataRole.UserRole, chat.get('id'))
            self.chat_list.addItem(item)

        self.file_list.clear()
        for path in self.project_data.get('files', []):
            if os.path.exists(path):
                size = format_file_size(os.path.getsize(path))
                self.file_list.addItem(f"📎 {os.path.basename(path)} ({size})")
            else:
                self.file_list.addItem(f"📎 {os.path.basename(path)} (Dosya bulunamadı)")

        self.instructions_edit.setPlainText(self.project_data.get('instructions', ''))

    def new_chat(self):
        if self.main_app:
            self.main_app.proje_sohbeti_olustur(self.project_data.get('id'))

    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
        if file_path:
            self.project_data.setdefault('files', [])
            if file_path not in self.project_data['files']:
                self.project_data['files'].append(file_path)
                if self.main_app:
                    self.main_app.save_app_state()
                self.refresh_view()

    def load_chat(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if self.main_app:
            self.main_app.load_chat_by_id(chat_id)

