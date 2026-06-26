from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
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

# API Routes
@app.get("/api/status", dependencies=[Depends(authenticate)])
async def get_status():
    return db.get_status()

@app.get("/api/trades", dependencies=[Depends(authenticate)])
async def get_trades():
    return db.get_trades()

@app.get("/api/symbols", dependencies=[Depends(authenticate)])
async def get_symbols():
    return db.get_symbols()

@app.get("/api/logs", dependencies=[Depends(authenticate)])
async def get_logs():
    return db.get_logs(log_path=os.getenv("LOG_FILE", "bot.log"))

@app.post("/api/command", dependencies=[Depends(authenticate)])
async def send_command(req: CommandRequest):
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
