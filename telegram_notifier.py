import requests
from config import ConfigManager
from triangle_calculator import Triangle
from triangle_executor import ExecutionResult

class TelegramNotifier:
    _instance = None
    
    def __init__(self):
        config = ConfigManager.instance().get_config()
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    @staticmethod
    def instance():
        if TelegramNotifier._instance is None:
            TelegramNotifier._instance = TelegramNotifier()
        return TelegramNotifier._instance
    
    def send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(
                f"{self.api_url}/sendMessage",
                data=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    def send_execution_report(self, triangle: Triangle, result: ExecutionResult) -> bool:
        """Send execution report"""
        message = f"""
=== Execution Result ===

Triangle: USDT → {triangle.symbol_a} → {triangle.symbol_b} → USDT

Initial: {result.initial_usdt} USDT
Final: {result.final_usdt:.6f} USDT
Gross Profit: {result.gross_profit:.6f} USDT
Total Fees: {result.total_fees:.6f} USDT
Net Profit: {result.net_profit:.6f} USDT
Net Profit %: {result.net_profit_pct:.4f}%
Execution Time: {result.execution_time:.2f}ms
        """
        return self.send_message(message)
    
    def send_error(self, error_message: str) -> bool:
        """Send error notification"""
        message = f"❌ Error: {error_message}"
        return self.send_message(message)
