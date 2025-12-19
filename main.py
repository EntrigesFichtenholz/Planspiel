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
from fastapi.middleware.wsgi import WSGIMiddleware
from dashboard import app as dash_app
from models import GameSession, BusinessFirm, FirmCreate, DecisionInput, JoinFirmInput
from state import game

# DEBUG Mode (from environment)
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# FastAPI App
app = FastAPI(
    title="BWL Planspiel API",
    description="Backend API fuer das BWL Planspiel mit integriertem Dashboard",
    version="2.0"
)

# CORS Middleware (fuer Entwicklung)
if DEBUG_MODE:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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


# Game Session (Shared State)
from state import game

# ============ API ENDPOINTS ============

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
    """Liste aller Firmen (inkl. Bot-Firmen)"""
    firms = []
    for firm in game.firms.values():
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


@app.post("/api/firms/{firm_id}/acquire/{target_firm_id}")
async def acquire_firm(firm_id: int, target_firm_id: int):
    """Firma kauft andere Firma auf (M&A)"""
    try:
        # Berechne zuerst den Preis (für Frontend-Anzeige)
        target_firm = game.get_firm_by_id(target_firm_id)
        if not target_firm:
            raise HTTPException(status_code=404, detail="Ziel-Firma nicht gefunden")

        acquisition_cost = game.calculate_acquisition_cost(target_firm)

        # Führe Aufkauf durch
        acquisition_info = game.acquire_firm(firm_id, target_firm_id)

        # Broadcast M&A event
        await manager.broadcast({
            "type": "firm_acquired",
            "acquiring_firm_id": firm_id,
            "target_firm_id": target_firm_id,
            "acquisition_info": acquisition_info,
            "market": game.get_market_overview()
        })

        return {
            "success": True,
            "acquisition_info": acquisition_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aufkauf fehlgeschlagen: {str(e)}")


@app.get("/api/firms/{firm_id}/acquisition-cost/{target_firm_id}")
async def get_acquisition_cost(firm_id: int, target_firm_id: int):
    """Berechnet Aufkaufpreis für Ziel-Firma (Preview)"""
    try:
        target_firm = game.get_firm_by_id(target_firm_id)
        if not target_firm:
            raise HTTPException(status_code=404, detail="Ziel-Firma nicht gefunden")

        acquiring_firm = game.get_firm_by_id(firm_id)
        if not acquiring_firm:
            raise HTTPException(status_code=404, detail="Aufkaufende Firma nicht gefunden")

        acquisition_cost = game.calculate_acquisition_cost(target_firm)
        can_afford = acquiring_firm.cash >= acquisition_cost

        return {
            "target_firm_id": target_firm_id,
            "target_firm_name": target_firm.name,
            "acquisition_cost": round(acquisition_cost, 2),
            "your_cash": round(acquiring_firm.cash, 2),
            "can_afford": can_afford,
            "target_inventory": round(target_firm.inventory, 0),
            "target_capacity": round(target_firm.production_capacity, 0),
            "target_revenue": round(target_firm.revenue, 2),
            "target_market_share": round(target_firm.market_share * 100, 2)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/firms/{firm_id}/decision")
async def submit_decision(firm_id: int, decision: DecisionInput):
    """Submitted Quartalsentscheidung"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    # Apply decisions (ERWEITERT mit neuen Parametern)
    firm.apply_decisions(
        price=decision.product_price,
        capacity=decision.production_capacity,
        marketing=decision.marketing_budget,
        rd=decision.rd_budget,
        quality=decision.quality_level,
        jit_safety=decision.jit_safety_stock,
        process_opt=decision.process_optimization,
        supplier_neg=decision.supplier_negotiation,
        overhead_red=decision.overhead_reduction,
        buildings_depr=decision.buildings_depreciation,
        machines_depr=decision.machines_depreciation,
        equipment_depr=decision.equipment_depreciation
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


# ============ M&A ENDPOINTS ============

class AcquisitionInput(BaseModel):
    acquirer_firm_id: int
    target_firm_id: int
    percentage: float  # Prozent der Anteile

@app.post("/api/acquisitions")
async def acquire_firm(acquisition: AcquisitionInput):
    """Führt Unternehmensübernahme durch"""
    acquirer = game.get_firm_by_id(acquisition.acquirer_firm_id)
    target = game.get_firm_by_id(acquisition.target_firm_id)

    if not acquirer:
        raise HTTPException(status_code=404, detail="Käufer-Firma nicht gefunden")
    if not target:
        raise HTTPException(status_code=404, detail="Ziel-Firma nicht gefunden")

    # Übernahme durchführen
    success, message = target.acquire_shares(acquirer, acquisition.percentage, game)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Broadcast update
    await manager.broadcast({
        "type": "acquisition_completed",
        "acquirer": acquirer.to_dict(),
        "target": target.to_dict(),
        "message": message
    })

    return {
        "success": True,
        "message": message,
        "acquirer": acquirer.to_dict(),
        "target": target.to_dict()
    }

@app.get("/api/firms/{firm_id}/valuation")
async def get_firm_valuation(firm_id: int):
    """Holt Firmenbewertung für M&A"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    enterprise_value = firm.calculate_enterprise_value()

    return {
        "firm_id": firm_id,
        "firm_name": firm.name,
        "enterprise_value": enterprise_value,
        "acquisition_price_10": firm.calculate_acquisition_price(10),
        "acquisition_price_25": firm.calculate_acquisition_price(25),
        "acquisition_price_51": firm.calculate_acquisition_price(51),
        "acquisition_price_100": firm.calculate_acquisition_price(100),
        "shares": firm.shares,
        "is_public": firm.is_public,
        "market_share": firm.market_share * 100
    }

@app.get("/api/antitrust/check")
async def check_antitrust(acquirer_id: int, target_id: int, percentage: float):
    """Prüft Kartellrecht"""
    acquirer = game.get_firm_by_id(acquirer_id)
    target = game.get_firm_by_id(target_id)

    if not acquirer or not target:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    allowed, reason = target.can_be_acquired(acquirer, percentage, game)

    return {
        "allowed": allowed,
        "reason": reason,
        "combined_market_share": (acquirer.market_share + target.market_share * percentage/100.0) * 100
    }


# ============ NEUE SYSTEME - API ENDPOINTS ============

# MASCHINENSYSTEM
class MachineUpgradeInput(BaseModel):
    target_class: str  # "professional" or "premium"

@app.post("/api/firms/{firm_id}/machines/upgrade")
async def upgrade_machines(firm_id: int, upgrade: MachineUpgradeInput):
    """Upgraded Maschinenklasse"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    success, message = firm.upgrade_machines(upgrade.target_class)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await manager.broadcast({
        "type": "machines_upgraded",
        "firm_id": firm_id,
        "new_class": upgrade.target_class,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": message,
        "firm": firm.to_dict()
    }

@app.get("/api/firms/{firm_id}/machines")
async def get_machine_info(firm_id: int):
    """Holt Maschinen-Informationen"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    upgrade_options = {
        "basic": {
            "current": "Basic Machines",
            "next": "Professional Machines",
            "cost": 3_000_000,
            "efficiency_gain": "0.8 → 1.0 (25% boost)",
            "energy_savings": "20% weniger Energiekosten"
        },
        "professional": {
            "current": "Professional Machines",
            "next": "Premium Machines",
            "cost": 6_000_000,
            "efficiency_gain": "1.0 → 1.3 (30% boost)",
            "energy_savings": "30% weniger Energiekosten"
        },
        "premium": {
            "current": "Premium Machines",
            "next": "None (Maximum erreicht)",
            "cost": 0,
            "efficiency_gain": "Already at maximum",
            "energy_savings": "Already at maximum"
        }
    }

    return {
        "current_class": firm.machine_class,
        "efficiency_factor": firm.machines_efficiency_factor,
        "energy_cost_factor": firm.machine_energy_cost_factor,
        "upgrade_info": upgrade_options.get(firm.machine_class, {})
    }

# FINANZIERUNGSSYSTEM - KREDITE
class LoanInput(BaseModel):
    amount: float
    quarters: int = 12  # Standard: 3 Jahre

@app.post("/api/firms/{firm_id}/financing/loan")
async def take_loan(firm_id: int, loan_input: LoanInput):
    """Nimmt Kredit auf"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    success, message = firm.take_loan(loan_input.amount, loan_input.quarters)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    firm.update_credit_rating()

    await manager.broadcast({
        "type": "loan_taken",
        "firm_id": firm_id,
        "amount": loan_input.amount,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": message,
        "firm": firm.to_dict()
    }

@app.get("/api/firms/{firm_id}/financing/loans")
async def get_loans(firm_id: int):
    """Holt Kredit-Informationen"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    return {
        "loans": firm.loans,
        "total_debt": firm.debt,
        "max_loan_capacity": firm.max_loan_capacity,
        "available_credit": firm.max_loan_capacity - firm.debt,
        "credit_rating": firm.credit_rating,
        "estimated_interest_rate": (0.10 / firm.credit_rating) * 100  # in %
    }

