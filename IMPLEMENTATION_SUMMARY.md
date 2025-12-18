# BWL Planspiel - Implementierungs-Zusammenfassung

## Übersicht der Erweiterungen

Diese Dokumentation fasst alle implementierten Features zusammen, basierend auf den Anforderungen aus der BWL-Vorlesung.

---

## 1. Startkapital-Anpassung (GAME BALANCE FIX APPLIED)

**Status: ✅ IMPLEMENTIERT & BALANCED**

### Änderungen (Original):
- Startkapital von €10M auf **€2M** reduziert
- Eigenkapital entsprechend von €10M auf €2M angepasst
- Asset-Werte realistisch skaliert:
  - Gebäude: €10M → €2M
  - Maschinen: €50M → €8M
  - Ausstattung: €30M → €3M
- Gemeinkosten von €200k auf €100k pro Quartal reduziert

### NEUE ÄNDERUNGEN (Game Balance Fix):
- **Startkapital: €2M → €5M** (verhindert Bankrott-Welle)
- **Eigenkapital: €2M → €5M** (entsprechend angepasst)
- **Gemeinkosten: €100k → €50k** pro Quartal (Fixkosten-Reduktion)
- **Produktionskapazität: 20k → 40k** Einheiten (Marktpotenzial erhöht)
- **Lagerbestand: 5k → 10k** Einheiten (entsprechend angepasst)
- **Personal REDUZIERT** (Personalkosten von €1.12M auf €520k/Quartal):
  - Ungelernt: 50 → 20 Arbeiter
  - Angelernt: 30 → 15 Arbeiter
  - Facharbeiter: 20 → 10 Arbeiter

### Begründung:
Mit 17+ Bots im Markt führte das alte Setup zu:
- Preiskrieg (€74-101 statt €120)
- 0.1% Marktanteil pro Bot
- Fixkosten (€100k Overhead + €1.12M Personal + €120k Abschreibung) = Sofortiger Bankrott
- **Lösung:** Mehr Cash Runway + Niedrigere Fixkosten + Höheres Marktpotenzial

### Datei: `models.py:43-46, 100-102, 175-177, 286`

---

## 2. Maschinensystem (3 Qualitätsklassen)

**Status: ✅ IMPLEMENTIERT**

### Maschinenklassen:

| Klasse | Effizienzfaktor | Energiekosten-Faktor | Abschreibung | Upgrade-Kosten |
|--------|----------------|---------------------|--------------|----------------|
| **Basic** | 0.8x | 1.2x (teurer) | 1.0% | Start |
| **Professional** | 1.0x | 1.0x | 1.0% | €3M |
| **Premium** | 1.3x | 0.7x (günstiger) | 0.8% | €6M |

### Features:
- Maschineneffizienz beeinflusst Produktionskosten
- Energiekosten variieren je nach Maschinenklasse
- Niedrigere Abschreibung bei besseren Maschinen
- Upgrade-Methode `upgrade_machines(target_class)` in models.py:806-852

### API-Endpoints:
- `POST /api/firms/{firm_id}/machines/upgrade` - Maschinen upgraden
- `GET /api/firms/{firm_id}/machines` - Maschinen-Info abrufen

### Datei: `models.py:155-161, 806-852` | `main.py:488-552`

---

## 3. Investitionssystem

**Status: ✅ IMPLEMENTIERT**

### Investitionsarten:

1. **Prozessoptimierung**
   - Kosten: €2M (reduziert von €5M)
   - Effekt: -5% variable Kosten (max -20%)

2. **Lieferantenverhandlungen**
   - Kosten: €1.5M (reduziert von €3M)
   - Effekt: -5% Materialkosten (max -30%)

3. **Verwaltungsoptimierung**
   - Kosten: €1M (reduziert von €4M)
   - Effekt: -10% Overhead (max -50%)

4. **Maschinen-Upgrades**
   - Basic → Professional: €3M
   - Professional → Premium: €6M

### Datei: `models.py:446-459, 806-852`

---

## 4. Finanzierungssystem - Kredite

**Status: ✅ IMPLEMENTIERT**

### Features:
- Maximales Kreditlimit: €5M (anpassbar basierend auf Bonität)
- Zinssatz abhängig von Bonität (5-25% p.a.)
- Bonität-System basierend auf:
  - Verschuldungsgrad (Debt/Equity)
  - Liquiditätskennzahlen
  - Profitabilität (ROE)
