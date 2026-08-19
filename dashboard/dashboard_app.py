from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import shutil
import subprocess
import sys
from dotenv import load_dotenv
from dashboard.shared_db import DashboardDB
import secrets

load_dotenv()

app = FastAPI(title="Crypto Bot Dashboard")
db = DashboardDB()
security = HTTPBasic()

# Authentication
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if secrets.compare_digest(credentials.password, DASHBOARD_PASSWORD):
        return credentials.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect password",
        headers={"WWW-Authenticate": "Basic"},
    )

# Models
class CommandRequest(BaseModel):
    command: str

class SymbolRequest(BaseModel):
    symbol: str

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_user"

# Global orchestrator initialized on startup
orchestrator = None

@app.on_event("startup")
def startup_event():
    global orchestrator
    from app.agents import CryptoOrchestrator
    orchestrator = CryptoOrchestrator()

@app.on_event("shutdown")
def shutdown_event():
    global orchestrator
    if orchestrator:
        orchestrator.close()

# API Routes
@app.get("/api/status", dependencies=[Depends(authenticate)])
async def get_status():
    status_info = db.get_status()
    last_update_str = status_info.get('last_update')
    if last_update_str:
        try:
            from datetime import datetime, timezone
            last_update = datetime.fromisoformat(last_update_str)
            if last_update.tzinfo is not None:
                diff = (datetime.now(timezone.utc) - last_update).total_seconds()
            else:
                diff = (datetime.now() - last_update).total_seconds()
            
            if diff > 45:  # 30s status_updater loop + 15s grace period
                status_info['status'] = 'OFFLINE'
        except Exception:
            status_info['status'] = 'OFFLINE'
    else:
        status_info['status'] = 'OFFLINE'
    return status_info


@app.get("/api/trades", dependencies=[Depends(authenticate)])
async def get_trades():
    return db.get_trades()

@app.get("/api/symbols", dependencies=[Depends(authenticate)])
async def get_symbols():
    return db.get_symbols()

@app.get("/api/logs", dependencies=[Depends(authenticate)])
async def get_logs():
    return db.get_logs(log_path=os.getenv("LOG_FILE", "bot.log"))

bot_proc = None

@app.post("/api/command", dependencies=[Depends(authenticate)])
async def send_command(req: CommandRequest):
    global bot_proc
    if req.command == 'start':
        status_info = db.get_status()
        is_running = True
        last_update_str = status_info.get('last_update')
        if last_update_str:
            try:
                from datetime import datetime, timezone
                last_update = datetime.fromisoformat(last_update_str)
                if last_update.tzinfo is not None:
                    diff = (datetime.now(timezone.utc) - last_update).total_seconds()
                else:
                    diff = (datetime.now() - last_update).total_seconds()
                if diff > 45:
                    is_running = False
            except Exception:
                is_running = False
        else:
            is_running = False
            
        if is_running:
            return {"message": "Bot is already running"}
            
        env = os.environ.copy()
        env["LOG_FILE"] = os.getenv("LOG_FILE", "bot.log")
        env["PYTHONPATH"] = os.getcwd()
        # Force AUTOSTART_DASHBOARD to false so the bot doesn't try to kill/restart the dashboard
        env["AUTOSTART_DASHBOARD"] = "false"
        bot_proc = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=os.getcwd(),
            env=env
        )
        return {"message": "Bot process started"}
        
    elif req.command == 'stop':
        db.send_command(req.command)
        bot_proc = None
        return {"message": "Stop command sent"}
    else:
        db.send_command(req.command)
        return {"message": f"Command {req.command} sent"}

@app.post("/api/symbols", dependencies=[Depends(authenticate)])
async def add_symbol(req: SymbolRequest):
    db.add_symbol(req.symbol)
    return {"message": f"Symbol {req.symbol} added"}

@app.delete("/api/symbols/{symbol}", dependencies=[Depends(authenticate)])
async def remove_symbol(symbol: str, user=Depends(authenticate)):
    db.remove_symbol(symbol)
    return {"message": f"Symbol {symbol} removed"}

@app.post("/api/chat", dependencies=[Depends(authenticate)])
async def chat_with_agent(req: ChatRequest):
    global orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    try:
        report = await orchestrator.run_analysis(req.message, thread_id=req.thread_id)
        
        # Extract parsed coin and timeframe for storage
        coin = "BTC"
        timeframe = "1h"
        for symbol in ["BTC", "ETH", "SOL", "ADA", "DOT", "XRP", "LTC"]:
            if f"{symbol} Thesis" in report or f"Report for {symbol}" in report or symbol in req.message.upper():
                coin = symbol
                break
        db.add_report(coin, timeframe, req.message, report)
        return {"response": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/upload", dependencies=[Depends(authenticate)])
async def upload_rag_document(file: UploadFile = File(...)):
    try:
        doc_dir = "./data/documents"
        os.makedirs(doc_dir, exist_ok=True)
        file_path = os.path.join(doc_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Trigger ingestion
        from app.rag.retriever import RAGService
        service = RAGService()
        chunks_count = service.ingest_directory(doc_dir)
        
        return {
            "message": f"File '{file.filename}' uploaded and indexed successfully",
            "chunks_ingested": chunks_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports", dependencies=[Depends(authenticate)])
async def get_reports():
    return db.get_reports()

# Serve Frontend
@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("dashboard/static/index.html", "r", encoding="utf-8") as f:
        return f.read()

# Static files (for CSS/JS if separated, but we'll put it in index.html for simplicity)
# app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