# EIGENKAPITALERHÖHUNG
class SharesInput(BaseModel):
    amount: float

@app.post("/api/firms/{firm_id}/financing/issue-shares")
async def issue_shares(firm_id: int, shares_input: SharesInput):
    """Gibt neue Aktien aus (IPO oder Capital Raise)"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    success, message = firm.issue_shares(shares_input.amount)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await manager.broadcast({
        "type": "shares_issued",
        "firm_id": firm_id,
        "amount": shares_input.amount,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": message,
        "firm": firm.to_dict()
    }

@app.post("/api/firms/{firm_id}/financing/buyback-shares")
async def buyback_shares_to_go_private(firm_id: int):
    """Kauft alle öffentlichen Anteile zurück und geht von der Börse (Delisting)"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    success, message = firm.buyback_shares_to_go_private()

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await manager.broadcast({
        "type": "shares_bought_back",
        "firm_id": firm_id,
        "message": message,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": message,
        "firm": firm.to_dict(),
        "is_now_private": not firm.is_public
    }

# PERSONALMANAGEMENT
class PersonnelInput(BaseModel):
    qualification: str  # "ungelernt", "angelernt", "facharbeiter"
    count: int

@app.post("/api/firms/{firm_id}/personnel/hire")
async def hire_personnel(firm_id: int, personnel_input: PersonnelInput):
    """Stellt Personal ein"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    success, message = firm.hire_personnel(personnel_input.qualification, personnel_input.count)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await manager.broadcast({
        "type": "personnel_hired",
        "firm_id": firm_id,
        "qualification": personnel_input.qualification,
        "count": personnel_input.count,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": message,
        "firm": firm.to_dict()
    }

@app.post("/api/firms/{firm_id}/personnel/fire")
async def fire_personnel(firm_id: int, personnel_input: PersonnelInput):
    """Entlässt Personal"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    success, message = firm.fire_personnel(personnel_input.qualification, personnel_input.count)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    await manager.broadcast({
        "type": "personnel_fired",
        "firm_id": firm_id,
        "qualification": personnel_input.qualification,
        "count": personnel_input.count,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": message,
        "firm": firm.to_dict()
    }

