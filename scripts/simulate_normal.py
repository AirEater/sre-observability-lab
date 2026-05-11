import requests
import random
import time
import threading

BASE_URL = "http://localhost:8000"

def steady_traffic():
    """Normal user browsing - moderate pace"""
    while True:
        requests.get(f"{BASE_URL}/", timeout=5)
        time.sleep(random.uniform(1, 4))

def occasional_burst():
    """Burst of requests, then quiet - simulates a user session"""
    while True:
        burst_size = random.randint(3, 8)
        for _ in range(burst_size):
            requests.get(f"{BASE_URL}/", timeout=5)
            time.sleep(random.uniform(0.1, 0.4))
        time.sleep(random.uniform(5, 15))  # quiet period after burst

def rare_errors():
    """Occasional errors - low background noise"""
    while True:
        time.sleep(random.uniform(20, 45))
        requests.get(f"{BASE_URL}/simulate-error", timeout=5)

def rare_latency():
    """Occasional slow requests"""
    while True:
        time.sleep(random.uniform(30, 60))
        requests.get(f"{BASE_URL}/simulate-latency", timeout=10)

DURATION = 300  # 5 minutes

print(f"Simulating normal traffic for {DURATION}s. Press Ctrl+C to stop early.")

threads = [
    threading.Thread(target=steady_traffic),
    threading.Thread(target=occasional_burst),
    threading.Thread(target=rare_errors),
    threading.Thread(target=rare_latency),
]

for t in threads:
    t.daemon = True
    t.start()

time.sleep(DURATION)
print("Done.")
