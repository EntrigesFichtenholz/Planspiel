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
from enum import Enum
from pydantic import BaseModel


class MachineClass(Enum):
    """Maschinenklassen mit unterschiedlicher Qualität und Kosten"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"


# ============ Pydantic Models (für API & Logic) ============
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

    # NEUE STELLSCHRAUBEN - Effizienz-Investitionen
    process_optimization: Optional[float] = 0
    supplier_negotiation: Optional[float] = 0
    overhead_reduction: Optional[float] = 0

    # NEUE STELLSCHRAUBEN - Abschreibungsraten (in %)
    buildings_depreciation: Optional[float] = None
    machines_depreciation: Optional[float] = None
    equipment_depreciation: Optional[float] = None


class JoinFirmInput(BaseModel):
    user_name: str
# ===========================================================



# LOT/BATCH SYSTEM - Konvertierung zwischen Einheiten und Losen
LOT_SIZE = 100  # 1 Los = 100 Einheiten
UNITS_PER_LOT = 100

# MASCHINEN-KAPAZITÄTEN (Lose pro Quartal)
MACHINE_LOT_CAPACITIES = {
    "basic": 400,        # 400 Lose/Quartal = 40.000 Einheiten
    "professional": 600, # 600 Lose/Quartal = 60.000 Einheiten
    "premium": 1000      # 1000 Lose/Quartal = 100.000 Einheiten
}


class PersonnelQualification(Enum):
    """Personalqualifikationsstufen"""
    UNGELERNT = "ungelernt"  # Unskilled
    ANGELERNT = "angelernt"  # Semi-skilled
    FACHARBEITER = "facharbeiter"  # Skilled worker


class ProductLifecycleStage(Enum):
    """Produktlebenszyklus-Phasen"""
    INTRODUCTION = "introduction"  # Einführung
    GROWTH = "growth"  # Wachstum
    MATURITY = "maturity"  # Reife
    DECLINE = "decline"  # Rückgang


@dataclass
class BusinessFirm:
    """Repräsentiert eine Firma im BWL-Planspiel"""
    id: int
    name: str
    user_names: List[str] = field(default_factory=list)  # Multi-User-Support

    # Financial State - ERHÖHT auf 5M Startkapital (Game Balance Fix)
    cash: float = 5_000_000.0  # Startkapital 5M (gegen Bankrott-Welle)
    debt: float = 0.0  # Fremdkapital/Kredite
    equity: float = 18_300_000.0  # Eigenkapital (= Cash 5M + Assets 13M + Inventory 0.3M, damit Bilanz ausgleicht!)

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
    production_capacity: float = 40_000.0  # Einheiten (ERHÖHT: Game Balance Fix)
    inventory_level: float = 10_000.0  # Lagerbestand (entsprechend erhöht)
    safety_stock_percentage: float = 0.20  # 20% Sicherheitsbestand (JIT-Strategie)

    # Investments
    marketing_budget: float = 30_000.0  # Marketing Budget
    rd_budget: float = 0.0  # F&E Budget
    quality_level: int = 5  # Qualitätslevel (1-10)

    # Fixed Assets & Depreciation - ANGEPASST an 2M Startkapital
    buildings_value: float = 2_000_000.0  # Gebäude (reduziert von 10M)
    machines_value: float = 8_000_000.0  # Maschinen (reduziert von 50M)
    equipment_value: float = 3_000_000.0  # Ausstattung (reduziert von 30M)

    # Quarterly Depreciation Rates (JETZT ANPASSBAR!)
    buildings_depreciation_rate: float = 0.005  # 0.5% pro Quartal = 50k (vorher: 1% = 250k)
    machines_depreciation_rate: float = 0.01  # 1% pro Quartal = 500k (vorher: 2.5% = 1.25M)
    equipment_depreciation_rate: float = 0.01  # 1% pro Quartal = 300k (vorher: 2.5% = 750k)

    # NEUE STELLSCHRAUBEN - Kostenoptimierung
    variable_cost_efficiency: float = 1.0  # 1.0 = normal, 0.8 = -20% durch Prozessoptimierung
    material_cost_reduction: float = 1.0  # 1.0 = normal, 0.9 = -10% durch bessere Lieferanten
    overhead_efficiency: float = 1.0  # 1.0 = normal, 0.7 = -30% durch Verwaltungsoptimierung

    # Investitionen in Effizienz (einmalige Kosten)
    process_optimization_investment: float = 0.0  # Investition in Prozessoptimierung
    supplier_negotiation_investment: float = 0.0  # Investition in Lieferantenverhandlungen
    overhead_reduction_investment: float = 0.0  # Investition in Verwaltungsoptimierung

    # Current Quarter
    current_quarter: int = 0
    last_update: float = field(default_factory=time.time)

    # Historical Data (stores last 20 quarters)
    history: List[Dict] = field(default_factory=list)

    # Trading metrics
    customer_satisfaction: float = 0.7
    supplier_trust: float = 0.8
    brand_value: float = 1_000_000.0

    # M&A & AKTIEN-SYSTEM (nach deutschem Modell)
    shares: Dict[str, float] = field(default_factory=lambda: {})  # {owner_name: percentage} - Who owns shares IN this firm
    portfolio: Dict[int, float] = field(default_factory=lambda: {})  # {firm_id: percentage} - Shares this firm owns IN other firms
    is_public: bool = False  # Börsennotiert oder privat
    share_price: float = 0.0  # Aktienkurs (bei börsennotierten Firmen)
    market_capitalization: float = 0.0  # Marktkapitalisierung
    enterprise_value: float = 0.0  # Unternehmenswert (für Übernahmen)

    # Insolvenz & Gläubiger
    creditors: Dict[str, float] = field(default_factory=lambda: {})  # {creditor: amount}
    is_bankrupt: bool = False
    bankruptcy_quarter: int = 0

    # NEUE SYSTEME - BWL-Erweiterungen

    # LOT/BATCH SYSTEM CONSTANTS
    LOT_SIZE: int = 100  # Units per lot/batch (1 machine = 1 lot = 100 units)

    # MASCHINENSYSTEM (3 Qualitätsklassen)
    machine_class: str = "basic"  # basic, professional, premium
    machines_efficiency_factor: float = 0.8  # Basic = 0.8, Pro = 1.0, Premium = 1.3

    # Maschinenklassen-Eigenschaften (werden bei Upgrade aktualisiert)
    machine_purchase_cost: float = 0.0  # Kosten für nächstes Upgrade
    machine_energy_cost_factor: float = 1.2  # Basic = 1.2 (teurer), Pro = 1.0, Premium = 0.7

    # FINANZIERUNG & KREDITE
    loans: List[Dict] = field(default_factory=list)  # [{amount, interest_rate, quarters_remaining, quarterly_payment}]
    max_loan_capacity: float = 5_000_000.0  # Max Kreditlimit (basierend auf Bonität)
    credit_rating: float = 1.0  # Bonität 0.5-1.5 (beeinflusst Zinssatz)

    # LIQUIDITÄTSKENNZAHLEN
    liquidity_1: float = float('inf')  # Barliquidität (Cash / kurzfristige Verbindlichkeiten) - Start: unendlich
    liquidity_2: float = float('inf')  # Einzugsbedingte Liquidität - Start: unendlich
    liquidity_3: float = float('inf')  # Umsatzbedingte Liquidität - Start: unendlich
    current_liabilities: float = 0.0  # Kurzfristige Verbindlichkeiten

    # PERSONALQUALIFIKATION (REDUZIERT: Game Balance Fix)
    personnel_ungelernt: int = 20  # Anzahl ungelernte Arbeiter (reduziert von 50)
    personnel_angelernt: int = 15  # Anzahl angelernte Arbeiter (reduziert von 30)
    personnel_facharbeiter: int = 10  # Anzahl Facharbeiter (reduziert von 20)

    # Personalkosten (€/Quartal pro Person)
    cost_ungelernt: float = 8_000.0  # €8k/Quartal
    cost_angelernt: float = 12_000.0  # €12k/Quartal
    cost_facharbeiter: float = 18_000.0  # €18k/Quartal

    # Produktivitätsfaktoren nach Qualifikation
    productivity_ungelernt: float = 0.7  # 70% Effizienz
    productivity_angelernt: float = 1.0  # 100% Effizienz
    productivity_facharbeiter: float = 1.4  # 140% Effizienz

    # PRODUKTLEBENSZYKLUS
    product_lifecycle_stage: str = "introduction"  # introduction, growth, maturity, decline
    product_age_quarters: int = 0  # Wie lange ist das Produkt am Markt?
    innovation_investment: float = 0.0  # Investment in Produkterneuerung
    product_innovation_level: int = 1  # Generation des Produkts (1, 2, 3, ...)

    # BILANZ & GuV Komponenten (für Reporting)
    # Aktiva (Assets)
    current_assets: float = 0.0  # Umlaufvermögen (Cash + Inventory)
    fixed_assets: float = 0.0  # Anlagevermögen (Buildings + Machines + Equipment)

    # Passiva (Liabilities & Equity)
    long_term_liabilities: float = 0.0  # Langfristige Verbindlichkeiten (Loans)

    # GuV Komponenten
    total_revenue: float = 0.0  # Gesamtumsatz
    total_costs: float = 0.0  # Gesamtkosten
    net_income: float = 0.0  # Jahresüberschuss (aktuelles Quartal)
    retained_earnings: float = 0.0  # Kumulierte Gewinne/Verluste (Bilanz-Fix)

    # DECKUNGSBEITRAG (Contribution Margin)
    variable_costs_total: float = 0.0  # Gesamte variable Kosten
    fixed_costs_total: float = 0.0  # Gesamte Fixkosten
    contribution_margin_total: float = 0.0  # Deckungsbeitrag (Revenue - Variable Costs)
    contribution_margin_per_unit: float = 0.0  # Deckungsbeitrag pro Einheit

    def calculate_max_production_capacity(self) -> float:
        """
        Berechnet maximale Produktionskapazität basierend auf:
        - Maschinenklasse (Kapazität in Losen pro Quartal)
        - Personalproduktivität (gewichteter Durchschnitt)

        Returns: Maximale Produktionskapazität in Einheiten
        """
        # 1. Maschinenkapazität in Losen
        machine_lot_capacity = MACHINE_LOT_CAPACITIES.get(self.machine_class, 400)

        # 2. Personalproduktivität berechnen (gewichteter Durchschnitt)
        total_personnel = (
            self.personnel_ungelernt +
            self.personnel_angelernt +
            self.personnel_facharbeiter
        )

        if total_personnel == 0:
            personnel_productivity = 0.0
        else:
            weighted_productivity = (
                self.personnel_ungelernt * self.productivity_ungelernt +
                self.personnel_angelernt * self.productivity_angelernt +
                self.personnel_facharbeiter * self.productivity_facharbeiter
            ) / total_personnel
            personnel_productivity = weighted_productivity

        # 3. Maschineneffizienz (abhängig von Maschinenklasse)
        machine_efficiency = self.machines_efficiency_factor

        # 4. Maximale Kapazität = Maschinenkapazität × Personalproduktivität × Maschineneffizienz
        max_lots = machine_lot_capacity * personnel_productivity * machine_efficiency
        max_units = max_lots * UNITS_PER_LOT

        return max_units

    def get_production_in_lots(self) -> float:
        """Konvertiert aktuelle Produktionskapazität in Lose"""
        return self.production_capacity / UNITS_PER_LOT

    def get_inventory_in_lots(self) -> float:
        """Konvertiert Lagerbestand in Lose"""
        return self.inventory_level / UNITS_PER_LOT

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
        # Variable Kosten: Material + Produktion (MIT EFFIZIENZFAKTOREN + MASCHINENKLASSE!)
        base_material_cost_per_unit = 30.0  # €30 Material pro Einheit (Basis)
        base_production_cost_per_unit = 20.0  # €20 Produktion pro Einheit (Basis)

        # Anwenden der Effizienzfaktoren (Prozessoptimierung + Maschinenklasse)
        material_cost_per_unit = base_material_cost_per_unit * self.material_cost_reduction
        production_cost_per_unit = base_production_cost_per_unit * self.variable_cost_efficiency * (2.0 - self.machines_efficiency_factor)  # Bessere Maschinen = niedrigere Produktionskosten

        # PERSONALKOSTEN (Variable, abhängig von Qualifikation)
        total_personnel = self.personnel_ungelernt + self.personnel_angelernt + self.personnel_facharbeiter
        personnel_costs = (
            self.personnel_ungelernt * self.cost_ungelernt +
            self.personnel_angelernt * self.cost_angelernt +
            self.personnel_facharbeiter * self.cost_facharbeiter
        )

        # Durchschnittliche Personalproduktivität
        if total_personnel > 0:
            avg_productivity = (
                self.personnel_ungelernt * self.productivity_ungelernt +
                self.personnel_angelernt * self.productivity_angelernt +
                self.personnel_facharbeiter * self.productivity_facharbeiter
            ) / total_personnel
        else:
            avg_productivity = 1.0

        # Produktionskapazität wird durch Personalproduktivität beeinflusst
        effective_capacity = self.production_capacity * avg_productivity

        # ENERGIEKOSTEN (abhängig von Maschinenklasse)
        energy_cost_per_unit = 5.0 * self.machine_energy_cost_factor  # Basic: 6€, Pro: 5€, Premium: 3.5€
        energy_costs = self.production_capacity * energy_cost_per_unit

        variable_costs = self.production_capacity * (material_cost_per_unit + production_cost_per_unit) + energy_costs

        # Lagerkosten: 2% des Lagerwerts pro Quartal
        avg_inventory_value = (self.inventory_level * material_cost_per_unit)
        inventory_costs = avg_inventory_value * 0.02

        # Fixkosten: Abschreibungen
        depreciation_buildings = self.buildings_value * self.buildings_depreciation_rate
        depreciation_machines = self.machines_value * self.machines_depreciation_rate
        depreciation_equipment = self.equipment_value * self.equipment_depreciation_rate
        total_depreciation = depreciation_buildings + depreciation_machines + depreciation_equipment

        # Gemeinkosten (Verwaltung, Vertrieb) - MIT EFFIZIENZFAKTOR
        base_overhead_costs = 50_000.0  # 50k€ pro Quartal (REDUZIERT: Game Balance Fix)
        overhead_costs = base_overhead_costs * self.overhead_efficiency  # Reduzierbar durch Investitionen

        # KREDITZINSEN: Berechne Zinsen für alle laufenden Kredite
        interest_costs = self.debt * 0.025  # Alte Schulden: 10% p.a. = 2.5% pro Quartal
        loan_payments = 0.0
        for loan in self.loans:
            loan_payments += loan.get('quarterly_payment', 0)
            interest_costs += loan.get('interest_payment', 0)

        # Effizienz-Investitionen (einmalige Kosten dieses Quartals)
        efficiency_investments = (
            self.process_optimization_investment +
            self.supplier_negotiation_investment +
            self.overhead_reduction_investment
        )

        # Total Costs (ERWEITERT mit Personalkosten, Kreditzahlungen, Innovation)
        total_costs = (
            variable_costs +
            inventory_costs +
            total_depreciation +
            overhead_costs +
            personnel_costs +  # NEUE KOSTEN: Personal
            self.marketing_budget +
            self.rd_budget +
            interest_costs +
            loan_payments +  # NEUE KOSTEN: Kredittilgung
            efficiency_investments +  # Einmalige Investitionen
            self.innovation_investment  # NEUE KOSTEN: Produktinnovation
        )

        # 3. PROFIT CALCULATION
        gross_profit = self.revenue - variable_costs
        ebit = gross_profit - overhead_costs - personnel_costs - total_depreciation - self.marketing_budget - self.rd_budget
        ebt = ebit - interest_costs  # Earnings Before Tax

        # Steuern (33.33% = 1/3)
        taxes = max(0, ebt * 0.3333)
        net_profit = ebt - taxes

        self.profit = net_profit
        self.ebit = ebit
        self.units_sold = actual_sales

        # Store cost breakdown for transparency (UMFASSEND ERWEITERT)
        self.cost_breakdown = {
            "variable": variable_costs,
            "energy": energy_costs,
            "inventory": inventory_costs,
            "depreciation": total_depreciation,
            "depreciation_buildings": depreciation_buildings,
            "depreciation_machines": depreciation_machines,
            "depreciation_equipment": depreciation_equipment,
            "overhead": overhead_costs,
            "personnel": personnel_costs,
            "personnel_ungelernt": self.personnel_ungelernt * self.cost_ungelernt,
            "personnel_angelernt": self.personnel_angelernt * self.cost_angelernt,
            "personnel_facharbeiter": self.personnel_facharbeiter * self.cost_facharbeiter,
            "marketing": self.marketing_budget,
            "rd": self.rd_budget,
            "interest": interest_costs,
            "loan_payments": loan_payments,
            "innovation": self.innovation_investment,
            "efficiency_investments": efficiency_investments,
            "total": total_costs
        }

        # DECKUNGSBEITRAG (Contribution Margin Calculation)
        self.variable_costs_total = variable_costs + energy_costs + personnel_costs
        self.fixed_costs_total = total_depreciation + overhead_costs + self.marketing_budget + self.rd_budget + interest_costs
        self.contribution_margin_total = self.revenue - self.variable_costs_total
        if actual_sales > 0:
            self.contribution_margin_per_unit = self.contribution_margin_total / actual_sales
        else:
            self.contribution_margin_per_unit = 0.0

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

        # 3.5 EFFICIENCY IMPROVEMENTS basierend auf Investitionen
        # Prozessoptimierung: €2M → -5% variable Kosten (max -20%)
        if self.process_optimization_investment >= 2_000_000:
            self.variable_cost_efficiency = max(0.8, self.variable_cost_efficiency - 0.05)
            self.process_optimization_investment = 0  # Investment verbraucht

        # Lieferantenverhandlungen: €1.5M → -5% Materialkosten (max -30%)
        if self.supplier_negotiation_investment >= 1_500_000:
            self.material_cost_reduction = max(0.7, self.material_cost_reduction - 0.05)
            self.supplier_negotiation_investment = 0  # Investment verbraucht

        # Verwaltungsoptimierung: €1M → -10% Overhead (max -50%)
        if self.overhead_reduction_investment >= 1_000_000:
            self.overhead_efficiency = max(0.5, self.overhead_efficiency - 0.10)
            self.overhead_reduction_investment = 0  # Investment verbraucht

        # 3.6 PRODUKTLEBENSZYKLUS (Product Lifecycle Management)
        self.product_age_quarters += 1

        # Produktinnovation: €5M → neues Produkt (Generation++)
        if self.innovation_investment >= 5_000_000:
            self.product_innovation_level += 1
            self.product_age_quarters = 0
            self.product_lifecycle_stage = "introduction"
            self.innovation_investment = 0

        # Automatische Lifecycle-Übergänge
        if self.product_age_quarters <= 4:
            self.product_lifecycle_stage = "introduction"
        elif self.product_age_quarters <= 12:
            self.product_lifecycle_stage = "growth"
        elif self.product_age_quarters <= 24:
            self.product_lifecycle_stage = "maturity"
        else:
            self.product_lifecycle_stage = "decline"

        # Lifecycle-Effekte auf Nachfrage (multiplicativ)
        lifecycle_demand_factor = {
            "introduction": 0.7,  # 70% Nachfrage (Markteinführung schwierig)
            "growth": 1.3,  # 130% Nachfrage (Wachstumsphase)
            "maturity": 1.0,  # 100% Nachfrage (stabile Phase)
            "decline": 0.6  # 60% Nachfrage (Produkt veraltet)
        }
        # Anwendung des Lifecycle-Faktors auf zukünftige Berechnungen
        # (wird im nächsten Quartal wirksam)

        # 3.7 KREDITABWICKLUNG (Loan Processing)
        loans_to_remove = []
        for i, loan in enumerate(self.loans):
            # Tilgung der Laufzeit
            loan['quarters_remaining'] -= 1

            # Berechne Zinszahlung
            quarterly_interest_rate = loan['interest_rate'] / 4.0  # p.a. → pro Quartal
            interest_payment = loan['amount'] * quarterly_interest_rate
            loan['interest_payment'] = interest_payment

            # Berechne Tilgung
            if loan['quarters_remaining'] > 0:
                principal_payment = loan['amount'] / (loan['quarters_remaining'] + 1)
                loan['quarterly_payment'] = principal_payment + interest_payment
                loan['amount'] -= principal_payment
            else:
                # Kredit abbezahlt
                loans_to_remove.append(i)

        # Entferne abbezahlte Kredite
        for i in reversed(loans_to_remove):
            del self.loans[i]

        # Update total debt
        self.debt = sum(loan['amount'] for loan in self.loans)

        # 3.8 LIQUIDITÄTSKENNZAHLEN (Liquidity Ratios nach BWL-Vorlesung)
        # Kurzfristige Verbindlichkeiten = Quartalszahlungen + kleine Kredite
        self.current_liabilities = loan_payments + overhead_costs + personnel_costs

        if self.current_liabilities > 0:
            # Liquidität 1. Grades (Barliquidität): Cash / kurzfr. Verbindlichkeiten
            self.liquidity_1 = self.cash / self.current_liabilities

            # Liquidität 2. Grades: (Cash + Forderungen) / kurzfr. Verbindlichkeiten
            # Vereinfacht: Cash + 50% Inventory Value
            receivables = self.inventory_level * material_cost_per_unit * 0.5
            self.liquidity_2 = (self.cash + receivables) / self.current_liabilities

            # Liquidität 3. Grades: (Cash + Forderungen + Vorräte) / kurzfr. Verbindlichkeiten
            inventory_value = self.inventory_level * material_cost_per_unit
            self.liquidity_3 = (self.cash + receivables + inventory_value) / self.current_liabilities
        else:
            self.liquidity_1 = float('inf')
            self.liquidity_2 = float('inf')
            self.liquidity_3 = float('inf')

        # 3.9 BILANZ-KOMPONENTEN UPDATE (Balance Sheet Components)
        self.current_assets = self.cash + (self.inventory_level * material_cost_per_unit)
        self.fixed_assets = self.buildings_value + self.machines_value + self.equipment_value
        self.long_term_liabilities = self.debt
        self.total_revenue = self.revenue
        self.total_costs = total_costs
        self.net_income = net_profit
        self.retained_earnings += net_profit  # Kumuliere Gewinne/Verluste für Bilanz

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

        # Aktualisiere Unternehmenswert
        self.calculate_enterprise_value()

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
                       rd: float, quality: int, jit_safety: float,
                       process_opt: float = 0, supplier_neg: float = 0, overhead_red: float = 0,
                       buildings_depr: float = None, machines_depr: float = None, equipment_depr: float = None):
        """Wendet Quartalsentscheidungen an (ERWEITERT mit Effizienz-Investitionen)"""
        self.product_price = max(50, min(500, price))

        # NEUE LOGIK: Produktionskapazität wird von Maschinen + Personal begrenzt
        max_capacity = self.calculate_max_production_capacity()
        requested_capacity = max(0, capacity)
        self.production_capacity = min(requested_capacity, max_capacity)

        # Marketing max 30% von Cash
        max_marketing = self.cash * 0.3
        self.marketing_budget = max(0, min(max_marketing, marketing))

        # F&E max 20% von Cash
        max_rd = self.cash * 0.2
        self.rd_budget = max(0, min(max_rd, rd))

        self.quality_level = max(1, min(10, quality))
        self.safety_stock_percentage = max(0.0, min(1.0, jit_safety / 100.0))

        # NEUE STELLSCHRAUBEN: Effizienz-Investitionen (max 10% von Cash pro Investment)
        max_efficiency_investment = self.cash * 0.1
        self.process_optimization_investment = max(0, min(max_efficiency_investment, process_opt))
        self.supplier_negotiation_investment = max(0, min(max_efficiency_investment, supplier_neg))
        self.overhead_reduction_investment = max(0, min(max_efficiency_investment, overhead_red))

        # NEUE STELLSCHRAUBEN: Abschreibungsraten (wenn angegeben)
        if buildings_depr is not None:
            self.buildings_depreciation_rate = max(0.001, min(0.05, buildings_depr / 100.0))  # 0.1% - 5%
        if machines_depr is not None:
            self.machines_depreciation_rate = max(0.001, min(0.05, machines_depr / 100.0))  # 0.1% - 5%
        if equipment_depr is not None:
            self.equipment_depreciation_rate = max(0.001, min(0.05, equipment_depr / 100.0))  # 0.1% - 5%

    def calculate_enterprise_value(self) -> float:
        """
        Berechnet Unternehmenswert nach deutschem Modell
        EV = Eigenkapital + Marktwert Assets + Goodwill (Brand Value) - Schulden
        """
        total_assets = self.buildings_value + self.machines_value + self.equipment_value
        goodwill = self.brand_value

        # Unternehmenswert = Buchwert + Goodwill
        enterprise_value = self.equity + total_assets + goodwill - self.debt

        # Bei profitablen Firmen: Premium basierend auf EBIT-Multiple (typisch 5-10x EBIT)
        if self.ebit > 0:
            ebit_multiple = 7.0  # Konservativ
            enterprise_value += self.ebit * ebit_multiple

        self.enterprise_value = max(0, enterprise_value)

        # Aktienkurs berechnen (falls börsennotiert)
        if self.is_public:
            # Annahme: 1 Million Aktien ausgegeben
            total_shares = 1_000_000
            self.share_price = self.enterprise_value / total_shares
            self.market_capitalization = self.enterprise_value

        return self.enterprise_value

    def calculate_acquisition_price(self, percentage: float) -> float:
        """
        Berechnet Übernahmepreis mit Premium (deutsches M&A-Modell)
        Premium: 20-40% über Unternehmenswert (typisch bei feindlichen Übernahmen)
        """
        base_value = self.calculate_enterprise_value()

        # Übernahmeprämie: 30% (Durchschnitt in Deutschland)
        acquisition_premium = 0.30

        # Preis = (Unternehmenswert * (1 + Premium)) * Anteil
        price = base_value * (1 + acquisition_premium) * (percentage / 100.0)

        return price

    def can_be_acquired(self, acquirer_firm: 'BusinessFirm', percentage: float, game_session: 'GameSession') -> tuple[bool, str]:
        """
        Prüft ob Übernahme möglich ist (inkl. Kartellamt-Prüfung)

        Returns: (is_allowed, reason)
        """
        # 1. Prüfe ob Firma bereits bankrott ist
        if self.is_bankrupt:
            return False, "Firma ist bereits insolvent"

        # 2. Prüfe ob Käufer genug Cash hat
        acquisition_price = self.calculate_acquisition_price(percentage)
        if acquirer_firm.cash < acquisition_price:
            return False, f"Nicht genug Bargeld. Benötigt: €{acquisition_price:,.0f}, Verfügbar: €{acquirer_firm.cash:,.0f}"

        # 3. KARTELLAMT-PRÜFUNG (deutsches Modell)
        # GWB §35-39: Fusionskontrolle

        # Berechne neuen Marktanteil nach Übernahme
        combined_market_share = acquirer_firm.market_share + (self.market_share * percentage / 100.0)

        # Schwelle 1: >25% Marktanteil = Vermutung marktbeherrschender Stellung
        if combined_market_share > 0.25:
            return False, f"⚖️ KARTELLAMT: Übernahme untersagt! Kombinierter Marktanteil würde {combined_market_share*100:.1f}% betragen (>25% Schwelle)"

        # Schwelle 2: Prüfe ob Top-3 Firmen zusammen >50% haben würden
        # (vereinfachte Prüfung für oligopolistische Marktstrukturen)
        market_overview = game_session.get_market_overview()
        top_3_market_share = sum(f['market_share'] for f in market_overview[:3]) / 100.0

        if top_3_market_share > 0.50 and acquirer_firm.market_share in [f['market_share']/100.0 for f in market_overview[:3]]:
            return False, "⚖️ KARTELLAMT: Übernahme untersagt! Oligopolbildung verhindert (Top-3 hätten >50% Marktanteil)"

        return True, "Übernahme kartellrechtlich zulässig"

    def acquire_shares(self, acquirer_firm: 'BusinessFirm', percentage: float, game_session: 'GameSession') -> tuple[bool, str]:
        """
        Führt Unternehmens-Übernahme durch
        """
        # Kartellamt-Prüfung
        allowed, reason = self.can_be_acquired(acquirer_firm, percentage, game_session)
        if not allowed:
            return False, reason

        # Berechne Kaufpreis
        acquisition_price = self.calculate_acquisition_price(percentage)

        # Transaktion durchführen
        acquirer_firm.cash -= acquisition_price

        # Aktien übertragen
        acquirer_name = acquirer_firm.user_names[0] if acquirer_firm.user_names else f"Firma_{acquirer_firm.id}"

        if acquirer_name not in acquirer_firm.shares:
            acquirer_firm.shares[acquirer_name] = 0.0

        # Übernehme Anteile vom ersten Eigentümer (vereinfacht)
        if self.shares:
            first_owner = list(self.shares.keys())[0]
            if self.shares[first_owner] >= percentage:
                self.shares[first_owner] -= percentage
                if self.shares[first_owner] <= 0:
                    del self.shares[first_owner]
            else:
                return False, "Nicht genug Anteile verfügbar"
        else:
            # Firma hat keine definierten Eigentümer - gehört sich selbst
            pass

        # Füge Käufer als neuen Eigentümer hinzu
        if acquirer_name not in self.shares:
            self.shares[acquirer_name] = 0.0
        self.shares[acquirer_name] += percentage

        # PORTFOLIO TRACKING: Track shares acquirer owns in this firm
        if self.id not in acquirer_firm.portfolio:
            acquirer_firm.portfolio[self.id] = 0.0
        acquirer_firm.portfolio[self.id] += percentage

        # Check if 100% ownership achieved
        ownership_status = ""
        if acquirer_firm.portfolio[self.id] >= 100.0:
            ownership_status = " [100% EIGENTUM - VOLLSTÄNDIGE ÜBERNAHME]"

        # Cash geht an die Firma (bei Kapitalerhöhung) oder an Altaktionäre (bei Anteilsverkauf)
        # Hier: Vereinfacht - Cash geht direkt an die Ziel-Firma
        self.cash += acquisition_price * 0.7  # 70% gehen an Firma, 30% Transaktionskosten/Steuern

        return True, f"Übernahme erfolgreich! {percentage}% Anteile für €{acquisition_price:,.0f} erworben{ownership_status}"

    def process_bankruptcy(self, game_session: 'GameSession') -> Dict:
        """
        Erweiterte Insolvenz-Mechanik nach deutschem Insolvenzrecht

        Ablauf:
        1. Firma wird als insolvent markiert
        2. Assets werden bewertet und verkauft
        3. Gläubiger werden nach Rangfolge bedient
        4. Restliche Schulden werden erlassen
        """
        if not self.is_bankrupt:
            self.is_bankrupt = True
            self.bankruptcy_quarter = game_session.current_quarter

        # ASSET-LIQUIDATION (Notverkauf = 60% des Buchwertes)
        liquidation_value = (
            self.buildings_value * 0.6 +
            self.machines_value * 0.6 +
            self.equipment_value * 0.6 +
            self.inventory_level * 30 * 0.5  # Lagerbestand zum halben Materialpreis
        )

        total_available = self.cash + liquidation_value

        # GLÄUBIGER-RANGFOLGE (deutsches Insolvenzrecht)
        # 1. Massekost en (Insolvenzverwalter) - 10%
        insolvency_costs = total_available * 0.10
        remaining = total_available - insolvency_costs

        # 2. Vorrangige Forderungen (Löhne, Steuern)
        # Vereinfacht: 20% der Schulden
        priority_claims = min(self.debt * 0.20, remaining * 0.30)
        remaining -= priority_claims

        # 3. Normale Gläubiger (Banken, Lieferanten)
        # Quotale Befriedigung
        if self.debt > 0:
            quota = remaining / self.debt  # Insolvenzquote
        else:
            quota = 1.0

        return {
            "liquidation_value": liquidation_value,
            "total_available": total_available,
            "insolvency_costs": insolvency_costs,
            "priority_claims": priority_claims,
            "creditor_quota": quota * 100,  # in %
            "remaining_debt": max(0, self.debt - remaining)
        }

    def upgrade_machines(self, target_class: str) -> tuple[bool, str]:
        """
        Upgrade zu besserer Maschinenklasse

        Kosten:
        - Basic → Professional: €3M
        - Professional → Premium: €6M

        Returns: (success, message)
        """
        upgrades = {
            "basic": {
                "next": "professional",
                "cost": 3_000_000,
                "efficiency": 1.0,
                "energy_factor": 1.0,
                "depreciation": 0.01
            },
            "professional": {
                "next": "premium",
                "cost": 6_000_000,
                "efficiency": 1.3,
                "energy_factor": 0.7,
                "depreciation": 0.008
            }
        }

        if self.machine_class not in upgrades:
            return False, "Maximale Maschinenklasse bereits erreicht"

        upgrade_info = upgrades[self.machine_class]

        if target_class != upgrade_info["next"]:
            return False, f"Kann nur zu {upgrade_info['next']} upgraden"

        if self.cash < upgrade_info["cost"]:
            return False, f"Nicht genug Cash. Benötigt: €{upgrade_info['cost']:,.0f}, Verfügbar: €{self.cash:,.0f}"

        # Upgrade durchführen
        self.cash -= upgrade_info["cost"]
        self.machine_class = target_class
        self.machines_efficiency_factor = upgrade_info["efficiency"]
        self.machine_energy_cost_factor = upgrade_info["energy_factor"]
        self.machines_depreciation_rate = upgrade_info["depreciation"]
        self.machines_value += upgrade_info["cost"]  # Wertsteigerung der Maschinen

        return True, f"Maschinen erfolgreich zu {target_class} upgraded für €{upgrade_info['cost']:,.0f}"

    def take_loan(self, amount: float, quarters: int = 12) -> tuple[bool, str]:
        """
        Nimmt Kredit auf

        Args:
            amount: Kreditbetrag
            quarters: Laufzeit in Quartalen (Standard: 12 = 3 Jahre)

        Returns: (success, message)
        """
        # Prüfe Kreditlimit
        total_debt = self.debt + amount
        if total_debt > self.max_loan_capacity:
            return False, f"Kreditlimit überschritten. Max: €{self.max_loan_capacity:,.0f}, Aktuell: €{self.debt:,.0f}"

        # Berechne Zinssatz basierend auf Bonität
        # Bessere Bonität = niedrigere Zinsen
        # Bonität 1.0 → 10% p.a., Bonität 0.5 → 20% p.a., Bonität 1.5 → 5% p.a.
        base_interest_rate = 0.10  # 10% p.a.
        interest_rate = base_interest_rate / self.credit_rating
        interest_rate = min(0.25, max(0.05, interest_rate))  # 5-25% p.a.

        # Erstelle Kredit
        loan = {
            "amount": amount,
            "original_amount": amount,
            "interest_rate": interest_rate,
            "quarters_remaining": quarters,
            "quarterly_payment": 0,  # Wird in calculate_quarterly_results berechnet
            "interest_payment": 0
        }

        self.loans.append(loan)
        self.cash += amount
        self.debt += amount

        # Bonität verschlechtert sich mit höherer Verschuldung
        self.update_credit_rating()

        return True, f"Kredit über €{amount:,.0f} aufgenommen. Zinssatz: {interest_rate*100:.1f}% p.a., Laufzeit: {quarters} Quartale"

    def update_credit_rating(self):
        """Aktualisiert Bonität basierend auf Kennzahlen"""
        # Bonität basiert auf:
        # 1. Verschuldungsgrad (Debt/Equity)
        # 2. Liquidität
        # 3. Profitabilität (ROE)

        rating = 1.0  # Basis

        # Verschuldungsgrad: <0.5 = gut, >2.0 = schlecht
        if self.equity > 0:
            debt_equity = self.debt / self.equity
            if debt_equity < 0.5:
                rating += 0.3
            elif debt_equity > 2.0:
                rating -= 0.4
            elif debt_equity > 1.0:
                rating -= 0.2

        # Liquidität: >1.5 = gut, <0.5 = schlecht
        if self.liquidity_1 > 1.5:
            rating += 0.2
        elif self.liquidity_1 < 0.5:
            rating -= 0.3

        # ROE: >15% = gut, <0% = schlecht
        if self.roe > 15:
            rating += 0.1
        elif self.roe < 0:
            rating -= 0.2

        self.credit_rating = max(0.5, min(1.5, rating))

    def hire_personnel(self, qualification: str, count: int) -> tuple[bool, str]:
        """
        Stellt Personal ein

        Args:
            qualification: "ungelernt", "angelernt", "facharbeiter"
            count: Anzahl Mitarbeiter

        Returns: (success, message)
        """
        costs_per_quarter = {
            "ungelernt": self.cost_ungelernt,
            "angelernt": self.cost_angelernt,
            "facharbeiter": self.cost_facharbeiter
        }

        if qualification not in costs_per_quarter:
            return False, "Ungültige Qualifikation"

        hiring_cost = costs_per_quarter[qualification] * count * 0.5  # 50% eines Quartalsgehalts als Einstellungskosten

        if self.cash < hiring_cost:
            return False, f"Nicht genug Cash für Einstellung. Benötigt: €{hiring_cost:,.0f}"

        self.cash -= hiring_cost

        if qualification == "ungelernt":
            self.personnel_ungelernt += count
        elif qualification == "angelernt":
            self.personnel_angelernt += count
        elif qualification == "facharbeiter":
            self.personnel_facharbeiter += count

        return True, f"{count} {qualification} Mitarbeiter eingestellt für €{hiring_cost:,.0f}"

    def fire_personnel(self, qualification: str, count: int) -> tuple[bool, str]:
        """
        Entlässt Personal (mit Abfindung)

        Args:
            qualification: "ungelernt", "angelernt", "facharbeiter"
            count: Anzahl Mitarbeiter

        Returns: (success, message)
        """
        costs_per_quarter = {
            "ungelernt": self.cost_ungelernt,
            "angelernt": self.cost_angelernt,
            "facharbeiter": self.cost_facharbeiter
        }

        current_count = {
            "ungelernt": self.personnel_ungelernt,
            "angelernt": self.personnel_angelernt,
            "facharbeiter": self.personnel_facharbeiter
        }

        if qualification not in costs_per_quarter:
            return False, "Ungültige Qualifikation"

        if current_count[qualification] < count:
            return False, f"Nur {current_count[qualification]} {qualification} Mitarbeiter verfügbar"

        # Abfindung: 1 Quartalsgehalt pro Mitarbeiter (deutsches Arbeitsrecht vereinfacht)
        severance_cost = costs_per_quarter[qualification] * count

        if self.cash < severance_cost:
            return False, f"Nicht genug Cash für Abfindungen. Benötigt: €{severance_cost:,.0f}"

        self.cash -= severance_cost

        if qualification == "ungelernt":
            self.personnel_ungelernt -= count
        elif qualification == "angelernt":
            self.personnel_angelernt -= count
        elif qualification == "facharbeiter":
            self.personnel_facharbeiter -= count

        return True, f"{count} {qualification} Mitarbeiter entlassen mit €{severance_cost:,.0f} Abfindung"

    def issue_shares(self, amount: float) -> tuple[bool, str]:
        """
        Eigenkapitalerhöhung durch Aktienausgabe (IPO oder Capital Raise)

        Args:
            amount: Gewünschter Kapitalbetrag

        Returns: (success, message)
        """
        # Prüfe ob Firma schon börsennotiert ist
        if not self.is_public:
            # IPO (Initial Public Offering)
            # Kosten: 10% des aufgenommenen Kapitals (Banken, Anwälte, Börsengebühren)
            ipo_costs = amount * 0.10

            if self.cash < ipo_costs:
                return False, f"IPO-Kosten zu hoch. Benötigt: €{ipo_costs:,.0f}"

            self.cash -= ipo_costs
            self.cash += amount
            self.equity += amount
            self.is_public = True

            # Gründer behält 70%, neue Investoren bekommen 30%
            founder = list(self.shares.keys())[0] if self.shares else "Founder"
            self.shares = {founder: 70.0, "Public_Investors": 30.0}

            self.calculate_enterprise_value()

            return True, f"IPO erfolgreich! €{amount:,.0f} aufgenommen (Kosten: €{ipo_costs:,.0f}). Firma ist jetzt börsennotiert"
        else:
            # Capital Raise (Kapitalerhöhung bei schon börsennotierten Firmen)
            # Kosten: 5% des aufgenommenen Kapitals
            raise_costs = amount * 0.05

            if self.cash < raise_costs:
                return False, f"Kapitalerhöhungs-Kosten zu hoch. Benötigt: €{raise_costs:,.0f}"

            self.cash -= raise_costs
            self.cash += amount
            self.equity += amount

            # Bestehende Anteile werden verwässert (simplified)
            dilution_factor = 0.9  # 10% Verwässerung
            for shareholder in self.shares:
                self.shares[shareholder] *= dilution_factor

            self.shares["New_Investors"] = self.shares.get("New_Investors", 0) + 10.0

            self.calculate_enterprise_value()

            return True, f"Kapitalerhöhung erfolgreich! €{amount:,.0f} aufgenommen (Kosten: €{raise_costs:,.0f})"

    def buyback_shares_to_go_private(self) -> tuple[bool, str]:
        """
        Aktienrückkauf um von der Börse zu gehen (Delisting)
        Kauft alle Anteile von Public_Investors und New_Investors zurück
        """
        if not self.is_public:
            return False, "Firma ist nicht börsennotiert"

        # Berechne Wert der öffentlichen Anteile
        public_shares = 0.0
        public_shareholders = []

        for shareholder, percentage in list(self.shares.items()):
            if shareholder in ["Public_Investors", "New_Investors"]:
                public_shares += percentage
                public_shareholders.append(shareholder)

        if public_shares == 0:
            # Keine öffentlichen Aktionäre mehr - einfach delisten
            self.is_public = False
            return True, "Firma ist jetzt privat (keine öffentlichen Aktionäre)"

        # Berechne Rückkaufpreis (Enterprise Value * Anteil + 20% Premium)
        self.calculate_enterprise_value()
        base_value = self.enterprise_value * (public_shares / 100.0)
        buyback_premium = 0.20  # 20% Premium für Rückkauf
        buyback_price = base_value * (1 + buyback_premium)

        # Transaktionskosten (5% für Banken, Anwälte, Delisting-Gebühren)
        transaction_costs = buyback_price * 0.05
        total_cost = buyback_price + transaction_costs

        # Prüfe ob genug Cash vorhanden
        if self.cash < total_cost:
            return False, f"Nicht genug Bargeld für Rückkauf. Benötigt: €{total_cost:,.0f}, Verfügbar: €{self.cash:,.0f}"

        # Führe Rückkauf durch
        self.cash -= total_cost

        # Entferne öffentliche Aktionäre
        for shareholder in public_shareholders:
            del self.shares[shareholder]

        # Normalisiere verbleibende Anteile auf 100%
        if self.shares:
            remaining_total = sum(self.shares.values())
            if remaining_total > 0:
                for shareholder in self.shares:
                    self.shares[shareholder] = (self.shares[shareholder] / remaining_total) * 100.0

        # Delisting
        self.is_public = False
        self.share_price = 0.0
        self.market_capitalization = 0.0

        return True, f"Rückkauf erfolgreich! {public_shares:.1f}% für €{buyback_price:,.0f} zurückgekauft (Kosten: €{transaction_costs:,.0f}). Firma ist jetzt privat"

    def generate_balance_sheet(self) -> Dict:
        """
        Generiert Bilanz (Balance Sheet) nach deutschem HGB

        AKTIVA (Assets)              |  PASSIVA (Liabilities + Equity)
        ---------------------------- | ------------------------------
        A. Anlagevermögen           |  A. Eigenkapital
        B. Umlaufvermögen           |  B. Fremdkapital
        """
        # AKTIVA
        anlagevermoegen_summe = self.buildings_value + self.machines_value + self.equipment_value

        anlagevermoegen = {
            "gebaeude": self.buildings_value,
            "maschinen": self.machines_value,
            "ausstattung": self.equipment_value,
            "summe": anlagevermoegen_summe
        }

        inventory_value = self.inventory_level * 30.0 * self.material_cost_reduction  # Material cost per unit
        umlaufvermoegen_summe = self.cash + inventory_value

        umlaufvermoegen = {
            "kasse_bank": self.cash,
            "vorraete": inventory_value,
            "summe": umlaufvermoegen_summe
        }

        aktiva_gesamt = anlagevermoegen_summe + umlaufvermoegen_summe

        # PASSIVA
        eigenkapital = {
            "gezeichnetes_kapital": self.equity,
            "gewinnruecklagen": self.retained_earnings,
            "jahresueberschuss": self.net_income,
            "summe": self.equity + self.retained_earnings
        }

        fremdkapital = {
            "langfristige_verbindlichkeiten": self.long_term_liabilities,
            "kurzfristige_verbindlichkeiten": self.current_liabilities,
            "summe": self.long_term_liabilities + self.current_liabilities
        }

        passiva_gesamt = eigenkapital["summe"] + fremdkapital["summe"]

        return {
            "aktiva": {
                "anlagevermoegen": anlagevermoegen,
                "umlaufvermoegen": umlaufvermoegen,
                "summe": aktiva_gesamt
            },
            "passiva": {
                "eigenkapital": eigenkapital,
                "fremdkapital": fremdkapital,
                "summe": passiva_gesamt
            },
            "bilanzsumme": aktiva_gesamt
        }

    def generate_income_statement(self) -> Dict:
        """
        Generiert Gewinn- und Verlustrechnung (GuV / P&L) nach deutschem HGB
        """
        return {
            "umsatzerloese": self.total_revenue,
            "variable_kosten": self.variable_costs_total,
            "deckungsbeitrag": self.contribution_margin_total,
            "fixkosten": self.fixed_costs_total,
            "ebitda": self.ebitda,
            "abschreibungen": self.cost_breakdown.get("depreciation", 0),
            "ebit": self.ebit,
            "zinsen": self.cost_breakdown.get("interest", 0),
            "ebt": self.ebit - self.cost_breakdown.get("interest", 0),
            "steuern": max(0, (self.ebit - self.cost_breakdown.get("interest", 0)) * 0.3333),
            "jahresueberschuss": self.net_income
        }

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
                "depreciation_buildings": round(self.cost_breakdown.get("depreciation_buildings", 0), 2),
                "depreciation_machines": round(self.cost_breakdown.get("depreciation_machines", 0), 2),
                "depreciation_equipment": round(self.cost_breakdown.get("depreciation_equipment", 0), 2),
                "overhead": round(self.cost_breakdown.get("overhead", 0), 2),
                "marketing": round(self.cost_breakdown.get("marketing", 0), 2),
                "rd": round(self.cost_breakdown.get("rd", 0), 2),
                "interest": round(self.cost_breakdown.get("interest", 0), 2),
                "efficiency_investments": round(self.cost_breakdown.get("efficiency_investments", 0), 2),
                "total": round(self.cost_breakdown.get("total", 0), 2)
            },
            "efficiency_factors": {
                "variable_cost_efficiency": round(self.variable_cost_efficiency, 3),
                "material_cost_reduction": round(self.material_cost_reduction, 3),
                "overhead_efficiency": round(self.overhead_efficiency, 3),
                "variable_cost_savings_percent": round((1.0 - self.variable_cost_efficiency) * 100, 1),
                "material_cost_savings_percent": round((1.0 - self.material_cost_reduction) * 100, 1),
                "overhead_savings_percent": round((1.0 - self.overhead_efficiency) * 100, 1)
            },
            "depreciation_rates": {
                "buildings": round(self.buildings_depreciation_rate * 100, 2),
                "machines": round(self.machines_depreciation_rate * 100, 2),
                "equipment": round(self.equipment_depreciation_rate * 100, 2)
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
            "m_and_a": {
                "shares": self.shares,
                "is_public": self.is_public,
                "share_price": round(self.share_price, 2),
                "market_capitalization": round(self.market_capitalization, 2),
                "enterprise_value": round(self.enterprise_value, 2),
                "is_bankrupt": self.is_bankrupt,
                "bankruptcy_quarter": self.bankruptcy_quarter,
                "major_shareholder": max(self.shares.items(), key=lambda x: x[1])[0] if self.shares else "Keine Eigentümer",
                "ownership_structure": "Privat" if not self.is_public else "Börsennotiert"
            },
            "machines": {
                "class": self.machine_class,
                "efficiency_factor": round(self.machines_efficiency_factor, 2),
                "energy_cost_factor": round(self.machine_energy_cost_factor, 2),
                "lot_capacity_per_quarter": MACHINE_LOT_CAPACITIES.get(self.machine_class, 400),
                "max_production_capacity_units": round(self.calculate_max_production_capacity(), 2),
                "max_production_capacity_lots": round(self.calculate_max_production_capacity() / UNITS_PER_LOT, 2),
                "next_upgrade_cost": 3_000_000 if self.machine_class == "basic" else (6_000_000 if self.machine_class == "professional" else 0)
            },
            "production": {
                "capacity_units": round(self.production_capacity, 2),
                "capacity_lots": round(self.get_production_in_lots(), 2),
                "inventory_units": round(self.inventory_level, 2),
                "inventory_lots": round(self.get_inventory_in_lots(), 2),
                "lot_size": UNITS_PER_LOT
            },
            "personnel": {
                "ungelernt": {
                    "count": self.personnel_ungelernt,
                    "cost_per_quarter": self.cost_ungelernt,
                    "productivity": self.productivity_ungelernt,
                    "total_cost": self.personnel_ungelernt * self.cost_ungelernt
                },
                "angelernt": {
                    "count": self.personnel_angelernt,
                    "cost_per_quarter": self.cost_angelernt,
                    "productivity": self.productivity_angelernt,
                    "total_cost": self.personnel_angelernt * self.cost_angelernt
                },
                "facharbeiter": {
                    "count": self.personnel_facharbeiter,
                    "cost_per_quarter": self.cost_facharbeiter,
                    "productivity": self.productivity_facharbeiter,
                    "total_cost": self.personnel_facharbeiter * self.cost_facharbeiter
                },
                "total_count": self.personnel_ungelernt + self.personnel_angelernt + self.personnel_facharbeiter,
                "total_cost": (self.personnel_ungelernt * self.cost_ungelernt +
                              self.personnel_angelernt * self.cost_angelernt +
                              self.personnel_facharbeiter * self.cost_facharbeiter)
            },
            "financing": {
                "loans": self.loans,
                "total_debt": round(self.debt, 2),
                "max_loan_capacity": round(self.max_loan_capacity, 2),
                "credit_rating": round(self.credit_rating, 2),
                "available_credit": round(self.max_loan_capacity - self.debt, 2)
            },
            "liquidity": {
                "liquidity_1": round(self.liquidity_1, 2) if self.liquidity_1 != float('inf') else None,
                "liquidity_2": round(self.liquidity_2, 2) if self.liquidity_2 != float('inf') else None,
                "liquidity_3": round(self.liquidity_3, 2) if self.liquidity_3 != float('inf') else None,
                "current_liabilities": round(self.current_liabilities, 2),
                "status": "HEALTHY" if (self.liquidity_1 == float('inf') or self.liquidity_1 >= 1.5) else ("GOOD" if self.liquidity_1 >= 1.0 else ("WARNING" if self.liquidity_1 >= 0.5 else "CRITICAL"))
            },
            "product": {
                "lifecycle_stage": self.product_lifecycle_stage,
                "age_quarters": self.product_age_quarters,
                "innovation_level": self.product_innovation_level,
                "innovation_investment": round(self.innovation_investment, 2),
                "stage_description": {
                    "introduction": "Produkteinführung - 70% Nachfrage",
                    "growth": "Wachstumsphase - 130% Nachfrage",
                    "maturity": "Reifephase - 100% Nachfrage",
                    "decline": "Rückgang - 60% Nachfrage"
                }.get(self.product_lifecycle_stage, "Unknown")
            },
            "balance_sheet": self.generate_balance_sheet(),
            "income_statement": self.generate_income_statement(),
            "contribution_margin": {
                "total": round(self.contribution_margin_total, 2),
                "per_unit": round(self.contribution_margin_per_unit, 2),
                "variable_costs": round(self.variable_costs_total, 2),
                "fixed_costs": round(self.fixed_costs_total, 2)
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

    def create_firm(self, firm_name: str, user_name: str, is_public: bool = False) -> BusinessFirm:
        """Erstellt eine neue Firma mit Aktien-Initialisierung"""
        firm = BusinessFirm(
            id=self.next_firm_id,
            name=firm_name,
            user_names=[user_name],  # Erster User wird hinzugefügt
            is_public=is_public
        )

        # AKTIEN-INITIALISIERUNG: Gründer erhält 100% der Anteile
        firm.shares = {user_name: 100.0}

        # Berechne initialen Unternehmenswert
        firm.calculate_enterprise_value()

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

    def enforce_kartellamt_regulations(self):
        """
        Kartellamt (Antitrust Authority) enforcement to prevent market dominance
        - Fines for dominant firms
        - Forced price reductions
        - Support for smaller firms
        - Potential forced divestitures
        """
        if not self.firms:
            return

        # Thresholds for intervention
        WARNING_THRESHOLD = 0.30    # 30% market share
        PENALTY_THRESHOLD = 0.40    # 40% market share
        CRITICAL_THRESHOLD = 0.50   # 50% market share

        kartellamt_actions = []

        for firm in self.firms.values():
            if firm.market_share < WARNING_THRESHOLD:
                # Small firms get subsidies to help competition
                if firm.market_share < 0.10 and firm.profit < 0:  # Struggling small firms
                    subsidy = min(50000, abs(firm.profit) * 0.5)
                    firm.cash += subsidy
                    kartellamt_actions.append(f"Mittelstandsförderung: {firm.name} erhält €{subsidy:,.0f} Subvention")
                continue

            # WARNING LEVEL: 30-40% market share
            if WARNING_THRESHOLD <= firm.market_share < PENALTY_THRESHOLD:
                warning_fine = firm.revenue * 0.02  # 2% of revenue
                firm.cash -= warning_fine
                kartellamt_actions.append(
                    f"[WARNUNG] Kartellamt: {firm.name} (Marktanteil {firm.market_share*100:.1f}%) - Warnung + €{warning_fine:,.0f} Bußgeld"
                )

            # PENALTY LEVEL: 40-50% market share
            elif PENALTY_THRESHOLD <= firm.market_share < CRITICAL_THRESHOLD:
                # Heavy fines
                penalty_fine = firm.revenue * 0.05  # 5% of revenue
                firm.cash -= penalty_fine

                # Force price reduction to help competitors
                if firm.price > 80:
                    old_price = firm.price
                    firm.price = max(80, firm.price * 0.90)  # 10% price reduction, minimum 80
                    kartellamt_actions.append(
                        f"[STRAFE] Kartellamt: {firm.name} (Marktanteil {firm.market_share*100:.1f}%) - €{penalty_fine:,.0f} Strafe + Preissenkung €{old_price:.2f} -> €{firm.price:.2f}"
                    )
                else:
                    kartellamt_actions.append(
                        f"[STRAFE] Kartellamt: {firm.name} (Marktanteil {firm.market_share*100:.1f}%) - €{penalty_fine:,.0f} Strafe"
                    )

            # CRITICAL LEVEL: 50%+ market share
            elif firm.market_share >= CRITICAL_THRESHOLD:
                # Extreme penalties
                critical_fine = firm.revenue * 0.10  # 10% of revenue
                firm.cash -= critical_fine

                # Forced price reduction
                if firm.price > 75:
                    old_price = firm.price
                    firm.price = max(75, firm.price * 0.85)  # 15% price reduction, maximum 75

                # Forced capacity reduction (simulate divestiture)
                if firm.machines > 5:
                    machines_to_remove = max(1, int(firm.machines * 0.10))  # Remove 10% of machines
                    firm.machines -= machines_to_remove
                    firm.max_capacity = firm.machines * 100

                    kartellamt_actions.append(
                        f"[ZERSCHLAGUNG] KARTELLAMT: {firm.name} (Marktanteil {firm.market_share*100:.1f}%) - €{critical_fine:,.0f} Strafe + Preissenkung €{old_price:.2f} -> €{firm.price:.2f} + Zwangsverkauf von {machines_to_remove} Maschinen"
                    )
                else:
                    kartellamt_actions.append(
                        f"[ZERSCHLAGUNG] KARTELLAMT: {firm.name} (Marktanteil {firm.market_share*100:.1f}%) - €{critical_fine:,.0f} Strafe + Preissenkung"
                    )

        # Print all enforcement actions
        if kartellamt_actions:
            print("\n" + "="*80)
            print("KARTELLAMT QUARTALSBERICHT")
            print("="*80)
            for action in kartellamt_actions:
                print(f"  {action}")
            print("="*80 + "\n")

    def advance_quarter(self):
        """Führt Quartalsabschluss für alle Firmen durch"""
        print(f"[DEBUG] ========== QUARTER {self.current_quarter + 1} STARTING ==========")
        print(f"[DEBUG] Total firms in game: {len(self.firms)}")

        # Bots treffen automatisch Entscheidungen
        self.make_bot_decisions()

        self.current_quarter += 1
        self.quarter_start_time = time.time()

        results = {}
        for firm_id, firm in self.firms.items():
            result = firm.calculate_quarterly_results()
            results[firm_id] = result
            print(f"[DEBUG] Firm {firm_id} ({firm.name}): Revenue={firm.revenue:.2f}, Profit={firm.profit:.2f}, Cash={firm.cash:.2f}")

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

        # KARTELLAMT ENFORCEMENT: Prevent market dominance
        self.enforce_kartellamt_regulations()

        # INSOLVENZ-MECHANIK: Erweitert nach deutschem Recht
        bankrupt_firms = []
        bankruptcy_results = {}
        for firm_id, firm in list(self.firms.items()):
            if firm.cash <= 0 and not firm.is_bankrupt:
                bankruptcy_info = firm.process_bankruptcy(self)
                bankrupt_firms.append(firm.name)
                bankruptcy_results[firm.name] = bankruptcy_info

                # Firma wird aus dem Markt entfernt nach Insolvenz-Abwicklung
                del self.firms[firm_id]

        if bankrupt_firms:
            print(f"💀 INSOLVENZEN: {', '.join(bankrupt_firms)}")
            for firm_name, info in bankruptcy_results.items():
                print(f"   {firm_name}: Insolvenzquote {info['creditor_quota']:.1f}%, Liquidationswert €{info['liquidation_value']:,.0f}")

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
                "id": firm.id,  # ADDED: Firm ID für Aufkauf-Funktionalität
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

        print(f"[DEBUG] create_bot_firms: Starting creation of {count} bots")
        print(f"[DEBUG] Firms before creation: {len(self.firms)}")

        bot_prefixes = ["Tech", "Innovation", "Global", "Market", "Digital", "Smart", "Future", "Quantum", "Cyber", "Mega"]
        bot_suffixes = ["Corp", "Industries", "Systems", "Solutions", "Dynamics", "Ventures", "Labs", "Group", "Partners", "Innovations"]
        strategies = ["Conservative", "Aggressive", "Balanced", "Risk-Taker", "Cautious"]

        created_count = 0
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
            created_count += 1
            print(f"[DEBUG] Created bot #{created_count}: ID={firm.id}, Name={firm_name}, User={bot_type}")

        print(f"[DEBUG] Firms after creation: {len(self.firms)}")
        print(f"[DEBUG] Successfully created {created_count} bot firms")

    def make_bot_decisions(self):
        """Lässt alle Bot-Firmen automatisch Entscheidungen treffen - MIT MARKTDATEN"""
        bot_count = 0
        print(f"[DEBUG] make_bot_decisions: Checking {len(self.firms)} firms")

        # MARKTANALYSE - Bots sehen dieselben Daten wie Spieler!
        all_firms = list(self.firms.values())
        active_firms = [f for f in all_firms if f.revenue > 0 or self.current_quarter == 0]

        # Durchschnittswerte berechnen
        avg_price = sum(f.product_price for f in active_firms) / len(active_firms) if active_firms else 120
        avg_capacity = sum(f.production_capacity for f in active_firms) / len(active_firms) if active_firms else 20000
        avg_marketing = sum(f.marketing_budget for f in active_firms) / len(active_firms) if active_firms else 50000
        avg_quality = sum(f.quality_level for f in active_firms) / len(active_firms) if active_firms else 5

        # Marktführer finden
        market_leader = max(active_firms, key=lambda f: f.market_share) if active_firms else None

        for firm in self.firms.values():
            # Check if it's a bot (user_name contains "Bot")
            if any("bot" in user.lower() for user in firm.user_names):
                bot_count += 1

                # BOT HAT ZUGRIFF AUF DIESELBEN DATEN WIE SPIELER:
                my_market_share = firm.market_share
                my_cash = firm.cash
                my_profit = firm.profit
                my_revenue = firm.revenue
                my_lifecycle_stage = firm.product_lifecycle_stage  # String: "introduction", "growth", "maturity", "decline"
                my_product_age = firm.product_age_quarters  # Alter des Produkts in Quartalen
                my_rank = sum(1 for f in all_firms if f.revenue > firm.revenue) + 1

                # NEUE LOGIK: Berechne maximale Produktionskapazität basierend auf Maschinen
                my_max_capacity = firm.calculate_max_production_capacity()

                # KARTELLAMT AWARENESS: Adjust strategy based on market dominance
                # Thresholds: 30% warning, 40% penalty, 50% critical
                kartellamt_risk = "NONE"
                if my_market_share >= 0.50:
                    kartellamt_risk = "CRITICAL"
                elif my_market_share >= 0.40:
                    kartellamt_risk = "PENALTY"
                elif my_market_share >= 0.30:
                    kartellamt_risk = "WARNING"
                elif my_market_share >= 0.25:
                    kartellamt_risk = "APPROACHING"

                # STRATEGISCHE ENTSCHEIDUNGEN basierend auf Marktposition
                if kartellamt_risk in ["CRITICAL", "PENALTY"]:
                    # DEFENSIVE: Reduce market aggression to avoid heavy Kartellamt penalties
                    # High prices, reduced capacity, lower marketing to lose market share intentionally
                    price = avg_price * random.uniform(1.15, 1.30)  # 15-30% over market (lose customers)
                    capacity = my_max_capacity * random.uniform(0.60, 0.75)  # Low production
                    marketing = min(my_cash * 0.08, random.uniform(20000, 40000))  # Minimal marketing
                    rd = min(my_cash * 0.15, random.uniform(80000, 150000))  # Focus on innovation instead
                    quality = random.randint(6, 8)
                    jit = random.uniform(20, 30)
                    strategy = f"KARTELLAMT_DEFENSIVE ({kartellamt_risk})"

                elif kartellamt_risk in ["WARNING", "APPROACHING"]:
                    # CAUTIOUS: Maintain position but don't grow aggressively
                    price = avg_price * random.uniform(1.05, 1.15)  # Slightly above market
                    capacity = my_max_capacity * random.uniform(0.80, 0.90)  # Moderate production
                    marketing = min(my_cash * 0.12, random.uniform(40000, 70000))
                    rd = min(my_cash * 0.10, random.uniform(40000, 80000))
                    quality = random.randint(6, 8)
                    jit = random.uniform(18, 28)
                    strategy = f"KARTELLAMT_CAUTIOUS ({kartellamt_risk})"

                elif my_market_share > 0.15 and my_cash > 3_000_000:
                    # MARKTFÜHRER-STRATEGIE: Premium Pricing, hohe Qualität, maximale Kapazitätsauslastung
                    price = avg_price * random.uniform(1.1, 1.25)  # 10-25% über Markt
                    capacity = my_max_capacity * random.uniform(0.95, 1.0)  # 95-100% Auslastung
                    marketing = min(my_cash * 0.20, random.uniform(80000, 150000))
                    rd = min(my_cash * 0.12, random.uniform(50000, 120000))
                    quality = random.randint(7, 9)
                    jit = random.uniform(15, 25)
                    strategy = "MARKET_LEADER"

                elif my_market_share < 3 and my_profit < 0:
                    # AGGRESSIVE GROWTH: Niedrige Preise, maximale Kapazität
                    price = avg_price * random.uniform(0.85, 0.95)  # 5-15% unter Markt
                    capacity = my_max_capacity * random.uniform(0.90, 1.0)  # 90-100% Auslastung
                    marketing = min(my_cash * 0.25, random.uniform(60000, 100000))
                    rd = min(my_cash * 0.05, random.uniform(20000, 50000))
                    quality = random.randint(4, 6)
                    jit = random.uniform(20, 30)
                    strategy = "AGGRESSIVE_GROWTH"

                elif my_cash < 500_000:
                    # SURVIVAL MODE: Kosten senken, reduzierte Kapazität
                    price = avg_price * random.uniform(1.0, 1.1)
                    capacity = my_max_capacity * random.uniform(0.60, 0.75)  # Nur 60-75% Auslastung (Kostensparen)
                    marketing = min(my_cash * 0.10, random.uniform(10000, 30000))
                    rd = min(my_cash * 0.02, random.uniform(5000, 15000))
                    quality = random.randint(4, 5)
                    jit = random.uniform(25, 35)
                    strategy = "SURVIVAL"

                elif my_lifecycle_stage == "decline" and my_cash > 5_000_000:
                    # INNOVATION NEEDED: Investiere in F&E für neues Produkt
                    price = avg_price * random.uniform(0.9, 1.0)
                    capacity = my_max_capacity * random.uniform(0.70, 0.85)  # Reduzierte Produktion während Transition
                    marketing = min(my_cash * 0.15, random.uniform(40000, 80000))
                    rd = min(my_cash * 0.20, random.uniform(100000, 200000))  # Hohe F&E!
                    quality = random.randint(5, 7)
                    jit = random.uniform(20, 30)
                    strategy = "INNOVATION_FOCUS"

                else:
                    # BALANCED STRATEGY: Moderate Kapazitätsauslastung
                    price = avg_price * random.uniform(0.95, 1.05)
                    capacity = my_max_capacity * random.uniform(0.80, 0.95)  # 80-95% Auslastung
                    marketing = min(my_cash * 0.15, random.uniform(40000, 80000))
                    rd = min(my_cash * 0.10, random.uniform(30000, 60000))
                    quality = int(avg_quality + random.uniform(-1, 1))
                    quality = max(4, min(9, quality))  # Clamp 4-9
                    jit = random.uniform(18, 28)
                    strategy = "BALANCED"

                # STRATEGISCHE HEBEL - Bots nutzen dieselben Optionen wie Spieler!
                # ABER: Viel konservativer um Bankrott zu vermeiden!

                # 1. MASCHINEN-UPGRADE (nur wenn sehr profitabel & viel Cash!)
                if my_cash > 6_000_000 and my_profit > 500_000 and self.current_quarter > 8 and firm.machine_class == "basic":
                    try:
                        firm.upgrade_machines("professional")
                        print(f"[DEBUG] Bot {firm.id}: Upgraded machines to PROFESSIONAL")
                    except Exception as e:
                        print(f"[ERROR] Bot {firm.id}: Machine upgrade failed: {e}")
                elif my_cash > 10_000_000 and my_profit > 800_000 and self.current_quarter > 12 and firm.machine_class == "professional":
                    try:
                        firm.upgrade_machines("premium")
                        print(f"[DEBUG] Bot {firm.id}: Upgraded machines to PREMIUM")
                    except Exception as e:
                        print(f"[ERROR] Bot {firm.id}: Machine upgrade failed: {e}")

                # 2. KREDITE AUFNEHMEN (nur im Notfall!)
                if my_cash < 300_000 and firm.credit_rating >= 0.7 and len(firm.loans) < 1 and my_revenue > 1_500_000:
                    try:
                        loan_amount = min(1_000_000, firm.max_loan_amount)  # Nur €1M max
                        firm.take_loan(loan_amount, quarters=12)
                        print(f"[DEBUG] Bot {firm.id}: EMERGENCY loan €{loan_amount:,.0f}")
                    except:
                        pass

                # 3. EIGENKAPITAL AUSGEBEN (sehr selten, nur wenn wirklich nötig!)
                if my_cash < 500_000 and my_revenue > 3_000_000 and not firm.is_public and my_profit > 200_000 and self.current_quarter > 6:
                    try:
                        firm.issue_shares(2_000_000)  # IPO - reduziert auf €2M
                        print(f"[DEBUG] Bot {firm.id}: IPO €2M")
                    except:
                        pass
                elif my_cash < 200_000 and firm.is_public and my_revenue > 4_000_000 and self.current_quarter > 10:
                    try:
                        firm.issue_shares(1_500_000)  # Capital raise - reduziert
                        print(f"[DEBUG] Bot {firm.id}: Capital raise €1.5M")
                    except:
                        pass

                # 4. PERSONAL - DEAKTIVIERT (zu teuer, Bots gehen bankrott!)
                # Bots nutzen nur das Start-Personal (100 Arbeiter)

                # 5. INNOVATION - DEAKTIVIERT (zu teuer!)
                # Nur wenn absolut nötig und sehr viel Cash

                # 6. PROZESS-OPTIMIERUNGEN - DEAKTIVIERT (zu teuer!)
                # Bots fokussieren sich auf Preis/Kapazität/Marketing/F&E
                # Keine teuren Investitionen in frühen Quartalen!

                print(f"[DEBUG] Bot {firm.id} ({firm.name}): {strategy} | Rank={my_rank}, Share={my_market_share:.1f}%, Price={price:.2f}, Cap={capacity:.0f}")
                firm.apply_decisions(price, capacity, marketing, rd, quality, jit)

        print(f"[DEBUG] Made decisions for {bot_count} bots out of {len(self.firms)} firms")

    def check_antitrust(self, acquirer_id: int, target_id: int, percentage: float) -> Dict:
        """Prüft kartellrechtliche Zulässigkeit einer Übernahme"""
        acquirer = self.get_firm_by_id(acquirer_id)
        target = self.get_firm_by_id(target_id)
        
        if not acquirer or not target:
            return {"allowed": False, "reason": "Firma nicht gefunden", "combined_market_share": 0}

        # Berechne hypothetischen Marktanteil
        # Wenn percentage < 100, addieren wir anteilig? Nein, Kartellrecht zählt oft Kontrolle.
        # Vereinfacht: Wir addieren die Marktanteile.
        current_share = acquirer.market_share
        target_share = target.market_share
        combined_share = current_share + target_share

        # Kartellrechtliche Schwellen
        DOMINANCE_THRESHOLD = 0.40  # 40% ist marktbeherrschend

        if combined_share >= DOMINANCE_THRESHOLD:
            return {
                "allowed": False,
                "reason": f"Marktbeherrschung ({combined_share*100:.1f}% > 40%)",
                "combined_market_share": combined_share * 100
            }
        
        return {
            "allowed": True,
            "reason": "Unbedenklich",
            "combined_market_share": combined_share * 100
        }

    def acquire_firm(self, acquirer_id: int, target_id: int, percentage: float = 100.0) -> Dict:
        """Führt eine Firmenübernahme durch"""
        acquirer = self.get_firm_by_id(acquirer_id)
        target = self.get_firm_by_id(target_id)
        
        if not acquirer or not target:
            raise ValueError("Firma nicht gefunden")
            
        if acquirer_id == target_id:
            raise ValueError("Selbstübernahme nicht möglich")

        # 1. Kartellprüfung
        antitrust = self.check_antitrust(acquirer_id, target_id, percentage)
        if not antitrust['allowed']:
            raise ValueError(f"Kartellamt untersagt Übernahme: {antitrust['reason']}")

        # 2. Kosten berechnen
        cost_info = self.calculate_acquisition_cost(target)
        acquisition_price = cost_info['total_cost'] * (percentage / 100.0)

        # 3. Finanzierungsprüfung
        if acquirer.cash < acquisition_price:
            raise ValueError(f"Nicht genug Bargeld. Benötigt: €{acquisition_price:,.2f}, Verfügbar: €{acquirer.cash:,.2f}")

        # 4. Durchführung
        acquirer.cash -= acquisition_price
        target_shareholders_cash = acquisition_price # Geht an die alten Eigentümer (aus dem System raus, oder an Bots)
        
        # Assets übertragen (anteilig)
        transfer_ratio = percentage / 100.0
        
        inventory_transfer = int(target.inventory_level * transfer_ratio)
        capacity_transfer = int(target.production_capacity * transfer_ratio)
        machines_transfer = int(target.machines * transfer_ratio)
        
        acquirer.inventory_level += inventory_transfer
        acquirer.production_capacity += capacity_transfer
        acquirer.machines += machines_transfer
        
        target.inventory_level -= inventory_transfer
        target.production_capacity -= capacity_transfer
        target.machines -= machines_transfer

        # Goodwill Berechnung (Kaufpreis - Buchwert des Anteils)
        book_value_share = target.equity * transfer_ratio
        goodwill = max(0, acquisition_price - book_value_share)

        return {
            "message": f"Übernahme von {percentage}% an {target.name} erfolgreich",
            "price": acquisition_price,
            "goodwill": goodwill,
            "new_cash": acquirer.cash
        }

    def calculate_acquisition_cost(self, target_firm: BusinessFirm) -> Dict:
        """Berechnet Aufkaufpreis basierend auf Unternehmenswert"""
        # BEWERTUNGSFORMEL - Berücksichtigt mehrere Faktoren:
        # 1. Cash + Inventarwert + Sachwerte (20% Premium)
        asset_value = target_firm.cash + (target_firm.inventory_level * 50) + (target_firm.machines_value + target_firm.buildings_value + target_firm.equipment_value)

        # 2. Umsatz-Multiplikator (1.5x Quartalsumsatz)
        revenue_value = target_firm.revenue * 1.5

        # 3. Eigenkapital mit Premium (10% Aufschlag)
        equity_value = target_firm.equity * 1.1

        # 4. Nehme das Maximum dieser Werte
        base_price = max(asset_value * 1.2, revenue_value, equity_value)

        # 5. Mindestpreis: €500k (damit Aufkauf sich lohnen muss)
        return max(base_price, 500_000)

    def acquire_firm(self, acquiring_firm_id: int, target_firm_id: int) -> Dict:
        """Firma kauft andere Firma auf (M&A)"""
        # Validierung
        if acquiring_firm_id == target_firm_id:
            raise ValueError("Eine Firma kann sich nicht selbst aufkaufen!")

        acquiring_firm = self.get_firm_by_id(acquiring_firm_id)
        target_firm = self.get_firm_by_id(target_firm_id)

        if not acquiring_firm:
            raise ValueError("Aufkaufende Firma nicht gefunden!")
        if not target_firm:
            raise ValueError("Ziel-Firma nicht gefunden!")

        if target_firm.is_bankrupt:
            raise ValueError("Firma ist bereits insolvent - kann nicht aufgekauft werden!")

        # Berechne Aufkaufpreis
        acquisition_cost = self.calculate_acquisition_cost(target_firm)

        # Prüfe ob genug Cash vorhanden
        if acquiring_firm.cash < acquisition_cost:
            raise ValueError(f"Nicht genug Cash! Benötigt: €{acquisition_cost:,.0f}, Verfügbar: €{acquiring_firm.cash:,.0f}")

        # TRANSAKTION DURCHFÜHREN:
        # 1. Zahle Aufkaufpreis
        acquiring_firm.cash -= acquisition_cost

        # 2. Übernehme Assets der Zielfirma
        acquiring_firm.inventory_level += target_firm.inventory_level
        acquiring_firm.production_capacity += target_firm.production_capacity

        # 3. Übernehme Sachwerte (Maschinen, Gebäude, Ausrüstung)
        acquiring_firm.machines_value += target_firm.machines_value
        acquiring_firm.buildings_value += target_firm.buildings_value
        acquiring_firm.equipment_value += target_firm.equipment_value

        # 4. Schulden werden NICHT übernommen (Asset Deal, kein Share Deal)
        # Debt bleibt beim Verkäufer

        # 5. Eigenkapital erhöhen um Nettowert der Assets
        net_asset_value = target_firm.cash + (target_firm.inventory_level * 50) + target_firm.machines_value + target_firm.buildings_value + target_firm.equipment_value - target_firm.debt
        acquiring_firm.equity += max(0, net_asset_value - acquisition_cost)

        # 6. Goodwill berechnen (Aufpreis über Buchwert)
        book_value = target_firm.equity
        goodwill = acquisition_cost - book_value

        # 7. Entferne Zielfirma aus dem Spiel
        acquisition_info = {
            "acquiring_firm": acquiring_firm.name,
            "target_firm": target_firm.name,
            "acquisition_cost": round(acquisition_cost, 2),
            "inventory_gained": round(target_firm.inventory_level, 0),
            "capacity_gained": round(target_firm.production_capacity, 0),
            "net_asset_value": round(net_asset_value, 2),
            "goodwill": round(goodwill, 2),
            "acquiring_firm_cash_after": round(acquiring_firm.cash, 2)
        }

        del self.firms[target_firm_id]

        print(f"🤝 M&A: {acquiring_firm.name} kauft {target_firm.name} für €{acquisition_cost:,.0f}")
        print(f"   Übernommene Assets: {target_firm.inventory_level:.0f} Einheiten Inventar, {target_firm.production_capacity:.0f} Kapazität")
        print(f"   Goodwill: €{goodwill:,.0f}")

        return acquisition_info
