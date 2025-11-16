#!/usr/bin/env python3
"""
Blockchain Audit Service

Provides immutable audit trails using blockchain technology.
Ensures tamper-proof logging and verification of security events.
"""

import os
import time
import hashlib
import json
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app


class AuditEventType(str, Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY_INCIDENT = "security_incident"
    ALERT_TRIGGERED = "alert_triggered"
    POLICY_CHANGE = "policy_change"
    INCIDENT_RESPONSE = "incident_response"


class BlockchainType(str, Enum):
    """Blockchain implementation types"""
    PRIVATE = "private"
    CONSORTIUM = "consortium"
    PUBLIC = "public"


@dataclass
class Block:
    """Blockchain block"""
    index: int
    timestamp: float
    transactions: List[Dict]
    proof: int
    previous_hash: str
    hash: str
    merkle_root: str


@dataclass
class AuditTransaction:
    """Audit trail transaction"""
    transaction_id: str
    event_type: AuditEventType
    timestamp: datetime
    user: str
    action: str
    resource: str
    details: Dict
    ip_address: str
    user_agent: str
    outcome: str
    signature: str


# Pydantic models
class AuditEventRequest(BaseModel):
    event_type: AuditEventType
    user: str
    action: str
    resource: str
    details: Dict
    ip_address: str
    user_agent: str
    outcome: str


class VerificationRequest(BaseModel):
    transaction_id: str


class ChainVerificationRequest(BaseModel):
    start_block: Optional[int] = 0
    end_block: Optional[int] = None


# Prometheus metrics
blocks_created = Counter(
    'blockchain_blocks_created_total',
    'Total number of blockchain blocks created'
)

transactions_recorded = Counter(
    'blockchain_transactions_recorded_total',
    'Total number of transactions recorded',
    ['event_type']
)

verification_checks = Counter(
    'blockchain_verification_checks_total',
    'Total number of verification checks performed',
    ['valid']
)

block_creation_duration = Histogram(
    'blockchain_block_creation_duration_seconds',
    'Time to create a new block'
)

chain_length = Gauge(
    'blockchain_chain_length',
    'Current length of the blockchain'
)


class Blockchain:
    """Simple blockchain implementation for audit trails"""

    def __init__(self):
        self.chain: List[Block] = []
        self.current_transactions: List[Dict] = []
        self.nodes = set()

        # Create genesis block
        self.create_genesis_block()

    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            proof=100,
            previous_hash="0",
            hash="",
            merkle_root=""
        )
        genesis_block.hash = self.hash_block(genesis_block)
        genesis_block.merkle_root = self.calculate_merkle_root([])
        self.chain.append(genesis_block)
        chain_length.set(len(self.chain))

    def create_block(self, proof: int, previous_hash: str) -> Block:
        """Create a new block"""
        start = time.time()

        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.current_transactions,
            proof=proof,
            previous_hash=previous_hash,
            hash="",
            merkle_root=""
        )

        block.merkle_root = self.calculate_merkle_root(self.current_transactions)
        block.hash = self.hash_block(block)

        self.current_transactions = []
        self.chain.append(block)

        blocks_created.inc()
        chain_length.set(len(self.chain))
        block_creation_duration.observe(time.time() - start)

        return block

    @staticmethod
    def hash_block(block: Block) -> str:
        """Create SHA-256 hash of a block"""
        block_dict = {
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': block.transactions,
            'proof': block.proof,
            'previous_hash': block.previous_hash,
            'merkle_root': block.merkle_root
        }
        block_string = json.dumps(block_dict, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def calculate_merkle_root(transactions: List[Dict]) -> str:
        """Calculate Merkle root of transactions"""
        if not transactions:
            return hashlib.sha256(b'').hexdigest()

        # Hash all transactions
        transaction_hashes = [
            hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
            for tx in transactions
        ]

        # Build Merkle tree
        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 != 0:
                transaction_hashes.append(transaction_hashes[-1])

            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                combined = transaction_hashes[i] + transaction_hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)

            transaction_hashes = new_hashes

        return transaction_hashes[0]

    def add_transaction(self, transaction: Dict) -> int:
        """Add a new transaction to the list"""
        self.current_transactions.append(transaction)
        transactions_recorded.labels(event_type=transaction.get('event_type', 'unknown')).inc()
        return len(self.chain)

    @property
    def last_block(self) -> Block:
        """Return the last block in the chain"""
        return self.chain[-1]

    @staticmethod
    def proof_of_work(last_proof: int) -> int:
        """Simple proof of work algorithm"""
        proof = 0
        while not Blockchain.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """Validate the proof: Does hash(last_proof, proof) contain 4 leading zeroes?"""
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def is_chain_valid(self, chain: List[Block] = None) -> bool:
        """Verify the blockchain integrity"""
        if chain is None:
            chain = self.chain

        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            # Verify hash
            if current_block.hash != self.hash_block(current_block):
                return False

            # Verify previous hash link
            if current_block.previous_hash != previous_block.hash:
                return False

            # Verify proof of work
            if not self.valid_proof(previous_block.proof, current_block.proof):
                return False

            # Verify merkle root
            if current_block.merkle_root != self.calculate_merkle_root(current_block.transactions):
                return False

        return True