@app.get("/api/firms/{firm_id}/personnel")
async def get_personnel_info(firm_id: int):
    """Holt Personal-Informationen"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    total_personnel = firm.personnel_ungelernt + firm.personnel_angelernt + firm.personnel_facharbeiter

    return {
        "personnel": {
            "ungelernt": {
                "count": firm.personnel_ungelernt,
                "cost_per_quarter": firm.cost_ungelernt,
                "productivity": firm.productivity_ungelernt,
                "total_cost": firm.personnel_ungelernt * firm.cost_ungelernt
            },
            "angelernt": {
                "count": firm.personnel_angelernt,
                "cost_per_quarter": firm.cost_angelernt,
                "productivity": firm.productivity_angelernt,
                "total_cost": firm.personnel_angelernt * firm.cost_angelernt
            },
            "facharbeiter": {
                "count": firm.personnel_facharbeiter,
                "cost_per_quarter": firm.cost_facharbeiter,
                "productivity": firm.productivity_facharbeiter,
                "total_cost": firm.personnel_facharbeiter * firm.cost_facharbeiter
            },
            "total": total_personnel,
            "average_productivity": (
                (firm.personnel_ungelernt * firm.productivity_ungelernt +
                 firm.personnel_angelernt * firm.productivity_angelernt +
                 firm.personnel_facharbeiter * firm.productivity_facharbeiter) / total_personnel
            ) if total_personnel > 0 else 0
        }
    }

# INNOVATION / PRODUKTLEBENSZYKLUS
class InnovationInput(BaseModel):
    amount: float

@app.post("/api/firms/{firm_id}/innovation/invest")
async def invest_in_innovation(firm_id: int, innovation_input: InnovationInput):
    """Investiert in Produktinnovation"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    if firm.cash < innovation_input.amount:
        raise HTTPException(status_code=400, detail=f"Nicht genug Cash. Verfügbar: €{firm.cash:,.0f}")

    firm.cash -= innovation_input.amount
    firm.innovation_investment += innovation_input.amount

    await manager.broadcast({
        "type": "innovation_invested",
        "firm_id": firm_id,
        "amount": innovation_input.amount,
        "firm": firm.to_dict()
    })

    return {
        "success": True,
        "message": f"€{innovation_input.amount:,.0f} in Innovation investiert",
        "total_innovation_investment": firm.innovation_investment,
        "innovation_threshold": 5_000_000,
        "firm": firm.to_dict()
    }

