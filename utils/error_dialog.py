from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
)
import os


class ErrorDialog(QDialog):
    """Uygulamada oluşan hataları kullanıcıya gösteren basit diyalog."""

    def __init__(self, error_msg: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ Hata Raporu")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout(self)

        error_label = QLabel("Aşağıdaki hata oluştu:")
        layout.addWidget(error_label)

        self.error_text = QTextEdit()
        self.error_text.setPlainText(error_msg)
        self.error_text.setReadOnly(True)
        layout.addWidget(self.error_text)

        log_btn = QPushButton("Log Dosyasını Aç")
        log_btn.clicked.connect(self.open_log)
        layout.addWidget(log_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def open_log(self):
        try:
            if os.path.exists("app.log"):
                os.startfile("app.log")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Log dosyası açılamadı: {str(e)}")

