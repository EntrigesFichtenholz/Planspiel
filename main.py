"""
BWL Planspiel - FastAPI Backend
Mit Debug-Modus und WebSocket für Live-Updates
"""
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import asyncio
from models import GameSession, BusinessFirm

# DEBUG MODE - deaktivierbar via Umgebungsvariable
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

app = FastAPI(
    title="BWL Planspiel API",
    description="Backend für BWL Business Simulation Game",
    version="1.0.0",
    debug=DEBUG_MODE
)

# CORS für Dash Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game Session (In-Memory für MVP, später SQLite)
game = GameSession()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# Pydantic Models für API
class FirmCreate(BaseModel):
    firm_name: str
    user_name: str


class DecisionInput(BaseModel):
    product_price: float
    production_capacity: float
    marketing_budget: float
    rd_budget: float
    quality_level: int
    jit_safety_stock: float  # in %


class JoinFirmInput(BaseModel):
    user_name: str


# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "message": "BWL Planspiel API",
        "version": "1.0.0",
        "debug_mode": DEBUG_MODE,
        "endpoints": {
            "health": "/health",
            "create_firm": "POST /api/firms",
            "get_firm": "GET /api/firms/{firm_id}",
            "submit_decision": "POST /api/firms/{firm_id}/decision",
            "market_overview": "GET /api/market",
            "quarter_status": "GET /api/quarter",
            "websocket": "WS /ws"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "debug_mode": DEBUG_MODE,
        "active_firms": len(game.firms),
        "current_quarter": game.current_quarter
    }


