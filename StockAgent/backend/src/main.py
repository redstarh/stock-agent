"""FastAPI 앱 엔트리포인트"""

from fastapi import FastAPI

from src.api.account import router as account_router
from src.api.reports import router as reports_router
from src.api.scanner import router as scanner_router
from src.api.strategy import router as strategy_router
from src.api.trades import router as trades_router
from src.api.ws import router as ws_router

app = FastAPI(
    title="StockAgent",
    description="키움 REST API 기반 한국 주식 자동매매 시스템",
    version="0.1.0",
)

app.include_router(account_router)
app.include_router(reports_router)
app.include_router(scanner_router)
app.include_router(strategy_router)
app.include_router(trades_router)
app.include_router(ws_router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": app.version}
