"""Constants for Solakon integration."""
DOMAIN = "solakon"
PLATFORMS = ["sensor"]

API_BASE = "https://api.app.solakon.de"
DB_BASE = "https://db.app.solakon.de"
ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJhbnprdXNmb3BzZHNleXR0cXZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDE0MjI1NjIsImV4cCI6MjAxNjk5ODU2Mn0"
    ".7DSCHpXmLq2BJMwPvTNyDUc8Y6NkS_ZbOrQhKLbT4MU"
)

CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EMAIL = "email"

UPDATE_INTERVAL = 300  # seconds
