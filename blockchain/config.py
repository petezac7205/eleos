"""
Blockchain Configuration Module (Polygon Amoy Testnet)
"""

import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class BlockchainSettings(BaseSettings):
    # Polygon Amoy Testnet RPC
    POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "https://polygon-amoy-bor-rpc.publicnode.com")
    CHAIN_ID: int = int(os.getenv("CHAIN_ID", "80002"))  # 80002 for Polygon Amoy Testnet
    
    # Contract Address & Private Key
    CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000000")
    BACKEND_PRIVATE_KEY: str = os.getenv("BACKEND_PRIVATE_KEY", "your_private_key_here")
    
    # Block Explorer
    POLYGONSCAN_BASE_URL: str = os.getenv("POLYGONSCAN_BASE_URL", "https://amoy.polygonscan.com")
    
    # Gas Settings
    DEFAULT_GAS_LIMIT: int = 150000
    GAS_PRICE_MULTIPLIER: float = 1.15  # 15% buffer for testnet congestion
    
    # Simulation & Test Mode
    TEST_MODE: bool = os.getenv("BLOCKCHAIN_TEST_MODE", "false").lower() in ("true", "1", "yes")

    def is_simulation_mode(self) -> bool:
        """
        Determines whether the blockchain service should run in deterministic simulation mode.
        Simulation mode activates if:
        1. TEST_MODE is explicitly True, OR
        2. BACKEND_PRIVATE_KEY is a placeholder or not 64 hex chars, OR
        3. CONTRACT_ADDRESS is zero address or placeholder.
        """
        if self.TEST_MODE:
            return True
        key = self.BACKEND_PRIVATE_KEY.strip().removeprefix("0x")
        if not key or "placeholder" in key or "your_private_key" in key or len(key) != 64:
            return True
        addr = self.CONTRACT_ADDRESS.strip()
        if not addr or addr == "0x0000000000000000000000000000000000000000" or "0x0000" in addr:
            return True
        return False

    def get_explorer_tx_url(self, tx_hash: str) -> str:
        """Returns the public Polygonscan URL for a transaction hash."""
        return f"{self.POLYGONSCAN_BASE_URL}/tx/{tx_hash}"

    def get_explorer_address_url(self, address: str) -> str:
        """Returns the public Polygonscan URL for an address/contract."""
        return f"{self.POLYGONSCAN_BASE_URL}/address/{address}"


settings = BlockchainSettings()

