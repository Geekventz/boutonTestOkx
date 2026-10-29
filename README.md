# OKX Singapore API Access Test

Application Python minimale permettant de vérifier si l'API OKX accepte les requêtes de trading **Futures Demo** (Simulateur) provenant d'un VPS Cloudzy situé à Singapour.

> **Question unique du projet :** OKX accepte-t-il une requête d'ordre Futures Demo provenant de l'adresse IP publique du VPS Cloudzy à Singapour ?

---

## 1. Caractéristiques & Architecture

- **Stack technique minimale :** Python 3, FastAPI, Uvicorn, HTTPX.
- **Zéro composant lourd :** Aucun conteneur Docker, aucune base de données PostgreSQL/Redis, aucun framework JavaScript complexe, aucun WebSocket ni Celery.
- **Sécurité stricte :** 
  - Utilise exclusivement l'environnement **OKX Demo Trading** avec l'en-tête `x-simulated-trading: 1`.
  - Signature `HMAC-SHA256` conforme à l'API OKX V5.
  - Les clés API et secrets ne sont **jamais** exposés au navigateur ni journalisés.
  - Double protection anti-clic et boîte de confirmation obligatoire avant tout ordre.

---

## 2. Structure du Projet

```
boutonTestOkx/
├── .env.example              # Modèle de configuration pour les clés Démo OKX
├── .gitignore                # Protection des secrets et fichiers temporaires
├── requirements.txt          # Dépendances minimales (FastAPI, Uvicorn, HTTPX, python-dotenv)
├── run.py                    # Script de démarrage de l'application
├── DEPLOY_CLOUDSY.md         # Guide de déploiement pas à pas sur Ubuntu Cloudzy
├── app/
│   ├── __init__.py
│   ├── config.py             # Chargement sécurisé des variables d'environnement
│   ├── okx_client.py         # Client API OKX V5 Démo (Signature HMAC-SHA256 & requêtes)
│   ├── main.py               # Serveur FastAPI (Points d'accès Étapes A, B et C)
│   ├── templates/
│   │   └── index.html        # Interface Web légère avec boutons ACHETER / VENDRE
│   └── static/
│       ├── style.css         # Thème sombre épuré et moderne
│       └── app.js            # Logique progressive et boîte de confirmation
```

---

## 3. Installation et Test Local

### 1. Cloner ou ouvrir le dossier
```bash
cd boutonTestOkx
```

### 2. Créer l'environnement virtuel et installer les dépendances
```bash
python -m venv venv
# Sous Windows :
venv\Scripts\activate
# Sous Linux / macOS :
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurer le fichier `.env`
Copiez le modèle `.env.example` en `.env` :
```bash
cp .env.example .env
```
Renseignez vos clés API **OKX Demo Trading** (Simulateur) :
```dotenv
OKX_API_KEY=votre_cle_api_demo
OKX_SECRET_KEY=votre_cle_secrete_demo
OKX_PASSPHRASE=votre_passphrase_demo
APP_HOST=127.0.0.1
APP_PORT=8000
```

### 4. Démarrer l'application
```bash
python run.py
```
Accédez à l'application dans votre navigateur :
👉 **http://127.0.0.1:8000**

---

## 4. Déroulement du Test Progressif

1. **Vérification IP & Clés** : Affiche l'adresse IP publique de la machine hôte et confirme la présence des clés Démo (masquées).
2. **Étape A — Connectivité Réseau** : Teste `/api/v5/public/time` sans authentification (mesure le code HTTP, la latence et les erreurs éventuelles de routage).
3. **Étape B — Authentification Démo** : Vérifie la signature privée en lecture seule (`/api/v5/account/config` et `balance`). Déverrouille l'étape C si acceptée.
4. **Étape C — Ordre Futures Démo** :
   - Deux boutons explicites : **ACHETER (LONG)** et **VENDRE (SHORT)** sur le contrat `BTC-USDT-SWAP`.
   - Paramètres de l'ordre : 1 contrat (taille minimale = 0.01 BTC), ordre `limit` avec prix contrôlé, mode marge `cross`.
   - Affichage d'une boîte de confirmation avec le récapitulatif avant l'envoi.
   - Désactivation immédiate des boutons pendant la requête (anti-double soumission).
   - Rapport complet : code HTTP, code OKX (`code`), sous-code (`sCode`), message OKX, identifiant d'ordre (`ordId`), statut moteur (`live`/`filled`).

---

## 5. Déploiement sur le VPS Cloudzy Singapour

Pour le déploiement sur Ubuntu et la sécurisation par tunnel SSH, consultez le guide dédié :
📄 [DEPLOY_CLOUDSY.md](file:///c:/Users/DELL/Desktop/boutonTestOkx/DEPLOY_CLOUDSY.md)
