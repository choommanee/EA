"""
Gold Trading Dashboard - FastAPI Backend
Real-time integration with MT5 trading system
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass, asdict
import uvicorn
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gold Trading Dashboard API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@dataclass
class TradingSignal:
    id: int
    type: str  # BUY/SELL
    entry: float
    sl: float
    tp: List[float]
    confidence: int
    status: str  # pending/active/executed/closed
    time: str
    provider: str
    analysis: str
    risk_reward: str
    symbol: str = "XAUUSD"

@dataclass
class Position:
    id: int
    type: str
    lots: float
    open_price: float
    current_price: float
    pips: int
    profit: float
    time: str
    symbol: str = "XAUUSD"

@dataclass
class AccountInfo:
    balance: float
    equity: float
    margin: float
    free_margin: float
    profit: float
    today_pnl: float
    weekly_pnl: float
    total_trades: int
    win_rate: float

class MT5DataProvider:
    def __init__(self):
        self.symbol = "GOLDm#"  # Adjust based on your broker
        self.connected = False
        self.last_price = 0.0
        
    async def initialize(self):
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                logger.error("MT5 initialization failed")
                return False
            
            # Check symbol
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logger.error(f"Symbol {self.symbol} not found")
                # Try alternative symbols
                for alt_symbol in ["XAUUSD", "GOLD", "XAU/USD"]:
                    if mt5.symbol_info(alt_symbol):
                        self.symbol = alt_symbol
                        logger.info(f"Using alternative symbol: {alt_symbol}")
                        break
                else:
                    logger.error("No valid gold symbol found")
                    return False
            
            self.connected = True
            logger.info(f"MT5 connected successfully with symbol: {self.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False

    async def get_current_price(self) -> Optional[float]:
        """Get current gold price"""
        try:
            if not self.connected:
                return None
                
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                self.last_price = (tick.bid + tick.ask) / 2
                return self.last_price
            return None
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        try:
            if not self.connected:
                return None
                
            account = mt5.account_info()
            if account:
                return AccountInfo(
                    balance=account.balance,
                    equity=account.equity,
                    margin=account.margin,
                    free_margin=account.margin_free,
                    profit=account.profit,
                    today_pnl=account.profit,  # Simplified
                    weekly_pnl=account.profit,  # Simplified
                    total_trades=0,  # Would need to calculate
                    win_rate=75.0  # Would need to calculate
                )
            return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        try:
            if not self.connected:
                return []
                
            positions = mt5.positions_get(symbol=self.symbol)
            if positions:
                result = []
                for pos in positions:
                    current_price = await self.get_current_price()
                    if current_price:
                        pips = int((current_price - pos.price_open) * (1 if pos.type == 0 else -1) * 100)
                        profit = pos.profit
                        
                        result.append(Position(
                            id=pos.ticket,
                            type="BUY" if pos.type == 0 else "SELL",
                            lots=pos.volume,
                            open_price=pos.price_open,
                            current_price=current_price,
                            pips=pips,
                            profit=profit,
                            time=datetime.fromtimestamp(pos.time).strftime("%H:%M")
                        ))
                return result
            return []
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

# Initialize MT5 provider
mt5_provider = MT5DataProvider()

# Database setup
def init_database():
    """Initialize SQLite database for signals and history"""
    conn = sqlite3.connect('trading_dashboard.db')
    cursor = conn.cursor()
    
    # Signals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            entry REAL NOT NULL,
            sl REAL NOT NULL,
            tp TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            status TEXT NOT NULL,
            time TEXT NOT NULL,
            provider TEXT NOT NULL,
            analysis TEXT NOT NULL,
            risk_reward TEXT NOT NULL,
            symbol TEXT DEFAULT 'XAUUSD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Price history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# API Routes
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    init_database()
    await mt5_provider.initialize()
    
    # Start background tasks
    asyncio.create_task(price_update_task())
    asyncio.create_task(signal_generation_task())

@app.get("/")
async def root():
    return {"message": "Gold Trading Dashboard API", "status": "running"}

@app.get("/api/account")
async def get_account():
    """Get account information"""
    account = await mt5_provider.get_account_info()
    if account:
        return asdict(account)
    else:
        # Return mock data if MT5 not available
        return {
            "balance": 25000.0,
            "equity": 27150.0,
            "margin": 850.0,
            "free_margin": 26300.0,
            "profit": 2150.0,
            "today_pnl": 680.0,
            "weekly_pnl": 1450.0,
            "total_trades": 47,
            "win_rate": 74.5
        }

@app.get("/api/price")
async def get_current_price():
    """Get current gold price"""
    price = await mt5_provider.get_current_price()
    if price:
        return {"symbol": "XAUUSD", "price": price, "timestamp": datetime.now().isoformat()}
    else:
        # Return mock data
        return {"symbol": "XAUUSD", "price": 2032.45, "timestamp": datetime.now().isoformat()}

@app.get("/api/positions")
async def get_positions():
    """Get open positions"""
    positions = await mt5_provider.get_positions()
    return [asdict(pos) for pos in positions]

@app.get("/api/signals")
async def get_signals():
    """Get trading signals"""
    conn = sqlite3.connect('trading_dashboard.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM signals 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    
    signals = []
    for row in cursor.fetchall():
        signals.append({
            "id": row[0],
            "type": row[1],
            "entry": row[2],
            "sl": row[3],
            "tp": json.loads(row[4]),
            "confidence": row[5],
            "status": row[6],
            "time": row[7],
            "provider": row[8],
            "analysis": row[9],
            "risk_reward": row[10],
            "symbol": row[11]
        })
    
    conn.close()
    return signals

@app.post("/api/signals")
async def create_signal(signal_data: dict):
    """Create new trading signal"""
    conn = sqlite3.connect('trading_dashboard.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO signals (type, entry, sl, tp, confidence, status, time, provider, analysis, risk_reward, symbol)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        signal_data["type"],
        signal_data["entry"],
        signal_data["sl"],
        json.dumps(signal_data["tp"]),
        signal_data["confidence"],
        signal_data["status"],
        signal_data["time"],
        signal_data["provider"],
        signal_data["analysis"],
        signal_data["risk_reward"],
        signal_data.get("symbol", "XAUUSD")
    ))
    
    conn.commit()
    signal_id = cursor.lastrowid
    conn.close()
    
    # Broadcast new signal
    await manager.broadcast(json.dumps({
        "type": "new_signal",
        "data": {**signal_data, "id": signal_id}
    }))
    
    return {"id": signal_id, "status": "created"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background tasks
async def price_update_task():
    """Background task to update prices"""
    while True:
        try:
            price = await mt5_provider.get_current_price()
            if price:
                # Store in database
                conn = sqlite3.connect('trading_dashboard.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO price_history (symbol, price)
                    VALUES (?, ?)
                ''', ("XAUUSD", price))
                conn.commit()
                conn.close()
                
                # Broadcast price update
                await manager.broadcast(json.dumps({
                    "type": "price_update",
                    "data": {
                        "symbol": "XAUUSD",
                        "price": price,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
            
            await asyncio.sleep(2)  # Update every 2 seconds
        except Exception as e:
            logger.error(f"Price update task error: {e}")
            await asyncio.sleep(5)

async def signal_generation_task():
    """Background task to generate signals from trading system"""
    while True:
        try:
            # This would integrate with your working_scalping_trader.py
            # For now, we'll simulate signal generation
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Signal generation task error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
