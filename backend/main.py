import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("finsight")

app = FastAPI(title="FinSight Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "model": settings.llm_model, "provider": settings.llm_provider}


@app.get("/api/kpi")
async def kpi() -> dict:
    """Hardcoded KPI dashboard data (week 2: aggregate from SQLite)."""
    return {
        "period": "2026-03",
        "updated_at": "2026-04-18T09:00:00Z",
        "metrics": [
            {"name": "获客量", "value": "12,450", "change": "+5.2%", "trend": "up", "alert": False},
            {"name": "激活率", "value": "78.3%", "change": "-1.1%", "trend": "down", "alert": False},
            {"name": "交易额", "value": "8,230万", "change": "+3.4%", "trend": "up", "alert": False},
            {"name": "逾期率", "value": "3.8%", "change": "+0.6%", "trend": "up", "alert": True},
            {"name": "催收回收率", "value": "85.2%", "change": "-2.1%", "trend": "down", "alert": False},
        ],
    }
