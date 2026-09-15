from typing import Dict, List

class MarketData:
    _instance = None
    
    def __init__(self):
        self.symbols: List[str] = []
        self.prices: Dict[str, float] = {}
    
    @staticmethod
    def instance():
        if MarketData._instance is None:
            MarketData._instance = MarketData()
        return MarketData._instance
    
    def set_all_symbols(self, symbols: List[str]):
        """Set all trading symbols"""
        self.symbols = symbols
        for symbol in symbols:
            if symbol not in self.prices:
                self.prices[symbol] = 0.0
    
    def update_price(self, symbol: str, price: float):
        """Update price for a symbol"""
        self.prices[symbol] = price
    
    def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        return self.prices.get(symbol, 0.0)
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols"""
        return self.symbols