@app.get("/api/firms/{firm_id}/product-lifecycle")
async def get_product_lifecycle(firm_id: int):
    """Holt Produktlebenszyklus-Informationen"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    lifecycle_info = {
        "introduction": {
            "stage": "Einführung",
            "demand_factor": 0.7,
            "description": "Produkt wird am Markt eingeführt. Geringe Nachfrage.",
            "quarters_range": "0-4"
        },
        "growth": {
            "stage": "Wachstum",
            "demand_factor": 1.3,
            "description": "Produkt wächst stark. Hohe Nachfrage!",
            "quarters_range": "5-12"
        },
        "maturity": {
            "stage": "Reife",
            "demand_factor": 1.0,
            "description": "Stabile Marktphase. Normale Nachfrage.",
            "quarters_range": "13-24"
        },
        "decline": {
            "stage": "Rückgang",
            "demand_factor": 0.6,
            "description": "Produkt veraltet. Niedrige Nachfrage. Innovation nötig!",
            "quarters_range": "25+"
        }
    }

    return {
        "current_stage": firm.product_lifecycle_stage,
        "age_quarters": firm.product_age_quarters,
        "innovation_level": firm.product_innovation_level,
        "innovation_investment": firm.innovation_investment,
        "innovation_threshold": 5_000_000,
        "lifecycle_stages": lifecycle_info,
        "recommendation": "Innovation investieren!" if firm.product_lifecycle_stage == "decline" else "Produkt läuft gut"
    }

# BILANZ & GuV
@app.get("/api/firms/{firm_id}/balance-sheet")
async def get_balance_sheet(firm_id: int):
    """Holt Bilanz"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    return firm.generate_balance_sheet()

