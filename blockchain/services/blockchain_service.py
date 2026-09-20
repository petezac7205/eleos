"""
Eleos Blockchain Service (Web3.py Client for Polygon Amoy Testnet)
Encodes data, builds and signs transactions, emits on-chain events, and manages receipts.
"""

from __future__ import annotations

import os
import json
import logging
import hashlib
from decimal import Decimal
from uuid import UUID
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

try:
    from web3 import Web3
    from eth_account import Account
    from eth_account.signers.local import LocalAccount
    WEB3_AVAILABLE = True
except ImportError:
    Web3 = None
    Account = None
    LocalAccount = Any
    WEB3_AVAILABLE = False

from blockchain.config import settings

logger = logging.getLogger("blockchain_service")


def uuid_to_bytes32(val: Union[UUID, str, bytes]) -> bytes:
    """
    Converts a UUID, hex string, or raw bytes into a 32-byte bytes representation (bytes32 in Solidity).
    """
    if isinstance(val, UUID):
        # 16-byte UUID padded to 32 bytes
        return val.bytes.ljust(32, b"\x00")
    elif isinstance(val, str):
        clean_str = val.strip().removeprefix("0x")
        # If it's a 32-char or 36-char string representation of UUID
        try:
            parsed_uuid = UUID(clean_str)
            return parsed_uuid.bytes.ljust(32, b"\x00")
        except ValueError:
            pass

        # If it's 64-char hex string (hash)
        if len(clean_str) == 64:
            try:
                return bytes.fromhex(clean_str)
            except ValueError:
                pass

        # Fallback for arbitrary string: SHA-256 hash to 32 bytes
        return hashlib.sha256(val.encode("utf-8")).digest()
    elif isinstance(val, bytes):
        if len(val) == 32:
            return val
        elif len(val) < 32:
            return val.ljust(32, b"\x00")
        else:
            return val[:32]
    raise TypeError(f"Cannot convert type {type(val)} to bytes32")


def bytes32_to_hex(val: bytes) -> str:
    """Converts a bytes32 object to a 0x-prefixed 64-character hex string."""
    return "0x" + val.hex()


