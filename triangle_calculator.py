from dataclasses import dataclass
from typing import List
from datetime import datetime
from market_data import MarketData
from config import ConfigManager

@dataclass
class Triangle:
    symbol_a: str  # USDT/A
    symbol_b: str  # A/B
    symbol_c: str  # B/USDT
    
    pattern: str  # "ASK_BID_BID" or "ASK_ASK_BID"
    
    theoretical_return: float = 0.0  # in USDT
    theoretical_return_pct: float = 0.0  # in percent
    
    last_calculation: datetime = None

class TriangleCalculator:
    _instance = None
    
    def __init__(self):
        self.triangles: List[Triangle] = []
        self.market_data = MarketData.instance()
        self.config = ConfigManager.instance().get_config()
    
    @staticmethod
    def instance():
        if TriangleCalculator._instance is None:
            TriangleCalculator._instance = TriangleCalculator()
        return TriangleCalculator._instance
    
    def build_triangles(self, all_pairs: List[str]):
        """Build all possible triangles starting and ending with USDT"""
        self.triangles = []
        self.build_triangles_internal(all_pairs)
    
    def build_triangles_internal(self, pairs: List[str]):
        """Internal method to build triangles"""
        # Extract all currencies from USDT pairs
        currencies = set()
        for pair in pairs:
            if pair.endswith('USDT'):
                currency = pair[:-4]
                currencies.add(currency)
        
        # Build triangles: USDT -> A -> B -> USDT
        for curr_a in currencies:
            pair_1 = f"{curr_a}USDT"
            if pair_1 not in pairs:
                continue
            
            for curr_b in currencies:
                if curr_a == curr_b:
                    continue
                
                pair_2 = f"{curr_a}{curr_b}" if f"{curr_a}{curr_b}" in pairs else None
                if not pair_2:
                    pair_2 = f"{curr_b}{curr_a}" if f"{curr_b}{curr_a}" in pairs else None
                if not pair_2:
                    continue
                
                pair_3 = f"{curr_b}USDT"
                if pair_3 not in pairs:
                    continue
                
                triangle = Triangle(
                    symbol_a=pair_1,
                    symbol_b=pair_2,
                    symbol_c=pair_3,
                    pattern="ASK_BID_BID",
                    last_calculation=datetime.now()
                )
                
                self.triangles.append(triangle)
    
    def recalculate_for_symbol(self, symbol: str) -> List[Triangle]:
        """Recalculate only triangles containing this symbol"""
        affected = []
        for triangle in self.triangles:
            if symbol in [triangle.symbol_a, triangle.symbol_b, triangle.symbol_c]:
                profit = self.calculate_net_profit(triangle)
                triangle.theoretical_return_pct = profit
                affected.append(triangle)
        return affected
    
    def get_profitable_triangles(self) -> List[Triangle]:
        """Get all profitable triangles (>= MIN_NET_PROFIT_PERCENT)"""
        profitable = []
        for triangle in self.triangles:
            profit = self.calculate_net_profit(triangle)
            if profit >= self.config.min_net_profit_percent:
                triangle.theoretical_return_pct = profit
                profitable.append(triangle)
        return profitable
    
    def get_all_triangles(self) -> List[Triangle]:
        """Get all triangles"""
        return self.triangles
    
    def calculate_triangle(self, a: str, b: str) -> Triangle:
        """Calculate triangle profit"""
        pass
    
    def calculate_net_profit(self, triangle: Triangle) -> float:
        """Calculate net profit percentage for a triangle"""
        # Get prices
        price_a = self.market_data.get_price(triangle.symbol_a)
        price_b = self.market_data.get_price(triangle.symbol_b)
        price_c = self.market_data.get_price(triangle.symbol_c)
        
        if price_a == 0 or price_b == 0 or price_c == 0:
            return 0.0
        
        # Calculate flow: 1 USDT -> currency_a -> currency_b -> USDT
        initial = self.config.trade_amount_usdt
        
        # Step 1: USDT -> Currency A
        fee_1 = initial * (self.config.taker_fee_percent / 100)
        amount_after_fee_1 = initial - fee_1
        currency_a = amount_after_fee_1 / price_a
        
        # Step 2: Currency A -> Currency B
        fee_2 = currency_a * price_a * (self.config.taker_fee_percent / 100)
        currency_b = (currency_a * price_a - fee_2) / price_b
        
        # Step 3: Currency B -> USDT
        fee_3 = currency_b * price_b * (self.config.taker_fee_percent / 100)
        final_usdt = currency_b * price_c - fee_3
        
        # Calculate profit
        net_profit = final_usdt - initial
        profit_pct = (net_profit / initial) * 100
        
        triangle.theoretical_return = net_profit
        
        return profit_pct
