import requests
import random
import time
import threading

BASE_URL = "http://localhost:8000"

def error_flood():
    """High error rate - main incident driver"""
    while True:
        requests.get(f"{BASE_URL}/simulate-error", timeout=5)
        time.sleep(random.uniform(0.2, 0.6))

def latency_spike():
    """Concurrent slow requests - causes latency to spike"""
    while True:
        requests.get(f"{BASE_URL}/simulate-latency", timeout=15)
        time.sleep(random.uniform(0.5, 1.5))

def normal_mixed_in():
    """Some normal traffic still coming in during incident"""
    while True:
        requests.get(f"{BASE_URL}/", timeout=5)
        time.sleep(random.uniform(1, 3))

DURATION = 180  # 3 minutes

print(f"Simulating incident for {DURATION}s. Wait ~20s then check Grafana.")

threads = [
    threading.Thread(target=error_flood),
    threading.Thread(target=error_flood),   # two error threads = higher rate
    threading.Thread(target=latency_spike),
    threading.Thread(target=normal_mixed_in),
]

for t in threads:
    t.daemon = True
    t.start()

time.sleep(DURATION)
print("Done.")
