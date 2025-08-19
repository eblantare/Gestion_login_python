# import json
# import hashlib
# from pathlib import Path

# USER_FILE = Path(__file__).parent / "users.json"

# def load_users():
#     if not USER_FILE.exists():
#         return {}
#     with open(USER_FILE, "r") as f:
#         return json.load(f)
    
# def has_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def login_user(username, password):
#     users = load_users()
#     if username not in users:
#         return False, "Utilisateur introuvable."
#     if users[username]!= has_password(password):
#         return False, "Mot de passe incorrect."
#     return True, "Connexion réussie."
    