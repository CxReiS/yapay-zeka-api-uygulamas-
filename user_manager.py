import os
import json
import hashlib
import logging
import uuid

logger = logging.getLogger('DeepSeekChat.user_manager')

class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.users = self.load_users()
        logger.info("Kullanıcı yöneticisi başlatıldı")
    
    def load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Kullanıcı dosyası yüklenirken hata: {str(e)}")
                return {}
        return {}
    
    def save_users(self):
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            logger.info("Kullanıcı verileri kaydedildi")
        except Exception as e:
            logger.error(f"Kullanıcı verileri kaydedilirken hata: {str(e)}")
    
    def register_user(self, email, password):
        if email in self.users:
            logger.warning(f"Kullanıcı zaten kayıtlı: {email}")
            return False, "Bu e-posta adresi zaten kayıtlı"
        
        # Şifre hashleme
        salt = os.urandom(16).hex()
        hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
        
        self.users[email] = {
            'password_hash': hashed_password,
            'salt': salt,
            'api_key': None,
            'projects': {
                "default": {
                    'name': "📁 Varsayılan Proje",
                    'chats': [],
                    'instructions': "",
                    'files': []
                }
            },
            'chats': {},
            'settings': {
                'theme': 'dark',
                'shortcuts': {
                    'send_message': 'Ctrl+Return',
                    'new_line': 'Shift+Return',
                    'new_chat': 'Ctrl+N'
                }
            }
        }
        self.save_users()
        logger.info(f"Yeni kullanıcı kaydedildi: {email}")
        return True, "Kayıt başarılı"
    
    def authenticate(self, email, password):
        if email not in self.users:
            logger.warning(f"Kullanıcı bulunamadı: {email}")
            return False, "Kullanıcı bulunamadı"
        
        user = self.users[email]
        hashed_password = hashlib.sha256((password + user['salt']).encode()).hexdigest()
        
        if hashed_password == user['password_hash']:
            logger.info(f"Kullanıcı giriş yaptı: {email}")
            return True, "Giriş başarılı"
        logger.warning(f"Geçersiz şifre: {email}")
        return False, "Geçersiz şifre"
    
    def get_user(self, email):
        return self.users.get(email, None)
    
    def update_user(self, email, data):
        if email in self.users:
            self.users[email].update(data)
            self.save_users()
            logger.info(f"Kullanıcı güncellendi: {email}")
            return True
        return False
    
    def add_chat_to_project(self, email, project_id, chat_id):
        if email in self.users and project_id in self.users[email]['projects']:
            if chat_id not in self.users[email]['projects'][project_id]['chats']:
                self.users[email]['projects'][project_id]['chats'].append(chat_id)
                self.save_users()
                return True
        return False