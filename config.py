import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    mexc_api_key: str = os.getenv('MEXC_API_KEY')
    mexc_api_secret: str = os.getenv('MEXC_API_SECRET')
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID')
    
    trade_amount_usdt: float = float(os.getenv('TRADE_AMOUNT_USDT', 5.0))
    taker_fee_percent: float = float(os.getenv('TAKER_FEE_PERCENT', 0.05))
    min_net_profit_percent: float = float(os.getenv('MIN_NET_PROFIT_PERCENT', 0.50))
    
    dry_run: bool = os.getenv('DRY_RUN', 'false').lower() == 'true'

class ConfigManager:
    _instance = None
    
    def __init__(self):
        self.config = Config()
    
    @staticmethod
    def instance():
        if ConfigManager._instance is None:
            ConfigManager._instance = ConfigManager()
        return ConfigManager._instance
    
    def load_from_env(self) -> bool:
        return all([
            self.config.mexc_api_key,
            self.config.mexc_api_secret,
            self.config.telegram_bot_token,
            self.config.telegram_chat_id
        ])
    
    def get_config(self) -> Config:
        return self.config
