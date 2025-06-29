from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QListWidget, QPushButton, QFileDialog
from PyQt6.QtGui import QIcon
import os

class ProjectSettingsView(QWidget):
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Proje Adı
        name_layout = QHBoxLayout()
        name_label = QLabel("Proje Adı:")
        self.name_edit = QLineEdit(self.project_data.get('name', 'Yeni Proje'))
        self.name_edit.textChanged.connect(self.save_name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit, 1)
        layout.addLayout(name_layout)
        
        # Talimatlar
        instructions_label = QLabel("📋 Proje Talimatları:")
        self.instructions_edit = QTextEdit(self.project_data.get('instructions', ''))
        self.instructions_edit.setPlaceholderText("Proje için özel talimatlar girin...")
        self.instructions_edit.textChanged.connect(self.save_instructions)
        layout.addWidget(instructions_label)
        layout.addWidget(self.instructions_edit)
        
        # Dosya Yönetimi
        files_label = QLabel("📎 Ekli Dosyalar:")
        self.file_list = QListWidget()
        self.file_list.addItems(self.project_data.get('files', []))
        layout.addWidget(files_label)
        layout.addWidget(self.file_list)
        
        # Dosya Ekle Butonu
        file_button_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Dosya Ekle")
        self.add_file_button.setIcon(QIcon("icons/add_file.png"))
        self.add_file_button.clicked.connect(self.add_file)
        
        self.remove_file_button = QPushButton("Seçiliyi Kaldır")
        self.remove_file_button.setIcon(QIcon("icons/remove.png"))
        self.remove_file_button.clicked.connect(self.remove_file)
        self.remove_file_button.setEnabled(False)
        
        # DÜZELTİLMİŞ SATIR:
        self.file_list.itemSelectionChanged.connect(
            lambda: self.remove_file_button.setEnabled(bool(self.file_list.selectedItems()))
        )
        
        file_button_layout.addWidget(self.add_file_button)
        file_button_layout.addWidget(self.remove_file_button)
        layout.addLayout(file_button_layout)
        
        self.setLayout(layout)
    
    def save_name(self):
        self.project_data['name'] = self.name_edit.text()
    
    def save_instructions(self):
        self.project_data['instructions'] = self.instructions_edit.toPlainText()
    
    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
        if file_path:
            file_name = os.path.basename(file_path)
            if 'files' not in self.project_data:
                self.project_data['files'] = []
            
            if file_name not in self.project_data['files']:
                self.project_data['files'].append(file_name)
                self.file_list.addItem(file_name)
    
    def remove_file(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            file_name = item.text()
            if file_name in self.project_data['files']:
                self.project_data['files'].remove(file_name)
                self.file_list.takeItem(self.file_list.row(item))