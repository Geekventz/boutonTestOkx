import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables du fichier .env s'il existe
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

OKX_BASE_URL = "https://www.okx.com"
OKX_API_KEY = os.getenv("OKX_API_KEY", "").strip()
OKX_SECRET_KEY = os.getenv("OKX_SECRET_KEY", "").strip()
OKX_PASSPHRASE = os.getenv("OKX_PASSPHRASE", "").strip()

APP_HOST = os.getenv("APP_HOST", "127.0.0.1").strip()
APP_PORT = int(os.getenv("APP_PORT", "8000").strip() or 8000)

def are_credentials_set() -> bool:
    """Vérifie si les clés sont renseignées et non factices."""
    placeholders = {"", "votre_cle_api_demo", "votre_cle_secrete_demo", "votre_passphrase_demo"}
    return (
        bool(OKX_API_KEY) and OKX_API_KEY not in placeholders and
        bool(OKX_SECRET_KEY) and OKX_SECRET_KEY not in placeholders and
        bool(OKX_PASSPHRASE) and OKX_PASSPHRASE not in placeholders
    )

def get_masked_credentials_info() -> dict:
    """Retourne l'état de configuration des identifiants sans jamais exposer les secrets."""
    is_set = are_credentials_set()
    if not is_set:
        return {
            "configured": False,
            "message": "Fichier .env non configuré ou clés démo manquantes."
        }
    
    # Masquage strict : seuls les 3 premiers et 2 derniers caractères de la clé publique
    masked_key = (
        f"{OKX_API_KEY[:3]}...{OKX_API_KEY[-2:]}" if len(OKX_API_KEY) > 6 else "***"
    )
    return {
        "configured": True,
        "api_key_masked": masked_key,
        "secret_set": bool(OKX_SECRET_KEY),
        "passphrase_set": bool(OKX_PASSPHRASE),
        "environment": "OKX Demo (x-simulated-trading: 1)"
    }