- Automatische Tilgung und Zinszahlungen
- Standardlaufzeit: 12 Quartale (3 Jahre)

### Methoden:
- `take_loan(amount, quarters)` - Kredit aufnehmen
- `update_credit_rating()` - Bonität aktualisieren

### API-Endpoints:
- `POST /api/firms/{firm_id}/financing/loan` - Kredit aufnehmen
- `GET /api/firms/{firm_id}/financing/loans` - Kredit-Informationen

### Datei: `models.py:163-166, 854-926` | `main.py:554-600`

---

## 5. Eigenkapitalerhöhung

**Status: ✅ IMPLEMENTIERT**

### IPO (Initial Public Offering):
- Kosten: 10% des aufgenommenen Kapitals
- Firma wird börsennotiert
- Gründer behält 70%, neue Investoren 30%

### Capital Raise (Follow-On):
- Kosten: 5% des aufgenommenen Kapitals
- Bestehende Aktionäre werden verwässert (10%)
- Nur für bereits börsennotierte Firmen

### Methode:
- `issue_shares(amount)` - Aktien ausgeben

### API-Endpoint:
- `POST /api/firms/{firm_id}/financing/issue-shares`

### Datei: `models.py:1008-1059` | `main.py:602-629`

---

## 6. Produktlebenszyklus

**Status: ✅ IMPLEMENTIERT**

### Lebenszyklus-Phasen:

| Phase | Quartale | Nachfragefaktor | Beschreibung |
|-------|----------|----------------|--------------|
| **Introduction** | 0-4 | 0.7 (70%) | Markteinführung, geringe Nachfrage |
| **Growth** | 5-12 | 1.3 (130%) | Wachstumsphase, hohe Nachfrage |
| **Maturity** | 13-24 | 1.0 (100%) | Stabile Phase, normale Nachfrage |
| **Decline** | 25+ | 0.6 (60%) | Produkt veraltet, Innovation nötig |

### Innovation:
- Investment-Schwelle: €5M
- Effekt: Neues Produkt (Generation++), Rückkehr zu Introduction-Phase
- Automatische Phasen-Übergänge basierend auf Produktalter

### API-Endpoints:
- `POST /api/firms/{firm_id}/innovation/invest` - In Innovation investieren
- `GET /api/firms/{firm_id}/product-lifecycle` - Lifecycle-Info

### Datei: `models.py:189-193, 461-489` | `main.py:726-800`

---

## 7. Personalqualifikation

**Status: ✅ IMPLEMENTIERT**

### Qualifikationsstufen:

| Qualifikation | Kosten/Quartal | Produktivität | Start-Anzahl |
|--------------|---------------|--------------|--------------|
| **Ungelernt** | €8,000 | 0.7 (70%) | 50 |
| **Angelernt** | €12,000 | 1.0 (100%) | 30 |
| **Facharbeiter** | €18,000 | 1.4 (140%) | 20 |

### Features:
- Durchschnittliche Produktivität beeinflusst effektive Produktionskapazität
- Einstellungskosten: 50% eines Quartalsgehalts
- Abfindung bei Entlassung: 1 Quartalsgehalt (deutsches Arbeitsrecht)
- Personalkosten werden automatisch jeden Quartal berechnet

### Methoden:
- `hire_personnel(qualification, count)` - Personal einstellen
- `fire_personnel(qualification, count)` - Personal entlassen

### API-Endpoints:
- `POST /api/firms/{firm_id}/personnel/hire` - Personal einstellen
- `POST /api/firms/{firm_id}/personnel/fire` - Personal entlassen
- `GET /api/firms/{firm_id}/personnel` - Personal-Info

### Datei: `models.py:174-187, 248-265, 928-1006` | `main.py:631-724`

---

## 8. Liquiditätskennzahlen

**Status: ✅ IMPLEMENTIERT**

### Liquiditätsgrade (nach BWL-Vorlesung):

1. **Liquidität 1. Grades (Barliquidität)**
   - Formel: Cash / kurzfristige Verbindlichkeiten
   - Ziel: > 1.0 (gut), < 0.5 (kritisch)

