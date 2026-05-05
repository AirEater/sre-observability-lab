import random
import time

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="sre-observability-demo")

# ---- Prometheus 自动注入 ----
# 这一行干了三件事:
#   1. 注册中间件,自动统计 http_requests_total{method, handler, status}
#   2. 自动统计 http_request_duration_seconds (histogram)
#   3. 把 /metrics endpoint 挂到 app 上
Instrumentator().instrument(app).expose(app)

# ---- 自定义指标 ----
# Counter 只增不减。labels 用来切片(按 type 分别统计三种故障)。
SIMULATED_INCIDENTS = Counter(
    "simulated_incidents_total",
    "Number of simulated incidents triggered, by type",
    ["type"],
)

# ---- 应用状态 ----
# /readyz 用这个判断,后面 Phase 4 做 chaos 时可以手动改成 False 模拟 NotReady
APP_READY = True

@app.get("/")
def root():
    return {"service": "sre-observability-demo", "status": "ok"}

@app.get("/healthz")
def healthz():
    """Liveness — 进程活着就返回 200。K8s livenessProbe 用。"""
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    """Readiness — 应用准备好接流量才返回 200。K8s readinessProbe 用。"""
    if APP_READY:
        return {"status": "ok"}
    raise HTTPException(status_code=503, detail="Not ready for traffic")

@app.get("/simulate-error")
def simulate_error():
    """故意抛 500,用来在 Grafana / Alertmanager 里看 error rate 飙升。"""
    SIMULATED_INCIDENTS.labels(type="error").inc()
    raise HTTPException(status_code=500, detail="simulated error")

@app.get("/simulate-latency")
def simulate_latency():
    """sleep 2-5 秒,用来观察 P95 延迟告警触发。"""
    SIMULATED_INCIDENTS.labels(type="latency").inc()
    time.sleep(random.uniform(2, 5))
    return {"status": "slow"}

@app.get("/simulate-cpu")
def simulate_cpu():
    """CPU busy loop 1 秒,用来观察 container_cpu_usage 飙升 + HPA 反应。"""
    SIMULATED_INCIDENTS.labels(type="cpu").inc()
    deadline = time.time() + 1.0
    x = 0
    while time.time() < deadline:
        x += 1  # 纯 CPU 烧
    return {"status": "hot", "iterations": x}