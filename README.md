# BWL Planspiel - Server

Business Simulation Game portiert von ESP32/C++ zu Python/FastAPI/Dash

## Features

- **Multi-User**: Mehrere Spieler können gleichzeitig teilnehmen
- **Live-Updates**: WebSocket für Echtzeit-Dashboard-Updates
- **Vollständige Spielmechanik**: Alle BWL-Planspiel-Mechaniken implementiert
- **Debug-Modus**: Lokales Debugging mit zusätzlichen Endpunkten
- **Docker-Support**: Einfaches Deployment auf Render.com

## Schnellstart (Lokal)

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Lokales Development

```bash
python run_local.py
```

Öffne dann:
- Dashboard: http://localhost:8050
- API Docs: http://localhost:8000/docs

### 3. Mit Docker

```bash
# Development mit Debug-Modus
DEBUG_MODE=true docker-compose up

# Produktion
DEBUG_MODE=false docker-compose up -d
```

## Spielmechanik

### Quartalsentscheidungen

Jedes Quartal (120 Sekunden) müssen Spieler folgende Entscheidungen treffen:

1. **Produktpreis** (€50-€500)
2. **Produktionskapazität** (Einheiten)
3. **Marketing Budget** (Max 30% von Cash)
4. **F&E Budget** (Max 20% von Cash)
5. **Qualitätslevel** (1-10)
6. **JIT-Strategie** (% Sicherheitsbestand)

### Kosten

**Fixkosten pro Quartal:**
- Abschreibungen Gebäude: €250,000
- Abschreibungen Maschinen: €1,250,000
- Abschreibungen Ausstattung: €750,000
- Zinsen: 2.5% pro Quartal auf Fremdkapital

**Variable Kosten:**
- Material: €30/Einheit
- Produktion: €20/Einheit
- Lagerkosten: 2% des Lagerwerts/Quartal

### Mechaniken

- **Preiselastizität**: +10% Preis → -15% Absatz
- **Marketing**: 1M€ → +0.5% Marktanteil (logarithmisch)
- **Qualität**: Level 5 → bis +12.5% Preisaufschlag
- **F&E**: Level 6 kostet €12M
- **JIT-Risiko**: Bei 0% Safety Stock → möglicher Umsatzverlust

## API Endpunkte

### Haupt-Endpunkte

```
POST /api/firms                   - Firma erstellen
GET  /api/firms/{firm_id}         - Firmendaten abrufen
POST /api/firms/{firm_id}/decision - Entscheidung einreichen
GET  /api/market                  - Marktübersicht
GET  /api/quarter                 - Quartalsstatus
WS   /ws                          - WebSocket für Live-Updates
```

### Debug-Endpunkte (nur DEBUG_MODE=true)

```
GET  /debug/firms                 - Liste aller Firmen
POST /debug/populate              - Test-Firmen erstellen
POST /api/quarter/advance         - Manueller Quartals-Trigger
POST /api/game/reset              - Spiel zurücksetzen
```

## Deployment auf Render.com

### 1. Repository vorbereiten

```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Auf Render.com

1. Neuer Web Service erstellen
2. Repository verbinden
3. Build Command: `docker build -t bwl_planspiel .`
4. Start Command: `docker-compose up`
5. Environment Variables:
   - `DEBUG_MODE=false`

### 3. Free Tier Optimierungen

- Auto-Sleep nach 15 Minuten Inaktivität
- WebSocket keep-alive implementiert
- Health-Check für Uptime-Monitoring

## Entwicklung

### Struktur

```
bwl_planspiel_server/
├── models.py           # Business-Logik (BusinessFirm, GameSession)
├── main.py             # FastAPI Backend + WebSocket
├── dashboard.py        # Dash Frontend
├── run_local.py        # Lokales Development Script
├── Dockerfile          # Docker Container
├── docker-compose.yml  # Multi-Container Setup
└── requirements.txt    # Python Dependencies
```

### Neue Features hinzufügen

1. Business-Logik in `models.py` erweitern
2. API-Endpunkt in `main.py` hinzufügen
3. UI-Komponente in `dashboard.py` erstellen
4. Testen mit `python run_local.py`

## Testing

```bash
# Backend testen
curl http://localhost:8000/health

# Test-Firma erstellen
curl -X POST http://localhost:8000/api/firms \
  -H "Content-Type: application/json" \
  -d '{"firm_name":"TestCorp","user_name":"test"}'

# Debug: Test-Firmen erstellen
curl -X POST http://localhost:8000/debug/populate
```

## Troubleshooting

### "Firma bereits registriert"
→ Jeder Username kann nur eine Firma haben. Nutze `/api/game/reset` im Debug-Modus.

### WebSocket verbindet nicht
→ Prüfe ob Backend läuft: `curl http://localhost:8000/health`

### Dashboard zeigt keine Daten
→ Prüfe Browser Console auf Fehler. API-URL in `dashboard.py` anpassen falls nötig.

## Lizenz

Educational Use Only - BWL Planspiel Uni Projekt

## Kontakt

Bei Fragen: johannes@example.com
