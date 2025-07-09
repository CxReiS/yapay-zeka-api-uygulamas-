from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication


def apply_font_settings(app_instance):
    """Uygulamanın tanımlı font ayarlarını uygular."""
    try:
        font = QFont(app_instance.font_family, app_instance.font_size)
        QApplication.instance().setFont(font)

        if hasattr(app_instance, 'chat_display'):
            app_instance.chat_display.setFont(font)
        if hasattr(app_instance, 'message_input'):
            app_instance.message_input.setFont(font)

        return font
    except Exception as e:
        if hasattr(app_instance, 'logger'):
            app_instance.logger.error(f"Yazı tipi uygulanırken hata: {str(e)}")
        return None