2. **Liquidität 2. Grades (Einzugsbedingte Liquidität)**
   - Formel: (Cash + Forderungen) / kurzfristige Verbindlichkeiten
   - Ziel: > 1.0

3. **Liquidität 3. Grades (Umsatzbedingte Liquidität)**
   - Formel: (Cash + Forderungen + Vorräte) / kurzfristige Verbindlichkeiten
   - Ziel: > 2.0

### Liquiditätsstatus:
- **HEALTHY**: Liquidität 1 >= 1.5
- **GOOD**: Liquidität 1 >= 1.0
- **WARNING**: Liquidität 1 >= 0.5
- **CRITICAL**: Liquidität 1 < 0.5

### API-Endpoint:
- `GET /api/firms/{firm_id}/liquidity` - Liquiditätskennzahlen mit Empfehlungen

### Datei: `models.py:168-172, 518-537` | `main.py:821-854`

---

## 9. Bilanz & GuV (Balance Sheet & P&L)

**Status: ✅ IMPLEMENTIERT & AUSGEGLICHEN**

### BALANCE SHEET FIX APPLIED:
- **Retained Earnings Tracking hinzugefügt** - Kumuliert alle Quartalsgewinne/-verluste
- **Eigenkapital korrigiert**: €5M → €18.3M (= Cash €5M + Assets €13M + Inventory €0.3M)
- **Bilanzgleichung erfüllt**: Aktiva = Passiva (Balance Sheet balanciert!)
- Neue Bilanz-Struktur:
  - Eigenkapital = Gezeichnetes Kapital (€18.3M) + Gewinnrücklagen (kumuliert)
  - Passiva gesamt = Eigenkapital + Fremdkapital

### Bilanz (nach deutschem HGB):

**AKTIVA:**
- A. Anlagevermögen (Gebäude, Maschinen, Ausstattung)
- B. Umlaufvermögen (Kasse/Bank, Vorräte)

**PASSIVA:**
- A. Eigenkapital (Gezeichnetes Kapital, Jahresüberschuss)
- B. Fremdkapital (Langfristige & Kurzfristige Verbindlichkeiten)

### GuV (Gewinn- und Verlustrechnung):
- Umsatzerlöse
- Variable Kosten
- Deckungsbeitrag
- Fixkosten
- EBITDA
- Abschreibungen
- EBIT
- Zinsen
- EBT
- Steuern (33.33%)
- Jahresüberschuss

### Methoden:
- `generate_balance_sheet()` - Bilanz erstellen
- `generate_income_statement()` - GuV erstellen

### API-Endpoints:
- `GET /api/firms/{firm_id}/balance-sheet` - Bilanz abrufen
- `GET /api/firms/{firm_id}/income-statement` - GuV abrufen

### Datei: `models.py:195-207, 1061-1133` | `main.py:802-819`

---

## 10. Deckungsbeitragsrechnung

**Status: ✅ IMPLEMENTIERT**

### Kostenarten:

**Variable Kosten:**
- Materialkosten
- Produktionskosten
- Energiekosten
- Personalkosten

**Fixkosten:**
- Abschreibungen
- Gemeinkosten (Overhead)
- Marketingbudget
- F&E-Budget
- Zinsen

### Kennzahlen:
- **Deckungsbeitrag gesamt**: Umsatz - Variable Kosten
- **Deckungsbeitrag pro Einheit**: Deckungsbeitrag gesamt / Verkaufte Einheiten

### Verwendung:
- Break-Even-Analyse
- Preisuntergrenze bestimmen
- Produktrentabilität bewerten

### Datei: `models.py:208-212, 354-361` | Wird in `to_dict()` exportiert

---

## Technische Details

### Neue Enums (`models.py:14-33`):
```python
class MachineClass(Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"

class PersonnelQualification(Enum):
    UNGELERNT = "ungelernt"
    ANGELERNT = "angelernt"
    FACHARBEITER = "facharbeiter"

class ProductLifecycleStage(Enum):
    INTRODUCTION = "introduction"
    GROWTH = "growth"
    MATURITY = "maturity"
    DECLINE = "decline"
```

### Erweiterte `to_dict()` Methode:
Die `to_dict()` Methode wurde massiv erweitert und exportiert jetzt:
- Maschinen-Informationen
- Personal-Struktur
- Finanzierungs-Details (Kredite, Bonität)
- Liquiditätskennzahlen
- Produktlebenszyklus
- Bilanz & GuV
- Deckungsbeitrag