@app.get("/api/firms/{firm_id}/income-statement")
async def get_income_statement(firm_id: int):
    """Holt Gewinn- und Verlustrechnung (GuV)"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    return firm.generate_income_statement()

# LIQUIDITÄTSKENNZAHLEN
@app.get("/api/firms/{firm_id}/liquidity")
async def get_liquidity_ratios(firm_id: int):
    """Holt Liquiditätskennzahlen"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    # Liquiditätsstatus (mit Handling für unendliche Liquidität)
    if firm.liquidity_1 == float('inf') or firm.liquidity_1 >= 1.5:
        liquidity_status = "HEALTHY"
    elif firm.liquidity_1 >= 1.0:
        liquidity_status = "GOOD"
    elif firm.liquidity_1 >= 0.5:
        liquidity_status = "WARNING"
    else:
        liquidity_status = "CRITICAL"

    # Recommendations basierend auf Status
    recommendations = []
    if liquidity_status == "HEALTHY":
        if firm.liquidity_1 == float('inf'):
            recommendations.append("Perfekte Liquidität! Keine Verbindlichkeiten vorhanden. Bereit für Investitionen.")
        else:
            recommendations.append("Liquidität gesund. Gute finanzielle Position.")
    elif liquidity_status == "GOOD":
        recommendations.append("Liquidität gut. Weiter überwachen.")
    elif liquidity_status == "WARNING":
        recommendations.append("Liquidität niedrig. Cashflow überwachen und Kosten reduzieren.")
    elif liquidity_status == "CRITICAL":
        recommendations.append("KRITISCH! Sofort Kredit aufnehmen oder Kosten drastisch senken!")

    return {
        "liquidity_1": firm.liquidity_1 if firm.liquidity_1 != float('inf') else None,
        "liquidity_2": firm.liquidity_2 if firm.liquidity_2 != float('inf') else None,
        "liquidity_3": firm.liquidity_3 if firm.liquidity_3 != float('inf') else None,
        "current_liabilities": firm.current_liabilities,
        "status": liquidity_status,
        "interpretation": {
            "liquidity_1": "Barliquidität (>1.0 = gut, <0.5 = kritisch)",
            "liquidity_2": "Einzugsbedingte Liquidität (>1.0 = gut)",
            "liquidity_3": "Umsatzbedingte Liquidität (>2.0 = gut)"
        },
        "recommendations": recommendations
    }


# ============ M&A COMPLEX SYSTEM ENDPOINTS ============

