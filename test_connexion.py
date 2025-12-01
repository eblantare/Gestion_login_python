import os

def check_files():
    print("🔍 Vérification des fichiers...")
    
    files_to_check = [
        'static/css/bootstrap.min.css',
        'static/css/dataTables.bootstrap5.min.css',
        'static/js/e_dashboard.js',
        'static/vendor/bootstrap-icons/bootstrap-icons.css',
        'static/vendor/fontawesome/css/all.min.css'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MANQUANT")

if __name__ == "__main__":
    check_files()