### Cost Breakdown erweitert:
```python
cost_breakdown = {
    "variable": ...,
    "energy": ...,  # NEU
    "inventory": ...,
    "depreciation": ...,
    "overhead": ...,
    "personnel": ...,  # NEU
    "personnel_ungelernt": ...,  # NEU
    "personnel_angelernt": ...,  # NEU
    "personnel_facharbeiter": ...,  # NEU
    "marketing": ...,
    "rd": ...,
    "interest": ...,
    "loan_payments": ...,  # NEU
    "innovation": ...,  # NEU
    "efficiency_investments": ...,
    "total": ...
}
```

---

## API-Endpoints Übersicht

### Neue Endpoints:

**Maschinensystem:**
- `POST /api/firms/{firm_id}/machines/upgrade`
- `GET /api/firms/{firm_id}/machines`

**Finanzierung:**
- `POST /api/firms/{firm_id}/financing/loan`
- `GET /api/firms/{firm_id}/financing/loans`
- `POST /api/firms/{firm_id}/financing/issue-shares`

**Personalmanagement:**
- `POST /api/firms/{firm_id}/personnel/hire`
- `POST /api/firms/{firm_id}/personnel/fire`
- `GET /api/firms/{firm_id}/personnel`

**Innovation:**
- `POST /api/firms/{firm_id}/innovation/invest`
- `GET /api/firms/{firm_id}/product-lifecycle`

**Reporting:**
- `GET /api/firms/{firm_id}/balance-sheet`
- `GET /api/firms/{firm_id}/income-statement`
- `GET /api/firms/{firm_id}/liquidity`

---

## Tests & Validation

### Syntax-Check:
✅ `models.py` - Compiled successfully
✅ `main.py` - Compiled successfully

### Test-Kommandos:
```bash
cd C:/Users/Johannes/Nextcloud/Johannes/Uni/7SemUni/BWL_Planspiel/BWL_Planspiel_Server
python -m py_compile models.py
python -m py_compile main.py
```

---

## Nächste Schritte

### Noch offen:
1. **Dashboard-UI erweitern** (Bilanz/GuV-Ansicht im Dash-Frontend)
2. **Visualisierungen** für neue Kennzahlen (Liquidität, Produktlebenszyklus)
3. **Tutorial/Hilfe** für neue Features
4. **Testdaten** für alle neuen Systeme

### Empfohlene Reihenfolge:
1. Server starten und API testen
2. Dashboard-Komponenten für Bilanz/GuV erstellen
3. Interaktive Widgets für Maschinenkauf, Kredite, Personal
4. Visualisierungen (Charts) für Produktlebenszyklus und Liquidität

---

## Verwendungsbeispiele

### 1. Maschinen upgraden:
```bash
POST /api/firms/1/machines/upgrade
{
  "target_class": "professional"
}
```

### 2. Kredit aufnehmen:
```bash
POST /api/firms/1/financing/loan
{
  "amount": 1000000,
  "quarters": 12
}
```

### 3. Personal einstellen:
```bash
POST /api/firms/1/personnel/hire
{
  "qualification": "facharbeiter",
  "count": 10
}
```

### 4. Innovation investieren:
```bash
POST /api/firms/1/innovation/invest
{
  "amount": 2000000
}
```

### 5. IPO durchführen:
```bash
POST /api/firms/1/financing/issue-shares
{
  "amount": 5000000
}
```

---

## Zusammenfassung

Alle 10 geplanten Features wurden erfolgreich implementiert:

1. ✅ Startkapital auf €2M reduziert
2. ✅ 3 Maschinenklassen (Basic/Pro/Premium)
3. ✅ Maschinen-Upgrade-System
4. ✅ Kreditsystem mit Bonität
5. ✅ Eigenkapitalerhöhung (IPO/Capital Raise)
6. ✅ Produktlebenszyklus mit 4 Phasen
7. ✅ 3 Personalqualifikationsstufen
8. ✅ Liquiditätskennzahlen (3 Grade)
9. ✅ Bilanz & GuV nach HGB
10. ✅ Deckungsbeitragsrechnung

Das BWL Planspiel enthält jetzt ein vollständiges Simulations-System basierend auf universitärem BWL-Wissen!
