"""
Trading System Integration Module
Connects web dashboard with existing Python trading system
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import logging

# Add parent directory to path to import existing trading system
sys.path.append(str(Path(__file__).parent.parent))

try:
    from working_scalping_trader import WorkingGoldScalpingTrader
except ImportError:
    logging.warning("Could not import WorkingGoldScalpingTrader - using mock data")
    WorkingGoldScalpingTrader = None

class TradingSystemBridge:
    """Bridge between web dashboard and existing trading system"""
    
    def __init__(self):
        self.trader = None
        self.is_running = False
        self.signals_queue = []
        
    async def initialize_trader(self):
        """Initialize the existing trading system"""
        try:
            if WorkingGoldScalpingTrader:
                self.trader = WorkingGoldScalpingTrader()
                # Initialize MT5 connection
                if hasattr(self.trader, 'initialize_mt5'):
                    success = self.trader.initialize_mt5()
                    if success:
                        logging.info("Trading system initialized successfully")
                        return True
                    else:
                        logging.error("Failed to initialize MT5 connection")
                        return False
                else:
                    logging.warning("Trading system missing initialize_mt5 method")
                    return False
            else:
                logging.warning("Trading system not available - using mock mode")
                return False
        except Exception as e:
            logging.error(f"Error initializing trading system: {e}")
            return False
    
    async def get_live_signals(self):
        """Get live trading signals from the existing system"""
        try:
            if self.trader and hasattr(self.trader, 'generate_bb_zigzag_ai_signal'):
                signal_data = self.trader.generate_bb_zigzag_ai_signal()
                if signal_data and signal_data.get('signal') != 'HOLD':
                    # Convert to web dashboard format
                    signal = {
                        'type': signal_data['signal'],
                        'entry': signal_data.get('entry_price', 0),
                        'sl': signal_data.get('sl', 0),
                        'tp': signal_data.get('tp_levels', []),
                        'confidence': signal_data.get('confidence', 0),
                        'status': 'pending',
                        'time': datetime.now().strftime('%H:%M'),
                        'provider': 'AI Gold Expert',
                        'analysis': signal_data.get('reason', 'Technical analysis signal'),
                        'risk_reward': f"1:{signal_data.get('risk_reward', 2.0):.1f}",
                        'symbol': 'XAUUSD'
                    }
                    return signal
            return None
        except Exception as e:
            logging.error(f"Error getting live signals: {e}")
            return None
    
    async def execute_trade(self, signal_data):
        """Execute trade through existing trading system"""
        try:
            if self.trader and hasattr(self.trader, 'place_order'):
                result = self.trader.place_order(
                    signal=signal_data['type'],
                    entry_price=signal_data['entry'],
                    sl=signal_data['sl'],
                    tp=signal_data['tp'][0] if signal_data['tp'] else None
                )
                return result
            else:
                # Mock execution for testing
                logging.info(f"Mock execution: {signal_data['type']} at {signal_data['entry']}")
                return {'success': True, 'order_id': f"mock_{datetime.now().timestamp()}"}
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_account_status(self):
        """Get account information from trading system"""
        try:
            if self.trader and hasattr(self.trader, 'get_account_info'):
                return self.trader.get_account_info()
            return None
        except Exception as e:
            logging.error(f"Error getting account status: {e}")
            return None
    
    async def get_open_positions(self):
        """Get open positions from trading system"""
        try:
            if self.trader and hasattr(self.trader, 'get_positions'):
                return self.trader.get_positions()
            return []
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return []

# Global instance
trading_bridge = TradingSystemBridge()
