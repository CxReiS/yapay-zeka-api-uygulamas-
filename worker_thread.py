import requests
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('DeepSeekChat.worker')

class WorkerThread(QThread):
    response_received = pyqtSignal(str, float)
    error_occurred = pyqtSignal(str)
    thinking_updated = pyqtSignal(str)

    def __init__(self, conversation_history, model="gemma:2b", endpoint="http://localhost:11434/api/generate"):
        super().__init__()
        self.conversation_history = conversation_history
        self.model = model
        self.endpoint = endpoint

    def run(self):
        try:
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in self.conversation_history)
            payload = {"model": self.model, "prompt": prompt, "stream": False}

            start_time = time.time()
            thinking_steps = [
                "🤔 Sorunuzu analiz ediyorum...",
                "🔍 Bilgilerimi tarıyorum...",
                "🧠 En iyi cevabı oluşturuyorum...",
            ]
            for step in thinking_steps:
                self.thinking_updated.emit(step)
                time.sleep(0.8)

            response = requests.post(self.endpoint, json=payload, timeout=120)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    self.response_received.emit(data["response"], response_time)
                else:
                    self.error_occurred.emit("API yanıtı geçersiz")
            else:
                self.error_occurred.emit(f"API hatası ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Ağ hatası: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Beklenmeyen hata: {str(e)}")
