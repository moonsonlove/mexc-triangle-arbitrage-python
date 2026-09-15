import requests
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import List, Dict
from urllib.parse import urlencode
from config import ConfigManager

@dataclass
class TradeInfo:
    symbol: str
    side: str  # BUY or SELL
    price: float
    quantity: float
    order_id: str
    status: str  # FILLED, PARTIALLY_FILLED, CANCELED, REJECTED
    filled_quantity: float = 0.0

class APIClient:
    def __init__(self):
        config = ConfigManager.instance().get_config()
        self.api_key = config.mexc_api_key
        self.api_secret = config.mexc_api_secret
        self.base_url = "https://api.mexc.com"
        self.ws_connected = False
    
    def fetch_all_trading_pairs(self) -> List[str]:
        """Fetch all USDT trading pairs"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/exchangeInfo", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pairs = []
            for symbol in data.get('symbols', []):
                if symbol['symbol'].endswith('USDT') and symbol['status'] == 'TRADING':
                    pairs.append(symbol['symbol'])
            
            return pairs
        except Exception as e:
            print(f"Error fetching trading pairs: {e}")
            return []
    
    def get_orderbook(self, symbol: str) -> Dict:
        """Get orderbook for a symbol"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v3/depth",
                params={'symbol': symbol, 'limit': 10},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting orderbook for {symbol}: {e}")
            return {}
    
    def place_order(self, symbol: str, side: str, quantity: float, price: float) -> TradeInfo:
        """Place a limit order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': quantity,
                'price': price,
                'timestamp': int(time.time() * 1000)
            }
            
            signature = self._sign_request(params)
            params['signature'] = signature
            
            headers = {'X-MEXC-APIKEY': self.api_key}
            response = requests.post(
                f"{self.base_url}/api/v3/order",
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return TradeInfo(
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                order_id=data.get('orderId', ''),
                status=data.get('status', ''),
                filled_quantity=float(data.get('executedQty', 0))
            )
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
    
    def check_order_status(self, order_id: str) -> TradeInfo:
        """Check order status"""
        try:
            params = {
                'orderId': order_id,
                'timestamp': int(time.time() * 1000)
            }
            
            signature = self._sign_request(params)
            params['signature'] = signature
            
            headers = {'X-MEXC-APIKEY': self.api_key}
            response = requests.get(
                f"{self.base_url}/api/v3/order",
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error checking order status: {e}")
            return None
    
    def connect_websocket(self, symbols: List[str]):
        """Connect to WebSocket for real-time prices"""
        self.ws_connected = True
    
    def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        self.ws_connected = False
    
    def is_websocket_connected(self) -> bool:
        return self.ws_connected
    
    def _sign_request(self, params: Dict) -> str:
        """Sign request with HMAC SHA256"""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
