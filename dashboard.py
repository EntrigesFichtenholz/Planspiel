"""
BWL Planspiel - Dash Frontend Dashboard
Nutzt fertige Dash Bootstrap Components
"""
import os
import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime
from state import game  # Direkter Zugriff auf den Spielstatus
from models import DecisionInput  # Für Typ-Sicherheit

# Dash App mit Bootstrap Theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    requests_pathname_prefix='/'
)

server = app.server

app.title = "BWL Planspiel"

# ============ HELPER FUNCTIONS ============

def format_de(value):
    """Formatiert Zahlen im deutschen Format (1.000.000 statt 1,000,000)"""
    return f"{value:,.0f}".replace(",", ".")

# ============ LAYOUT COMPONENTS ============

def create_header():
    """Header mit Titel und Quartals-Timer"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.H3("BWL Planspiel", className="text-white mb-0"), width="auto"),
                dbc.Col(
                    html.Div([
                        html.I(className="fas fa-clock me-2"),
                        html.Span(id="quarter-timer", className="fw-bold")
                    ], className="text-white"),
                    width="auto"
                ),
            ], align="center", className="g-4 w-100", justify="between"),
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-4"
    )


def create_login_form():
    """Login/Registrierungs-Formular mit zwei Tabs"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("BWL Planspiel - Anmeldung")),
                    dbc.CardBody([
                        dbc.Tabs([
                            # Tab 1: Firma erstellen
                            dbc.Tab(label="Neue Firma erstellen", children=[
                                html.Div([
                                    dbc.Input(
                                        id="input-user-name-create",
                                        placeholder="Dein Name",
                                        type="text",
                                        className="mb-3 mt-3"
                                    ),
                                    dbc.Input(
                                        id="input-firm-name",
                                        placeholder="Firmenname",
                                        type="text",
                                        className="mb-3"
                                    ),
                                    dbc.Button(
                                        "Firma Erstellen",
                                        id="btn-create-firm",
                                        color="primary",
                                        className="w-100"
                                    )
                                ])
                            ]),
                            # Tab 2: Firma beitreten
                            dbc.Tab(label="Firma beitreten", children=[
                                html.Div([
                                    dbc.Input(
                                        id="input-user-name-join",
                                        placeholder="Dein Name",
                                        type="text",
                                        className="mb-3 mt-3"
                                    ),
                                    html.Div(id="firms-list-container", className="mb-3"),
                                    dbc.Button(
                                        "Liste aktualisieren",
                                        id="btn-refresh-firms",
                                        color="secondary",
                                        className="w-100 mb-2",
                                        size="sm"
                                    ),
                                    dbc.Button(
                                        "Firma beitreten",
                                        id="btn-join-firm",
                                        color="success",
                                        className="w-100",
                                        disabled=True
                                    ),
                                    dcc.Store(id="selected-firm-id")
                                ])
                            ])
                        ]),
                        html.Div(id="login-feedback", className="mt-3")
                    ])
                ])
            ], width=8, lg=6, className="mx-auto")
        ], className="mt-5")
    ], fluid=True)


