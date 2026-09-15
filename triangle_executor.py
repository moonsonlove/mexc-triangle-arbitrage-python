from dataclasses import dataclass
from typing import Tuple
import time
from triangle_calculator import Triangle
from api_client import APIClient
from config import ConfigManager

@dataclass
class ExecutionResult:
    success: bool
    initial_usdt: float = 5.0
    final_usdt: float = 0.0
    gross_profit: float = 0.0
    total_fees: float = 0.0
    net_profit: float = 0.0
    net_profit_pct: float = 0.0
    execution_time: float = 0.0
    error_message: str = ""

class TriangleExecutor:
    _instance = None
    
    def __init__(self):
        self.api_client = APIClient()
        self.config = ConfigManager.instance().get_config()
    
    @staticmethod
    def instance():
        if TriangleExecutor._instance is None:
            TriangleExecutor._instance = TriangleExecutor()
        return TriangleExecutor._instance
    
    def execute(self, triangle: Triangle) -> ExecutionResult:
        """Execute triangle: returns result with actual filled quantities"""
        start_time = time.time()
        result = ExecutionResult()
        result.initial_usdt = self.config.trade_amount_usdt
        
        if self.config.dry_run:
            return self.execute_dry_run(triangle, result, start_time)
        else:
            return self.execute_real_trade(triangle, result, start_time)
    
    def execute_dry_run(self, triangle: Triangle, result: ExecutionResult, start_time: float) -> ExecutionResult:
        """Execute dry run (simulation)"""
        result.success = True
        result.final_usdt = result.initial_usdt * 1.005  # Assume 0.5% profit
        result.gross_profit = result.final_usdt - result.initial_usdt
        result.net_profit = result.gross_profit
        result.net_profit_pct = (result.net_profit / result.initial_usdt) * 100
        result.total_fees = result.initial_usdt * (self.config.taker_fee_percent / 100) * 3
        result.execution_time = (time.time() - start_time) * 1000
        
        return result
    
    def execute_real_trade(self, triangle: Triangle, result: ExecutionResult, start_time: float) -> ExecutionResult:
        """Execute real trade"""
        try:
            # Leg 1: USDT -> Currency A
            leg1_result, leg1_quantity = self.execute_leg_1(triangle)
            if not leg1_result:
                result.success = False
                result.error_message = "Leg 1 execution failed"
                return result
            
            # Leg 2: Currency A -> Currency B
            leg2_result, leg2_quantity = self.execute_leg_2(triangle, leg1_quantity)
            if not leg2_result:
                result.success = False
                result.error_message = "Leg 2 execution failed"
                return result
            
            # Leg 3: Currency B -> USDT
            leg3_result, final_usdt = self.execute_leg_3(triangle, leg2_quantity)
            if not leg3_result:
                result.success = False
                result.error_message = "Leg 3 execution failed"
                return result
            
            # Calculate results
            result.success = True
            result.final_usdt = final_usdt
            result.gross_profit = final_usdt - result.initial_usdt
            result.net_profit = result.gross_profit
            result.net_profit_pct = (result.net_profit / result.initial_usdt) * 100
            result.total_fees = result.initial_usdt * (self.config.taker_fee_percent / 100) * 3
            result.execution_time = (time.time() - start_time) * 1000
            
            return result
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.execution_time = (time.time() - start_time) * 1000
            return result
    
    def execute_leg_1(self, triangle: Triangle) -> Tuple[bool, float]:
        """Execute leg 1: USDT -> Currency A"""
        order = self.api_client.place_order(
            triangle.symbol_a,
            "BUY",
            self.config.trade_amount_usdt / 100,  # dummy quantity
            100  # dummy price
        )
        if order:
            return True, order.filled_quantity
        return False, 0.0
    
    def execute_leg_2(self, triangle: Triangle, leg1_quantity: float) -> Tuple[bool, float]:
        """Execute leg 2: Currency A -> Currency B"""
        order = self.api_client.place_order(
            triangle.symbol_b,
            "SELL",
            leg1_quantity,
            100  # dummy price
        )
        if order:
            return True, order.filled_quantity
        return False, 0.0
    
    def execute_leg_3(self, triangle: Triangle, leg2_quantity: float) -> Tuple[bool, float]:
        """Execute leg 3: Currency B -> USDT"""
        order = self.api_client.place_order(
            triangle.symbol_c,
            "SELL",
            leg2_quantity,
            100  # dummy price
        )
        if order:
            return True, order.filled_quantity * 100  # dummy conversion to USDT
        return False, 0.0
    
    def apply_taker_fee(self, amount: float) -> float:
        """Apply taker fee to amount"""
        fee = amount * (self.config.taker_fee_percent / 100)
        return amount - fee
