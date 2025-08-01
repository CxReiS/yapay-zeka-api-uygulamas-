import requests
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger('DeepSeekChat.worker')

class WorkerThread(QThread):
    response_received = pyqtSignal(str, float)
    error_occurred = pyqtSignal(str)
    thinking_updated = pyqtSignal(str)  # Thinking messages signal

    def __init__(self, api_key, conversation_history, model="deepseek/deepseek-r1:free"):
        """Arka planda API isteği yapan iş parçacığı"""
        super().__init__()
        self.api_key = api_key
        self.conversation_history = conversation_history
        self.model = model
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def run(self):
        """API isteğini çalıştır ve sonuçları sinyallerle döndür"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/CxReiS/DeepSeekChat",
                "X-Title": "DeepSeek Chat",
            }

            payload = {
                "model": self.model,
                "messages": self.conversation_history,
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            
            start_time = time.time()

            # Düşünme adımları
            thinking_steps = [
                "🤔 Sorunuzu analiz ediyorum...",
                "🔍 Bilgilerimi tarıyorum...",
                "🧠 En iyi cevabı oluşturuyorum..."
            ]
            for step in thinking_steps:
                self.thinking_updated.emit(step)
                time.sleep(0.8)  # Simulate thinking time

            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=120)
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
            self.response_received.emit("Üzgünüm, bir hata oluştu. Lütfen bağlantınızı kontrol edin.", 0)    
