# C:\projets\python\gestion_scolaire\app\logging_config.py
import logging
import json
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        # Logger complètement isolé
        self.logger = logging.getLogger('security_app')
        self.logger.setLevel(logging.INFO)
        
        # Supprimer tous les handlers existants
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Créer un nouveau handler avec format simple
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Désactiver la propagation
        self.logger.propagate = False

    def log_event(self, user_id, action, resource, status, details=None):
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": str(user_id),
                "action": action,
                "resource": resource,
                "status": status,
                "details": details or {}
            }
            
            message = json.dumps(log_data, ensure_ascii=False)
            
            if status == "SUCCESS":
                self.logger.info(message)
            else:
                self.logger.warning(message)
                
        except Exception as e:
            # Fallback en cas d'erreur
            print(f"🔐 SECURITY LOG ERROR: {action} - {status} - User: {user_id}")

# Instance globale
security_logger = SecurityLogger()