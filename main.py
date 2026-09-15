#!/usr/bin/env python3

import time
import sys
from config import ConfigManager
from api_client import APIClient
from market_data import MarketData
from triangle_calculator import TriangleCalculator
from triangle_executor import TriangleExecutor
from telegram_notifier import TelegramNotifier

class ArbitrageBot:
    def __init__(self):
        print("=== MEXC Triangle Arbitrage Bot ===")
        self.running = False
    
    def initialize(self) -> bool:
        """Initialize bot"""
        # Load configuration
        config_mgr = ConfigManager.instance()
        if not config_mgr.load_from_env():
            print("❌ Failed to load configuration")
            return False
        
        config = config_mgr.get_config()
        print("✅ Configuration loaded successfully")
        print(f"  Trade Amount: {config.trade_amount_usdt} USDT")
        print(f"  Taker Fee: {config.taker_fee_percent}%")
        print(f"  Min Profit: {config.min_net_profit_percent}%")
        print(f"  Dry Run: {'YES' if config.dry_run else 'NO'}")
        
        # Fetch all trading pairs
        print("\nFetching MEXC trading pairs...")
        api = APIClient()
        pairs = api.fetch_all_trading_pairs()
        
        if not pairs:
            print("❌ Failed to fetch trading pairs")
            return False
        
        print(f"✅ Fetched {len(pairs)} trading pairs")
        
        # Initialize market data
        market_data = MarketData.instance()
        market_data.set_all_symbols(pairs)
        
        # Build triangles
        print("\nBuilding triangles...")
        triangle_calc = TriangleCalculator.instance()
        triangle_calc.build_triangles(pairs)
        
        triangles = triangle_calc.get_all_triangles()
        print(f"✅ Built {len(triangles)} potential triangles")
        
        # Connect WebSocket
        print("\nConnecting to MEXC WebSocket...")
        api.connect_websocket(pairs)
        
        return True
    
    def run(self):
        """Main bot loop"""
        self.running = True
        print("\n=== Bot Started ===")
        
        triangle_calc = TriangleCalculator.instance()
        executor = TriangleExecutor.instance()
        notifier = TelegramNotifier.instance()
        
        check_count = 0
        
        try:
            while self.running:
                check_count += 1
                
                # Get profitable triangles
                profitable = triangle_calc.get_profitable_triangles()
                
                if profitable:
                    print(f"\n[Check #{check_count}] Found {len(profitable)} profitable triangle(s)")
                    
                    # Execute each profitable triangle
                    for triangle in profitable:
                        print(f"\nExecuting triangle: USDT → {triangle.symbol_a} → {triangle.symbol_b} → USDT")
                        print(f"Expected profit: {triangle.theoretical_return_pct:.4f}%")
                        
                        result = executor.execute(triangle)
                        
                        if result.success:
                            print("\n=== Execution Result ===")
                            print(f"Initial: {result.initial_usdt} USDT")
                            print(f"Final: {result.final_usdt:.6f} USDT")
                            print(f"Gross Profit: {result.gross_profit:.6f} USDT")
                            print(f"Total Fees: {result.total_fees:.6f} USDT")
                            print(f"Net Profit: {result.net_profit:.6f} USDT")
                            print(f"Net Profit %: {result.net_profit_pct:.4f}%")
                            print(f"Execution Time: {result.execution_time:.2f}ms")
                            
                            # Send Telegram notification
                            notifier.send_execution_report(triangle, result)
                        else:
                            print(f"❌ Execution failed: {result.error_message}")
                            notifier.send_error(result.error_message)
                
                # Sleep before next check (1 second)
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n⏹️ Stopping bot...")
            self.stop()
    
    def stop(self):
        """Stop bot"""
        self.running = False
        api = APIClient()
        api.disconnect_websocket()

def main():
    try:
        bot = ArbitrageBot()
        
        if not bot.initialize():
            print("❌ Bot initialization failed")
            sys.exit(1)
        
        bot.run()
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
