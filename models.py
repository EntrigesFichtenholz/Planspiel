"""
BWL Planspiel - Business Logic Models
Portiert von C++ ESP32 zu Python Server
"""
import random
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import math


@dataclass
class BusinessFirm:
    """Repräsentiert eine Firma im BWL-Planspiel"""
    id: int
    name: str
    user_names: List[str] = field(default_factory=list)  # Multi-User-Support

    # Financial State
    cash: float = 10_000_000.0  # Startkapital 10M
    debt: float = 0.0  # Fremdkapital/Kredite
    equity: float = 10_000_000.0  # Eigenkapital

    # Business Metrics
    revenue: float = 0.0
    profit: float = 0.0
    ebit: float = 0.0
    ebitda: float = 0.0
    market_share: float = 0.0
    roi: float = 0.0
    roe: float = 0.0  # Return on Equity
    roa: float = 0.0  # Return on Assets
    units_sold: float = 0.0

    # Profitability Ratios (Rentabilitätskennzahlen)
    gross_margin: float = 0.0  # (Revenue - Variable Costs) / Revenue
    operating_margin: float = 0.0  # EBIT / Revenue
    net_margin: float = 0.0  # Net Profit / Revenue
    contribution_margin: float = 0.0  # (Revenue - Variable Costs) / Revenue

    # Efficiency Ratios (Effizienzkennzahlen)
    asset_turnover: float = 0.0  # Revenue / Total Assets
    inventory_turnover: float = 0.0  # COGS / Average Inventory
    capacity_utilization: float = 0.0  # Units Produced / Max Capacity

    # Leverage Ratios (Verschuldungskennzahlen)
    debt_to_equity: float = 0.0  # Debt / Equity
    equity_ratio: float = 0.0  # Equity / Total Assets
    debt_ratio: float = 0.0  # Debt / Total Assets
    interest_coverage: float = 0.0  # EBIT / Interest Expenses

    # Growth Metrics (Wachstumskennzahlen)
    revenue_growth: float = 0.0  # % change from previous quarter
    profit_growth: float = 0.0  # % change from previous quarter
    market_share_growth: float = 0.0  # % change from previous quarter

    # Previous Quarter Values (for growth calculations)
    prev_revenue: float = 0.0
    prev_profit: float = 0.0
    prev_market_share: float = 0.0

    # Cost Breakdown (for transparency)
    cost_breakdown: Dict = field(default_factory=lambda: {
        "variable": 0.0,
        "inventory": 0.0,
        "depreciation": 0.0,
        "overhead": 0.0,
        "marketing": 0.0,
        "rd": 0.0,
        "interest": 0.0,
        "total": 0.0
    })

    # Production & Inventory
    product_price: float = 120.0  # Produktpreis in €
    production_capacity: float = 20_000.0  # Einheiten
    inventory_level: float = 5_000.0  # Lagerbestand
    safety_stock_percentage: float = 0.20  # 20% Sicherheitsbestand (JIT-Strategie)

    # Investments
    marketing_budget: float = 30_000.0  # Marketing Budget
    rd_budget: float = 0.0  # F&E Budget
    quality_level: int = 5  # Qualitätslevel (1-10)

    # Fixed Assets & Depreciation
    buildings_value: float = 10_000_000.0  # Gebäude
    machines_value: float = 50_000_000.0  # Maschinen
    equipment_value: float = 30_000_000.0  # Ausstattung

    # Quarterly Depreciation Rates
    buildings_depreciation_rate: float = 0.005  # 0.5% pro Quartal = 50k (vorher: 1% = 250k)
    machines_depreciation_rate: float = 0.01  # 1% pro Quartal = 500k (vorher: 2.5% = 1.25M)
    equipment_depreciation_rate: float = 0.01  # 1% pro Quartal = 300k (vorher: 2.5% = 750k)

    # Current Quarter
    current_quarter: int = 0
    last_update: float = field(default_factory=time.time)

    # Historical Data (stores last 20 quarters)
    history: List[Dict] = field(default_factory=list)

    # Trading metrics
    customer_satisfaction: float = 0.7
    supplier_trust: float = 0.8
    brand_value: float = 1_000_000.0

    def calculate_quarterly_results(self) -> Dict:
        """Berechnet Quartalsergebnisse basierend auf Entscheidungen"""

        # 1. REVENUE CALCULATION
        # Basis-Nachfrage berechnen (Price-Elasticity: +10% Preis → -15% Absatz)
        base_demand = self.production_capacity
        price_factor = (100.0 / self.product_price) ** 1.5  # Elastizität

        # Marketing-Effekt (logarithmische Sättigung ab 50M€)
        marketing_factor = 1.0 + min(0.5, math.log(1 + self.marketing_budget / 1_000_000) * 0.05)

        # Qualitätsprämie (Level 5 → bis +12.5% Preisaufschlag)
        quality_premium = 1.0 + (self.quality_level / 10.0) * 0.125

        effective_demand = base_demand * price_factor * marketing_factor
        actual_sales = min(effective_demand, self.inventory_level + self.production_capacity)

        # Stockout-Risiko bei niedrigem Safety Stock
        if self.safety_stock_percentage < 0.1:
            stockout_risk = 0.15 * (0.1 - self.safety_stock_percentage) / 0.1
            actual_sales *= (1.0 - stockout_risk)

        effective_price = self.product_price * quality_premium
        self.revenue = actual_sales * effective_price

        # 2. COST CALCULATION
        # Variable Kosten: Material + Produktion
        material_cost_per_unit = 30.0  # €30 Material pro Einheit
        production_cost_per_unit = 20.0  # €20 Produktion pro Einheit
        variable_costs = self.production_capacity * (material_cost_per_unit + production_cost_per_unit)

        # Lagerkosten: 2% des Lagerwerts pro Quartal
        avg_inventory_value = (self.inventory_level * material_cost_per_unit)
        inventory_costs = avg_inventory_value * 0.02

        # Fixkosten: Abschreibungen
        depreciation_buildings = self.buildings_value * self.buildings_depreciation_rate
        depreciation_machines = self.machines_value * self.machines_depreciation_rate
        depreciation_equipment = self.equipment_value * self.equipment_depreciation_rate
        total_depreciation = depreciation_buildings + depreciation_machines + depreciation_equipment

        # Gemeinkosten (Verwaltung, Vertrieb)
        overhead_costs = 200_000.0  # 200k€ pro Quartal (vorher: 6M€)

        # Zinsen auf Fremdkapital (10% p.a. = 2.5% pro Quartal)
        interest_costs = self.debt * 0.025

        # Total Costs
        total_costs = (
            variable_costs +
            inventory_costs +
            total_depreciation +
            overhead_costs +
            self.marketing_budget +
            self.rd_budget +
            interest_costs
        )

        # 3. PROFIT CALCULATION
        gross_profit = self.revenue - variable_costs
        ebit = gross_profit - overhead_costs - total_depreciation - self.marketing_budget - self.rd_budget
        ebt = ebit - interest_costs  # Earnings Before Tax

        # Steuern (33.33% = 1/3)
        taxes = max(0, ebt * 0.3333)
        net_profit = ebt - taxes

        self.profit = net_profit
        self.ebit = ebit
        self.units_sold = actual_sales

        # Store cost breakdown for transparency
        self.cost_breakdown = {
            "variable": variable_costs,
            "inventory": inventory_costs,
            "depreciation": total_depreciation,
            "overhead": overhead_costs,
            "marketing": self.marketing_budget,
            "rd": self.rd_budget,
            "interest": interest_costs,
            "total": total_costs
        }

        # 3.5 CALCULATE ALL BWL KENNZAHLEN (Business Metrics)

        # EBITDA (EBIT + Depreciation)
        self.ebitda = ebit + total_depreciation

        # Profitability Ratios (Rentabilitätskennzahlen)
        if self.revenue > 0:
            self.gross_margin = (gross_profit / self.revenue) * 100  # in %
            self.operating_margin = (ebit / self.revenue) * 100  # in %
            self.net_margin = (net_profit / self.revenue) * 100  # in %
            self.contribution_margin = ((self.revenue - variable_costs) / self.revenue) * 100  # in %
        else:
            self.gross_margin = 0.0
            self.operating_margin = 0.0
            self.net_margin = 0.0
            self.contribution_margin = 0.0

        # Efficiency Ratios (Effizienzkennzahlen)
        total_assets = self.cash + self.buildings_value + self.machines_value + self.equipment_value
        if total_assets > 0:
            self.asset_turnover = self.revenue / total_assets  # Kapitalumschlag
            self.roa = (net_profit / total_assets) * 100  # Return on Assets in %
        else:
            self.asset_turnover = 0.0
            self.roa = 0.0

        # Inventory Turnover (Lagerumschlag)
        avg_inventory = (self.inventory_level + (self.inventory_level + self.production_capacity - actual_sales)) / 2
        if avg_inventory > 0:
            cogs = variable_costs  # Cost of Goods Sold
            self.inventory_turnover = cogs / (avg_inventory * material_cost_per_unit)
        else:
            self.inventory_turnover = 0.0

        # Capacity Utilization (Kapazitätsauslastung)
        max_capacity = 120_000.0  # Maximum production capacity
        if max_capacity > 0:
            self.capacity_utilization = (self.production_capacity / max_capacity) * 100  # in %
        else:
            self.capacity_utilization = 0.0

        # Leverage Ratios (Verschuldungskennzahlen)
        if self.equity > 0:
            self.debt_to_equity = self.debt / self.equity
            self.roe = (net_profit / self.equity) * 100  # Return on Equity in %
        else:
            self.debt_to_equity = 0.0
            self.roe = 0.0

        if total_assets > 0:
            self.equity_ratio = (self.equity / total_assets) * 100  # Eigenkapitalquote in %
            self.debt_ratio = (self.debt / total_assets) * 100  # Fremdkapitalquote in %
        else:
            self.equity_ratio = 0.0
            self.debt_ratio = 0.0

        if interest_costs > 0:
            self.interest_coverage = ebit / interest_costs  # Zinsdeckungsgrad
        else:
            self.interest_coverage = float('inf') if ebit > 0 else 0.0

        # Growth Metrics (Wachstumskennzahlen) - compare to previous quarter
        if self.prev_revenue > 0:
            self.revenue_growth = ((self.revenue - self.prev_revenue) / self.prev_revenue) * 100
        else:
            self.revenue_growth = 0.0

        if self.prev_profit != 0:
            self.profit_growth = ((net_profit - self.prev_profit) / abs(self.prev_profit)) * 100
        else:
            self.profit_growth = 0.0 if net_profit == 0 else 100.0

        if self.prev_market_share > 0:
            self.market_share_growth = ((self.market_share - self.prev_market_share) / self.prev_market_share) * 100
        else:
            self.market_share_growth = 0.0

        # Update previous quarter values for next calculation
        self.prev_revenue = self.revenue
        self.prev_profit = net_profit
        self.prev_market_share = self.market_share

        # 4. UPDATE CASH & INVENTORY
        self.cash += net_profit
        self.inventory_level = max(0, self.inventory_level + self.production_capacity - actual_sales)

        # 5. UPDATE ASSETS (Abschreibung)
        self.buildings_value -= depreciation_buildings
        self.machines_value -= depreciation_machines
        self.equipment_value -= depreciation_equipment

        # 6. CALCULATE ROI
        total_assets = self.cash + self.buildings_value + self.machines_value + self.equipment_value
        if total_assets > 0:
            self.roi = (ebit / total_assets) * 100  # ROI in %

        # 7. UPDATE QUALITY (F&E Investment)
        if self.rd_budget > 0:
            # Level 6 kostet €12M
            cost_per_level = 12_000_000.0
            if self.rd_budget >= cost_per_level and self.quality_level < 10:
                self.quality_level += 1
                self.rd_budget -= cost_per_level

        self.current_quarter += 1
        self.last_update = time.time()

        return {
            "quarter": self.current_quarter,
            "revenue": self.revenue,
            "profit": net_profit,
            "ebit": ebit,
            "cash": self.cash,
            "inventory": self.inventory_level,
            "roi": self.roi,
            "market_share": self.market_share,
            "costs": {
                "variable": variable_costs,
                "inventory": inventory_costs,
                "depreciation": total_depreciation,
                "overhead": overhead_costs,
                "marketing": self.marketing_budget,
                "rd": self.rd_budget,
                "interest": interest_costs,
                "total": total_costs
            },
            "sales": {
                "units_sold": actual_sales,
                "effective_price": effective_price,
                "quality_premium": quality_premium
            }
        }

    def apply_decisions(self, price: float, capacity: float, marketing: float,
                       rd: float, quality: int, jit_safety: float):
        """Wendet Quartalsentscheidungen an"""
        self.product_price = max(50, min(500, price))
        self.production_capacity = max(0, min(120_000, capacity))

        # Marketing max 30% von Cash
        max_marketing = self.cash * 0.3
        self.marketing_budget = max(0, min(max_marketing, marketing))

        # F&E max 20% von Cash
        max_rd = self.cash * 0.2
        self.rd_budget = max(0, min(max_rd, rd))

        self.quality_level = max(1, min(10, quality))
        self.safety_stock_percentage = max(0.0, min(1.0, jit_safety / 100.0))

    def to_dict(self) -> Dict:
        """Konvertiert Firma zu Dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "user_names": self.user_names,
            "cash": round(self.cash, 2),
            "debt": round(self.debt, 2),
            "equity": round(self.equity, 2),
            "revenue": round(self.revenue, 2),
            "profit": round(self.profit, 2),
            "ebit": round(self.ebit, 2),
            "market_share": round(self.market_share, 4),
            "roi": round(self.roi, 2),
            "units_sold": round(self.units_sold, 2),
            "product_price": round(self.product_price, 2),
            "production_capacity": round(self.production_capacity, 2),
            "inventory_level": round(self.inventory_level, 2),
            "safety_stock_percentage": round(self.safety_stock_percentage * 100, 1),
            "marketing_budget": round(self.marketing_budget, 2),
            "rd_budget": round(self.rd_budget, 2),
            "quality_level": self.quality_level,
            "current_quarter": self.current_quarter,
            "assets": {
                "buildings": round(self.buildings_value, 2),
                "machines": round(self.machines_value, 2),
                "equipment": round(self.equipment_value, 2),
                "total": round(self.buildings_value + self.machines_value + self.equipment_value, 2)
            },
            "costs": {
                "variable": round(self.cost_breakdown.get("variable", 0), 2),
                "inventory": round(self.cost_breakdown.get("inventory", 0), 2),
                "depreciation": round(self.cost_breakdown.get("depreciation", 0), 2),
                "overhead": round(self.cost_breakdown.get("overhead", 0), 2),
                "marketing": round(self.cost_breakdown.get("marketing", 0), 2),
                "rd": round(self.cost_breakdown.get("rd", 0), 2),
                "interest": round(self.cost_breakdown.get("interest", 0), 2),
                "total": round(self.cost_breakdown.get("total", 0), 2)
            },
            "profitability_ratios": {
                "ebitda": round(self.ebitda, 2),
                "gross_margin": round(self.gross_margin, 2),
                "operating_margin": round(self.operating_margin, 2),
                "net_margin": round(self.net_margin, 2),
                "contribution_margin": round(self.contribution_margin, 2),
                "roe": round(self.roe, 2),
                "roa": round(self.roa, 2)
            },
            "efficiency_ratios": {
                "asset_turnover": round(self.asset_turnover, 4),
                "inventory_turnover": round(self.inventory_turnover, 2),
                "capacity_utilization": round(self.capacity_utilization, 2)
            },
            "leverage_ratios": {
                "debt_to_equity": round(self.debt_to_equity, 4),
                "equity_ratio": round(self.equity_ratio, 2),
                "debt_ratio": round(self.debt_ratio, 2),
                "interest_coverage": round(self.interest_coverage, 2) if self.interest_coverage != float('inf') else "infinite"
            },
            "growth_metrics": {
                "revenue_growth": round(self.revenue_growth, 2),
                "profit_growth": round(self.profit_growth, 2),
                "market_share_growth": round(self.market_share_growth, 2)
            },
            "history": self.history
        }


class GameSession:
    """Verwaltet eine Spielsession mit mehreren Firmen"""

    def __init__(self):
        self.firms: Dict[int, BusinessFirm] = {}
        self.current_quarter: int = 0
        self.quarter_duration: int = 120  # 120 Sekunden pro Quartal
        self.quarter_start_time: float = time.time()
        self.is_active: bool = False
        self.next_firm_id: int = 1

    def create_firm(self, firm_name: str, user_name: str) -> BusinessFirm:
        """Erstellt eine neue Firma"""
        firm = BusinessFirm(
            id=self.next_firm_id,
            name=firm_name,
            user_names=[user_name]  # Erster User wird hinzugefügt
        )
        self.firms[firm.id] = firm
        self.next_firm_id += 1
        return firm

    def get_firm_by_id(self, firm_id: int) -> Optional[BusinessFirm]:
        """Holt Firma nach ID"""
        return self.firms.get(firm_id)

    def get_firm_by_user(self, user_name: str) -> Optional[BusinessFirm]:
        """Holt Firma nach Username"""
        for firm in self.firms.values():
            if user_name in firm.user_names:
                return firm
        return None

    def add_user_to_firm(self, firm_id: int, user_name: str) -> bool:
        """Fügt User zu bestehender Firma hinzu"""
        firm = self.get_firm_by_id(firm_id)
        if not firm:
            return False
        if user_name in firm.user_names:
            return False  # User bereits in Firma
        firm.user_names.append(user_name)
        return True

    def get_time_until_next_quarter(self) -> int:
        """Berechnet verbleibende Zeit bis nächstes Quartal"""
        elapsed = time.time() - self.quarter_start_time
        remaining = max(0, self.quarter_duration - int(elapsed))
        return remaining

    def should_advance_quarter(self) -> bool:
        """Prüft ob Quartal vorbei ist"""
        return time.time() - self.quarter_start_time >= self.quarter_duration

    def advance_quarter(self):
        """Führt Quartalsabschluss für alle Firmen durch"""
        # Bots treffen automatisch Entscheidungen
        self.make_bot_decisions()

        self.current_quarter += 1
        self.quarter_start_time = time.time()

        results = {}
        for firm_id, firm in self.firms.items():
            result = firm.calculate_quarterly_results()
            results[firm_id] = result

            # Store historical data (after quarter results calculated)
            firm.history.append({
                "quarter": self.current_quarter,
                "revenue": firm.revenue,
                "profit": firm.profit,
                "cash": firm.cash,
                "roi": firm.roi,
                "market_share": firm.market_share,
                "units_sold": firm.units_sold
            })

            # Keep only last 20 quarters
            if len(firm.history) > 20:
                firm.history = firm.history[-20:]

        # Berechne Market Shares
        total_revenue = sum(f.revenue for f in self.firms.values())
        if total_revenue > 0:
            for firm in self.firms.values():
                firm.market_share = firm.revenue / total_revenue

        # PLEITE-MECHANIK: Entferne Firmen mit Cash < 0
        bankrupt_firms = []
        for firm_id, firm in list(self.firms.items()):
            if firm.cash <= 0:
                bankrupt_firms.append(firm.name)
                del self.firms[firm_id]

        if bankrupt_firms:
            print(f"💀 PLEITE: {', '.join(bankrupt_firms)}")

        # Neue Bots hinzufügen alle 5 Quartale
        if self.current_quarter % 5 == 0 and len(self.firms) < 30:
            new_bots = random.randint(1, 3)
            self.create_bot_firms(count=new_bots)
            print(f"📈 {new_bots} neue Bot-Firmen betreten den Markt!")

        return results

    def get_market_overview(self) -> List[Dict]:
        """Gibt Marktübersicht zurück"""
        overview = []
        for firm in sorted(self.firms.values(), key=lambda f: f.market_share, reverse=True):
            overview.append({
                "rank": len(overview) + 1,
                "name": firm.name,
                "user_names": firm.user_names,
                "market_share": round(firm.market_share * 100, 2),
                "revenue": round(firm.revenue, 2),
                "profit": round(firm.profit, 2),
                "roi": round(firm.roi, 2),
                "cash": round(firm.cash, 2)
            })
        return overview

    def create_bot_firms(self, count: int = None):
        """Erstellt KI-Bot-Firmen als Konkurrenz"""
        if count is None:
            count = random.randint(10, 25)  # Zufällige Anzahl zwischen 10-25

        bot_prefixes = ["Tech", "Innovation", "Global", "Market", "Digital", "Smart", "Future", "Quantum", "Cyber", "Mega"]
        bot_suffixes = ["Corp", "Industries", "Systems", "Solutions", "Dynamics", "Ventures", "Labs", "Group", "Partners", "Innovations"]
        strategies = ["Conservative", "Aggressive", "Balanced", "Risk-Taker", "Cautious"]

        for i in range(count):
            prefix = random.choice(bot_prefixes)
            suffix = random.choice(bot_suffixes)
            strategy = random.choice(strategies)
            firm_name = f"{prefix}{suffix}_AI_{i+1}"
            bot_type = f"{strategy} Bot"

            firm = self.create_firm(firm_name, bot_type)
            # Bots starten mit leicht unterschiedlichen Werten
            firm.marketing_budget = random.randint(20000, 50000)
            firm.quality_level = random.randint(4, 7)

    def make_bot_decisions(self):
        """Lässt alle Bot-Firmen automatisch Entscheidungen treffen"""
        for firm in self.firms.values():
            # Check if it's a bot (user_name contains "Bot")
            if any("bot" in user.lower() for user in firm.user_names):
                # Simple AI strategy based on current state
                if firm.cash > 5_000_000:
                    # Aggressive strategy when cash is high
                    price = random.uniform(100, 140)
                    capacity = random.uniform(18000, 25000)
                    marketing = min(firm.cash * 0.25, random.uniform(50000, 200000))
                    rd = min(firm.cash * 0.15, random.uniform(30000, 150000))
                    quality = random.randint(5, 8)
                    jit = random.uniform(10, 25)
                else:
                    # Conservative strategy when cash is low
                    price = random.uniform(110, 130)
                    capacity = random.uniform(15000, 20000)
                    marketing = min(firm.cash * 0.15, random.uniform(20000, 80000))
                    rd = min(firm.cash * 0.08, random.uniform(10000, 50000))
                    quality = random.randint(4, 6)
                    jit = random.uniform(15, 30)

                firm.apply_decisions(price, capacity, marketing, rd, quality, jit)
