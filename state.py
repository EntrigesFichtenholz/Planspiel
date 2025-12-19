from models import GameSession

# Globaler Spielzustand (Singleton)
# Wird von main.py (API) und dashboard.py (UI) gemeinsam genutzt
game = GameSession()