@app.get("/api/firms/{firm_id}/valuation")
async def get_firm_valuation(firm_id: int):
    """Berechnet Unternehmensbewertung für M&A"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    # Enterprise Value Berechnung
    # EV = Eigenkapital + Schulden - Cash + Goodwill
    # Vereinfacht: Assets + Umsatz-Multiplikator + Marktposition

    asset_value = (
        firm.cash +
        (firm.inventory_level * 50) +  # Inventar zum Einkaufspreis
        firm.machines_value +
        firm.buildings_value +
        firm.equipment_value
    )

    # Umsatz-Multiplikator (4x Jahresumsatz = 16x Quartalsumsatz)
    revenue_value = firm.revenue * 16

    # Marktpositions-Bonus
    market_position_value = firm.market_share * 1_000_000  # €1M pro 1% Marktanteil

    # Enterprise Value = Gewichteter Durchschnitt
    enterprise_value = (
        asset_value * 0.3 +
        revenue_value * 0.5 +
        market_position_value * 0.2
    )

    # Mindestbewertung
    enterprise_value = max(enterprise_value, 500_000)

    return {
        "firm_id": firm_id,
        "firm_name": firm.name,
        "enterprise_value": round(enterprise_value, 2),
        "components": {
            "asset_value": round(asset_value, 2),
            "revenue_value": round(revenue_value, 2),
            "market_position_value": round(market_position_value, 2)
        },
        "market_share": round(firm.market_share * 100, 2),
        "revenue": round(firm.revenue, 2),
        "equity": round(firm.equity, 2)
    }


@app.get("/api/firms/{firm_id}/ownership")
async def get_firm_ownership(firm_id: int):
    """Zeigt Besitzstruktur und Portfolio-Übersicht"""
    firm = game.get_firm_by_id(firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    # Portfolio: Shares this firm owns IN other companies
    portfolio_details = []
    total_portfolio_value = 0.0
    for target_firm_id, percentage in firm.portfolio.items():
        target_firm = game.get_firm_by_id(target_firm_id)
        if target_firm:
            # Calculate value of this stake
            valuation = await get_firm_valuation(target_firm_id)
            stake_value = valuation["enterprise_value"] * (percentage / 100.0)
            total_portfolio_value += stake_value

            portfolio_details.append({
                "firm_id": target_firm_id,
                "firm_name": target_firm.name,
                "percentage_owned": round(percentage, 2),
                "stake_value": round(stake_value, 2),
                "is_full_ownership": percentage >= 100.0,
                "is_majority": percentage >= 51.0,
                "is_blocking_minority": percentage >= 25.0
            })

    # Sort by percentage owned (descending)
    portfolio_details.sort(key=lambda x: x["percentage_owned"], reverse=True)

    # Shareholders: Who owns shares IN this firm
    shareholders_details = []
    for shareholder_name, percentage in firm.shares.items():
        shareholders_details.append({
            "shareholder": shareholder_name,
            "percentage": round(percentage, 2),
            "is_majority_shareholder": percentage >= 51.0,
            "is_blocking_minority": percentage >= 25.0
        })

    # Sort by percentage (descending)
    shareholders_details.sort(key=lambda x: x["percentage"], reverse=True)

    return {
        "firm_id": firm_id,
        "firm_name": firm.name,
        "portfolio": {
            "total_investments": len(portfolio_details),
            "total_portfolio_value": round(total_portfolio_value, 2),
            "holdings": portfolio_details,
            "has_full_ownership": any(h["is_full_ownership"] for h in portfolio_details)
        },
        "shareholders": {
            "total_shareholders": len(shareholders_details),
            "ownership_structure": "Privat" if not firm.is_public else "Börsennotiert",
            "shareholders_list": shareholders_details
        }
    }


@app.get("/api/antitrust/check")
async def check_antitrust(acquirer_id: int, target_id: int, percentage: float):
    """Prüft ob Übernahme kartellrechtlich zulässig ist"""
    acquirer = game.get_firm_by_id(acquirer_id)
    target = game.get_firm_by_id(target_id)

    if not acquirer or not target:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    # Berechne kombinierten Marktanteil
    combined_market_share = (acquirer.market_share + target.market_share) * 100

    # Schwellenwerte
    CRITICAL_THRESHOLD = 40.0  # Ab 40% kritisch
    BLOCKED_THRESHOLD = 50.0   # Ab 50% verboten

    allowed = combined_market_share < BLOCKED_THRESHOLD

    if combined_market_share >= BLOCKED_THRESHOLD:
        reason = f"Marktbeherrschung! Kombinierter Marktanteil {combined_market_share:.1f}% überschreitet Grenze von {BLOCKED_THRESHOLD}%"
        risk_level = "BLOCKED"
    elif combined_market_share >= CRITICAL_THRESHOLD:
        reason = f"Kritischer Marktanteil {combined_market_share:.1f}% - Übernahme unter Auflagen möglich"
        risk_level = "WARNING"
    else:
        reason = f"Übernahme unbedenklich - Kombinierter Marktanteil {combined_market_share:.1f}%"
        risk_level = "OK"

    return {
        "allowed": allowed,
        "combined_market_share": round(combined_market_share, 2),
        "acquirer_market_share": round(acquirer.market_share * 100, 2),
        "target_market_share": round(target.market_share * 100, 2),
        "reason": reason,
        "risk_level": risk_level,
        "threshold": BLOCKED_THRESHOLD
    }


class AcquisitionRequest(BaseModel):
    acquirer_firm_id: int
    target_firm_id: int
    percentage: float


@app.post("/api/acquisitions")
async def execute_partial_acquisition(req: AcquisitionRequest):
    """Führt teilweise oder vollständige Übernahme durch"""
    acquirer = game.get_firm_by_id(req.acquirer_firm_id)
    target = game.get_firm_by_id(req.target_firm_id)

    if not acquirer or not target:
        raise HTTPException(status_code=404, detail="Firma nicht gefunden")

    if req.acquirer_firm_id == req.target_firm_id:
        raise HTTPException(status_code=400, detail="Firma kann sich nicht selbst übernehmen")

    if req.percentage < 1 or req.percentage > 100:
        raise HTTPException(status_code=400, detail="Prozentsatz muss zwischen 1% und 100% liegen")

    # Kartellrecht prüfen
    antitrust_check = await check_antitrust(req.acquirer_firm_id, req.target_firm_id, req.percentage)
    if not antitrust_check["allowed"]:
        raise HTTPException(status_code=403, detail=f"Kartellamt verbietet Übernahme: {antitrust_check['reason']}")

    # Bewertung holen
    valuation = await get_firm_valuation(req.target_firm_id)
    enterprise_value = valuation["enterprise_value"]

    # Preis berechnen (30% Premium)
    acquisition_price = enterprise_value * 1.30 * (req.percentage / 100.0)

    # Prüfe ob genug Cash vorhanden
    if acquirer.cash < acquisition_price:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht genug Cash! Benötigt: €{acquisition_price:,.0f}, Verfügbar: €{acquirer.cash:,.0f}"
        )

    # Wenn 100% - vollständige Übernahme (wie bisheriges System)
    if req.percentage >= 99.9:
        # Nutze die existierende acquire_firm Methode
        acquisition_info = game.acquire_firm(req.acquirer_firm_id, req.target_firm_id)

        await manager.broadcast({
            "type": "full_acquisition",
            "acquirer_firm_id": req.acquirer_firm_id,
            "target_firm_id": req.target_firm_id,
            "acquisition_info": acquisition_info,
            "market": game.get_market_overview()
        })

        return {
            "success": True,
            "type": "full_acquisition",
            "message": f"{acquirer.name} hat {acquisition_info['target_firm']} vollständig übernommen für €{acquisition_info['acquisition_cost']:,.0f}",
            "details": acquisition_info
        }

    else:
        # Teilübernahme (< 100%)
        # Vereinfacht: Kaufe Anteil, übertrage proportionale Assets, Target bleibt bestehen

        # Bezahle
        acquirer.cash -= acquisition_price
        target.cash += acquisition_price * 0.7  # 70% geht an Target (30% sind Transaktionskosten/Premium)

        # Übertrage proportionale Assets
        inventory_transfer = target.inventory_level * (req.percentage / 100.0)
        capacity_transfer = target.production_capacity * (req.percentage / 100.0)

        acquirer.inventory_level += inventory_transfer
        acquirer.production_capacity += capacity_transfer

        target.inventory_level -= inventory_transfer
        target.production_capacity -= capacity_transfer

        # Goodwill
        goodwill = acquisition_price - (target.equity * req.percentage / 100.0)

        message = f"{acquirer.name} hat {req.percentage:.1f}% von {target.name} für €{acquisition_price:,.0f} erworben"

        await manager.broadcast({
            "type": "partial_acquisition",
            "acquirer_firm_id": req.acquirer_firm_id,
            "target_firm_id": req.target_firm_id,
            "percentage": req.percentage,
            "price": acquisition_price,
            "market": game.get_market_overview()
        })

        return {
            "success": True,
            "type": "partial_acquisition",
            "message": message,
            "details": {
                "acquirer_firm": acquirer.name,
                "target_firm": target.name,
                "percentage_acquired": req.percentage,
                "acquisition_price": round(acquisition_price, 2),
                "inventory_transferred": round(inventory_transfer, 0),
                "capacity_transferred": round(capacity_transfer, 0),
                "goodwill": round(goodwill, 2),
                "acquirer_cash_after": round(acquirer.cash, 2),
                "target_cash_after": round(target.cash, 2)
            }
        }


# MOUNT DASHBOARD (at root)
app.mount("/", WSGIMiddleware(dash_app.server))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"""
    ================================================
       BWL Planspiel Server (Integrated)
       Debug Mode: {DEBUG_MODE}
    ================================================

    Dashboard: http://localhost:{port}
    API Docs: http://localhost:{port}/docs
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=DEBUG_MODE,
        log_level="debug" if DEBUG_MODE else "info"
    )
