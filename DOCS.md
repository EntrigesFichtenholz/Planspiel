# BWL Planspiel - Dokumentation

**Live-URL:** https://planspiel-6al4.onrender.com

**Wichtig:** Da eine kostenlose Render-Instanz verwendet wird, kann der Container beim ersten Aufruf hochgefahren werden muessen. Dies dauert etwa 30-60 Sekunden. Bitte haben Sie etwas Geduld bei der ersten Anfrage.

---

## Inhaltsverzeichnis

1. [Uebersicht](#uebersicht)
2. [Architektur](#architektur)
3. [Features](#features)
4. [Deployment](#deployment)
5. [Spielmechanik](#spielmechanik)
6. [API-Endpunkte](#api-endpunkte)
7. [Lokale Entwicklung](#lokale-entwicklung)
8. [Troubleshooting](#troubleshooting)

---

## Uebersicht

Business Simulation Game fuer BWL-Studenten. Spieler fuehren Unternehmen, treffen Quartalsentscheidungen und konkurrieren am Markt.

**Technologie-Stack:**
- Backend: Python 3.11 + FastAPI
- Frontend: Dash (Plotly)
- Datenbank: In-Memory (GameSession Singleton)
- Deployment: Render.com (Docker)

**Zugriff:**
- Live-System: https://planspiel-6al4.onrender.com
- Beim ersten Aufruf: Wartezeit 30-60 Sekunden (Container-Start)

---

## Architektur

### Integrierte Architektur (Single Process)

```
┌─────────────────────────────────────────┐
│         Render Container                │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  FastAPI App (main.py)            │ │
│  │  - API Endpoints                  │ │
│  │  - WebSocket Server               │ │
│  │  - Dash App (WSGIMiddleware)      │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  Shared State (state.py)          │ │
│  │  - game = GameSession()           │ │
│  │  - Singleton Pattern              │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│  ┌───────────────▼───────────────────┐ │
│  │  Business Logic (models.py)       │ │
│  │  - BusinessFirm                   │ │
│  │  - GameSession                    │ │
│  │  - Alle Berechnungen              │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Datenzugriff: Direkt statt HTTP

**Alt (vor Optimierung):**
```
Dashboard -> HTTP Request -> API -> GameSession
```

**Neu (aktuell):**
```
Dashboard -> Direkter Zugriff -> game (state.py) -> GameSession
```

**Vorteile:**
- Keine HTTP-Overhead
- Keine Connection-Fehler
- Schnellere Updates (5s Intervall)
- Ein Prozess = stabiler auf Render Free Tier

---

## Features

### Kernfunktionen

**Firmenverwaltung**
- Firma erstellen oder bestehender Firma beitreten
- Multi-User-Support (mehrere Spieler pro Firma)
- Automatische Bot-Firmen als Konkurrenz

**Quartalssystem**
- Quartale laufen automatisch (60 Sekunden pro Quartal)
- Timer zeigt verbleibende Zeit
- Automatischer Quartalsabschluss

**Entscheidungen**
- Produktpreis
- Produktionskapazitaet
- Marketing-Budget
- F&E-Budget
- Qualitaetslevel
- JIT-Sicherheitsbestand
- Prozessoptimierung
- Lieferantenverhandlungen
- Overhead-Reduktion
- Abschreibungsraten (Gebaeude, Maschinen, Ausstattung)

### Erweiterte Systeme

**Kreditsystem**
- Kredit aufnehmen (max. 1 gleichzeitig)
- Bonitats-basierte Zinssaetze
- Transparente Quartalsraten (Tilgung + Zinsen)
- Kredit-Details in Echtzeit

**M&A (Mergers & Acquisitions)**
- Firmen aufkaufen (teilweise oder vollstaendig)
- Kartellrecht-Pruefung
- Enterprise-Value-Berechnung
- Goodwill-Accounting

**Personalmanagement**
- Einstellen/Entlassen von Personal
- 3 Qualifikationsstufen: Ungelernt, Angelernt, Facharbeiter
- Produktivitaets-basierte Kosten

**Maschinenupgrades**
- 3 Klassen: Basic, Professional, Premium
- Effizienzsteigerung + Energiekostensenkung

**Eigenkapital**
- IPO durchfuehren
- Kapitalerhoehungen
- Share-Buyback (Delisting)

### Dashboard-Features

**Live-Updates (alle 5 Sekunden)**
- KPI-Anzeige (Umsatz, Gewinn, ROI, Cash)
- Marktanteile (Pie Chart)
- Marktvolumen-Entwicklung
- Firmenranking-Tabelle

**Finanzberichte**
- Bilanz (Aktiva/Passiva)
- Gewinn- und Verlustrechnung (GuV)
- Liquiditaetskennzahlen
- Kostenstruktur-Analyse

**Visualisierungen**
- Pie Chart: Marktanteile (Top 10 + Rest)
- Line Chart: Marktvolumen-Entwicklung
- Bar Chart: Produktionsmetriken
- Gauge: Lagerbestand


---

## Deployment

### Render.com (Aktuelles Production-System)

**Live-URL:** https://planspiel-6al4.onrender.com

**Setup:**
1. GitHub Repository: https://github.com/EntrigesFichtenholz/Planspiel
2. Render Blueprint: render.yaml
3. Deployment: Automatisch bei Push zu main

**Free Tier Einschraenkungen:**
- Container schlaeft nach 15 Minuten Inaktivitaet
- Beim ersten Aufruf: 30-60 Sekunden Startzeit
- 750 Stunden/Monat (ausreichend fuer Projekt)

**Wichtiger Hinweis fuer Nutzer:**
Wenn Sie die URL das erste Mal aufrufen oder nach laengerer Inaktivitaet, kann es 30-60 Sekunden dauern, bis der Container hochgefahren ist. Bitte haben Sie Geduld und laden Sie die Seite ggf. einmal neu.


---

## Spielmechanik

### Quartalsablauf

1. Entscheidungsphase (60 Sekunden)
2. Quartalsabschluss (automatisch)
3. Marktanteil-Update
4. Finanzberichte-Generierung

### Kostenstruktur

**Fixkosten (pro Quartal):**
- Abschreibungen Gebaeude: variabel (2-10% p.a.)
- Abschreibungen Maschinen: variabel (5-20% p.a.)
- Abschreibungen Ausstattung: variabel (10-30% p.a.)
- Personal: 50k-100k EUR/Q je nach Qualifikation
- Overhead: 200k EUR/Q (reduzierbar)

**Variable Kosten:**
- Material: 30 EUR/Einheit
- Produktion: 20 EUR/Einheit
- Lagerkosten: 2% des Lagerwerts/Quartal

### Kreditsystem

- Max. 1 Kredit gleichzeitig
- Zinssatz: 5-25% p.a. (boniaetsabhaengig)
- Laufzeit: 4-20 Quartale
- Quartalsrate = Tilgung + Zinsen


---

## API-Endpunkte

### Firmenverwaltung
- POST /api/firms - Firma erstellen
- GET /api/firms/{firm_id} - Firmendaten
- POST /api/firms/{firm_id}/join - Firma beitreten
- POST /api/firms/{firm_id}/decision - Entscheidung einreichen

### Finanzierung
- POST /api/firms/{firm_id}/financing/loan - Kredit aufnehmen
- POST /api/firms/{firm_id}/financing/issue-shares - Aktien ausgeben

### Personal & Maschinen
- POST /api/firms/{firm_id}/personnel/hire - Personal einstellen
- POST /api/firms/{firm_id}/personnel/fire - Personal entlassen
- POST /api/firms/{firm_id}/machines/upgrade - Maschinen upgraden

### M&A
- GET /api/firms/{firm_id}/valuation - Firmenbewertung
- POST /api/acquisitions - Uebernahme durchfuehren

### Berichte
- GET /api/firms/{firm_id}/balance-sheet - Bilanz
- GET /api/firms/{firm_id}/income-statement - GuV
- GET /api/firms/{firm_id}/liquidity - Liquiditaetskennzahlen

### System
- GET /health - Health-Check
- GET /api/market - Marktueberblick
- WS /ws - WebSocket Live-Updates


---

## Lokale Entwicklung

### Installation

```bash
git clone https://github.com/EntrigesFichtenholz/Planspiel.git
cd Planspiel
pip install -r requirements.txt
```

### Starten

```bash
python main.py
```

Oeffne: http://localhost:8000

### Projektstruktur

```
Planspiel/
├── main.py         # FastAPI App + Dashboard Integration
├── dashboard.py    # Dash Frontend
├── models.py       # Business Logic
├── state.py        # Shared State (Singleton)
├── requirements.txt
├── render.yaml     # Render Config
└── DOCS.md        # Diese Dokumentation
```


---

## Troubleshooting

### Container startet nicht
- Render Logs pruefen
- state.py vorhanden?
- requirements.txt vollstaendig?

### Dashboard zeigt "Verbindung..."
- Backend erreichbar? (/health)
- game-Objekt initialisiert?
- Browser-Console pruefen

### "Nur ein Kredit gleichzeitig"
Dies ist beabsichtigt. Zahle bestehenden Kredit zuerst ab.

### Render Free Tier - Langsame Antwort
Container schlaeft nach 15 Min. Erste Anfrage dauert 30-60 Sek.
Dies ist normal bei Render Free Tier.

### Marktanteile-Chart leer
- Mindestens 1 Firma muss existieren
- Browser-Console auf Fehler pruefen

---

## Kontakt

**Repository:** https://github.com/EntrigesFichtenholz/Planspiel
**Live-System:** https://planspiel-6al4.onrender.com

Bei Fragen: GitHub Issues

---

Letzte Aktualisierung: 19. Dezember 2025
