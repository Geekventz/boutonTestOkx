#!/usr/bin/env python3
"""
Point d'entrée principal pour démarrer le serveur de test OKX Singapore.
Usage:
    python run.py
"""

import uvicorn
from app import config

if __name__ == "__main__":
    print("=" * 60)
    print("  OKX Singapore API Access Test — Démarrage du serveur")
    print(f"  Environnement  : OKX Demo Trading (Simulé)")
    print(f"  Hôte d'écoute  : http://{config.APP_HOST}:{config.APP_PORT}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=False
    )
