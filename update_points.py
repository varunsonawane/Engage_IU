"""
Run this once to assign varied point values to all events.
Usage: python update_points.py
Requires the app to be running at http://localhost:8000
"""
import requests

BASE = "http://localhost:8000"

# Varied point values — cycling through these gives a spread in the leaderboard
POINTS_CYCLE = [50, 10, 25, 30, 15, 40, 20, 35, 5, 45]

# 1. Login
resp = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "engageiu2025"})
resp.raise_for_status()
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 2. Fetch all events (past + upcoming)
events = requests.get(f"{BASE}/events?upcoming_only=false", headers=headers).json()
print(f"Found {len(events)} events\n")

# 3. Update each with a varied point value
for i, ev in enumerate(events):
    pts = POINTS_CYCLE[i % len(POINTS_CYCLE)]
    r = requests.patch(f"{BASE}/events/{ev['id']}", json={"points": pts}, headers=headers)
    r.raise_for_status()
    print(f"  [{ev['id']:>3}] {ev['title'][:45]:<45}  →  {pts} pts")

print("\nDone! Reload the leaderboard to see the updated scores.")