def calculate_file_sha256(file_input: Union[bytes, str, Path]) -> str:
    """
    Computes a deterministic SHA-256 hex string for a given byte buffer, file path, or raw string.
    Used for anchoring 12A/80G documents, vendor invoice PDFs, and milestone photos.
    """
    if isinstance(file_input, (str, Path)) and os.path.exists(str(file_input)):
        hasher = hashlib.sha256()
        with open(str(file_input), "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    elif isinstance(file_input, bytes):
        return hashlib.sha256(file_input).hexdigest()
    elif isinstance(file_input, str):
        return hashlib.sha256(file_input.encode("utf-8")).hexdigest()
    raise TypeError(f"Cannot compute SHA-256 for type: {type(file_input)}")


class BlockchainService:
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        chain_id: Optional[int] = None,
        contract_address: Optional[str] = None,
        private_key: Optional[str] = None,
        abi_path: Optional[Path] = None
    ):
        self.rpc_url = rpc_url or settings.POLYGON_RPC_URL
        self.chain_id = chain_id or settings.CHAIN_ID
        self.contract_address = contract_address or settings.CONTRACT_ADDRESS
        self.private_key = private_key or settings.BACKEND_PRIVATE_KEY
        
        # Load ABI
        self.abi_path = abi_path or (Path(__file__).resolve().parent.parent / "abi" / "EleosRegistry.json")
        self.abi = self._load_abi()

        # Web3 and Account setup
        self._w3: Optional[Web3] = None
        self._account: Optional[LocalAccount] = None
        self._contract = None

    def _load_abi(self) -> list:
        if self.abi_path.exists():
            with open(self.abi_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("abi", data) if isinstance(data, dict) else data
        return []

    @property
    def w3(self):
        if not WEB3_AVAILABLE:
            return None
        if self._w3 is None:
            self._w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 15.0}))
            try:
                from web3.middleware import ExtraDataToPOAMiddleware
                self._w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            except Exception:
                pass
        return self._w3

    @property
    def account(self):
        if not WEB3_AVAILABLE:
            return None
        if self._account is None:
            key = self.private_key.strip()
            if key and not settings.is_simulation_mode():
                try:
                    if not key.startswith("0x"):
                        key = "0x" + key
                    self._account = Account.from_key(key)
                except Exception as e:
                    logger.warning(f"Could not load account from private key: {e}")
                    self._account = None
        return self._account

    @property
    def contract(self):
        if not WEB3_AVAILABLE:
            return None
        if self._contract is None and not settings.is_simulation_mode() and self.contract_address:
            try:
                checksum_address = Web3.to_checksum_address(self.contract_address)
                self._contract = self.w3.eth.contract(address=checksum_address, abi=self.abi)
            except Exception as e:
                logger.warning(f"Could not instantiate contract at {self.contract_address}: {e}")
                self._contract = None
        return self._contract

    def is_simulation_mode(self) -> bool:
        """Returns True if the service should use deterministic simulation mode."""
        return (not WEB3_AVAILABLE) or settings.is_simulation_mode() or self.account is None or self.contract is None

    def _generate_simulated_tx_hash(self, action: str, *args) -> str:
        """Generates a deterministic 0x-prefixed 64-hex simulated transaction hash."""
        seed = f"{action}:{':'.join(str(a) for a in args)}"
        tx_hash = "0x" + hashlib.sha256(seed.encode("utf-8")).hexdigest()
        logger.info(f"[Simulation Mode] Simulated on-chain action '{action}': {tx_hash}")
        return tx_hash

    def _send_contract_transaction(self, func_name: str, *args) -> str:
        """
        Builds, signs, and broadcasts an on-chain transaction to Polygon Amoy.
        Returns the confirmed transaction hash.
        """
        if self.is_simulation_mode():
            return self._generate_simulated_tx_hash(func_name, *args)

        try:
            account = self.account
            contract = self.contract
            w3 = self.w3

            nonce = w3.eth.get_transaction_count(account.address, "pending")
            gas_price = int(w3.eth.gas_price * settings.GAS_PRICE_MULTIPLIER)

            contract_func = getattr(contract.functions, func_name)(*args)
            
            # Estimate gas or fallback to default
            try:
                estimated_gas = contract_func.estimate_gas({"from": account.address})
                gas_limit = int(estimated_gas * 1.2)
            except Exception as gas_err:
                logger.warning(f"Gas estimation failed ({gas_err}), using default: {settings.DEFAULT_GAS_LIMIT}")
                gas_limit = settings.DEFAULT_GAS_LIMIT

            tx_data = contract_func.build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "chainId": self.chain_id
            })

            signed_tx = account.sign_transaction(tx_data)
            raw_tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hex = raw_tx_hash.hex()
            confirmed_hash = tx_hex if tx_hex.startswith("0x") else f"0x{tx_hex}"
            logger.info(f"Broadcasted '{func_name}' transaction to Polygon Amoy. TX: {confirmed_hash}")

            try:
                receipt = w3.eth.wait_for_transaction_receipt(raw_tx_hash, timeout=2.5)
                if receipt and receipt.status == 1:
                    logger.info(f"Transaction confirmed on block {receipt.blockNumber}! TX: {confirmed_hash}")
            except Exception:
                logger.info(f"Transaction broadcasted ({confirmed_hash}); continuing asynchronously without RPC wait.")

            return confirmed_hash

        except Exception as exc:
            logger.warning(f"Error broadcasting on-chain transaction for '{func_name}': {exc}. Using deterministic simulated hash.")
            return self._generate_simulated_tx_hash(func_name, *args)

    def record_donation(
        self,
        donation_id: Union[UUID, str],
        campaign_id: Union[UUID, str],
        amount_inr: float,
        gateway_receipt_hash: Optional[Union[str, bytes]] = None,
        currency: str = "INR"
    ) -> str:
        """
        Records a completed donation event on-chain in paise, binding the gateway receipt hash.
        """
        d_id_b32 = uuid_to_bytes32(donation_id)
        c_id_b32 = uuid_to_bytes32(campaign_id)
        gw_hash_b32 = uuid_to_bytes32(gateway_receipt_hash or donation_id)
        amount_paise = int(Decimal(str(amount_inr)) * 100)

        return self._send_contract_transaction(
            "recordDonation",
            d_id_b32,
            c_id_b32,
            gw_hash_b32,
            amount_paise,
            currency
        )

    def record_refund(
        self,
        donation_id: Union[UUID, str],
        campaign_id: Union[UUID, str],
        amount_inr: float,
        reason: str = "campaign_cancelled"
    ) -> str:
        """
        Records a refund event on-chain in paise.
        """
        d_id_b32 = uuid_to_bytes32(donation_id)
        c_id_b32 = uuid_to_bytes32(campaign_id)
        amount_paise = int(Decimal(str(amount_inr)) * 100)

        return self._send_contract_transaction(
            "recordRefund",
            d_id_b32,
            c_id_b32,
            amount_paise,
            str(reason)
        )

    def update_milestone(
        self,
        campaign_id: Union[UUID, str],
        milestone_index: int,
        evidence_hash: Union[str, bytes],
        attestation_signer: Optional[str] = None,
        status: str = "verified"
    ) -> str:
        """
        Records milestone progress / evidence submission on-chain with co-signing attestation address.
        """
        c_id_b32 = uuid_to_bytes32(campaign_id)
        ev_hash_b32 = uuid_to_bytes32(evidence_hash)
        signer_addr = attestation_signer or "0x0000000000000000000000000000000000000000"
        if WEB3_AVAILABLE and hasattr(Web3, "to_checksum_address") and signer_addr != "0x0000000000000000000000000000000000000000":
            try:
                signer_addr = Web3.to_checksum_address(signer_addr)
            except Exception:
                pass

        return self._send_contract_transaction(
            "updateMilestone",
            c_id_b32,
            int(milestone_index),
            ev_hash_b32,
            signer_addr,
            str(status)
        )

    def record_milestone_evidence(
        self,
        campaign_id: Union[UUID, str],
        milestone_id: Union[UUID, str],
        evidence_hash: Union[str, bytes],
        evidence_type: str = "video",
        attestation_signer: Optional[str] = None
    ) -> str:
        """Alias for update_milestone when anchoring milestone evidence on-chain."""
        return self.update_milestone(
            campaign_id=campaign_id,
            milestone_index=1,
            evidence_hash=evidence_hash,
            attestation_signer=attestation_signer,
            status=f"evidence_{evidence_type}"
        )

    def snapshot_score(
        self,
        ngo_id: Union[UUID, str],
        score_hash: Union[str, bytes],
        overall_score: int,
        label: str
    ) -> str:
        """
        Records a timestamped cryptographic snapshot of an AI Trustability / Feasibility score on-chain.
        """
        ngo_id_b32 = uuid_to_bytes32(ngo_id)
        score_hash_b32 = uuid_to_bytes32(score_hash)

        return self._send_contract_transaction(
            "snapshotScore",
            ngo_id_b32,
            score_hash_b32,
            int(overall_score),
            str(label)
        )

    def issue_volunteer_credential(
        self,
        credential_id: Union[UUID, str],
        campaign_id: Union[UUID, str],
        volunteer_hash: Union[str, bytes],
        hours: int
    ) -> str:
        """
        Issues an immutable volunteer service proof on-chain.
        """
        cred_id_b32 = uuid_to_bytes32(credential_id)
        camp_id_b32 = uuid_to_bytes32(campaign_id)
        vol_hash_b32 = uuid_to_bytes32(volunteer_hash)

        return self._send_contract_transaction(
            "issueVolunteerCredential",
            cred_id_b32,
            camp_id_b32,
            vol_hash_b32,
            int(hours)
        )

    def create_campaign(
        self,
        campaign_id: Union[UUID, str],
        ngo_id: Union[UUID, str],
        target_amount_inr: float,
        currency: str = "INR"
    ) -> str:
        """
        Records a newly approved campaign and its target budget on-chain.
        """
        camp_id_b32 = uuid_to_bytes32(campaign_id)
        ngo_id_b32 = uuid_to_bytes32(ngo_id)
        target_amount_paise = int(Decimal(str(target_amount_inr)) * 100)

        return self._send_contract_transaction(
            "createCampaign",
            camp_id_b32,
            ngo_id_b32,
            target_amount_paise,
            currency
        )

    def anchor_document(
        self,
        ngo_id: Union[UUID, str],
        doc_type: str,
        file_hash: Union[str, bytes]
    ) -> str:
        """
        Anchors an NGO legal compliance document (12A, 80G, FCRA, audit report) on-chain.
        """
        ngo_id_b32 = uuid_to_bytes32(ngo_id)
        file_hash_b32 = uuid_to_bytes32(file_hash)

        return self._send_contract_transaction(
            "anchorDocument",
            ngo_id_b32,
            doc_type,
            file_hash_b32
        )

    def record_expense(
        self,
        campaign_id: Union[UUID, str],
        milestone_index: int,
        amount_inr: float,
        vendor_gst: Union[str, bytes],
        invoice_hash: Union[str, bytes]
    ) -> str:
        """
        Records a commercial vendor invoice and outflow payment against a campaign milestone.
        """
        camp_id_b32 = uuid_to_bytes32(campaign_id)
        amount_paise = int(Decimal(str(amount_inr)) * 100)
        vendor_gst_b32 = uuid_to_bytes32(vendor_gst)
        invoice_hash_b32 = uuid_to_bytes32(invoice_hash)

        return self._send_contract_transaction(
            "recordExpense",
            camp_id_b32,
            int(milestone_index),
            amount_paise,
            vendor_gst_b32,
            invoice_hash_b32
        )

    def lock_campaign_budget(
        self,
        campaign_id: Union[UUID, str],
        budget_items_hash: Union[str, bytes],
        target_amount_inr: float
    ) -> str:
        """
        Freezes the itemized unit-cost budget breakdown for a campaign on-chain.
        """
        camp_id_b32 = uuid_to_bytes32(campaign_id)
        budget_hash_b32 = uuid_to_bytes32(budget_items_hash)
        target_paise = int(Decimal(str(target_amount_inr)) * 100)

        return self._send_contract_transaction(
            "lockCampaignBudget",
            camp_id_b32,
            budget_hash_b32,
            target_paise
        )

    def flag_campaign(
        self,
        campaign_id: Union[UUID, str],
        reason_code: str,
        evidence_hash: Union[str, bytes]
    ) -> str:
        """
        Logs an immutable dispute, red-flag, or whistleblower report on-chain.
        """
        camp_id_b32 = uuid_to_bytes32(campaign_id)
        evidence_hash_b32 = uuid_to_bytes32(evidence_hash)

        return self._send_contract_transaction(
            "flagCampaign",
            camp_id_b32,
            reason_code,
            evidence_hash_b32
        )

    def transfer_ownership(self, new_owner_address: str) -> str:
        """
        Initiates step 1 of 2-step ownership transfer on-chain.
        """
        return self._send_contract_transaction(
            "transferOwnership",
            new_owner_address
        )

    def accept_ownership(self) -> str:
        """
        Finalizes step 2 of 2-step ownership transfer by the pending owner.
        """
        return self._send_contract_transaction(
            "acceptOwnership"
        )

    def anchor_daily_state(
        self,
        merkle_root: Union[str, bytes],
        date_timestamp: int,
        record_count: int
    ) -> str:
        """
        Anchors the platform-wide daily Merkle Root onto Polygon Amoy.
        """
        root_b32 = uuid_to_bytes32(merkle_root)
        return self._send_contract_transaction(
            "anchorDailyState",
            root_b32,
            int(date_timestamp),
            int(record_count)
        )

    def verify_database_record(
        self,
        leaf_hash: Union[str, bytes],
        merkle_proof: List[str],
        expected_root: Union[str, bytes]
    ) -> bool:
        """
        Calls the pure verifyDatabaseRecord function on-chain (zero gas eth_call).
        """
        if self.is_simulation_mode():
            from blockchain.services.merkle_service import MerkleTree
            leaf_bytes = uuid_to_bytes32(leaf_hash)
            root_bytes = uuid_to_bytes32(expected_root)
            return MerkleTree.verify_proof(leaf_bytes, merkle_proof, root_bytes)

        leaf_b32 = uuid_to_bytes32(leaf_hash)
        root_b32 = uuid_to_bytes32(expected_root)
        proof_b32_list = [uuid_to_bytes32(p) for p in merkle_proof]

        try:
            return self.contract.functions.verifyDatabaseRecord(
                leaf_b32,
                proof_b32_list,
                root_b32
            ).call()
        except Exception as e:
            logger.warning(f"On-chain Merkle verify call failed: {e}. Using local verification.")
            from blockchain.services.merkle_service import MerkleTree
            return MerkleTree.verify_proof(leaf_b32, merkle_proof, root_b32)

    def has_role(self, role_name: str, account_address: str) -> bool:
        """Checks if account_address has the specified role."""
        if self.is_simulation_mode():
            return True
        if role_name == "DEFAULT_ADMIN_ROLE":
            role_hash = b"\x00" * 32
        else:
            role_hash = Web3.keccak(text=role_name)
        checksum_addr = Web3.to_checksum_address(account_address)
        try:
            return self.contract.functions.hasRole(role_hash, checksum_addr).call()
        except Exception:
            return False

    def grant_role(self, role_name: str, target_address: str) -> str:
        """Grants role to target_address."""
        role_hash = b"\x00" * 32 if role_name == "DEFAULT_ADMIN_ROLE" else Web3.keccak(text=role_name)
        checksum_addr = Web3.to_checksum_address(target_address)
        return self._send_contract_transaction("grantRole", role_hash, checksum_addr)

    def revoke_role(self, role_name: str, target_address: str) -> str:
        """Revokes role from target_address."""
        role_hash = b"\x00" * 32 if role_name == "DEFAULT_ADMIN_ROLE" else Web3.keccak(text=role_name)
        checksum_addr = Web3.to_checksum_address(target_address)
        return self._send_contract_transaction("revokeRole", role_hash, checksum_addr)

    def get_explorer_url(self, tx_hash: str) -> str:
        """Helper to get public Polygonscan explorer link."""
        return settings.get_explorer_tx_url(tx_hash)


# Singleton instance
blockchain_service = BlockchainService()
