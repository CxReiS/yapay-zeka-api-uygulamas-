import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QPushButton, QFileDialog, QGroupBox, QTextEdit
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize
from utils import format_file_size

class ProjectView(QWidget):
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.ana_uygulama = parent  # Ana uygulamaya erişim
        self.init_ui() # init_ui metodunu çağır
        
    def init_ui(self):
        """Arayüz bileşenlerini başlatır"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)    
    
    def refresh_view(self):
        """Proje verilerini görünümde günceller"""
        self.name_edit.setText(self.project_data.get('name', 'Yeni Proje'))
        self.instructions_edit.setPlainText(self.project_data.get('instructions', ''))
        self.file_list.clear()
        self.file_list.addItems(self.project_data.get('files', []))
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Proje başlığı
        self.baslik = QLabel(f"📂 {self.project_data.get('name', 'Yeni Proje')}")
        self.baslik.setObjectName("project_title")
        layout.addWidget(self.baslik)
        
        # Yeni sohbet butonu
        self.yeni_sohbet_btn = QPushButton("💬 Yeni Sohbet")
        self.yeni_sohbet_btn.setIconSize(QSize(24, 24))
        self.yeni_sohbet_btn.clicked.connect(self.yeni_sohbet_olustur)
        layout.addWidget(self.yeni_sohbet_btn)
        
        # Sohbet listesi
        layout.addWidget(QLabel("Proje Sohbetleri:"))
        self.sohbet_listesi = QListWidget()
        self.sohbet_listesi.itemDoubleClicked.connect(self.sohbet_yukle)
        layout.addWidget(self.sohbet_listesi)
        
        # Araçlar bölümü
        araclar_grubu = QGroupBox("🛠️ Araçlar")
        araclar_duzeni = QVBoxLayout(araclar_grubu)
        
        # Dosya ekleme
        self.dosya_ekle_btn = QPushButton("📎 Dosya Ekle")
        self.dosya_ekle_btn.clicked.connect(self.dosya_ekle)
        araclar_duzeni.addWidget(self.dosya_ekle_btn)
        
        # Ekli dosyalar listesi
        self.dosya_listesi = QListWidget()
        araclar_duzeni.addWidget(self.dosya_listesi)
        
        # Talimatlar
        self.talimatlar = QTextEdit()
        self.talimatlar.setPlaceholderText("Proje talimatları...")
        araclar_duzeni.addWidget(QLabel("📝 Talimatlar:"))
        araclar_duzeni.addWidget(self.talimatlar)
        
        layout.addWidget(araclar_grubu)
        self.setLayout(layout)
        
        # Verileri yükle
        self.refresh_view()
    
    def refresh_view(self):
        """Proje verilerini görünüme yansıt"""
        
        # Başlık
        self.baslik.setText(f"📂 {self.project_data.get('name', 'Yeni Proje')}")
        
        # Sohbetleri doldur
        self.sohbet_listesi.clear()
        for sohbet in self.proje.get('sohbetler', []):
            oge = QListWidgetItem(f"💬 {sohbet['baslik']}")
            oge.setData(Qt.ItemDataRole.UserRole, sohbet['id'])
            self.sohbet_listesi.addItem(oge)
        
        # Dosyaları doldur
        self.dosya_listesi.clear()
        for dosya in self.project_data.get('files', []):
            if os.path.exists(dosya):
                file_size = os.path.getsize(dosya)
                size_text = format_file_size(file_size)
                self.dosya_listesi.addItem(f"📎 {os.path.basename(dosya)} ({size_text})")
            else:
                self.dosya_listesi.addItem(f"📎 {os.path.basename(dosya)} (Dosya bulunamadı)")
        
        # Talimatları doldur
        self.talimatlar.setPlainText(self.project_data.get('instructions', ''))
    
    def yeni_sohbet_olustur(self):
        """Ana uygulamada yeni sohbet oluştur"""
        if self.ana_uygulama:
            self.ana_uygulama.proje_sohbeti_olustur(self.project_data.get('id'))
    
    def dosya_ekle(self):
        """Projeye dosya ekle"""
        dosya_yolu, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Tüm Dosyalar (*)")
        if dosya_yolu:
            if 'files' not in self.project_data:
                self.project_data['files'] = []
                
            if dosya_yolu not in self.project_data['files']:
                self.project_data['files'].append(dosya_yolu)
                if self.ana_uygulama:
                    self.ana_uygulama.save_app_state()
                self.refresh_view()  # Görünümü yenile
    
    def sohbet_yukle(self, oge):
        """Sohbeti yükle"""
        sohbet_id = oge.data(Qt.ItemDataRole.UserRole)
        if self.ana_uygulama:
            self.ana_uygulama.load_chat_by_id(sohbet_id)
        