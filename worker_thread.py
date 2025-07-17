"""Arka planda API istekleriyle ilgilenen iş parçacığı."""

import time
import logging
from typing import Optional, List, Dict

from PyQt6.QtCore import QThread, pyqtSignal

from utils.api_client import send_chat_request

logger = logging.getLogger('DeepSeekChat.worker')

class WorkerThread(QThread):
    response_received = pyqtSignal(str, float)
    error_occurred = pyqtSignal(str)
    thinking_updated = pyqtSignal(str)

    def __init__(self, conversation_history: List[Dict[str, str]],
                 model: str = "gemma:2b",
                 endpoint: str = "http://localhost:11434/v1/chat/completions",
                 api_key: Optional[str] = None):
        super().__init__()
        self.conversation_history = conversation_history
        self.model = model
        self.endpoint = endpoint
        self.api_key = api_key

    def run(self):
        """İstek gönderip sonucu sinyallerle bildir."""
        try:
            start_time = time.time()
            for step in [
                "🤔 Sorunuzu analiz ediyorum...",
                "🔍 Bilgilerimi tarıyorum...",
                "🧠 En iyi cevabı oluşturuyorum...",
            ]:
                self.thinking_updated.emit(step)
                time.sleep(0.8)

            reply = send_chat_request(
                self.conversation_history,
                model=self.model,
                endpoint=self.endpoint,
                api_key=self.api_key,
            )
            elapsed = time.time() - start_time
            self.response_received.emit(reply, elapsed)
        except Exception as e:
            self.error_occurred.emit(str(e))
