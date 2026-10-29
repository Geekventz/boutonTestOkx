# Guide de Déploiement Minimal sur Ubuntu (VPS Cloudzy Singapour)

Ce guide décrit pas à pas comment déployer et exécuter le projet **OKX Singapore API Access Test** sur un VPS Cloudzy sous Ubuntu.

---

## 1. Prérequis sur le VPS Ubuntu

Connectez-vous à votre VPS Cloudzy en SSH :

```bash
ssh root@<IP_DU_VPS_SINGAPOUR>
# ou avec l'utilisateur configuré, ex: ubuntu@<IP_DU_VPS_SINGAPOUR>
```

Mettez à jour les paquets et assurez-vous que Python 3, `pip` et `venv` sont installés :

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
```

---

## 2. Copie du Projet sur le VPS

Vous pouvez cloner votre dépôt ou copier les fichiers via `scp` ou `rsync` depuis votre machine locale :

```bash
# Exemple depuis votre machine locale :
scp -r c:\Users\DELL\Desktop\boutonTestOkx ubuntu@<IP_DU_VPS_SINGAPOUR>:~/boutonTestOkx
```

Ou sur le VPS :
```bash
cd ~
mkdir -p boutonTestOkx
cd boutonTestOkx
```

---

## 3. Création de l'Environnement Virtuel & Installation

Sur le VPS, dans le dossier du projet :

```bash
# 1. Créer le venv isolé
python3 -m venv venv

# 2. Activer l'environnement
source venv/bin/activate

# 3. Mettre à jour pip et installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configuration Sécurisée du fichier `.env`

Créez le fichier `.env` à partir de l'exemple :

```bash
cp .env.example .env
nano .env
```

Renseignez **strictement** vos clés **OKX Démo** (Simulateur) :

```dotenv
OKX_API_KEY=votre_cle_api_demo
OKX_SECRET_KEY=votre_cle_secrete_demo
OKX_PASSPHRASE=votre_passphrase_demo

APP_HOST=127.0.0.1
APP_PORT=8000
```

> [!IMPORTANT]
> - Ne mettez **JAMAIS** de clés de production / réelles.
> - Laissez `APP_HOST=127.0.0.1` pour que l'application n'écoute qu'en local sur le VPS et ne soit pas exposée publiquement sur Internet sans authentification.

Verrouillez les permissions du fichier `.env` :

```bash
chmod 600 .env
```

---

## 5. Démarrage de l'Application

Activez le venv et lancez le serveur :

```bash
source venv/bin/activate
python3 run.py
```

Le serveur démarrera sur `http://127.0.0.1:8000`.

---

## 6. Accès Sécurisé via Tunnel SSH (Depuis votre PC)

Comme l'interface Web ne doit pas être exposée publiquement sur Internet, ouvrez un terminal sur votre ordinateur local et créez un tunnel SSH :

```bash
ssh -N -L 8000:127.0.0.1:8000 ubuntu@<IP_DU_VPS_SINGAPOUR>
```

Une fois le tunnel établi, ouvrez votre navigateur habituel à l'adresse :

👉 **`http://localhost:8000`**

Vous aurez alors accès directement à l'interface de test qui tourne sur le VPS Cloudzy à Singapour.

---

## 7. Déroulement du Test & Critère de Réussite

Suivez la progression sur l'interface :

1. **Vérification IP Publique** : L'IP détectée en haut à gauche doit correspondre à celle de votre VPS Cloudzy à Singapour.
2. **Étape A — Connectivité Réseau** : Cliquez sur `1. Tester la Connectivité Réseau`.
   - Si OK : Le réseau Cloudzy Singapour joint bien l'API OKX (HTTP 200, code OKX "0").
3. **Étape B — Authentification Démo** : Cliquez sur `2. Valider l'Authentification Démo`.
   - Si OK : La signature HMAC-SHA256 est acceptée par OKX pour l'environnement simulé. Le solde de démo s'affiche.
4. **Étape C — Ordre Futures Démo** :
   - Cliquez sur **`ACHETER (LONG)`** ou **`VENDRE (SHORT)`**.
   - Vérifiez les paramètres dans la boîte de dialogue de confirmation (Taille : 1 contrat, type Limite, contrat BTC-USDT-SWAP).
   - Confirmez l'envoi.
5. **Résultat attendu** :
   - **Code HTTP** : `200`
   - **Code OKX** : `0`
   - **Identifiant d'ordre (ordId)** : Présent (ex: `312269865356374016`)
   - **Statut Moteur** : `live` ou `filled`
   - **Sous-code** : `0`

---

## 8. Conclusion et Portée du Test

> [!NOTE]
> Ce test répond exclusivement à la question : **OKX accepte-t-il une requête d'ordre Futures Demo provenant de l'adresse IP publique du VPS Cloudzy à Singapour ?**
> La réussite de ce test valide l'accès à l'environnement Démo depuis l'IP du VPS, mais ne constitue pas à lui seul une garantie d'accès à l'environnement Live (en raison des éventuelles restrictions géographiques ou vérifications KYC spécifiques aux comptes de production).
