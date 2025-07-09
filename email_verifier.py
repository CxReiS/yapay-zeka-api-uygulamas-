 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/email_verifier.py b/email_verifier.py
index fbbcfd5452e6edc8eaae6e5504370f86556d850e..7af1fb7c6c54a21dbb080a5b6c98abe7c8526b4d 100644
--- a/email_verifier.py
+++ b/email_verifier.py
@@ -1,54 +1,59 @@
 import logging
 import smtplib
 import ssl
 from email.mime.text import MIMEText
 import uuid
 
 logger = logging.getLogger('DeepSeekChat.email_verifier')
 
-class EmailVerifier:
-    def __init__(self):
-        self.verification_codes = {}
-        self.smtp_config = None
-        logger.info("E-posta doğrulayıcı başlatıldı")
+class EmailVerifier:
+    def __init__(self):
+        """E-posta doğrulama işlemlerini yönetir"""
+        self.verification_codes = {}
+        self.smtp_config = None
+        logger.info("E-posta doğrulayıcı başlatıldı")
     
-    def set_smtp_config(self, config):
-        self.smtp_config = config
-        logger.info("SMTP konfigürasyonu güncellendi")
+    def set_smtp_config(self, config):
+        """SMTP ayarlarını uygular"""
+        self.smtp_config = config
+        logger.info("SMTP konfigürasyonu güncellendi")
     
-    def generate_code(self):
-        return str(uuid.uuid4())[:6].upper()
+    def generate_code(self):
+        """Rastgele doğrulama kodu üretir"""
+        return str(uuid.uuid4())[:6].upper()
     
-    def send_verification_email(self, receiver_email):
-        if not self.smtp_config:
-            logger.error("SMTP konfigürasyonu yapılmamış")
-            return False, "SMTP ayarları yapılandırılmamış"
+    def send_verification_email(self, receiver_email):
+        """Kullanıcıya doğrulama e-postası gönderir"""
+        if not self.smtp_config:
+            logger.error("SMTP konfigürasyonu yapılmamış")
+            return False, "SMTP ayarları yapılandırılmamış"
         
         try:
             sender_email = self.smtp_config['email']
             code = self.generate_code()
             
             message = MIMEText(f"🔐 DeepSeek Chat doğrulama kodunuz: {code}\n\nBu kodu uygulamaya girerek hesabınızı doğrulayabilirsiniz.")
             message["Subject"] = "DeepSeek Chat Doğrulama Kodu"
             message["From"] = sender_email
             message["To"] = receiver_email
             
             context = ssl.create_default_context()
             with smtplib.SMTP_SSL(self.smtp_config['server'], self.smtp_config['port'], context=context) as server:
                 server.login(sender_email, self.smtp_config['password'])
                 server.sendmail(sender_email, receiver_email, message.as_string())
             
             self.verification_codes[receiver_email] = code
             logger.info(f"Doğrulama kodu gönderildi: {receiver_email}")
             return True, "✅ Doğrulama kodu e-posta adresinize gönderildi"
         except Exception as e:
             logger.error(f"E-posta gönderilemedi: {str(e)}")
             return False, f"❌ E-posta gönderilemedi: {str(e)}"
     
-    def verify_code(self, email, code):
-        if email in self.verification_codes and self.verification_codes[email] == code:
-            del self.verification_codes[email]
-            logger.info(f"E-posta doğrulandı: {email}")
-            return True
-        logger.warning(f"Geçersiz doğrulama kodu: {email}")
+    def verify_code(self, email, code):
+        """Girilen kodu doğrular"""
+        if email in self.verification_codes and self.verification_codes[email] == code:
+            del self.verification_codes[email]
+            logger.info(f"E-posta doğrulandı: {email}")
+            return True
+        logger.warning(f"Geçersiz doğrulama kodu: {email}")
         return False
 
EOF
)