def create_dashboard_kpis(firm_data):
    """KPI Cards"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Bargeld", className="text-muted mb-1"),
                    html.H3(f"€{format_de(firm_data.get('cash', 0))}", className="mb-0"),
                    html.Small("Aktuell verfügbar", className="text-muted")
                ])
            ], className="shadow-sm")
        ], width=12, md=6, lg=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Marktanteil", className="text-muted mb-1"),
                    html.H3(f"{firm_data.get('market_share', 0) * 100:.2f}%", className="mb-0"),
                    html.Small("Markposition", className="text-muted")
                ])
            ], className="shadow-sm")
        ], width=12, md=6, lg=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("ROI", className="text-muted mb-1"),
                    html.H3(f"{firm_data.get('roi', 0):.1f}%", className="mb-0"),
                    html.Small("Return on Investment", className="text-muted")
                ])
            ], className="shadow-sm")
        ], width=12, md=6, lg=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Abschreibungen", className="text-muted mb-1"),
                    html.H3("€2.25M", className="mb-0"),
                    html.Small("Pro Quartal", className="text-muted")
                ])
            ], className="shadow-sm")
        ], width=12, md=6, lg=3),
    ], className="mb-4 g-3")


def create_current_settings_card(firm_data):
    """Zeigt die aktuell aktiven Einstellungen prominent an"""
    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-check-circle me-2 text-success"),
            "Aktuelle Einstellungen (Aktiv seit Q", firm_data.get('current_quarter', 0), ")"
        ])),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("Produktpreis", className="text-muted mb-1"),
                        html.H4(f"€{firm_data.get('product_price', 120):.2f}", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
                dbc.Col([
                    html.Div([
                        html.H6("Kapazität", className="text-muted mb-1"),
                        html.H4(f"{format_de(firm_data.get('production_capacity', 20000))}", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
                dbc.Col([
                    html.Div([
                        html.H6("Marketing", className="text-muted mb-1"),
                        html.H4(f"€{format_de(firm_data.get('marketing_budget', 30000))}", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("F&E Budget", className="text-muted mb-1"),
                        html.H4(f"€{format_de(firm_data.get('rd_budget', 0))}", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
                dbc.Col([
                    html.Div([
                        html.H6("Qualität", className="text-muted mb-1"),
                        html.H4(f"Level {firm_data.get('quality_level', 5)}/10", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
                dbc.Col([
                    html.Div([
                        html.H6("JIT Safety Stock", className="text-muted mb-1"),
                        html.H4(f"{firm_data.get('safety_stock_percentage', 20):.0f}%", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
            ])
        ])
    ], className="shadow-sm mb-4 border-success border-2")


def create_decision_form(firm_data):
    """Entscheidungs-Formular"""
    cash = firm_data.get('cash', 0)
    depr_rates = firm_data.get('depreciation_rates', {})

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-cogs me-2"),
            "Neue Entscheidungen eingeben (wirksam ab nächstem Quartal)"
        ])),
        dbc.CardBody([
            # Produktpreis
            dbc.Row([
                dbc.Col([
                    html.Label([
                        "Produktpreis ",
                        html.Span("(Min: €50, Max: €500)", className="text-danger fw-bold")
                    ]),
                    html.P(f"Aktuell: €{firm_data.get('product_price', 120):.2f}", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-price",
                        type="number",
                        value=firm_data.get('product_price', 120),
                        min=50, max=500, step=0.01,
                        className="border-primary"
                    )
                ], width=12, md=6, className="mb-3"),

                # Produktionskapazität
                dbc.Col([
                    html.Label([
                        "Produktionskapazität ",
                        html.Span("(Max: 120.000)", className="text-danger fw-bold")
                    ]),
                    html.P(f"Aktuell: {firm_data.get('production_capacity', 20000):.0f} Einheiten", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-capacity",
                        type="number",
                        value=firm_data.get('production_capacity', 20000),
                        min=0, max=500000, step=1000,  # Erhöht auf 500k (nach Aufkäufen möglich)
                        className="border-primary"
                    )
                ], width=12, md=6, className="mb-3"),
            ]),

            # Marketing Budget
            dbc.Row([
                dbc.Col([
                    html.Label([
                        "Marketing Budget ",
                        html.Span(f"(Max: €{format_de(firm_data.get('cash', 0) * 0.3)})", className="text-danger fw-bold")
                    ]),
                    html.P(f"Aktuell: €{format_de(firm_data.get('marketing_budget', 30000))} | Limit: 30% von Cash", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-marketing",
                        type="number",
                        value=firm_data.get('marketing_budget', 30000),
                        min=0,
                        step=1,
                        className="border-warning"
                    )
                ], width=12, md=6, className="mb-3"),

                # F&E Budget
                dbc.Col([
                    html.Label([
                        "F&E Budget ",
                        html.Span(f"(Max: €{format_de(firm_data.get('cash', 0) * 0.2)})", className="text-danger fw-bold")
                    ]),
                    html.P(f"Aktuell: €{format_de(firm_data.get('rd_budget', 0))} | Limit: 20% von Cash", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-rd",
                        type="number",
                        value=firm_data.get('rd_budget', 0),
                        min=0,
                        step=1,
                        className="border-warning"
                    )
                ], width=12, md=6, className="mb-3"),
            ]),

            # Qualitätslevel & JIT
            dbc.Row([
                dbc.Col([
                    html.Label("Qualitätslevel (1-10)"),
                    html.P(f"Aktuell: Level {firm_data.get('quality_level', 5)} von 10", className="small text-muted mb-1"),
                    dcc.Slider(
                        id="input-quality",
                        min=1, max=10, step=1,
                        value=firm_data.get('quality_level', 5),
                        marks={i: str(i) for i in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=12, md=6, className="mb-3"),

                dbc.Col([
                    html.Label("JIT-Strategie (% Sicherheitsbestand)"),
                    html.P(f"Aktuell: {firm_data.get('safety_stock_percentage', 20):.1f}% (0% = Pure JIT)", className="small text-muted mb-1"),
                    dcc.Slider(
                        id="input-jit",
                        min=0, max=100, step=5,
                        value=firm_data.get('safety_stock_percentage', 20),
                        marks={i: f"{i}%" for i in range(0, 101, 20)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=12, md=6, className="mb-3"),
            ]),

            html.H6("Kostenoptimierungs-Investitionen", className="mt-4 mb-3"),

            # Prozessoptimierung
            html.Label("Prozessoptimierung (€5M → -5% variable Kosten)"),
            dbc.Input(
                id="input-process-opt",
                type="number",
                value=0,
                min=0,
                step=1,
                className="mb-2"
            ),
            html.Small(f"Max: 10% von Cash = €{format_de(cash * 0.1)}", className="text-muted d-block mb-3"),

            # Lieferantenverhandlungen
            html.Label("Lieferantenverhandlungen (€3M → -5% Materialkosten)"),
            dbc.Input(
                id="input-supplier-neg",
                type="number",
                value=0,
                min=0,
                step=1,
                className="mb-2"
            ),
            html.Small(f"Max: 10% von Cash", className="text-muted d-block mb-3"),

            # Verwaltungsoptimierung
            html.Label("Verwaltungsoptimierung (€4M → -10% Overhead)"),
            dbc.Input(
                id="input-overhead-red",
                type="number",
                value=0,
                min=0,
                step=1,
                className="mb-2"
            ),
            html.Small(f"Max: 10% von Cash", className="text-muted d-block mb-3"),

            html.H6("Abschreibungsraten anpassen (in % pro Quartal)", className="mt-4 mb-3"),

            # Gebäude
            html.Label("AfA-Rate Gebäude (%)"),
            dbc.Input(
                id="input-buildings-depr",
                type="number",
                value=depr_rates.get('buildings', 0.5),
                min=0.1,
                max=5.0,
                step=0.1,
                className="mb-2"
            ),
            html.Small(f"Aktuell: {depr_rates.get('buildings', 0.5):.2f}% (0.1% - 5.0%)", className="text-muted d-block mb-3"),

            # Maschinen
            html.Label("AfA-Rate Maschinen (%)"),
            dbc.Input(
                id="input-machines-depr",
                type="number",
                value=depr_rates.get('machines', 1.0),
                min=0.1,
                max=5.0,
                step=0.1,
                className="mb-2"
            ),
            html.Small(f"Aktuell: {depr_rates.get('machines', 1.0):.2f}%", className="text-muted d-block mb-3"),

            # Ausstattung
            html.Label("AfA-Rate Ausstattung (%)"),
            dbc.Input(
                id="input-equipment-depr",
                type="number",
                value=depr_rates.get('equipment', 1.0),
                min=0.1,
                max=5.0,
                step=0.1,
                className="mb-2"
            ),
            html.Small(f"Aktuell: {depr_rates.get('equipment', 1.0):.2f}%", className="text-muted d-block mb-3"),

            dbc.Button(
                [html.I(className="fas fa-check me-2"), "Entscheidungen Anwenden"],
                id="btn-submit-decision",
                color="success",
                size="lg",
                className="w-100 mt-3"
            ),
            html.Div(id="decision-feedback", className="mt-3")
        ])
    ], className="shadow-sm mb-4")


def create_cost_info():
    """Kosten-Informationen"""
    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-info-circle me-2"),
            "Kostenstruktur & Spielmechanik (BWL-Planspiel)"
        ])),
        dbc.CardBody([
            dbc.Accordion([
                dbc.AccordionItem([
                    html.H6("Fixkosten pro Quartal:", className="mb-2"),
                    html.Ul([
                        html.Li("Abschreibungen: €0/Q (AfA Gebäude: €250,000, Maschinen: €1,250,000, Ausstattung: €750,000)"),
                        html.Li("Zinsen auf FK: €0/Q (10% p.a. = 2.5% p.Q.)")
                    ], className="mb-0")
                ], title="Fixkosten pro Quartal"),

                dbc.AccordionItem([
                    html.Ul([
                        html.Li("Materialkosten: ~€300,000,000/Q bei Vollauslastung"),
                        html.Li("Produktionskosten: Abhängig von Kapazitätsauslastung (50-100%)"),
                        html.Li("Lagerkosten: 2.0% des Lagerwertes pro Quartal")
                    ], className="mb-0")
                ], title="Variable Kosten"),

                dbc.AccordionItem([
                    html.Ul([
                        html.Li("Marketing-Effizienz: 1M€ → +0.5% Marktanteil (logarithmische Sättigung ab 50M€)"),
                        html.Li("F&E-Mechanik: Qualität Level 5/10 → Preispremium +0-25%"),
                        html.Li("F&E-Kosten: Level 6 kostet €12,000,000")
                    ], className="mb-0")
                ], title="Investitionen & Effekte"),

                dbc.AccordionItem([
                    html.Ul([
                        html.Li("Sicherheitsbestand 20.0%: Lagerkosten vs. Lieferrisiko"),
                        html.Li("Bei 0% Safety Stock: Umsatzverlust möglich"),
                        html.Li("10-15% Safety Stock = Best Practice")
                    ], className="mb-0")
                ], title="JIT-Strategie & Risikomanagement"),

                dbc.AccordionItem([
                    html.Ul([
                        html.Li("Marktpreis: €100 (Basis)"),
                        html.Li("+10% Preis → -15% Absatz (elastisch)"),
                        html.Li("Level 5 → bis +12.5% Preisaufschlag")
                    ], className="mb-0")
                ], title="Preisoptimierung"),
            ], start_collapsed=True)
        ])
    ], className="shadow-sm mb-4")


def create_market_table(market_data, current_firm_id=None):
    """Marktübersicht Tabelle (ohne Buttons - M&A über separates Interface)"""

    # Handle both dict (API format) and list (direct game.get_market_overview())
    firms = market_data.get('firms', []) if isinstance(market_data, dict) else market_data

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-chart-line me-2"),
            "Marktübersicht"
        ])),
        dbc.CardBody([
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Rang"),
                    html.Th("Firma"),
                    html.Th("Spieler"),
                    html.Th("Marktanteil"),
                    html.Th("Umsatz"),
                    html.Th("Gewinn"),
                    html.Th("ROI"),
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(f"#{firm['rank']}"),
                        html.Td(firm['name']),
                        html.Td(", ".join(firm['user_names'])),
                        html.Td(f"{firm['market_share']:.2f}%"),
                        html.Td(f"€{format_de(firm['revenue'])}"),
                        html.Td(f"€{format_de(firm['profit'])}"),
                        html.Td(f"{firm['roi']:.1f}%"),
                    ]) for firm in firms
                ])
            ], bordered=True, hover=True, responsive=True, striped=True)
        ])
    ], className="shadow-sm")


def create_financial_trends_chart(firm_data):
    """Finanztrends (Live-Charts)"""
    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-chart-area me-2"),
            "Finanztrends (Live)"
        ])),
        dbc.CardBody([
            dcc.Graph(
                id="financial-trends-chart",
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ], className="shadow-sm mb-4")


def create_production_inventory_status(firm_data):
    """Produktion & Lagerbestand (Live)"""
    inventory = firm_data.get('inventory_level', 0)
    capacity = firm_data.get('production_capacity', 0)

    # Gauge für Lagerbestand
    inventory_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=inventory,
        title={'text': "Lagerbestand (Einheiten)"},
        delta={'reference': capacity * 0.2},
        gauge={
            'axis': {'range': [None, capacity]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, capacity * 0.1], 'color': "red"},
                {'range': [capacity * 0.1, capacity * 0.3], 'color': "orange"},
                {'range': [capacity * 0.3, capacity], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': capacity * 0.1
            }
        }
    ))
    inventory_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))

    # Produktionskapazität Bar
    production_bar = go.Figure(go.Bar(
        x=['Kapazität'],
        y=[capacity],
        text=[f'{format_de(capacity)} Einheiten'],
        textposition='auto',
        marker_color='steelblue'
    ))
    production_bar.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False,
        yaxis_title="Einheiten"
    )

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-industry me-2"),
            "Produktion & Lagerbestand"
        ])),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=inventory_gauge,
                        config={'displayModeBar': False}
                    )
                ], width=12, md=6),
                dbc.Col([
                    html.Div([
                        html.H6("Produktionsmetriken (Quartal)", className="text-muted mb-3"),
                        html.Div(id="live-status-display", children=[
                            html.P([
                                html.Strong("Produzierte Einheiten: "),
                                html.Span(f"{format_de(firm_data.get('production_capacity', 0))} Stück", className="text-primary")
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Verkaufte Einheiten: "),
                                html.Span(f"{format_de(firm_data.get('units_sold', 0))} Stück", className="text-success")
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Kapazitätsauslastung: "),
                                html.Span(f"{firm_data.get('efficiency_ratios', {}).get('capacity_utilization', 0):.1f}%", className="text-info")
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Lagerbestand: "),
                                f"{format_de(firm_data.get('inventory_level', 0))} Einheiten"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Lagerumschlag: "),
                                f"{firm_data.get('efficiency_ratios', {}).get('inventory_turnover', 0):.2f}x"
                            ], className="mb-2"),
                        ])
                    ])
                ], width=12, md=6),
            ])
        ])
    ], className="shadow-sm mb-4")


def create_market_volume_card():
    """Marktvolumen-Übersicht"""
    try:
        # Direkter Zugriff auf Game State
        market_data = game.get_market_overview()

        # market_data ist bereits die Liste der Firmen
        firms = market_data
        total_market_volume = sum(f.get('revenue', 0) for f in firms)
        num_competitors = len(firms)

        # Calculate market growth (would need historical data, for now show current volume)
        avg_revenue_per_firm = total_market_volume / num_competitors if num_competitors > 0 else 0

        return dbc.Card([
            dbc.CardHeader(html.H5([
                html.I(className="fas fa-chart-line me-2"),
                "Gesamtmarkt-Übersicht"
            ])),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H6("Marktvolumen Gesamt", className="text-muted mb-1"),
                            html.H3(f"€{format_de(total_market_volume)}", className="text-success mb-0")
                        ])
                    ], width=12, md=4, className="mb-3"),
                    dbc.Col([
                        html.Div([
                            html.H6("Anzahl Wettbewerber", className="text-muted mb-1"),
                            html.H3(f"{num_competitors}", className="text-info mb-0")
                        ])
                    ], width=12, md=4, className="mb-3"),
                    dbc.Col([
                        html.Div([
                            html.H6("Ø Umsatz pro Firma", className="text-muted mb-1"),
                            html.H3(f"€{format_de(avg_revenue_per_firm)}", className="text-warning mb-0")
                        ])
                    ], width=12, md=4, className="mb-3"),
                ])
            ])
        ], className="shadow-sm mb-4")
    except Exception as e:
        return dbc.Alert(f"Marktdaten konnten nicht geladen werden: {str(e)}", color="warning")


def create_market_volume_graph():
    """Marktvolumen über Zeit - Zeigt Gesamtmarktentwicklung"""
    try:
        # Hole alle Firmen direkt aus dem Speicher
        firms = game.firms.values()

        # Sammle alle Quarter-Revenue Daten von allen Firmen
        all_quarters = set()
        firm_histories = {}

        for firm in firms:
            # history ist direkt verfügbar im Objekt
            history = firm.history

            if history:
                # History ist eine Liste von Dicts
                firm_histories[firm.name] = {h['quarter']: h['revenue'] for h in history}
                all_quarters.update(h['quarter'] for h in history)

        if not all_quarters:
            return dbc.Alert("Noch keine historischen Daten verfügbar", color="info", className="mb-4")

        # Sortiere Quartale
        quarters = sorted(list(all_quarters))

        # Berechne Gesamtmarktvolumen pro Quartal
        total_market_volumes = []
        for q in quarters:
            total = sum(firm_histories[firm_name].get(q, 0) for firm_name in firm_histories)
            total_market_volumes.append(total)

        # Erstelle Plotly Line Chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=quarters,
            y=total_market_volumes,
            mode='lines+markers',
            name='Gesamtmarktvolumen',
            line=dict(color='steelblue', width=3),
            marker=dict(size=10, color='steelblue'),
            fill='tozeroy',
            fillcolor='rgba(70, 130, 180, 0.2)'
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Quartal",
            yaxis_title="Marktvolumen (€)",
            hovermode='x unified',
            showlegend=False
        )

        return dbc.Card([
            dbc.CardHeader(html.H5([
                html.I(className="fas fa-chart-area me-2"),
                "Marktvolumen-Entwicklung"
            ])),
            dbc.CardBody([
                dcc.Graph(
                    figure=fig,
                    config={'displayModeBar': False}
                )
            ])
        ], className="shadow-sm mb-4")

    except Exception as e:
        return dbc.Alert(f"Fehler beim Laden der Marktdaten: {str(e)}", color="danger", className="mb-4")


def create_cost_structure_card(firm_data):
    """Kostenstruktur & Spielmechanik - Detaillierte Ansicht wie in PDF"""
    costs = firm_data.get('costs', {})
    efficiency = firm_data.get('efficiency_factors', {})
    depr_rates = firm_data.get('depreciation_rates', {})
    assets = firm_data.get('assets', {})

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-calculator me-2"),
            "Kostenstruktur & Spielmechanik (BWL-Planspiel)"
        ])),
        dbc.CardBody([
            # Fixkosten pro Quartal
            html.H6("Fixkosten pro Quartal:", className="text-primary fw-bold mb-3"),
            dbc.Alert([
                html.Strong("Abschreibungen: "),
                f"{format_de(costs.get('depreciation', 0))}/Q (AfA Geb\u00e4ude: {format_de(costs.get('depreciation_buildings', 0))}, "
                f"Maschinen: {format_de(costs.get('depreciation_machines', 0))}, "
                f"Ausstattung: {format_de(costs.get('depreciation_equipment', 0))})",
                html.Br(),
                html.Small([
                    f"Raten: Geb\u00e4ude {depr_rates.get('buildings', 0.5):.2f}%, "
                    f"Maschinen {depr_rates.get('machines', 1.0):.2f}%, "
                    f"Ausstattung {depr_rates.get('equipment', 1.0):.2f}%"
                ], className="text-muted")
            ], color="info", className="mb-2"),

            dbc.Alert([
                html.Strong("Zinsen auf FK: "),
                f"{format_de(costs.get('interest', 0))}/Q (10% p.a. = 2.5% p.Q.)"
            ], color="info", className="mb-3"),

            # Variable Kosten
            html.H6("Variable Kosten:", className="text-primary fw-bold mb-3"),
            dbc.Alert([
                html.Strong("Materialkosten: "),
                f"~{format_de(costs.get('variable', 0) * 0.6)}/Q bei aktueller Produktion",
                html.Br(),
                html.Small([
                    f"Effizienz: {efficiency.get('material_cost_savings_percent', 0):.1f}% Einsparung "
                    f"(Faktor: {efficiency.get('material_cost_reduction', 1.0):.3f})"
                ], className="text-success" if efficiency.get('material_cost_savings_percent', 0) > 0 else "text-muted")
            ], color="light", className="mb-2"),

            dbc.Alert([
                html.Strong("Produktionskosten: "),
                f"Abh\u00e4ngig von Kapazit\u00e4tsauslastung (~{format_de(costs.get('variable', 0) * 0.4)}/Q)",
                html.Br(),
                html.Small([
                    f"Effizienz: {efficiency.get('variable_cost_savings_percent', 0):.1f}% Einsparung "
                    f"(Faktor: {efficiency.get('variable_cost_efficiency', 1.0):.3f})"
                ], className="text-success" if efficiency.get('variable_cost_savings_percent', 0) > 0 else "text-muted")
            ], color="light", className="mb-2"),

            dbc.Alert([
                html.Strong("Lagerkosten: "),
                f"{format_de(costs.get('inventory', 0))}/Q (2.0% des Lagerwertes pro Quartal)"
            ], color="light", className="mb-3"),

            dbc.Alert([
                html.Strong("Gemeinkosten: "),
                f"{format_de(costs.get('overhead', 0))}/Q",
                html.Br(),
                html.Small([
                    f"Effizienz: {efficiency.get('overhead_savings_percent', 0):.1f}% Einsparung "
                    f"(Faktor: {efficiency.get('overhead_efficiency', 1.0):.3f})"
                ], className="text-success" if efficiency.get('overhead_savings_percent', 0) > 0 else "text-muted")
            ], color="light", className="mb-3"),

            # Investitionen & Effekte
            html.H6("Investitionen & Effekte:", className="text-primary fw-bold mb-3"),
            dbc.Alert([
                html.Strong("Marketing-Effizienz: "),
                f"1M \u2192 +0.5% Marktanteil (logarithmische S\u00e4ttigung ab 50M)",
                html.Br(),
                html.Small(f"Aktuelles Budget: {format_de(costs.get('marketing', 0))}/Q", className="text-muted")
            ], color="success", className="mb-2"),

            dbc.Alert([
                html.Strong("F&E-Mechanik: "),
                f"Qualit\u00e4t Level {firm_data.get('quality_level', 5)}/10 \u2192 Preispremium +0-25%",
                html.Br(),
                html.Small("Level 6 kostet 12.000.000", className="text-muted")
            ], color="success", className="mb-2"),

            # JIT-Strategie
            html.H6("JIT-Strategie & Risikomanagement:", className="text-primary fw-bold mb-3"),
            dbc.Alert([
                html.Strong(f"Sicherheitsbestand {firm_data.get('safety_stock_percentage', 20):.1f}%: "),
                "Lagerkosten vs. Lieferrisiko",
                html.Br(),
                html.Small("Bei 0% Safety Stock: Umsatzverlust m\u00f6glich", className="text-warning"),
                html.Br(),
                html.Small("10-15% Safety Stock = Best Practice", className="text-success")
            ], color="warning", className="mb-3"),

            # Preisoptimierung
            html.H6("Preisoptimierung:", className="text-primary fw-bold mb-3"),
            dbc.Alert([
                html.Strong("Marktpreis: "),
                "100 (Basis)",
                html.Br(),
                html.Strong("Preis-Absatz-Funktion: "),
                "+10% Preis \u2192 -15% Absatz (elastisch)",
                html.Br(),
                html.Strong("Qualit\u00e4tspr\u00e4mie: "),
                f"Level {firm_data.get('quality_level', 5)} \u2192 bis +{firm_data.get('quality_level', 5) * 1.25:.1f}% Preisaufschlag"
            ], color="info", className="mb-2"),

        ])
    ], className="shadow-sm mb-4")


def create_shares_overview_card(firm_data):
    """Aktien-Übersicht & Eigentümerstruktur"""
    m_and_a = firm_data.get('m_and_a', {})
    shares = m_and_a.get('shares', {})
    is_public = m_and_a.get('is_public', False)
    enterprise_value = m_and_a.get('enterprise_value', 0)
    major_shareholder = m_and_a.get('major_shareholder', 'Unbekannt')

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-chart-pie me-2"),
            "Aktien & Eigentümerstruktur"
        ])),
        dbc.CardBody([
            # Status
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("Unternehmenswert", className="text-muted mb-1"),
                        html.H4(f"€{format_de(enterprise_value)}", className="text-success mb-0")
                    ])
                ], width=6, className="mb-3"),
                dbc.Col([
                    html.Div([
                        html.H6("Status", className="text-muted mb-1"),
                        html.H4(
                            "Börsennotiert" if is_public else "Privat",
                            className="text-info mb-0"
                        )
                    ])
                ], width=6, className="mb-3"),
            ]),

            # Eigentümerstruktur
            html.H6("Eigentümerstruktur:", className="text-primary fw-bold mb-3 mt-3"),

            # Shares als Balken-Diagramm
            html.Div([
                html.Div([
                    html.Div([
                        html.Strong(f"{owner}: "),
                        html.Span(f"{percentage:.1f}%", className="text-success ms-2")
                    ], className="d-flex justify-content-between mb-2"),
                    dbc.Progress(
                        value=percentage,
                        max=100,
                        color="success" if percentage >= 50 else "info",
                        className="mb-3",
                        style={"height": "25px"}
                    )
                ]) for owner, percentage in sorted(shares.items(), key=lambda x: x[1], reverse=True)
            ] if shares else [html.P("Keine Eigentümer definiert", className="text-muted")]),

            # Mehrheitsaktionär
            html.Div([
                html.Hr(),
                html.P([
                    html.Strong("Mehrheitsaktionär: "),
                    html.Span(major_shareholder, className="text-primary")
                ], className="mb-0")
            ])
        ])
    ], className="shadow-sm mb-4")


def create_acquisition_card(firm_id):
    """M&A - Unternehmensübernahme Interface"""
    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-handshake me-2"),
            "M&A - Unternehmensübernahme"
        ])),
        dbc.CardBody([
            html.P("Übernehmen Sie andere Firmen (Kartellamt prüft automatisch)", className="text-muted mb-3"),

            # Ziel-Firma auswählen (wird dynamisch via Callback aktualisiert)
            html.Label("Ziel-Firma auswählen:", className="fw-bold mb-2"),
            html.Div(
                id="acquisition-target-container",
                children=[
                    dcc.Dropdown(
                        id="acquisition-target-select",
                        options=[],  # Wird via Callback gefüllt
                        value=None,
                        placeholder="Firma auswählen...",
                        className="mb-3",
                        clearable=False,
                        searchable=True
                    )
                ]
            ),

                # Anteil wählen
                html.Label("Anteil kaufen (%):"),
                dbc.Input(
                    id="acquisition-percentage",
                    type="number",
                    min=1,
                    max=100,
                    step=1,
                    value=51,
                    className="mb-3"
                ),

                # Bewertung anzeigen Button
                dbc.Button(
                    [html.I(className="fas fa-calculator me-2"), "Bewertung berechnen"],
                    id="btn-calculate-valuation",
                    color="info",
                    className="w-100 mb-3"
                ),

                # Bewertungs-Ergebnis
                html.Div(id="valuation-result", className="mb-3"),

                # Kartellamt-Prüfung
                html.Div(id="antitrust-check", className="mb-3"),

                # Übernahme durchführen Button
                dbc.Button(
                    [html.I(className="fas fa-gavel me-2"), "Übernahme durchführen"],
                    id="btn-execute-acquisition",
                    color="warning",
                    className="w-100",
                    disabled=True
                ),

                # Ergebnis
                html.Div(id="acquisition-result", className="mt-3")
            ])
        ], className="shadow-sm mb-4")


def create_machine_upgrade_card(firm_data):
    """Maschinensystem - Upgrade Interface"""
    machines = firm_data.get('machines', {})
    current_class = machines.get('class', 'basic')
    efficiency = machines.get('efficiency_factor', 0.8)
    energy_factor = machines.get('energy_cost_factor', 1.2)
    next_upgrade_cost = machines.get('next_upgrade_cost', 0)

    class_info = {
        'basic': {'color': 'secondary', 'name': 'Basic Machines', 'next': 'Professional'},
        'professional': {'color': 'primary', 'name': 'Professional Machines', 'next': 'Premium'},
        'premium': {'color': 'success', 'name': 'Premium Machines', 'next': None}
    }

    info = class_info.get(current_class, class_info['basic'])

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-industry me-2"),
            "Maschinen-Upgrade System"
        ])),
        dbc.CardBody([
            dbc.Alert([
                html.H6("Aktuelle Maschinenklasse:", className="mb-2"),
                html.H4(info['name'], className=f"text-{info['color']} mb-2"),
                html.P([
                    html.Strong("Effizienz: "), f"{efficiency:.2f}x",
                    html.Br(),
                    html.Strong("Energiekosten: "), f"{energy_factor:.2f}x"
                ], className="mb-0")
            ], color=info['color'], className="mb-3"),

            html.Div([
                html.H6("Upgrade verfügbar:" if info['next'] else "Maximale Stufe erreicht", className="mb-2"),
                html.P(f"Nächstes Upgrade: {info['next']}" if info['next'] else "Keine weiteren Upgrades", className="mb-2"),
                html.P(f"Kosten: €{format_de(next_upgrade_cost)}" if next_upgrade_cost > 0 else "", className="text-warning fw-bold mb-3"),

                dbc.Button(
                    [html.I(className="fas fa-arrow-up me-2"), f"Upgrade zu {info['next']}"],
                    id="btn-upgrade-machines",
                    color="warning",
                    className="w-100",
                    disabled=(info['next'] is None)
                ) if info['next'] else html.P("Alle Upgrades abgeschlossen!", className="text-success"),

                html.Div(id="machine-upgrade-feedback", className="mt-3")
            ])
        ])
    ], className="shadow-sm mb-4")


def create_financing_card(firm_data, loan_amount=500000, loan_quarters=12, shares_amount=1000000):
    """Finanzierungs-Interface: Kredite & Eigenkapitalerhöhung"""
    financing = firm_data.get('financing', {})
    loans = financing.get('loans', [])
    total_debt = financing.get('total_debt', 0)
    max_capacity = financing.get('max_loan_capacity', 5000000)
    available = financing.get('available_credit', 0)
    credit_rating = financing.get('credit_rating', 1.0)
    estimated_rate = financing.get('estimated_interest_rate', 10.0)

    is_public = firm_data.get('m_and_a', {}).get('is_public', False)

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-money-bill-wave me-2"),
            "Finanzierung & Kapitalbeschaffung"
        ])),
        dbc.CardBody([
            # Kreditübersicht
            html.H6("Kredit-Übersicht:", className="text-primary mb-2"),
            dbc.Alert([
                html.P([
                    html.Strong("Gesamtverschuldung: "), f"€{format_de(total_debt)}"
                ], className="mb-1"),
                html.P([
                    html.Strong("Verfügbares Kreditlimit: "), f"€{format_de(available)}"
                ], className="mb-1"),
                html.P([
                    html.Strong("Bonität: "), f"{credit_rating:.2f} / 1.5"
                ], className="mb-1"),
                html.P([
                    html.Strong("Geschätzter Zinssatz: "), f"{estimated_rate:.1f}% p.a."
                ], className="mb-0")
            ], color="info", className="mb-3"),

            # Laufende Kredite
            html.H6(f"Laufende Kredite ({len(loans)}):", className="mb-2") if loans else html.P("Keine laufenden Kredite", className="text-muted mb-3"),

            html.Div([
                dbc.Alert([
                    html.Small(f"Betrag: €{format_de(loan.get('amount', 0))} | Zinssatz: {loan.get('interest_rate', 0)*100:.1f}% p.a. | Restlaufzeit: {loan.get('quarters_remaining', 0)} Q", className="mb-0")
                ], color="light", className="mb-2")
                for loan in loans
            ]) if loans else None,

            html.Hr(),

            # Kredit aufnehmen
            html.H6("Neuen Kredit aufnehmen:", className="text-primary mb-2"),
            html.Label("Kreditbetrag (€):"),
            dbc.Input(
                id="input-loan-amount",
                type="number",
                value=loan_amount,
                min=100000,
                max=available,
                step=100000,
                className="mb-2"
            ),
            html.Small(f"Max: €{format_de(available)}", className="text-muted d-block mb-2"),

            html.Label("Laufzeit (Quartale):"),
            dbc.Select(
                id="input-loan-quarters",
                options=[
                    {"label": "4 Quartale (1 Jahr)", "value": 4},
                    {"label": "8 Quartale (2 Jahre)", "value": 8},
                    {"label": "12 Quartale (3 Jahre)", "value": 12},
                    {"label": "16 Quartale (4 Jahre)", "value": 16},
                    {"label": "20 Quartale (5 Jahre)", "value": 20}
                ],
                value=loan_quarters,
                className="mb-3"
            ),

            dbc.Button(
                [html.I(className="fas fa-hand-holding-usd me-2"), "Kredit aufnehmen"],
                id="btn-take-loan",
                color="primary",
                className="w-100 mb-3"
            ),

            html.Hr(),

            # Eigenkapitalerhöhung
            html.H6("Eigenkapitalerhöhung:", className="text-primary mb-2"),
            html.P("Status: " + ("Börsennotiert" if is_public else "Privat"), className="mb-2"),

            html.Label("Kapitalbetrag (€):"),
            dbc.Input(
                id="input-shares-amount",
                type="number",
                value=shares_amount,
                min=500000,
                max=10000000,
                step=500000,
                className="mb-2"
            ),
            html.Small("IPO-Kosten: 10% | Capital Raise: 5%", className="text-muted d-block mb-3"),

            dbc.Button(
                [html.I(className="fas fa-chart-line me-2"), "IPO durchführen" if not is_public else "Kapitalerhöhung"],
                id="btn-issue-shares",
                color="success",
                className="w-100"
            ),

            html.Div(id="financing-feedback", className="mt-3")
        ])
    ], className="shadow-sm mb-4")


def create_personnel_card(firm_data, hire_qual="angelernt", hire_count=5, fire_qual="ungelernt", fire_count=5):
    """Personal-Management Interface"""
    personnel = firm_data.get('personnel', {})
    total_count = personnel.get('total_count', 0)
    total_cost = personnel.get('total_cost', 0)

    ungelernt = personnel.get('ungelernt', {})
    angelernt = personnel.get('angelernt', {})
    facharbeiter = personnel.get('facharbeiter', {})

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-users me-2"),
            "Personal-Management"
        ])),
        dbc.CardBody([
            dbc.Alert([
                html.P([
                    html.Strong("Gesamt-Mitarbeiter: "), f"{total_count}",
                    html.Br(),
                    html.Strong("Personalkosten/Quartal: "), f"€{format_de(total_cost)}"
                ], className="mb-0")
            ], color="info", className="mb-3"),

            # Personal-Übersicht
            html.H6("Aktuelle Belegschaft:", className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Ungelernt", className="text-muted"),
                            html.H4(f"{ungelernt.get('count', 0)}", className="text-secondary"),
                            html.Small(f"€{format_de(ungelernt.get('cost_per_quarter', 0))}/Q | {ungelernt.get('productivity', 0):.0%} Produktivität", className="text-muted")
                        ])
                    ], className="mb-2")
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Angelernt", className="text-muted"),
                            html.H4(f"{angelernt.get('count', 0)}", className="text-primary"),
                            html.Small(f"€{format_de(angelernt.get('cost_per_quarter', 0))}/Q | {angelernt.get('productivity', 0):.0%} Produktivität", className="text-muted")
                        ])
                    ], className="mb-2")
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Facharbeiter", className="text-muted"),
                            html.H4(f"{facharbeiter.get('count', 0)}", className="text-success"),
                            html.Small(f"€{format_de(facharbeiter.get('cost_per_quarter', 0))}/Q | {facharbeiter.get('productivity', 0):.0%} Produktivität", className="text-muted")
                        ])
                    ], className="mb-2")
                ], width=4),
            ]),

            html.Hr(),

            # Personal einstellen
            html.H6("Personal einstellen:", className="text-success mb-2"),
            html.Label("Qualifikation:"),
            dbc.Select(
                id="input-hire-qualification",
                options=[
                    {"label": "Ungelernt (€8k/Q, 70% Produktivität)", "value": "ungelernt"},
                    {"label": "Angelernt (€12k/Q, 100% Produktivität)", "value": "angelernt"},
                    {"label": "Facharbeiter (€18k/Q, 140% Produktivität)", "value": "facharbeiter"}
                ],
                value=hire_qual,
                className="mb-2"
            ),
            html.Label("Anzahl:"),
            dbc.Input(
                id="input-hire-count",
                type="number",
                value=hire_count,
                min=1,
                max=50,
                step=1,
                className="mb-3"
            ),
            dbc.Button(
                [html.I(className="fas fa-user-plus me-2"), "Einstellen"],
                id="btn-hire-personnel",
                color="success",
                className="w-100 mb-3"
            ),

            html.Hr(),

            # Personal entlassen
            html.H6("Personal entlassen:", className="text-danger mb-2"),
            html.Label("Qualifikation:"),
            dbc.Select(
                id="input-fire-qualification",
                options=[
                    {"label": "Ungelernt", "value": "ungelernt"},
                    {"label": "Angelernt", "value": "angelernt"},
                    {"label": "Facharbeiter", "value": "facharbeiter"}
                ],
                value=fire_qual,
                className="mb-2"
            ),
            html.Label("Anzahl:"),
            dbc.Input(
                id="input-fire-count",
                type="number",
                value=fire_count,
                min=1,
                max=20,
                step=1,
                className="mb-3"
            ),
            html.Small("Abfindung: 1 Quartalsgehalt", className="text-muted d-block mb-3"),
            dbc.Button(
                [html.I(className="fas fa-user-minus me-2"), "Entlassen"],
                id="btn-fire-personnel",
                color="danger",
                className="w-100"
            ),

            html.Div(id="personnel-feedback", className="mt-3")
        ])
    ], className="shadow-sm mb-4")


def create_innovation_card(firm_data, innovation_amount=1000000):
    """Innovation & Produktlebenszyklus Interface"""
    product = firm_data.get('product', {})
    lifecycle_stage = product.get('lifecycle_stage', 'introduction')
    age_quarters = product.get('age_quarters', 0)
    innovation_level = product.get('innovation_level', 1)
    innovation_investment = product.get('innovation_investment', 0)
    stage_desc = product.get('stage_description', '')

    stage_colors = {
        'introduction': 'warning',
        'growth': 'success',
        'maturity': 'primary',
        'decline': 'danger'
    }

    stage_names = {
        'introduction': 'Einführung',
        'growth': 'Wachstum',
        'maturity': 'Reife',
        'decline': 'Rückgang'
    }

    color = stage_colors.get(lifecycle_stage, 'secondary')
    name = stage_names.get(lifecycle_stage, lifecycle_stage)

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-lightbulb me-2"),
            "Innovation & Produktlebenszyklus"
        ])),
        dbc.CardBody([
            dbc.Alert([
                html.H6("Aktuelles Produkt:", className="mb-2"),
                html.H4(f"Generation {innovation_level}", className="mb-2"),
                html.P([
                    html.Strong("Lebenszyklusphase: "), name,
                    html.Br(),
                    html.Strong("Alter: "), f"{age_quarters} Quartale"
                ], className="mb-0")
            ], color=color, className="mb-3"),

            html.P(stage_desc, className="mb-3"),

            # Lifecycle-Fortschritt
            html.H6("Lifecycle-Fortschritt:", className="mb-2"),
            dbc.Progress(
                value=min(100, (age_quarters / 25) * 100),
                label=f"{age_quarters} Q",
                color=color,
                className="mb-3",
                style={"height": "30px"}
            ),

            html.Hr(),

            # Innovation investieren
            html.H6("Innovation investieren:", className="text-primary mb-2"),
            html.P("Bei €5M Investment: Neues Produkt (Generation+1)", className="small text-muted mb-2"),

            dbc.Alert([
                html.P([
                    html.Strong("Bereits investiert: "), f"€{format_de(innovation_investment)}",
                    html.Br(),
                    html.Strong("Noch benötigt: "), f"€{format_de(max(0, 5000000 - innovation_investment))}"
                ], className="mb-0")
            ], color="light", className="mb-3"),

            html.Label("Investment-Betrag (€):"),
            dbc.Input(
                id="input-innovation-amount",
                type="number",
                value=innovation_amount,
                min=100000,
                max=5000000,
                step=100000,
                className="mb-3"
            ),

            dbc.Button(
                [html.I(className="fas fa-flask me-2"), "Innovation investieren"],
                id="btn-invest-innovation",
                color="primary",
                className="w-100"
            ),

            html.Div(id="innovation-feedback", className="mt-3")
        ])
    ], className="shadow-sm mb-4")


def create_balance_sheet_card(firm_data, active_tab="tab-0"):
    """Bilanz & GuV Anzeige"""
    balance_sheet = firm_data.get('balance_sheet', {})
    income_statement = firm_data.get('income_statement', {})

    aktiva = balance_sheet.get('aktiva', {})
    passiva = balance_sheet.get('passiva', {})

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-file-invoice me-2"),
            "Bilanz & GuV (Jahresabschluss)"
        ])),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(label="Bilanz", tab_id="tab-0", children=[
                    html.Div([
                        html.H6("AKTIVA (Assets)", className="text-primary mt-3 mb-2"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("Anlagevermögen"),
                                    html.Span(f"€{format_de(aktiva.get('anlagevermoegen', {}).get('summe', 0))}", className="float-end")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Small([
                                    "  - Gebäude: €", format_de(aktiva.get('anlagevermoegen', {}).get('gebaeude', 0))
                                ])
                            ], className="ps-4"),
                            dbc.ListGroupItem([
                                html.Small([
                                    "  - Maschinen: €", format_de(aktiva.get('anlagevermoegen', {}).get('maschinen', 0))
                                ])
                            ], className="ps-4"),
                            dbc.ListGroupItem([
                                html.Small([
                                    "  - Ausstattung: €", format_de(aktiva.get('anlagevermoegen', {}).get('ausstattung', 0))
                                ])
                            ], className="ps-4"),

                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("Umlaufvermögen"),
                                    html.Span(f"€{format_de(aktiva.get('umlaufvermoegen', {}).get('summe', 0))}", className="float-end")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Small([
                                    "  - Kasse/Bank: €", format_de(aktiva.get('umlaufvermoegen', {}).get('kasse_bank', 0))
                                ])
                            ], className="ps-4"),
                            dbc.ListGroupItem([
                                html.Small([
                                    "  - Vorräte: €", format_de(aktiva.get('umlaufvermoegen', {}).get('vorraete', 0))
                                ])
                            ], className="ps-4"),

                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("SUMME AKTIVA", className="text-success"),
                                    html.Span(f"€{format_de(balance_sheet.get('bilanzsumme', 0))}", className="float-end fw-bold text-success")
                                ])
                            ], color="light"),
                        ], className="mb-3"),

                        html.H6("PASSIVA (Liabilities & Equity)", className="text-primary mb-2"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("Eigenkapital"),
                                    html.Span(f"€{format_de(passiva.get('eigenkapital', {}).get('summe', 0))}", className="float-end")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("Fremdkapital"),
                                    html.Span(f"€{format_de(passiva.get('fremdkapital', {}).get('summe', 0))}", className="float-end")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("SUMME PASSIVA", className="text-success"),
                                    html.Span(f"€{format_de(passiva.get('summe', 0))}", className="float-end fw-bold text-success")
                                ])
                            ], color="light"),
                        ]),
                    ], className="p-2")
                ]),

                dbc.Tab(label="GuV (P&L)", tab_id="tab-1", children=[
                    html.Div([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div([
                                    "Umsatzerlöse",
                                    html.Span(f"€{format_de(income_statement.get('umsatzerloese', 0))}", className="float-end text-success")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    "- Variable Kosten",
                                    html.Span(f"€{format_de(income_statement.get('variable_kosten', 0))}", className="float-end text-danger")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("= Deckungsbeitrag"),
                                    html.Span(f"€{format_de(income_statement.get('deckungsbeitrag', 0))}", className="float-end fw-bold")
                                ])
                            ], color="light"),
                            dbc.ListGroupItem([
                                html.Div([
                                    "- Fixkosten",
                                    html.Span(f"€{format_de(income_statement.get('fixkosten', 0))}", className="float-end text-danger")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("= EBITDA"),
                                    html.Span(f"€{format_de(income_statement.get('ebitda', 0))}", className="float-end fw-bold text-info")
                                ])
                            ], color="light"),
                            dbc.ListGroupItem([
                                html.Div([
                                    "- Abschreibungen",
                                    html.Span(f"€{format_de(income_statement.get('abschreibungen', 0))}", className="float-end text-danger")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("= EBIT"),
                                    html.Span(f"€{format_de(income_statement.get('ebit', 0))}", className="float-end fw-bold text-primary")
                                ])
                            ], color="light"),
                            dbc.ListGroupItem([
                                html.Div([
                                    "- Zinsen",
                                    html.Span(f"€{format_de(income_statement.get('zinsen', 0))}", className="float-end text-danger")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("= EBT"),
                                    html.Span(f"€{format_de(income_statement.get('ebt', 0))}", className="float-end fw-bold")
                                ])
                            ], color="light"),
                            dbc.ListGroupItem([
                                html.Div([
                                    "- Steuern (33.33%)",
                                    html.Span(f"€{format_de(income_statement.get('steuern', 0))}", className="float-end text-danger")
                                ])
                            ]),
                            dbc.ListGroupItem([
                                html.Div([
                                    html.Strong("= Jahresüberschuss", className="text-success"),
                                    html.Span(f"€{format_de(income_statement.get('jahresueberschuss', 0))}", className="float-end fw-bold text-success")
                                ])
                            ], color="success"),
                        ], className="mt-3")
                    ], className="p-2")
                ]),

                dbc.Tab(label="Deckungsbeitrag", tab_id="tab-2", children=[
                    html.Div([
                        dbc.Alert([
                            html.H6("Deckungsbeitragsrechnung", className="mb-3"),
                            html.P([
                                html.Strong("Deckungsbeitrag gesamt: "),
                                f"€{format_de(firm_data.get('contribution_margin', {}).get('total', 0))}"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Deckungsbeitrag pro Einheit: "),
                                f"€{firm_data.get('contribution_margin', {}).get('per_unit', 0):.2f}"
                            ], className="mb-2"),
                            html.Hr(),
                            html.P([
                                html.Strong("Variable Kosten gesamt: "),
                                f"€{format_de(firm_data.get('contribution_margin', {}).get('variable_costs', 0))}"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Fixkosten gesamt: "),
                                f"€{format_de(firm_data.get('contribution_margin', {}).get('fixed_costs', 0))}"
                            ], className="mb-0")
                        ], color="info", className="mt-3")
                    ], className="p-2")
                ])
            ], id="balance-sheet-tabs", active_tab=active_tab)
        ])
    ], className="shadow-sm mb-4")


def create_liquidity_warning_card(firm_data):
    """Liquiditäts-Warning System"""
    liquidity = firm_data.get('liquidity', {})
    liq1 = liquidity.get('liquidity_1')  # None wenn unendlich
    liq2 = liquidity.get('liquidity_2')  # None wenn unendlich
    liq3 = liquidity.get('liquidity_3')  # None wenn unendlich
    status = liquidity.get('status', 'HEALTHY')

    status_colors = {
        'HEALTHY': 'success',
        'GOOD': 'primary',
        'WARNING': 'warning',
        'CRITICAL': 'danger'
    }

    status_icons = {
        'HEALTHY': 'fas fa-check-circle',
        'GOOD': 'fas fa-info-circle',
        'WARNING': 'fas fa-exclamation-triangle',
        'CRITICAL': 'fas fa-exclamation-circle'
    }

    color = status_colors.get(status, 'secondary')
    icon = status_icons.get(status, 'fas fa-question-circle')

    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className=f"{icon} me-2"),
            "Liquiditäts-Monitoring"
        ]), className=f"bg-{color} text-white"),
        dbc.CardBody([
            dbc.Alert([
                html.H4(status, className="mb-2"),
                html.P("Liquiditätslage Ihres Unternehmens", className="mb-0")
            ], color=color, className="mb-3"),

            # Liquiditätsgrade
            html.H6("Liquiditätsgrade:", className="mb-3"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong("Liquidität 1° (Barliquidität)"),
                        html.Span(f"{liq1:.2f}" if liq1 is not None else "∞", className="float-end")
                    ]),
                    dbc.Progress(
                        value=min(100, liq1 * 50) if liq1 is not None else 100,
                        color="success" if liq1 is None or liq1 >= 1.0 else "danger",
                        className="mt-2",
                        style={"height": "10px"}
                    )
                ]),
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong("Liquidität 2° (Einzugsbedingt)"),
                        html.Span(f"{liq2:.2f}" if liq2 is not None else "∞", className="float-end")
                    ]),
                    dbc.Progress(
                        value=min(100, liq2 * 50) if liq2 is not None else 100,
                        color="success" if liq2 is None or liq2 >= 1.0 else "warning",
                        className="mt-2",
                        style={"height": "10px"}
                    )
                ]),
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong("Liquidität 3° (Umsatzbedingt)"),
                        html.Span(f"{liq3:.2f}" if liq3 is not None else "∞", className="float-end")
                    ]),
                    dbc.Progress(
                        value=min(100, liq3 * 25) if liq3 is not None else 100,
                        color="success" if liq3 is None or liq3 >= 2.0 else "warning",
                        className="mt-2",
                        style={"height": "10px"}
                    )
                ]),
            ], className="mb-3"),

            # Empfehlungen
            html.H6("Empfehlungen:", className="mb-2"),
            html.Ul([
                html.Li(rec) for rec in liquidity.get('recommendations', []) if rec
            ]) if any(liquidity.get('recommendations', [])) else html.P("Keine Handlungsempfehlungen", className="text-muted"),

            # Interpretationen
            html.Small([
                html.P("Liquidität 1°: Cash / kurzfr. Verbindlichkeiten (Ziel: >1.0)", className="mb-1 text-muted"),
                html.P("Liquidität 2°: (Cash + Forderungen) / kurzfr. Verbindlichkeiten (Ziel: >1.0)", className="mb-1 text-muted"),
                html.P("Liquidität 3°: (Cash + Forderungen + Vorräte) / kurzfr. Verbindlichkeiten (Ziel: >2.0)", className="mb-0 text-muted")
            ])
        ])
    ], className="shadow-sm mb-4")


def create_dashboard_layout(firm_id, firm_data):
    """Main Dashboard Layout mit Live-Updates"""
    # Extract historical data from firm_data
    history = firm_data.get('history', [])
    historical_data = {
        "quarters": [h['quarter'] for h in history],
        "revenue": [h['revenue'] for h in history],
        "profit": [h['profit'] for h in history],
        "cash": [h['cash'] for h in history]
    }

    return html.Div([
        create_header(),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H4(f"Dashboard - {firm_data.get('name', 'Firma')}", className="mb-0"),
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-circle text-success me-2", id="connection-status"),
                        html.Small("Live verbunden", id="connection-text", className="text-muted me-3"),
                        dbc.Button(
                            [html.I(className="fas fa-sign-out-alt me-1"), "Firma verlassen"],
                            id="btn-leave-firm",
                            color="danger",
                            size="sm",
                            outline=True
                        )
                    ], className="d-flex align-items-center")
                ], width="auto", className="text-end"),
            ], justify="between", className="mb-4"),

            # KPIs - werden live aktualisiert
            html.Div(id="kpi-container", children=create_dashboard_kpis(firm_data)),

            # Liquiditäts-Warning (prominent oben) - LIVE UPDATE
            html.Div(id="liquidity-warning-container", children=create_liquidity_warning_card(firm_data)),

            # Finanztrends Chart - LIVE UPDATE
            html.Div(id="financial-trends-container", children=create_financial_trends_chart(firm_data)),

            dbc.Row([
                # Linke Spalte: Operatives & Entscheidungen
                dbc.Col([
                    # Aktuelle Einstellungen (prominent)
                    html.Div(id="current-settings-container", children=create_current_settings_card(firm_data)),

                    # Entscheidungsformular
                    create_decision_form(firm_data),
                    
                    # Produktion & Lagerbestand
                    create_production_inventory_status(firm_data),

                    # Maschinen-Upgrade
                    html.Div(id="machines-container", children=create_machine_upgrade_card(firm_data)),
                    
                    # Innovation
                    html.Div(id="innovation-container", children=create_innovation_card(firm_data)),
                    
                    create_cost_info(),
                ], width=12, lg=6),

                # Rechte Spalte: Finanzen, HR & M&A
                dbc.Col([
                    # Finanzierung (Kredite & Eigenkapital)
                    html.Div(id="financing-container", children=create_financing_card(firm_data)),

                    # Personal-Management
                    html.Div(id="personnel-container", children=create_personnel_card(firm_data)),

                    # M&A-Übernahme Interface
                    create_acquisition_card(firm_id),
                    
                    # Aktien-Übersicht
                    create_shares_overview_card(firm_data),
                    
                    # Marktvolumen-Übersicht & Graph
                    create_market_volume_card(),
                    create_market_volume_graph(),
                ], width=12, lg=6),
            ]),
            
            html.Hr(className="my-4"),
            html.H4("Berichte & Marktdaten", className="mb-3 text-center"),

            # Untere Zeile: Tabellen & Detaillierte Daten (Volle Breite / Mittig)
            dbc.Row([
                dbc.Col([
                    # Marktübersicht Tabelle
                    html.Div(id="market-overview-container", children=create_market_table({"firms": []})),
                ], width=12, lg=6),
                
                dbc.Col([
                    # Bilanz & GuV
                    html.Div(id="balance-sheet-container", children=create_balance_sheet_card(firm_data)),
                    
                    # Kostenstruktur
                    html.Div(id="cost-structure-container", children=create_cost_structure_card(firm_data)),
                ], width=12, lg=6),
            ]),

            # Hidden stores
            dcc.Store(id="firm-id-store", data=firm_id),
            dcc.Store(id="historical-data-store", data=historical_data),  # Initialize with history from backend
            dcc.Interval(id="refresh-interval", interval=5000, n_intervals=0),  # 5s refresh for data
            dcc.Interval(id="timer-interval", interval=1000, n_intervals=0),  # 1s refresh for timer
        ], fluid=True)
    ])


# ============ MAIN APP LAYOUT ============

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),  # Disable full page refresh - use callbacks instead
    dcc.Store(id="session-store", storage_type='session'),  # Session storage - cleared on tab close
    html.Div(id="page-content")
])


# ============ CALLBACKS ============

@app.callback(
    Output("quarter-timer", "children"),
    Input("timer-interval", "n_intervals")
)
def update_timer_only(n):
    """Sekündliches Update nur für den Timer"""
    try:
        # Direkter Zugriff
        time_left = game.get_time_remaining()
        quarter = game.current_quarter
        
        minutes = time_left // 60
        seconds = time_left % 60
        return f"Quartal {quarter} | {minutes:02d}:{seconds:02d} bis zum nächsten Quartal"
    except:
        return "Verbindung..."


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"),
     Input("session-store", "data")]
)
def display_page(pathname, session_data):
    """Route between login and dashboard"""
    if session_data and session_data.get("firm_id"):
        # Fetch firm data directly
        try:
            firm = game.get_firm_by_id(session_data['firm_id'])
            if firm:
                return create_dashboard_layout(session_data["firm_id"], firm.to_dict())
            return create_login_form()
        except:
            return create_login_form()
    return create_login_form()


@app.callback(
    [Output("session-store", "data"),
     Output("login-feedback", "children")],
    Input("btn-create-firm", "n_clicks"),
    [State("input-user-name-create", "value"),
     State("input-firm-name", "value")],
    prevent_initial_call=True
)
def create_firm(n_clicks, user_name, firm_name):
    """Create firm callback"""
    if not user_name or not firm_name:
        return dash.no_update, dbc.Alert("Bitte alle Felder ausfüllen", color="warning")

    try:
        # Check duplicate
        if game.get_firm_by_user(user_name):
            return dash.no_update, dbc.Alert("User bereits registriert", color="warning")

        firm = game.create_firm(firm_name, user_name)
        
        # Wir müssen hier manuell keine Broadcasts machen, da das Dashboard sich selbst updated
        # und die API für andere Clients zuständig wäre.
        
        return {"firm_id": firm.id}, dbc.Alert("Firma erfolgreich erstellt!", color="success")
    except Exception as e:
        return dash.no_update, dbc.Alert(f"Fehler: {str(e)}", color="danger")


@app.callback(
    Output("firms-list-container", "children"),
    [Input("btn-refresh-firms", "n_clicks"),
     Input("url", "pathname")],
    prevent_initial_call=False
)
def load_firms_list(n_clicks, pathname):
    """Load list of available firms"""
    try:
        firms_data = []
        for firm in game.firms.values():
            firms_data.append({
                "id": firm.id,
                "name": firm.name,
                "user_count": len(firm.user_names),
                "market_share": round(firm.market_share * 100, 2),
                "cash": round(firm.cash, 0)
            })

        if not firms_data:
            return dbc.Alert("Noch keine Firmen vorhanden", color="info", className="mt-2")

        # Create radio options with firm details
        options = []
        for firm in firms_data:
            label = html.Div([
                html.Strong(firm["name"]),
                html.Br(),
                html.Small([
                    f"Mitglieder: {firm['user_count']} | ",
                    f"Marktanteil: {firm['market_share']}% | ",
                    f"Cash: €{format_de(firm['cash'])}"
                ], className="text-muted")
            ])
            options.append({
                "label": firm["name"] + f" ({firm['user_count']} Mitglieder)",
                "value": firm["id"]
            })

        return dbc.RadioItems(
            id="firm-selector",
            options=options,
            value=None,
            className="mb-3"
        )
    except Exception as e:
        return dbc.Alert(f"Fehler: {str(e)}", color="danger")


@app.callback(
    [Output("selected-firm-id", "data"),
     Output("btn-join-firm", "disabled")],
    Input("firm-selector", "value"),
    prevent_initial_call=True
)
def select_firm(firm_id):
    """Handle firm selection"""
    if firm_id:
        return firm_id, False  # Enable join button
    return None, True  # Disable join button


@app.callback(
    [Output("session-store", "data", allow_duplicate=True),
     Output("login-feedback", "children", allow_duplicate=True)],
    Input("btn-join-firm", "n_clicks"),
    [State("input-user-name-join", "value"),
     State("selected-firm-id", "data")],
    prevent_initial_call=True
)
def join_firm(n_clicks, user_name, firm_id):
    """Join existing firm callback"""
    if not user_name:
        return dash.no_update, dbc.Alert("Bitte Namen eingeben", color="warning")

    if not firm_id:
        return dash.no_update, dbc.Alert("Bitte Firma auswählen", color="warning")

    try:
        # Check duplicate
        if game.get_firm_by_user(user_name):
            return dash.no_update, dbc.Alert("User bereits in einer Firma", color="warning")

        success = game.add_user_to_firm(firm_id, user_name)
        if success:
            return {"firm_id": firm_id}, dbc.Alert("Erfolgreich beigetreten!", color="success")
        else:
            return dash.no_update, dbc.Alert("Fehler beim Beitreten", color="danger")
    except Exception as e:
        return dash.no_update, dbc.Alert(f"Fehler: {str(e)}", color="danger")


@app.callback(
    Output("decision-feedback", "children"),
    Input("btn-submit-decision", "n_clicks"),
    [State("firm-id-store", "data"),
     State("input-price", "value"),
     State("input-capacity", "value"),
     State("input-marketing", "value"),
     State("input-rd", "value"),
     State("input-quality", "value"),
     State("input-jit", "value"),
     State("input-process-opt", "value"),
     State("input-supplier-neg", "value"),
     State("input-overhead-red", "value"),
     State("input-buildings-depr", "value"),
     State("input-machines-depr", "value"),
     State("input-equipment-depr", "value")],
    prevent_initial_call=True
)
def submit_decision(n_clicks, firm_id, price, capacity, marketing, rd, quality, jit,
                    process_opt, supplier_neg, overhead_red, buildings_depr, machines_depr, equipment_depr):
    """Submit decision callback mit Validierung"""
    # Hole aktuelle Firma für Validierung
    try:
        # Create decision object
        decision = DecisionInput(
            product_price=price,
            production_capacity=capacity,
            marketing_budget=marketing,
            rd_budget=rd,
            quality_level=quality,
            jit_safety_stock=jit,
            process_optimization=process_opt or 0,
            supplier_negotiation=supplier_neg or 0,
            overhead_reduction=overhead_red or 0,
            buildings_depreciation=buildings_depr,
            machines_depreciation=machines_depr,
            equipment_depreciation=equipment_depr
        )

        result = game.process_decision(firm_id, decision)
        
        success_msg = html.Div([
            html.H6("Erfolgreich gespeichert!", className="text-success mb-2"),
            html.P("Deine Entscheidungen werden im nächsten Quartal wirksam.", className="mb-0")
        ])
        return dbc.Alert(success_msg, color="success", dismissable=True, duration=4000)

    except Exception as e:
        return dbc.Alert(f"Fehler: {str(e)}", color="danger")


@app.callback(
    [Output("kpi-container", "children"),
     Output("current-settings-container", "children"),
     Output("market-overview-container", "children"),
     Output("live-status-display", "children"),
     Output("connection-status", "className"),
     Output("connection-text", "children"),
     Output("historical-data-store", "data"),
     # NEUE AUTO-REFRESH OUTPUTS:
     Output("liquidity-warning-container", "children"),
     Output("innovation-container", "children"),
     Output("machines-container", "children"),
     Output("financing-container", "children"),
     Output("personnel-container", "children"),
     Output("balance-sheet-container", "children"),
     Output("cost-structure-container", "children")],
    [Input("refresh-interval", "n_intervals"),
     Input("firm-id-store", "data")],
    [State("historical-data-store", "data"),
     State("balance-sheet-tabs", "active_tab"),
     # Inputs to preserve state for:
     # Financing
     State("input-loan-amount", "value"),
     State("input-loan-quarters", "value"),
     State("input-shares-amount", "value"),
     # Personnel
     State("input-hire-qualification", "value"),
     State("input-hire-count", "value"),
     State("input-fire-qualification", "value"),
     State("input-fire-count", "value"),
     # Innovation
     State("input-innovation-amount", "value")]
)
def live_update_dashboard(n, firm_id, historical_data, active_tab,
                         # Financing
                         loan_amount, loan_quarters, shares_amount,
                         # Personnel
                         hire_qual, hire_count, fire_qual, fire_count,
                         # Innovation
                         innovation_amount):
    """Live-Update ALLER Dashboard-Elemente inkl. neuer Features (5s Intervall)"""
    if not firm_id:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            "fas fa-circle text-danger me-2",
            "Nicht verbunden",
            historical_data,
            # Neue Outputs:
            dash.no_update,  # liquidity-warning
            dash.no_update,  # innovation
            dash.no_update,  # machines
            dash.no_update,  # financing
            dash.no_update,  # personnel
            dash.no_update,  # balance-sheet
            dash.no_update   # cost-structure
        )

    try:
        # Fetch firm data directly
        firm = game.get_firm_by_id(firm_id)
        if not firm:
            raise ValueError("Firma nicht gefunden")
        firm_data = firm.to_dict()

        # Fetch market data directly
        market_data = game.get_market_overview()

        # Update KPIs
        kpis = create_dashboard_kpis(firm_data)

        # Update current settings card
        current_settings = create_current_settings_card(firm_data)

        # Update market table (with current firm_id for acquisition buttons)
        market_table = create_market_table(market_data, current_firm_id=firm_id)

        # Update live status
        live_status = [
            html.P([
                html.Strong("Produktpreis: "),
                f"€{firm_data.get('product_price', 0):.2f}"
            ], className="mb-2"),
            html.P([
                html.Strong("Produktionskapazität: "),
                f"{format_de(firm_data.get('production_capacity', 0))} Einheiten"
            ], className="mb-2"),
            html.P([
                html.Strong("Lagerbestand: "),
                f"{format_de(firm_data.get('inventory_level', 0))} Einheiten"
            ], className="mb-2"),
            html.P([
                html.Strong("JIT-Effizienz: "),
                f"{firm_data.get('safety_stock_percentage', 0):.1f}%"
            ], className="mb-2"),
            html.P([
                html.Strong("Marketing Budget: "),
                f"€{format_de(firm_data.get('marketing_budget', 0))}"
            ], className="mb-2"),
            html.P([
                html.Strong("F&E Budget: "),
                f"€{format_de(firm_data.get('rd_budget', 0))}"
            ], className="mb-2"),
            html.P([
                html.Strong("Qualitätslevel: "),
                f"Level {firm_data.get('quality_level', 5)}/10"
            ], className="mb-2"),
            html.P([
                html.Strong("Aktuelles Quartal: "),
                f"Q{firm_data.get('current_quarter', 0)}"
            ], className="mb-2 text-primary fw-bold"),
        ]

        # Update historical data for chart
        if historical_data is None:
            historical_data = {"quarters": [], "revenue": [], "profit": [], "cash": []}

        current_quarter = firm_data.get('current_quarter', 0)

        # Nur neue Quartale hinzufügen
        if not historical_data['quarters'] or current_quarter > max(historical_data['quarters']):
            historical_data['quarters'].append(current_quarter)
            historical_data['revenue'].append(firm_data.get('revenue', 0))
            historical_data['profit'].append(firm_data.get('profit', 0))
            historical_data['cash'].append(firm_data.get('cash', 0))

            # Limit zu letzten 12 Quartalen
            if len(historical_data['quarters']) > 12:
                for key in ['quarters', 'revenue', 'profit', 'cash']:
                    historical_data[key] = historical_data[key][-12:]

        # NEUE KARTEN UPDATEN:
        liquidity_card = create_liquidity_warning_card(firm_data)
        
        # Innovation (State Preserved)
        innovation_val = innovation_amount if innovation_amount is not None else 1000000
        innovation_card = create_innovation_card(firm_data, innovation_amount=innovation_val)
        
        machines_card = create_machine_upgrade_card(firm_data)
        
        # Financing (State Preserved)
        loan_amt = loan_amount if loan_amount is not None else 500000
        loan_q = loan_quarters if loan_quarters is not None else 12
        shares_amt = shares_amount if shares_amount is not None else 1000000
        financing_card = create_financing_card(firm_data, loan_amount=loan_amt, loan_quarters=loan_q, shares_amount=shares_amt)
        
        # Personnel (State Preserved)
        h_qual = hire_qual if hire_qual else "angelernt"
        h_count = hire_count if hire_count is not None else 5
        f_qual = fire_qual if fire_qual else "ungelernt"
        f_count = fire_count if fire_count is not None else 5
        personnel_card = create_personnel_card(firm_data, hire_qual=h_qual, hire_count=h_count, fire_qual=f_qual, fire_count=f_count)
        
        # Balance Sheet mit State Preservation
        # Default zu tab-0 wenn None
        current_tab = active_tab if active_tab else "tab-0"
        balance_sheet_card = create_balance_sheet_card(firm_data, active_tab=current_tab)
        
        cost_structure_card = create_cost_structure_card(firm_data)

        return (
            kpis,
            current_settings,
            market_table,
            live_status,
            "fas fa-circle text-success me-2",
            "Live verbunden",
            historical_data,
            # Neue Karten:
            liquidity_card,
            innovation_card,
            machines_card,
            financing_card,
            personnel_card,
            balance_sheet_card,
            cost_structure_card
        )

    except Exception as e:
        import traceback
        error_msg = f"Fehler: {type(e).__name__}: {str(e)}"
        print(f"[Dashboard Error] {error_msg}")
        print(traceback.format_exc())
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            "fas fa-circle text-danger me-2",
            error_msg,
            historical_data,
            # Neue Outputs:
            dash.no_update,  # liquidity-warning
            dash.no_update,  # innovation
            dash.no_update,  # machines
            dash.no_update,  # financing
            dash.no_update,  # personnel
            dash.no_update,  # balance-sheet
            dash.no_update   # cost-structure
        )


@app.callback(
    Output("financial-trends-chart", "figure"),
    Input("historical-data-store", "data")
)
def update_financial_chart(historical_data):
    """Update Finanztrends Chart mit historischen Daten"""
    if not historical_data or not historical_data.get('quarters'):
        # Empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="Warte auf Quartalsdaten...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return fig

    fig = go.Figure()

    # Revenue Line
    fig.add_trace(go.Scatter(
        x=historical_data['quarters'],
        y=historical_data['revenue'],
        mode='lines+markers',
        name='Umsatz',
        line=dict(color='royalblue', width=3),
        marker=dict(size=8)
    ))

    # Profit Line
    fig.add_trace(go.Scatter(
        x=historical_data['quarters'],
        y=historical_data['profit'],
        mode='lines+markers',
        name='Gewinn',
        line=dict(color='green', width=3),
        marker=dict(size=8)
    ))

    # Cash Line
    fig.add_trace(go.Scatter(
        x=historical_data['quarters'],
        y=historical_data['cash'],
        mode='lines+markers',
        name='Bargeld',
        line=dict(color='orange', width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_title="Quartal",
        yaxis_title="€",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )

    return fig


@app.callback(
    Output("session-store", "data", allow_duplicate=True),
    Input("btn-leave-firm", "n_clicks"),
    prevent_initial_call=True
)
def leave_firm(n_clicks):
    """Firma verlassen - löscht Session und lädt Seite neu"""
    if n_clicks:
        # Return None to clear session, which will trigger redirect to login
        return None
    return dash.no_update


# ============ M&A CALLBACKS ============

@app.callback(
    Output("acquisition-target-select", "options"),
    [Input("url", "pathname"),
     Input("firm-id-store", "data")]
)
def load_acquisition_targets(pathname, firm_id):
    """Lädt verfügbare Ziel-Firmen für M&A (alle außer eigene Firma)"""
    if not firm_id:
        return []

    try:
        # Direkter Zugriff
        firms = game.firms.values()

        # Filtere eigene Firma aus und sortiere nach Marktanteil
        available_firms = [f for f in firms if f.id != firm_id]
        available_firms.sort(key=lambda x: x.market_share, reverse=True)

        # Erstelle RadioItems mit detaillierten Informationen
        target_options = [
            {
                "label": firm.name,
                "value": firm.id
            }
            for firm in available_firms
        ]

        return target_options
    except Exception as e:
        print(f"[ERROR] Failed to load acquisition targets: {e}")
        return []


@app.callback(
    [Output("valuation-result", "children"),
     Output("antitrust-check", "children"),
     Output("btn-execute-acquisition", "disabled")],
    Input("btn-calculate-valuation", "n_clicks"),
    [State("firm-id-store", "data"),
     State("acquisition-target-select", "value"),
     State("acquisition-percentage", "value")],
    prevent_initial_call=True
)
def calculate_acquisition_valuation(n_clicks, acquirer_id, target_id, percentage):
    """Berechnet Übernahme-Bewertung und prüft Kartellrecht"""
    if not target_id or not percentage:
        return None, None, True

    try:
        target_firm = game.get_firm_by_id(target_id)
        if not target_firm:
            return dbc.Alert("Firma nicht gefunden", color="danger"), None, True

        # Hole Bewertung
        valuation = game.calculate_acquisition_cost(target_firm)

        # Berechne Preis für gewählten Anteil
        base_value = valuation['enterprise_value']
        price_for_percentage = base_value * 1.30 * (percentage / 100.0)  # 30% Premium

        valuation_card = dbc.Alert([
            html.H6("Bewertung:", className="fw-bold mb-2"),
            html.P(f"Unternehmenswert: €{format_de(base_value)}", className="mb-1"),
            html.P(f"Übernahmeprämie: 30%", className="mb-1"),
            html.Hr(),
            html.H5(f"Preis für {percentage}%: €{format_de(price_for_percentage)}", className="text-warning mb-0")
        ], color="light")

        # Kartellamt-Prüfung
        antitrust = game.check_antitrust(acquirer_id, target_id, percentage)

        if antitrust['allowed']:
            antitrust_card = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                "Kartellamt: Übernahme zulässig",
                html.Br(),
                html.Small(f"Kombinierter Marktanteil: {antitrust['combined_market_share']:.1f}%", className="text-muted")
            ], color="success")
            button_disabled = False
        else:
            antitrust_card = dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                f"Kartellamt: {antitrust['reason']}"
            ], color="danger")
            button_disabled = True

        return valuation_card, antitrust_card, button_disabled

    except Exception as e:
        error = dbc.Alert(f"Fehler: {str(e)}", color="danger")
        return error, None, True


@app.callback(
    Output("acquisition-result", "children"),
    Input("btn-execute-acquisition", "n_clicks"),
    [State("firm-id-store", "data"),
     State("acquisition-target-select", "value"),
     State("acquisition-percentage", "value")],
    prevent_initial_call=True
)
def execute_acquisition(n_clicks, acquirer_id, target_id, percentage):
    """Führt Übernahme durch"""
    try:
        result = game.acquire_firm(acquirer_id, target_id, percentage)
        
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Übernahme erfolgreich!"),
            html.Br(),
            html.P(result['message'], className="mb-0 mt-2")
        ], color="success", dismissable=True, duration=5000)

    except ValueError as ve:
        return dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                html.Strong("Übernahme fehlgeschlagen:"),
                html.Br(),
                html.P(str(ve), className="mb-0 mt-2")
            ], color="danger", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fehler bei Übernahme: {str(e)}", color="danger", dismissable=True)


# ============ NEUE FEATURE CALLBACKS ============

@app.callback(
    Output("machine-upgrade-feedback", "children"),
    Input("btn-upgrade-machines", "n_clicks"),
    State("firm-id-store", "data"),
    prevent_initial_call=True
)
def upgrade_machines(n_clicks, firm_id):
    """Maschinen upgraden"""
    try:
        firm = game.get_firm_by_id(firm_id)
        if not firm:
            return dbc.Alert("Firma nicht gefunden", color="danger")
            
        success, message = firm.upgrade_machines("premium")

        if success:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                message
            ], color="success", dismissable=True, duration=4000)
        else:
            return dbc.Alert(message, color="danger", dismissable=True)

    except Exception as e:
        return dbc.Alert(f"Fehler: {str(e)}", color="danger", dismissable=True)


@app.callback(
    Output("financing-feedback", "children"),
    [Input("btn-request-loan", "n_clicks"),
     Input("btn-issue-shares", "n_clicks")],
    [State("firm-id-store", "data"),
     State("input-loan-amount", "value"),
     State("input-loan-quarters", "value"),
     State("input-shares-amount", "value")],
    prevent_initial_call=True
)
def handle_financing(loan_clicks, shares_clicks, firm_id, loan_amount, loan_quarters, shares_amount):
    """Kredite aufnehmen oder Aktien ausgeben"""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        firm = game.get_firm_by_id(firm_id)
        if not firm:
            return dbc.Alert("Firma nicht gefunden", color="danger")

        if button_id == "btn-request-loan":
            success, message = firm.take_loan(loan_amount, loan_quarters)
        elif button_id == "btn-issue-shares":
            success, message = firm.issue_shares(shares_amount)
        else:
            return dash.no_update

        if success:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                message
            ], color="success", dismissable=True, duration=4000)
        else:
            return dbc.Alert(message, color="danger", dismissable=True)

    except Exception as e:
        return dbc.Alert(f"Fehler: {str(e)}", color="danger", dismissable=True)


@app.callback(
    Output("personnel-feedback", "children"),
    [Input("btn-hire-personnel", "n_clicks"),
     Input("btn-fire-personnel", "n_clicks")],
    [State("firm-id-store", "data"),
     State("input-hire-qualification", "value"),
     State("input-hire-count", "value"),
     State("input-fire-qualification", "value"),
     State("input-fire-count", "value")],
    prevent_initial_call=True
)
def handle_personnel(hire_clicks, fire_clicks, firm_id, hire_qual, hire_count, fire_qual, fire_count):
    """Personal einstellen oder entlassen"""
    ctx = callback_context

    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        firm = game.get_firm_by_id(firm_id)
        if not firm:
            return dbc.Alert("Firma nicht gefunden", color="danger")

        if button_id == "btn-hire-personnel":
            success, message = firm.hire_personnel(hire_qual, hire_count)
        elif button_id == "btn-fire-personnel":
            success, message = firm.fire_personnel(fire_qual, fire_count)
        else:
            return dash.no_update

        if success:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                message
            ], color="success", dismissable=True, duration=4000)
        else:
            return dbc.Alert(message, color="danger", dismissable=True)

    except Exception as e:
        return dbc.Alert(f"Fehler: {str(e)}", color="danger", dismissable=True)


@app.callback(
    Output("innovation-feedback", "children"),
    Input("btn-invest-innovation", "n_clicks"),
    [State("firm-id-store", "data"),
     State("input-innovation-amount", "value")],
    prevent_initial_call=True
)
def invest_innovation(n_clicks, firm_id, amount):
    """Innovation investieren"""
    try:
        firm = game.get_firm_by_id(firm_id)
        if not firm:
            return dbc.Alert("Firma nicht gefunden", color="danger")
            
        if firm.cash < amount:
             return dbc.Alert(f"Nicht genug Cash. Verfügbar: €{format_de(firm.cash)}", color="danger")
             
        # Logic duplicated from main.py as it is not in models
        firm.cash -= amount
        firm.innovation_investment += amount

        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"€{format_de(amount)} in Innovation investiert",
            html.Br(),
            html.Small(f"Total investiert: €{format_de(firm.innovation_investment)} / €5M", className="mt-2")
        ], color="success", dismissable=True, duration=4000)

    except Exception as e:
        return dbc.Alert(f"Fehler: {str(e)}", color="danger", dismissable=True)
