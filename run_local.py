"""
Lokales Development Script
Startet Backend und Frontend gleichzeitig für lokales Debugging
"""
import subprocess
import sys
import time
import os

# Set Debug Mode
os.environ["DEBUG_MODE"] = "true"

print("""
╔════════════════════════════════════════════════════════╗
║   BWL Planspiel - Lokales Development                  ║
║   Debug-Modus: AKTIV                                   ║
╚════════════════════════════════════════════════════════╝

Starte Backend und Frontend...
""")

# Start Backend
print("[1/2] Starte FastAPI Backend auf Port 8000...")
backend_process = subprocess.Popen(
    [sys.executable, "main.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Wait for backend to start
time.sleep(3)

# Start Frontend
print("[2/2] Starte Dash Frontend auf Port 8050...")
frontend_process = subprocess.Popen(
    [sys.executable, "dashboard.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

print("""
✓ Server gestartet!

Öffne im Browser:
  - Dashboard: http://localhost:8050
  - API Docs:  http://localhost:8000/docs
  - Health:    http://localhost:8000/health

Debug-Endpunkte (nur im Debug-Modus):
  - GET  /debug/firms          - Liste aller Firmen
  - POST /debug/populate       - Erstelle Test-Firmen
  - POST /api/quarter/advance  - Manueller Quartals-Trigger
  - POST /api/game/reset       - Spiel zurücksetzen

Drücke Strg+C zum Beenden...
""")

try:
    # Keep processes running
    while True:
        time.sleep(1)

        # Check if processes are still running
        if backend_process.poll() is not None:
            print("\n[ERROR] Backend process terminated!")
            break
        if frontend_process.poll() is not None:
            print("\n[ERROR] Frontend process terminated!")
            break

except KeyboardInterrupt:
    print("\n\nBeende Server...")
    backend_process.terminate()
    frontend_process.terminate()
    backend_process.wait()
    frontend_process.wait()
    print("✓ Server beendet")
