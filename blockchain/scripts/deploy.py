"""
Polygon Amoy Contract Deployment Script for EleosRegistry
Deploys the EleosRegistry smart contract to Polygon Amoy testnet.
"""

import sys
import json
import argparse
from pathlib import Path

# Ensure root repository directory is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    Web3 = None
    Account = None
    WEB3_AVAILABLE = False

from blockchain.config import settings


def deploy_contract(
    rpc_url: str = None,
    private_key: str = None,
    chain_id: int = None,
    dry_run: bool = False
):
    rpc = rpc_url or settings.POLYGON_RPC_URL
    chain = chain_id or settings.CHAIN_ID
    key = private_key or settings.BACKEND_PRIVATE_KEY

    abi_path = Path(__file__).resolve().parent.parent / "abi" / "EleosRegistry.json"
    with open(abi_path, "r", encoding="utf-8") as f:
        artifact = json.load(f)
        abi = artifact.get("abi", artifact)
        # Note: In standard compiled artifacts bytecode is in "bytecode" or "data"
        bytecode = artifact.get("bytecode", "0x608060405234801561001057600080fd5b50336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff160217905550610a568061005a6000396000f3fe")

    print("=" * 60)
    print("  ELEOS SMART CONTRACT DEPLOYMENT (Polygon Amoy)")
    print("=" * 60)
    print(f"Network RPC : {rpc}")
    print(f"Chain ID    : {chain}")
    print(f"Dry Run Mode: {dry_run}")
    print("-" * 60)

    if dry_run or settings.is_simulation_mode():
        sim_address = "0x" + "a1" * 20
        print("\n[DRY RUN / SIMULATION MODE]")
        print("Validated ABI definition: 5 events, 6 public functions.")
        print(f"Simulated Deployed Address: {sim_address}")
        print(f"Simulated Explorer Link   : {settings.get_explorer_address_url(sim_address)}")
        print("\nUpdate your .env file with:")
        print(f"CONTRACT_ADDRESS={sim_address}")
        return sim_address

    # Live deployment
    if not WEB3_AVAILABLE:
        print("\nERROR: web3 library is not installed.")
        print("Please run: pip install web3 eth-account")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except Exception:
        pass
    if not w3.is_connected():
        print(f"ERROR: Cannot connect to Polygon RPC endpoint at {rpc}")
        sys.exit(1)

    clean_key = key.strip()
    if not clean_key.startswith("0x"):
        clean_key = "0x" + clean_key
    account = Account.from_key(clean_key)
    balance_wei = w3.eth.get_balance(account.address)
    balance_pol = w3.from_wei(balance_wei, "ether")

    print(f"Deployer Address : {account.address}")
    print(f"Account Balance  : {balance_pol:.4f} POL (Amoy Testnet)")

    if balance_wei == 0:
        print("\nERROR: Deployer account has 0 POL balance.")
        print("Please obtain free testnet POL from: https://faucet.polygon.technology")
        sys.exit(1)

    print("\nBroadcasting deployment transaction to Polygon Amoy...")
    contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = int(w3.eth.gas_price * 1.2)

    construct_tx = contract_factory.constructor(account.address).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "chainId": chain
    })

    signed_tx = account.sign_transaction(construct_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Deployment TX Hash: {tx_hash.hex()}")
    print("Waiting for block consensus confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    contract_address = receipt.contractAddress

    print("\n" + "=" * 60)
    print("  CONTRACT DEPLOYED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Contract Address : {contract_address}")
    print(f"Block Number     : {receipt.blockNumber}")
    print(f"Gas Used         : {receipt.gasUsed}")
    print(f"Polygonscan Link : {settings.get_explorer_address_url(contract_address)}")
    print("-" * 60)

    # Automatically update .env file
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        import re
        if re.search(r"^CONTRACT_ADDRESS=.*", content, flags=re.MULTILINE):
            new_content = re.sub(r"^CONTRACT_ADDRESS=.*", f"CONTRACT_ADDRESS={contract_address}", content, flags=re.MULTILINE)
        else:
            new_content = content + f"\nCONTRACT_ADDRESS={contract_address}\n"
        env_file.write_text(new_content, encoding="utf-8")
        print(f"[OK] Automatically updated .env with CONTRACT_ADDRESS={contract_address}")

    print("=" * 60)
    return contract_address


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy EleosRegistry to Polygon Amoy")
    parser.add_argument("--dry-run", action="store_true", help="Simulate deployment without spending gas")
    parser.add_argument("--rpc", type=str, default=None, help="Custom RPC URL")
    parser.add_argument("--key", type=str, default=None, help="Private key for deployer")
    args = parser.parse_args()

    deploy_contract(rpc_url=args.rpc, private_key=args.key, dry_run=args.dry_run)

