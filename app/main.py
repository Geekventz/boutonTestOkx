import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.okx_client import OKXClient

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="OKX Singapore API Access Test",
    description="Application minimale pour vérifier l'accès API OKX Futures Démo depuis un VPS Cloudzy Singapour",
    version="1.0.0"
)

# Montage des fichiers statiques et templates
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

okx_client = OKXClient()

# Verrou mémoire pour éviter les soumissions simultanées
order_lock = asyncio.Lock()

class OrderRequest(BaseModel):
    action: str = Field(..., description="BUY_LONG ou SELL_SHORT")
    confirmed: bool = Field(..., description="Confirmation explicite de l'utilisateur")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = templates_dir / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Interface en cours de chargement...</h1>", status_code=200)
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)

@app.get("/api/config-status")
async def get_config_status():
    """Retourne l'état des clés sans divulguer de secret."""
    return config.get_masked_credentials_info()

@app.get("/api/server-ip")
async def get_server_ip():
    """Détecte l'adresse IP publique du serveur (VPS Cloudzy)."""
    return await okx_client.get_server_public_ip()

@app.get("/api/step-a/connectivity")
async def run_step_a():
    """Étape A : Vérification de la connectivité réseau vers l'API OKX."""
    return await okx_client.check_connectivity()

@app.get("/api/step-b/auth")
async def run_step_b():
    """Étape B : Authentification Démo en lecture seule."""
    return await okx_client.check_demo_auth()

@app.get("/api/market/preview")
async def get_market_preview():
    """Récupère les informations de marché pour prévisualiser l'ordre exact."""
    return await okx_client.get_instrument_and_ticker("BTC-USDT-SWAP")

@app.post("/api/step-c/order")
async def run_step_c(req: OrderRequest):
    """
    Étape C : Envoi manuel d'un ordre Futures Démo (ACHETER LONG ou VENDRE SHORT).
    - Protégé contre les double-soumissions via asyncio.Lock.
    - Exige la confirmation explicite de l'utilisateur.
    """
    if not req.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirmation requise : vous devez confirmer explicitement l'ordre avant l'envoi."
        )

    if req.action not in ("BUY_LONG", "SELL_SHORT"):
        raise HTTPException(
            status_code=400,
            detail=f"Action inconnue '{req.action}'. Seuls 'BUY_LONG' et 'SELL_SHORT' sont autorisés."
        )

    # Protection anti-concurrence / anti-double clic
    if order_lock.locked():
        raise HTTPException(
            status_code=429,
            detail="Une requête d'ordre est déjà en cours de traitement. Veuillez patienter."
        )

    async with order_lock:
        result = await okx_client.place_futures_demo_order(
            action=req.action,
            inst_id="BTC-USDT-SWAP"
        )
        return result

@app.get("/api/order/status")
async def get_order_status(ordId: str, instId: str = "BTC-USDT-SWAP"):
    """Vérifie le statut d'un ordre placé."""
    if not ordId:
        raise HTTPException(status_code=400, detail="ordId manquant.")
    return await okx_client.get_order_status(instId, ordId)

@app.post("/api/order/cancel")
async def cancel_order(ordId: str, instId: str = "BTC-USDT-SWAP"):
    """Annule un ordre de test."""
    if not ordId:
        raise HTTPException(status_code=400, detail="ordId manquant.")
    return await okx_client.cancel_order(instId, ordId)
