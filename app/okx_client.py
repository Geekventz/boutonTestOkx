import time
import hmac
import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import httpx

from app import config

class OKXClient:
    """
    Client HTTP minimal et sécurisé pour l'API OKX V5 Demo Trading.
    Applique rigoureusement:
    - En-tête 'x-simulated-trading: 1'
    - Signature HMAC-SHA256 avec timestamp ISO 8601 UTC
    - Mesure précise de la latence
    - Zéro fuite de clés ou secrets
    """

    def __init__(self):
        self.base_url = config.OKX_BASE_URL
        self.timeout = 10.0  # 10 secondes max par requête

    def _generate_timestamp(self) -> str:
        """Génère le timestamp ISO 8601 UTC requis par OKX (ex: 2026-10-28T22:30:00.123Z)."""
        dt = datetime.now(timezone.utc)
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _sign(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Calcule la signature HMAC-SHA256 en Base64."""
        pre_hash = f"{timestamp}{method.upper()}{request_path}{body}"
        mac = hmac.new(
            config.OKX_SECRET_KEY.encode('utf-8'),
            pre_hash.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')

    def _get_auth_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """Prépare les en-têtes obligatoires pour les requêtes privées OKX Demo."""
        if not config.are_credentials_set():
            raise ValueError("Identifiants OKX Démo non configurés dans le fichier .env")

        ts = self._generate_timestamp()
        sign = self._sign(ts, method, request_path, body)

        return {
            "OK-ACCESS-KEY": config.OKX_API_KEY,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": config.OKX_PASSPHRASE,
            "x-simulated-trading": "1",  # STRICTEMENT Demo Trading
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OKX-Singapore-AccessTest/1.0"
        }

    async def get_server_public_ip(self) -> Dict[str, Any]:
        """Détecte l'adresse IP publique de la machine (utile pour certifier l'IP Cloudzy)."""
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("https://api.ipify.org?format=json")
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                if res.status_code == 200:
                    ip = res.json().get("ip", "Inconnue")
                    return {"success": True, "ip": ip, "duration_ms": duration_ms}
                return {"success": False, "error": f"HTTP {res.status_code}", "duration_ms": duration_ms}
        except Exception as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {"success": False, "error": str(e), "duration_ms": duration_ms}

    # =========================================================================
    # ÉTAPE A : Test de Connectivité Publique
    # =========================================================================
    async def check_connectivity(self) -> Dict[str, Any]:
        """
        Vérifie la joignabilité de l'API OKX via l'endpoint public /api/v5/public/time.
        Aucune clé requise.
        """
        path = "/api/v5/public/time"
        url = f"{self.base_url}{path}"
        start = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers={"User-Agent": "OKX-AccessTest/1.0"})
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                
                try:
                    data = response.json()
                except Exception:
                    data = {}

                okx_code = str(data.get("code", "N/A"))
                okx_msg = str(data.get("msg", ""))
                server_time_ms = None
                if data.get("data") and len(data["data"]) > 0:
                    server_time_ms = data["data"][0].get("ts")

                is_success = response.status_code == 200 and okx_code == "0"

                return {
                    "step": "Étape A — Connectivité Publique",
                    "endpoint": path,
                    "success": is_success,
                    "http_status": response.status_code,
                    "okx_code": okx_code,
                    "okx_msg": okx_msg or ("OK" if is_success else "Erreur API"),
                    "server_time_epoch_ms": server_time_ms,
                    "duration_ms": duration_ms,
                }
        except httpx.ConnectTimeout:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "step": "Étape A — Connectivité Publique",
                "endpoint": path,
                "success": False,
                "http_status": 0,
                "okx_code": "TIMEOUT",
                "okx_msg": "Délai de connexion dépassé (Timeout). Le VPS ne peut pas joindre www.okx.com",
                "duration_ms": duration_ms
            }
        except Exception as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "step": "Étape A — Connectivité Publique",
                "endpoint": path,
                "success": False,
                "http_status": 0,
                "okx_code": "NETWORK_ERROR",
                "okx_msg": f"Erreur de connexion : {str(e)}",
                "duration_ms": duration_ms
            }

    # =========================================================================
    # ÉTAPE B : Authentification Privée Démo (Lecture Seule)
    # =========================================================================
    async def check_demo_auth(self) -> Dict[str, Any]:
        """
        Vérifie l'authentification avec les clés Démo via:
        1. /api/v5/account/config (mode de position, niveau de compte)
        2. /api/v5/account/balance?ccy=USDT (solde disponible Démo)
        """
        if not config.are_credentials_set():
            return {
                "step": "Étape B — Authentification Démo",
                "success": False,
                "http_status": 400,
                "okx_code": "CONFIG_ERROR",
                "okx_msg": "Identifiants OKX Démo manquants dans le fichier .env",
                "duration_ms": 0
            }

        start = time.perf_counter()
        config_path = "/api/v5/account/config"
        balance_path = "/api/v5/account/balance?ccy=USDT"

        try:
            # 1. Vérifier config compte
            headers_cfg = self._get_auth_headers("GET", config_path)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res_cfg = await client.get(f"{self.base_url}{config_path}", headers=headers_cfg)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)

                data_cfg = res_cfg.json() if res_cfg.status_code == 200 else {}
                code_cfg = str(data_cfg.get("code", res_cfg.status_code))
                msg_cfg = str(data_cfg.get("msg", ""))

                if res_cfg.status_code != 200 or code_cfg != "0":
                    return {
                        "step": "Étape B — Authentification Démo",
                        "endpoint": config_path,
                        "success": False,
                        "http_status": res_cfg.status_code,
                        "okx_code": code_cfg,
                        "okx_msg": msg_cfg or "Échec de l'authentification OKX Démo",
                        "duration_ms": duration_ms,
                        "details": data_cfg
                    }

                # Config OK -> récupérer mode de position
                pos_mode = "net_mode"
                acct_lv = "N/A"
                if data_cfg.get("data") and len(data_cfg["data"]) > 0:
                    cfg_info = data_cfg["data"][0]
                    pos_mode = cfg_info.get("posMode", "long_short_mode")
                    acct_lv = cfg_info.get("acctLv", "N/A")

                # 2. Récupérer le solde USDT de démonstration
                headers_bal = self._get_auth_headers("GET", balance_path)
                res_bal = await client.get(f"{self.base_url}{balance_path}", headers=headers_bal)
                total_duration_ms = round((time.perf_counter() - start) * 1000, 2)
                
                demo_usdt_balance = "0.00"
                if res_bal.status_code == 200:
                    bal_json = res_bal.json()
                    if bal_json.get("code") == "0" and bal_json.get("data"):
                        details = bal_json["data"][0].get("details", [])
                        for d in details:
                            if d.get("ccy") == "USDT":
                                demo_usdt_balance = d.get("availBal", d.get("cashBal", "0.00"))
                                break

                return {
                    "step": "Étape B — Authentification Démo",
                    "endpoint": config_path,
                    "success": True,
                    "http_status": 200,
                    "okx_code": "0",
                    "okx_msg": "Authentification Démo validée avec succès",
                    "duration_ms": total_duration_ms,
                    "account_level": acct_lv,
                    "position_mode": pos_mode,
                    "demo_usdt_available": demo_usdt_balance,
                    "environment": "OKX Demo Trading"
                }

        except Exception as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "step": "Étape B — Authentification Démo",
                "endpoint": config_path,
                "success": False,
                "http_status": 0,
                "okx_code": "AUTH_EXCEPTION",
                "okx_msg": f"Exception lors de l'authentification : {str(e)}",
                "duration_ms": duration_ms
            }

    # =========================================================================
    # Récupération des informations sur l'instrument BTC-USDT-SWAP
    # =========================================================================
    async def get_instrument_and_ticker(self, inst_id: str = "BTC-USDT-SWAP") -> Dict[str, Any]:
        """
        Récupère les règles du contrat (taille min, lot size, tick size)
        et le ticker actuel (meilleur bid/ask/dernier prix) de manière concurrente.
        """
        import asyncio
        start = time.perf_counter()
        inst_path = f"/api/v5/public/instruments?instType=SWAP&instId={inst_id}"
        ticker_path = f"/api/v5/market/ticker?instId={inst_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res_inst, res_tick = await asyncio.gather(
                    client.get(f"{self.base_url}{inst_path}"),
                    client.get(f"{self.base_url}{ticker_path}"),
                    return_exceptions=True
                )
                duration_ms = round((time.perf_counter() - start) * 1000, 2)

                inst_data = {}
                if not isinstance(res_inst, Exception) and res_inst.status_code == 200:
                    inst_data = res_inst.json().get("data", [{}])[0]

                tick_data = {}
                if not isinstance(res_tick, Exception) and res_tick.status_code == 200:
                    tick_data = res_tick.json().get("data", [{}])[0]

                last_px = tick_data.get("last", "0.0")
                bid_px = tick_data.get("bidPx", last_px)
                ask_px = tick_data.get("askPx", last_px)

                return {
                    "success": True,
                    "inst_id": inst_id,
                    "ct_val": inst_data.get("ctVal", "0.01"),  # 1 contrat = 0.01 BTC
                    "ct_val_ccy": inst_data.get("ctValCcy", "BTC"),
                    "min_sz": inst_data.get("minSz", "1"),      # Min 1 contrat
                    "lot_sz": inst_data.get("lotSz", "1"),
                    "tick_sz": inst_data.get("tickSz", "0.1"),
                    "last_px": last_px,
                    "bid_px": bid_px,
                    "ask_px": ask_px,
                    "duration_ms": duration_ms
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # ÉTAPE C : Placement d'Ordre Futures Demo (BTC-USDT-SWAP)
    # =========================================================================
    async def place_futures_demo_order(
        self,
        action: str,  # "BUY_LONG" ou "SELL_SHORT"
        inst_id: str = "BTC-USDT-SWAP"
    ) -> Dict[str, Any]:
        """
        Envoie un ordre Futures Demo contrôlé sur BTC-USDT-SWAP:
        - action 'BUY_LONG' : side='buy', posSide='long'
        - action 'SELL_SHORT' : side='sell', posSide='short'
        - Type: 'limit'
        - Mode: 'cross'
        - Quantité: taille minimale (1 contrat = 0.01 BTC)
        - Prix limite fixé sur la base du carnet d'ordres pour garantir une requête d'ordre valide
        """
        if not config.are_credentials_set():
            return {
                "step": "Étape C — Ordre Futures Démo",
                "success": False,
                "http_status": 400,
                "okx_code": "CONFIG_ERROR",
                "okx_msg": "Clés Démo non configurées dans .env",
                "duration_ms": 0
            }

        # 1. Vérification du mode de position du compte
        auth_status = await self.check_demo_auth()
        if not auth_status.get("success"):
            return {
                "step": "Étape C — Ordre Futures Démo",
                "success": False,
                "http_status": auth_status.get("http_status", 400),
                "okx_code": auth_status.get("okx_code", "AUTH_REQUIRED"),
                "okx_msg": f"Échec préalable de l'authentification : {auth_status.get('okx_msg')}",
                "duration_ms": auth_status.get("duration_ms", 0)
            }

        pos_mode = auth_status.get("position_mode", "long_short_mode")

        # 2. Récupérer instrument & prix ticker actuel
        inst_info = await self.get_instrument_and_ticker(inst_id)
        if not inst_info.get("success"):
            return {
                "step": "Étape C — Ordre Futures Démo",
                "success": False,
                "http_status": 500,
                "okx_code": "MARKET_INFO_ERROR",
                "okx_msg": f"Impossible de récupérer le prix de {inst_id} : {inst_info.get('error')}",
                "duration_ms": 0
            }

        last_px = float(inst_info.get("last_px", 0.0) or 0.0)
        bid_px = float(inst_info.get("bid_px", 0.0) or last_px)
        ask_px = float(inst_info.get("ask_px", 0.0) or last_px)
        tick_sz = float(inst_info.get("tick_sz", "0.1") or 0.1)
        min_sz = inst_info.get("min_sz", "1")

        if last_px <= 0:
            return {
                "step": "Étape C — Ordre Futures Démo",
                "success": False,
                "http_status": 500,
                "okx_code": "INVALID_PRICE",
                "okx_msg": "Prix de marché indisponible pour calculer le prix limite.",
                "duration_ms": 0
            }

        # Configuration de l'ordre selon l'action
        # Pour BUY_LONG : side=buy, posSide=long. Prix limite = bid_px - 50 USDT (ordre limite sûr)
        # Pour SELL_SHORT : side=sell, posSide=short. Prix limite = ask_px + 50 USDT (ordre limite sûr)
        if action == "BUY_LONG":
            side = "buy"
            pos_side = "long" if pos_mode == "long_short_mode" else "net"
            # Prix limite légèrement sous le marché pour un test limite sûr et contrôlé
            target_px = round(bid_px * 0.995, 1)
        elif action == "SELL_SHORT":
            side = "sell"
            pos_side = "short" if pos_mode == "long_short_mode" else "net"
            # Prix limite légèrement au-dessus du marché
            target_px = round(ask_px * 1.005, 1)
        else:
            return {
                "step": "Étape C — Ordre Futures Démo",
                "success": False,
                "http_status": 400,
                "okx_code": "INVALID_ACTION",
                "okx_msg": f"Action non reconnue : {action}. Choisir BUY_LONG ou SELL_SHORT.",
                "duration_ms": 0
            }

        # Formatage du prix selon le tickSz
        px_str = f"{target_px:.1f}"

        # Construction du payload d'ordre OKX V5
        order_payload = {
            "instId": inst_id,
            "tdMode": "cross",        # Mode marge croisée en démo
            "side": side,             # buy ou sell
            "ordType": "limit",       # Ordre limite strict
            "sz": str(min_sz),        # Taille minimale (ex: 1 contrat)
            "px": px_str              # Prix limite contrôlé
        }

        # En mode long_short_mode, posSide est obligatoire
        if pos_mode == "long_short_mode":
            order_payload["posSide"] = pos_side

        import json
        body = json.dumps(order_payload, separators=(',', ':'))
        path = "/api/v5/trade/order"
        url = f"{self.base_url}{path}"

        start = time.perf_counter()
        try:
            headers = self._get_auth_headers("POST", path, body)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, content=body)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)

                res_json = response.json() if response.status_code == 200 else {}
                okx_code = str(res_json.get("code", response.status_code))
                okx_msg = str(res_json.get("msg", ""))

                data_items = res_json.get("data", [])
                order_item = data_items[0] if data_items else {}

                order_id = order_item.get("ordId")
                client_order_id = order_item.get("clOrdId")
                sub_code = str(order_item.get("sCode", ""))
                sub_msg = str(order_item.get("sMsg", ""))

                # Analyse rigoureuse du résultat :
                # - HTTP 200 + okx_code == '0' + sub_code == '0' => Accepté par le moteur de trading
                # - Si sub_code != '0' => Requête HTTP OK mais rejetée par le moteur OKX (ex: code 51000, 50114, IP non autorisée, etc.)
                is_accepted = (
                    response.status_code == 200 and
                    okx_code == "0" and
                    sub_code == "0" and
                    bool(order_id)
                )

                final_msg = okx_msg
                if sub_msg:
                    final_msg = f"{okx_msg} | Sous-message: {sub_msg}".strip(" |")

                order_result = {
                    "step": "Étape C — Ordre Futures Démo",
                    "action": action,
                    "order_params": {
                        "instId": inst_id,
                        "tdMode": "cross",
                        "side": side,
                        "posSide": pos_side,
                        "ordType": "limit",
                        "sz": str(min_sz),
                        "px": px_str,
                        "contract_value": f"{inst_info.get('ct_val')} {inst_info.get('ct_val_ccy')}"
                    },
                    "success": is_accepted,
                    "http_status": response.status_code,
                    "okx_code": okx_code,
                    "okx_sub_code": sub_code,
                    "okx_msg": final_msg or ("Ordre accepté par OKX Démo" if is_accepted else "Erreur de placement"),
                    "order_id": order_id,
                    "client_order_id": client_order_id,
                    "duration_ms": duration_ms,
                    "environment": "OKX Demo Trading"
                }

                # Si l'ordre a été accepté, interroger son état immédiat
                if is_accepted and order_id:
                    order_status_info = await self.get_order_status(inst_id, order_id)
                    order_result["order_status"] = order_status_info.get("state", "live")
                    order_result["order_status_details"] = order_status_info

                return order_result

        except Exception as e:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "step": "Étape C — Ordre Futures Démo",
                "action": action,
                "success": False,
                "http_status": 0,
                "okx_code": "ORDER_EXCEPTION",
                "okx_msg": f"Erreur lors de l'envoi de l'ordre : {str(e)}",
                "duration_ms": duration_ms
            }

    # =========================================================================
    # Vérification du statut d'un ordre
    # =========================================================================
    async def get_order_status(self, inst_id: str, order_id: str) -> Dict[str, Any]:
        """Interroge l'état de l'ordre: /api/v5/trade/order?instId=...&ordId=..."""
        path = f"/api/v5/trade/order?instId={inst_id}&ordId={order_id}"
        start = time.perf_counter()
        try:
            headers = self._get_auth_headers("GET", path)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}{path}", headers=headers)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                if res.status_code == 200:
                    data = res.json().get("data", [{}])[0]
                    return {
                        "success": True,
                        "state": data.get("state", "inconnu"),  # live, filled, canceled
                        "fill_sz": data.get("fillSz", "0"),
                        "avg_px": data.get("avgPx", "0"),
                        "acc_fill_sz": data.get("accFillSz", "0"),
                        "duration_ms": duration_ms
                    }
                return {"success": False, "http_status": res.status_code, "duration_ms": duration_ms}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Annulation d'un ordre de test (optionnel pour nettoyage propre)
    # =========================================================================
    async def cancel_order(self, inst_id: str, order_id: str) -> Dict[str, Any]:
        """Permet d'annuler l'ordre de test limite après vérification."""
        import json
        path = "/api/v5/trade/cancel-order"
        body = json.dumps({"instId": inst_id, "ordId": order_id}, separators=(',', ':'))
        try:
            headers = self._get_auth_headers("POST", path, body)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}{path}", headers=headers, content=body)
                return res.json() if res.status_code == 200 else {"success": False}
        except Exception as e:
            return {"success": False, "error": str(e)}