@app.post("/api/firms")
async def create_firm(firm_data: FirmCreate):
    """Erstellt eine neue Firma"""
    # Check if user already has a firm
    existing = game.get_firm_by_user(firm_data.user_name)
    if existing:
        raise HTTPException(status_code=400, detail="User bereits registriert")

    firm = game.create_firm(firm_data.firm_name, firm_data.user_name)

    # Broadcast update
    await manager.broadcast({
        "type": "firm_created",
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "firm_id": firm.id,
        "message": f"Firma '{firm.name}' erfolgreich erstellt"
    }


@app.get("/api/firms/{firm_id}")
async def get_firm(firm_id: int):
    """Holt Firmendaten"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    return firm.to_dict()


@app.get("/api/firms/user/{user_name}")
async def get_firm_by_user(user_name: str):
    """Holt Firma eines Users"""
    firm = game.get_firm_by_user(user_name)
    if not firm:
        raise HTTPException(status_code=404, detail="Keine Firma für diesen User")

    return firm.to_dict()


@app.get("/api/firms")
async def list_all_firms():
    """Liste aller Firmen (außer Bot-Firmen)"""
    firms = []
    for firm in game.firms.values():
        # Filter Bot-Firmen aus (erkennbar an Namen wie "Bot1", "AI_Trader", etc.)
        if not any(bot_name in firm.name.lower() for bot_name in ["bot", "ai_", "ki_"]):
            firms.append({
                "id": firm.id,
                "name": firm.name,
                "user_count": len(firm.user_names),
                "market_share": round(firm.market_share * 100, 2),
                "cash": round(firm.cash, 0)
            })
    return {"firms": firms}


@app.post("/api/firms/{firm_id}/join")
async def join_firm(firm_id: int, data: JoinFirmInput):
    """User tritt bestehender Firma bei"""
    # Check if user already has a firm
    existing = game.get_firm_by_user(data.user_name)
    if existing:
        raise HTTPException(status_code=400, detail="User ist bereits in einer Firma")

    # Add user to firm
    success = game.add_user_to_firm(firm_id, data.user_name)
    if not success:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    firm = game.get_firm_by_id(firm_id)

    # Broadcast update
    await manager.broadcast({
        "type": "user_joined_firm",
        "firm_id": firm_id,
        "user_name": data.user_name,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "firm_id": firm.id,
        "message": f"Erfolgreich Firma '{firm.name}' beigetreten"
    }


@app.post("/api/firms/{firm_id}/decision")
async def submit_decision(firm_id: int, decision: DecisionInput):
    """Submitted Quartalsentscheidung"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    # Apply decisions
    firm.apply_decisions(
        price=decision.product_price,
        capacity=decision.production_capacity,
        marketing=decision.marketing_budget,
        rd=decision.rd_budget,
        quality=decision.quality_level,
        jit_safety=decision.jit_safety_stock
    )

    # Broadcast update
    await manager.broadcast({
        "type": "decision_submitted",
        "firm_id": firm_id,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": "Entscheidungen gespeichert",
        "firm": firm.to_dict()
    }


@app.get("/api/market")
async def get_market_overview():
    """Marktübersicht mit allen Firmen"""
    return {
        "quarter": game.current_quarter,
        "firms": game.get_market_overview()
    }


@app.get("/api/quarter")
async def get_quarter_status():
    """Aktueller Quartalsstatus"""
    return {
        "current_quarter": game.current_quarter,
        "time_remaining": game.get_time_until_next_quarter(),
        "quarter_duration": game.quarter_duration,
        "is_active": game.is_active
    }


@app.post("/api/quarter/advance")
async def advance_quarter():
    """Führt Quartalsabschluss durch (Manual Trigger für Testing)"""
    if not DEBUG_MODE:
        raise HTTPException(status_code=403, detail="Nur im Debug-Modus verfügbar")

    results = game.advance_quarter()

    # Broadcast quarter results
    await manager.broadcast({
        "type": "quarter_completed",
        "quarter": game.current_quarter,
        "results": results,
        "market": game.get_market_overview()
    })

    return {
        "success": True,
        "quarter": game.current_quarter,
        "results": results
    }


@app.post("/api/game/start")
async def start_game():
    """Startet das Spiel"""
    game.is_active = True
    game.quarter_start_time = asyncio.get_event_loop().time()

    await manager.broadcast({
        "type": "game_started",
        "quarter": game.current_quarter
    })

    return {"success": True, "message": "Spiel gestartet"}


@app.post("/api/game/reset")
async def reset_game():
    """Reset game (nur Debug-Modus)"""
    if not DEBUG_MODE:
        raise HTTPException(status_code=403, detail="Nur im Debug-Modus verfügbar")

    game.firms.clear()
    game.current_quarter = 0
    game.is_active = False
    game.next_firm_id = 1

    await manager.broadcast({"type": "game_reset"})

    return {"success": True, "message": "Spiel zurückgesetzt"}


# ============ WEBSOCKET ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket für Live-Updates"""
    await manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "connected",
            "quarter": game.current_quarter,
            "firms_count": len(game.firms)
        })

        while True:
            # Keep connection alive & check for quarter advance
            await asyncio.sleep(1)

            if game.is_active and game.should_advance_quarter():
                results = game.advance_quarter()
                await manager.broadcast({
                    "type": "quarter_completed",
                    "quarter": game.current_quarter,
                    "results": results,
                    "market": game.get_market_overview()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============ DEBUG ENDPOINTS ============

if DEBUG_MODE:
    @app.get("/debug/firms")
    async def debug_list_firms():
        """Debug: Liste aller Firmen"""
        return {
            "firms": [firm.to_dict() for firm in game.firms.values()]
        }

    @app.post("/debug/populate")
    async def debug_populate():
        """Debug: Erstellt Test-Firmen"""
        test_firms = [
            ("TechCorp", "alice"),
            ("InnovateGmbH", "bob"),
            ("MarketLeader AG", "charlie")
        ]

        for firm_name, user_name in test_firms:
            if not game.get_firm_by_user(user_name):
                game.create_firm(firm_name, user_name)

        return {
            "success": True,
            "firms": [f.to_dict() for f in game.firms.values()]
        }


# Background task for automatic quarter advance
@app.on_event("startup")
async def startup_event():
    """Startup: Hintergrund-Task für Auto-Quarter-Advance + Bots erstellen"""
    # Verkürzte Quartalsdauer für schnellere Tests (60s statt 120s)
    game.quarter_duration = 60

    # Erstelle Bot-Firmen beim Startup
    game.create_bot_firms()
    game.is_active = True

    print(f"[OK] {len(game.firms)} Bot-Firmen erstellt")
    print(f"[OK] Quartalsdauer: {game.quarter_duration}s")

    async def quarter_timer():
        while True:
            await asyncio.sleep(1)
            if game.is_active and game.should_advance_quarter():
                results = game.advance_quarter()
                await manager.broadcast({
                    "type": "quarter_completed",
                    "quarter": game.current_quarter,
                    "results": results,
                    "market": game.get_market_overview()
                })

    asyncio.create_task(quarter_timer())


if __name__ == "__main__":
    print(f"""
    ================================================
       BWL Planspiel Server
       Debug Mode: {DEBUG_MODE}
    ================================================

    API: http://localhost:8000
    Docs: http://localhost:8000/docs
    Health: http://localhost:8000/health
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,  # Standard port for production
        reload=DEBUG_MODE,  # Enable reload in debug mode
        log_level="debug" if DEBUG_MODE else "info"
    )