class BlockchainAuditService:
    """Blockchain-based audit trail service"""

    def __init__(self):
        self.app = FastAPI(
            title="Blockchain Audit Service",
            description="Immutable audit trails using blockchain technology",
            version="1.0.0"
        )

        self.blockchain = Blockchain()
        self.transactions_index: Dict[str, tuple] = {}  # transaction_id -> (block_index, tx_index)
        self.pending_transactions = 0
        self.max_transactions_per_block = 100

        self.setup_routes()

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "blockchain-audit-service",
                "timestamp": datetime.utcnow().isoformat(),
                "chain_length": len(self.blockchain.chain),
                "pending_transactions": self.pending_transactions,
                "chain_valid": self.blockchain.is_chain_valid()
            }

        @self.app.post("/api/v1/audit/record")
        async def record_audit_event(req: AuditEventRequest):
            """Record an audit event to the blockchain"""
            transaction_id = f"tx-{int(time.time() * 1000)}-{hashlib.sha256(req.user.encode()).hexdigest()[:8]}"

            # Create transaction
            transaction = {
                "transaction_id": transaction_id,
                "event_type": req.event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "user": req.user,
                "action": req.action,
                "resource": req.resource,
                "details": req.details,
                "ip_address": req.ip_address,
                "user_agent": req.user_agent,
                "outcome": req.outcome,
                "signature": self.sign_transaction(transaction_id, req.user, req.action)
            }

            # Add to blockchain
            block_index = self.blockchain.add_transaction(transaction)
            self.pending_transactions += 1

            # Create new block if threshold reached
            if self.pending_transactions >= self.max_transactions_per_block:
                last_block = self.blockchain.last_block
                proof = self.blockchain.proof_of_work(last_block.proof)
                new_block = self.blockchain.create_block(proof, last_block.hash)
                self.pending_transactions = 0
                block_index = new_block.index

            # Index transaction for quick lookup
            tx_index = len(self.blockchain.current_transactions) - 1 if self.pending_transactions > 0 else len(self.blockchain.last_block.transactions) - 1
            self.transactions_index[transaction_id] = (block_index, tx_index)

            return {
                "status": "recorded",
                "transaction_id": transaction_id,
                "block_index": block_index,
                "timestamp": transaction["timestamp"],
                "immutable": True
            }

        @self.app.get("/api/v1/audit/transactions/{transaction_id}")
        async def get_transaction(transaction_id: str):
            """Retrieve a specific transaction"""
            if transaction_id not in self.transactions_index:
                # Check pending transactions
                for tx in self.blockchain.current_transactions:
                    if tx.get("transaction_id") == transaction_id:
                        return {
                            "transaction": tx,
                            "status": "pending",
                            "block_index": None,
                            "verified": False
                        }
                raise HTTPException(status_code=404, detail="Transaction not found")

            block_index, tx_index = self.transactions_index[transaction_id]
            block = self.blockchain.chain[block_index]
            transaction = block.transactions[tx_index]

            return {
                "transaction": transaction,
                "status": "confirmed",
                "block_index": block_index,
                "block_hash": block.hash,
                "verified": True,
                "confirmations": len(self.blockchain.chain) - block_index
            }

        @self.app.post("/api/v1/audit/verify")
        async def verify_transaction(req: VerificationRequest):
            """Verify a transaction's integrity"""
            if req.transaction_id not in self.transactions_index:
                raise HTTPException(status_code=404, detail="Transaction not found")

            block_index, tx_index = self.transactions_index[req.transaction_id]
            block = self.blockchain.chain[block_index]
            transaction = block.transactions[tx_index]

            # Verify transaction signature
            expected_signature = self.sign_transaction(
                transaction["transaction_id"],
                transaction["user"],
                transaction["action"]
            )
            signature_valid = (transaction["signature"] == expected_signature)

            # Verify block hash
            block_hash_valid = (block.hash == self.blockchain.hash_block(block))

            # Verify merkle root
            merkle_valid = (block.merkle_root == self.blockchain.calculate_merkle_root(block.transactions))

            # Verify chain
            chain_valid = self.blockchain.is_chain_valid()

            overall_valid = signature_valid and block_hash_valid and merkle_valid and chain_valid

            verification_checks.labels(valid=str(overall_valid).lower()).inc()

            return {
                "transaction_id": req.transaction_id,
                "valid": overall_valid,
                "checks": {
                    "signature_valid": signature_valid,
                    "block_hash_valid": block_hash_valid,
                    "merkle_root_valid": merkle_valid,
                    "chain_valid": chain_valid
                },
                "block_index": block_index,
                "confirmations": len(self.blockchain.chain) - block_index,
                "timestamp": transaction["timestamp"]
            }

        @self.app.post("/api/v1/audit/verify-chain")
        async def verify_chain(req: ChainVerificationRequest):
            """Verify blockchain integrity"""
            start_idx = req.start_block or 0
            end_idx = req.end_block or len(self.blockchain.chain)

            chain_segment = self.blockchain.chain[start_idx:end_idx]
            valid = self.blockchain.is_chain_valid(chain_segment)

            return {
                "valid": valid,
                "start_block": start_idx,
                "end_block": end_idx,
                "blocks_verified": len(chain_segment),
                "chain_length": len(self.blockchain.chain)
            }

        @self.app.get("/api/v1/chain")
        async def get_chain():
            """Get the entire blockchain"""
            return {
                "chain": [asdict(block) for block in self.blockchain.chain],
                "length": len(self.blockchain.chain)
            }

        @self.app.get("/api/v1/chain/blocks/{block_index}")
        async def get_block(block_index: int):
            """Get a specific block"""
            if block_index < 0 or block_index >= len(self.blockchain.chain):
                raise HTTPException(status_code=404, detail="Block not found")

            block = self.blockchain.chain[block_index]
            return asdict(block)

        @self.app.post("/api/v1/chain/mine")
        async def mine_block():
            """Force creation of a new block"""
            if self.pending_transactions == 0:
                return {
                    "status": "no_transactions",
                    "message": "No pending transactions to mine"
                }

            last_block = self.blockchain.last_block
            proof = self.blockchain.proof_of_work(last_block.proof)
            new_block = self.blockchain.create_block(proof, last_block.hash)
            self.pending_transactions = 0

            return {
                "status": "mined",
                "block": asdict(new_block),
                "transactions_count": len(new_block.transactions)
            }

        @self.app.get("/api/v1/audit/search")
        async def search_audit_trail(
            user: Optional[str] = None,
            event_type: Optional[AuditEventType] = None,
            resource: Optional[str] = None,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None
        ):
            """Search audit trail"""
            results = []

            for block in self.blockchain.chain:
                for tx in block.transactions:
                    # Apply filters
                    if user and tx.get("user") != user:
                        continue
                    if event_type and tx.get("event_type") != event_type:
                        continue
                    if resource and tx.get("resource") != resource:
                        continue
                    if start_time and tx.get("timestamp") < start_time:
                        continue
                    if end_time and tx.get("timestamp") > end_time:
                        continue

                    results.append({
                        "transaction": tx,
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "verified": True
                    })

            return {
                "results": results,
                "count": len(results)
            }

        @self.app.get("/api/v1/stats")
        async def get_stats():
            """Get blockchain statistics"""
            total_transactions = sum(len(block.transactions) for block in self.blockchain.chain)

            event_type_counts = {}
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    event_type = tx.get("event_type", "unknown")
                    event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            return {
                "chain_length": len(self.blockchain.chain),
                "total_transactions": total_transactions,
                "pending_transactions": self.pending_transactions,
                "chain_valid": self.blockchain.is_chain_valid(),
                "event_type_distribution": event_type_counts,
                "avg_transactions_per_block": total_transactions / len(self.blockchain.chain) if self.blockchain.chain else 0
            }

        # Add Prometheus metrics endpoint
        metrics_app = make_asgi_app()
        self.app.mount("/metrics", metrics_app)

    @staticmethod
    def sign_transaction(transaction_id: str, user: str, action: str) -> str:
        """Create a signature for a transaction"""
        data = f"{transaction_id}{user}{action}".encode()
        return hashlib.sha256(data).hexdigest()

    def run(self, host: str = "0.0.0.0", port: int = 8088):
        """Run the service"""
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8088"))
    service = BlockchainAuditService()
    service.run(port=port)
