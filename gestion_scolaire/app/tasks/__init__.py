import logging

# Configuration globale du logging
logging.basicConfig(
    level=logging.INFO,  # Niveau minimal des logs
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Optionnel : réduire le bruit de werkzeug
logging.getLogger("werkzeug").setLevel(logging.WARNING)

