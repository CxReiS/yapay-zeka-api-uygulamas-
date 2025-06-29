import requests
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('DeepSeekChat.worker')

class WorkerThread(QThread):
    response_received = pyqtSignal(str, float)  # Yanıt metni, geçen süre
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key, conversation_history, user_message, model="deepseek-chat", memory=""):
        super().__init__()
        self.api_key = api_key
        self.conversation_history = conversation_history
        self.user_message = user_message
        self.memory = memory
        self.model = model
        self.endpoint = "https://api.deepseek.com/v1/chat/completions"

    def run(self):
        try:
            # Mesaj geçmişini hazırla
            messages = [{"role": "system", "content": self.memory}] if self.memory else []
            for msg in self.conversation_history:
                messages.append({"role": msg['role'], "content": msg['content']})
            messages.append({"role": "user", "content": self.user_message})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            start_time = time.time()
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_data = response.json()
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    assistant_message = response_data['choices'][0]['message']['content']
                    self.response_received.emit(assistant_message, response_time)
                else:
                    self.error_occurred.emit("API yanıtı geçersiz: choices bulunamadı")
            else:
                error_msg = f"API hatası ({response.status_code}): {response.text}"
                self.error_occurred.emit(error_msg)
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Ağ hatası: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Beklenmeyen hata: {str(e)}")