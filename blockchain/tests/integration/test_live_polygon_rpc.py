"""
Post-Integration Live Tests: Polygon Amoy Testnet RPC Connectivity
Run with: pytest blockchain/tests/integration/test_live_polygon_rpc.py --live-polygon -v
"""

import pytest
web3 = pytest.importorskip("web3")
from web3 import Web3
from blockchain.config import settings


@pytest.fixture
def live_w3():
    w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL, request_kwargs={"timeout": 15.0}))
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except Exception:
        pass
    return w3


@pytest.mark.live_polygon
def test_live_polygon_amoy_connection(live_w3):
    """Verify live connectivity to Polygon Amoy RPC endpoint."""
    assert live_w3.is_connected(), f"Failed to connect to Polygon RPC at {settings.POLYGON_RPC_URL}"


@pytest.mark.live_polygon
def test_live_polygon_amoy_chain_id(live_w3):
    """Verify chain ID matches Polygon Amoy Testnet (80002)."""
    chain_id = live_w3.eth.chain_id
    assert chain_id == 80002, f"Expected Chain ID 80002 for Polygon Amoy, got {chain_id}"


@pytest.mark.live_polygon
def test_live_polygon_amoy_latest_block(live_w3):
    """Verify latest block number and block headers can be fetched."""
    block_num = live_w3.eth.block_number
    assert block_num > 0
    
    block = live_w3.eth.get_block("latest")
    assert block is not None
    assert "timestamp" in block
    assert "hash" in block


@pytest.mark.live_polygon
def test_live_polygon_amoy_gas_price(live_w3):
    """Verify gas price estimation from Polygon network."""
    gas_price = live_w3.eth.gas_price
    assert gas_price > 0
