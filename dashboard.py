"""
BWL Planspiel - Dash Frontend Dashboard
Nutzt fertige Dash Bootstrap Components
"""
import os
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime

# API Endpoint (kann via ENV überschrieben werden für Docker)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Dash App mit Bootstrap Theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)

app.title = "BWL Planspiel"

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
                    html.H3(f"€{firm_data.get('cash', 0):,.0f}", className="mb-0"),
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
                        html.H4(f"{firm_data.get('production_capacity', 20000):,.0f}", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
                dbc.Col([
                    html.Div([
                        html.H6("Marketing", className="text-muted mb-1"),
                        html.H4(f"€{firm_data.get('marketing_budget', 30000):,.0f}", className="text-primary mb-0")
                    ])
                ], width=6, md=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("F&E Budget", className="text-muted mb-1"),
                        html.H4(f"€{firm_data.get('rd_budget', 0):,.0f}", className="text-primary mb-0")
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
    return dbc.Card([
        dbc.CardHeader(html.H5([
            html.I(className="fas fa-cogs me-2"),
            "Neue Entscheidungen eingeben (wirksam ab nächstem Quartal)"
        ])),
        dbc.CardBody([
            # Produktpreis
            dbc.Row([
                dbc.Col([
                    html.Label(f"Produktpreis (€50-€500)"),
                    html.P(f"Aktuell: €{firm_data.get('product_price', 120):.2f}", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-price",
                        type="number",
                        value=firm_data.get('product_price', 120),
                        min=50, max=500, step=0.01
                    )
                ], width=12, md=6, className="mb-3"),

                # Produktionskapazität
                dbc.Col([
                    html.Label("Produktionskapazität (Einheiten)"),
                    html.P(f"Aktuell: {firm_data.get('production_capacity', 20000):.0f} Einheiten", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-capacity",
                        type="number",
                        value=firm_data.get('production_capacity', 20000),
                        min=0, max=120000, step=1000
                    )
                ], width=12, md=6, className="mb-3"),
            ]),

            # Marketing Budget
            dbc.Row([
                dbc.Col([
                    html.Label("Marketing Budget (€)"),
                    html.P(f"Aktuell: €{firm_data.get('marketing_budget', 30000):,.0f} (Max: 30% von Cash)", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-marketing",
                        type="number",
                        value=firm_data.get('marketing_budget', 30000),
                        min=0, step=1000
                    )
                ], width=12, md=6, className="mb-3"),

                # F&E Budget
                dbc.Col([
                    html.Label("F&E Budget (€)"),
                    html.P(f"Aktuell: €{firm_data.get('rd_budget', 0):,.0f} (Max: 20% von Cash)", className="small text-muted mb-1"),
                    dbc.Input(
                        id="input-rd",
                        type="number",
                        value=firm_data.get('rd_budget', 0),
                        min=0, step=1000
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


def create_market_table(market_data):
    """Marktübersicht Tabelle"""
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
                        html.Td(", ".join(firm['user_names'])),  # Show all users
                        html.Td(f"{firm['market_share']:.2f}%"),
                        html.Td(f"€{firm['revenue']:,.0f}"),
                        html.Td(f"€{firm['profit']:,.0f}"),
                        html.Td(f"{firm['roi']:.1f}%"),
                    ]) for firm in market_data.get('firms', [])
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
        text=[f'{capacity:,.0f} Einheiten'],
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
                        html.H6("Live-Status (Auto-Update)", className="text-muted mb-3"),
                        html.Div(id="live-status-display", children=[
                            html.P([
                                html.Strong("Produktpreis: "),
                                f"€{firm_data.get('product_price', 0):.2f}"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Produktionskapazität: "),
                                f"{firm_data.get('production_capacity', 0):,.0f} Einheiten"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Lagerbestand: "),
                                f"{firm_data.get('inventory_level', 0):,.0f} Einheiten"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("JIT-Effizienz: "),
                                f"{firm_data.get('safety_stock_percentage', 0):.1f}%"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Marketing Budget: "),
                                f"€{firm_data.get('marketing_budget', 0):,.0f}"
                            ], className="mb-2"),
                        ])
                    ])
                ], width=12, md=6),
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

            # Finanztrends Chart
            create_financial_trends_chart(firm_data),

            dbc.Row([
                dbc.Col([
                    # Aktuelle Einstellungen (prominent, live-update)
                    html.Div(id="current-settings-container", children=create_current_settings_card(firm_data)),

                    # Produktion & Lagerbestand Live-Anzeige
                    create_production_inventory_status(firm_data),

                    # Entscheidungsformular
                    create_decision_form(firm_data),
                    create_cost_info(),
                ], width=12, lg=8),

                dbc.Col([
                    # Marktübersicht - live aktualisiert
                    html.Div(id="market-overview-container", children=create_market_table({"firms": []})),
                ], width=12, lg=4),
            ]),

            # Hidden stores
            dcc.Store(id="firm-id-store", data=firm_id),
            dcc.Store(id="historical-data-store", data=historical_data),  # Initialize with history from backend
            dcc.Interval(id="refresh-interval", interval=1000, n_intervals=0),  # 1s refresh for LIVE timer
        ], fluid=True)
    ])


# ============ MAIN APP LAYOUT ============

app.layout = html.Div([
    dcc.Location(id="url", refresh=True),  # Enable page refresh
    dcc.Store(id="session-store", storage_type='session'),  # Session storage - cleared on tab close
    html.Div(id="page-content")
])


# ============ CALLBACKS ============

@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"),
     Input("session-store", "data")]
)
def display_page(pathname, session_data):
    """Route between login and dashboard"""
    if session_data and session_data.get("firm_id"):
        # Fetch firm data
        try:
            response = requests.get(f"{API_URL}/api/firms/{session_data['firm_id']}")
            firm_data = response.json()
            return create_dashboard_layout(session_data["firm_id"], firm_data)
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
        response = requests.post(
            f"{API_URL}/api/firms",
            json={"user_name": user_name, "firm_name": firm_name},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {"firm_id": data["firm_id"]}, dbc.Alert("Firma erfolgreich erstellt!", color="success")
        else:
            return dash.no_update, dbc.Alert(f"Fehler: {response.json().get('detail', 'Unbekannt')}", color="danger")
    except Exception as e:
        return dash.no_update, dbc.Alert(f"Verbindungsfehler: {str(e)}", color="danger")


@app.callback(
    Output("firms-list-container", "children"),
    [Input("btn-refresh-firms", "n_clicks"),
     Input("url", "pathname")],
    prevent_initial_call=False
)
def load_firms_list(n_clicks, pathname):
    """Load list of available firms"""
    try:
        response = requests.get(f"{API_URL}/api/firms", timeout=5)
        if response.status_code == 200:
            data = response.json()
            firms = data.get("firms", [])

            if not firms:
                return dbc.Alert("Noch keine Firmen vorhanden", color="info", className="mt-2")

            # Create radio options with firm details
            options = []
            for firm in firms:
                label = html.Div([
                    html.Strong(firm["name"]),
                    html.Br(),
                    html.Small([
                        f"Mitglieder: {firm['user_count']} | ",
                        f"Marktanteil: {firm['market_share']}% | ",
                        f"Cash: €{firm['cash']:,.0f}"
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
        else:
            return dbc.Alert("Fehler beim Laden der Firmen", color="danger")
    except Exception as e:
        return dbc.Alert(f"Verbindungsfehler: {str(e)}", color="danger")


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
        response = requests.post(
            f"{API_URL}/api/firms/{firm_id}/join",
            json={"user_name": user_name},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {"firm_id": data["firm_id"]}, dbc.Alert("Erfolgreich beigetreten!", color="success")
        else:
            return dash.no_update, dbc.Alert(f"Fehler: {response.json().get('detail', 'Unbekannt')}", color="danger")
    except Exception as e:
        return dash.no_update, dbc.Alert(f"Verbindungsfehler: {str(e)}", color="danger")


@app.callback(
    Output("decision-feedback", "children"),
    Input("btn-submit-decision", "n_clicks"),
    [State("firm-id-store", "data"),
     State("input-price", "value"),
     State("input-capacity", "value"),
     State("input-marketing", "value"),
     State("input-rd", "value"),
     State("input-quality", "value"),
     State("input-jit", "value")],
    prevent_initial_call=True
)
def submit_decision(n_clicks, firm_id, price, capacity, marketing, rd, quality, jit):
    """Submit decision callback"""
    try:
        response = requests.post(
            f"{API_URL}/api/firms/{firm_id}/decision",
            json={
                "product_price": price,
                "production_capacity": capacity,
                "marketing_budget": marketing,
                "rd_budget": rd,
                "quality_level": quality,
                "jit_safety_stock": jit
            }
        )
        if response.status_code == 200:
            return dbc.Alert("Entscheidungen erfolgreich gespeichert!", color="success", dismissable=True)
        else:
            return dbc.Alert(f"Fehler: {response.json().get('detail', 'Unbekannt')}", color="danger")
    except Exception as e:
        return dbc.Alert(f"Verbindungsfehler: {str(e)}", color="danger")


@app.callback(
    [Output("quarter-timer", "children"),
     Output("kpi-container", "children"),
     Output("current-settings-container", "children"),
     Output("market-overview-container", "children"),
     Output("live-status-display", "children"),
     Output("connection-status", "className"),
     Output("connection-text", "children"),
     Output("historical-data-store", "data")],
    [Input("refresh-interval", "n_intervals"),
     Input("firm-id-store", "data")],
    State("historical-data-store", "data")
)
def live_update_dashboard(n, firm_id, historical_data):
    """Live-Update aller Dashboard-Elemente (3 Sekunden Intervall)"""
    if not firm_id:
        return (
            "Keine Firma",
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            "fas fa-circle text-danger me-2",
            "Nicht verbunden",
            historical_data
        )

    try:
        # Fetch quarter status
        quarter_response = requests.get(f"{API_URL}/api/quarter", timeout=2)
        quarter_data = quarter_response.json()
        time_left = quarter_data.get("time_remaining", 0)
        quarter = quarter_data.get("current_quarter", 0)

        # Fetch firm data
        firm_response = requests.get(f"{API_URL}/api/firms/{firm_id}", timeout=2)
        firm_data = firm_response.json()

        # Fetch market data
        market_response = requests.get(f"{API_URL}/api/market", timeout=2)
        market_data = market_response.json()

        # Update timer
        minutes = time_left // 60
        seconds = time_left % 60
        timer_text = f"Quartal {quarter} | {minutes:02d}:{seconds:02d} bis zum nächsten Quartal"

        # Update KPIs
        kpis = create_dashboard_kpis(firm_data)

        # Update current settings card
        current_settings = create_current_settings_card(firm_data)

        # Update market table
        market_table = create_market_table(market_data)

        # Update live status
        live_status = [
            html.P([
                html.Strong("Produktpreis: "),
                f"€{firm_data.get('product_price', 0):.2f}"
            ], className="mb-2"),
            html.P([
                html.Strong("Produktionskapazität: "),
                f"{firm_data.get('production_capacity', 0):,.0f} Einheiten"
            ], className="mb-2"),
            html.P([
                html.Strong("Lagerbestand: "),
                f"{firm_data.get('inventory_level', 0):,.0f} Einheiten"
            ], className="mb-2"),
            html.P([
                html.Strong("JIT-Effizienz: "),
                f"{firm_data.get('safety_stock_percentage', 0):.1f}%"
            ], className="mb-2"),
            html.P([
                html.Strong("Marketing Budget: "),
                f"€{firm_data.get('marketing_budget', 0):,.0f}"
            ], className="mb-2"),
            html.P([
                html.Strong("F&E Budget: "),
                f"€{firm_data.get('rd_budget', 0):,.0f}"
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

        return (
            timer_text,
            kpis,
            current_settings,
            market_table,
            live_status,
            "fas fa-circle text-success me-2",
            "Live verbunden",
            historical_data
        )

    except Exception as e:
        return (
            "Verbindung zum Server...",
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            "fas fa-circle text-danger me-2",
            f"Verbindungsfehler",
            historical_data
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


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════╗
    ║   BWL Planspiel Dashboard                 ║
    ║   Dashboard: http://localhost:8050        ║
    ╚═══════════════════════════════════════════╝
    """)
    app.run(debug=True, host="0.0.0.0", port=8050)
