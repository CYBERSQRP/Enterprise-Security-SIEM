#!/usr/bin/env python3
"""
Quantum-Ready Security Service

Implements post-quantum cryptography algorithms for quantum-resistant security.
Supports NIST-approved PQC algorithms and hybrid classical/quantum schemes.
"""

import os
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app

# Simulated PQC implementations (in production, use real PQC libraries like liboqs)
# from oqs import Signature, KeyEncapsulation  # Would use in production


class PQCAlgorithm(str, Enum):
    """Post-Quantum Cryptography Algorithms"""
    CRYSTALS_DILITHIUM = "CRYSTALS-Dilithium"  # Digital signatures
    CRYSTALS_KYBER = "CRYSTALS-Kyber"          # Key encapsulation
    FALCON = "FALCON"                          # Compact signatures
    SPHINCS_PLUS = "SPHINCS+"                  # Hash-based signatures
    NTRU = "NTRU"                              # Lattice-based encryption
    SABER = "SABER"                            # Module-LWR KEM


class CryptoMode(str, Enum):
    """Cryptographic operation modes"""
    QUANTUM_ONLY = "quantum_only"
    HYBRID = "hybrid"  # Both classical and quantum
    CLASSICAL = "classical"


@dataclass
class CryptoKey:
    """Cryptographic key pair"""
    key_id: str
    algorithm: PQCAlgorithm
    public_key: str
    private_key: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    key_size: int
    usage: str  # "signing", "encryption", "kex"


@dataclass
class Signature:
    """Digital signature"""
    signature_id: str
    algorithm: PQCAlgorithm
    signature: str
    signed_data_hash: str
    timestamp: datetime
    key_id: str


@dataclass
class EncryptedData:
    """Encrypted data package"""
    encryption_id: str
    algorithm: PQCAlgorithm
    ciphertext: str
    encapsulated_key: str
    nonce: str
    timestamp: datetime


# Pydantic models for API
class KeyGenerationRequest(BaseModel):
    algorithm: PQCAlgorithm
    usage: str  # "signing", "encryption", "kex"
    mode: CryptoMode = CryptoMode.QUANTUM_ONLY
    validity_days: Optional[int] = 365


class SignRequest(BaseModel):
    key_id: str
    data: str
    mode: CryptoMode = CryptoMode.QUANTUM_ONLY


class VerifyRequest(BaseModel):
    signature_id: str
    data: str
    public_key_id: str


class EncryptRequest(BaseModel):
    recipient_key_id: str
    data: str
    mode: CryptoMode = CryptoMode.QUANTUM_ONLY


class DecryptRequest(BaseModel):
    encryption_id: str
    private_key_id: str


class MigrationRequest(BaseModel):
    key_ids: List[str]
    target_algorithm: PQCAlgorithm
    preserve_classical: bool = True


# Prometheus metrics
keys_generated = Counter(
    'quantum_crypto_keys_generated_total',
    'Total number of PQC keys generated',
    ['algorithm', 'usage']
)

signatures_created = Counter(
    'quantum_crypto_signatures_created_total',
    'Total number of PQC signatures created',
    ['algorithm']
)

encryptions_performed = Counter(
    'quantum_crypto_encryptions_total',
    'Total number of PQC encryptions performed',
    ['algorithm']
)

crypto_operation_duration = Histogram(
    'quantum_crypto_operation_duration_seconds',
    'Duration of cryptographic operations',
    ['operation', 'algorithm']
)

active_keys = Gauge(
    'quantum_crypto_active_keys',
    'Number of active PQC keys',
    ['algorithm']
)


class QuantumCryptoService:
    """Post-Quantum Cryptography Service"""

    def __init__(self):
        self.app = FastAPI(
            title="Quantum-Ready Security Service",
            description="Post-quantum cryptography for quantum-resistant security",
            version="1.0.0"
        )

        self.keys: Dict[str, CryptoKey] = {}
        self.signatures: Dict[str, Signature] = {}
        self.encrypted_data: Dict[str, EncryptedData] = {}

        # Algorithm capabilities
        self.algorithms = {
            PQCAlgorithm.CRYSTALS_DILITHIUM: {
                "type": "signature",
                "security_level": 5,
                "key_size": 2592,
                "signature_size": 3309,
                "nist_approved": True
            },
            PQCAlgorithm.CRYSTALS_KYBER: {
                "type": "kem",
                "security_level": 5,
                "public_key_size": 1568,
                "ciphertext_size": 1568,
                "nist_approved": True
            },
            PQCAlgorithm.FALCON: {
                "type": "signature",
                "security_level": 5,
                "key_size": 1793,
                "signature_size": 1280,
                "nist_approved": True
            },
            PQCAlgorithm.SPHINCS_PLUS: {
                "type": "signature",
                "security_level": 5,
                "key_size": 64,
                "signature_size": 29792,
                "nist_approved": True
            },
            PQCAlgorithm.NTRU: {
                "type": "kem",
                "security_level": 3,
                "public_key_size": 1230,
                "ciphertext_size": 1230,
                "nist_approved": False
            },
            PQCAlgorithm.SABER: {
                "type": "kem",
                "security_level": 5,
                "public_key_size": 1312,
                "ciphertext_size": 1472,
                "nist_approved": False
            }
        }

        self.setup_routes()

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "quantum-crypto-service",
                "timestamp": datetime.utcnow().isoformat(),
                "active_keys": len(self.keys),
                "supported_algorithms": len(self.algorithms)
            }

        @self.app.get("/api/v1/algorithms")
        async def list_algorithms():
            """List supported PQC algorithms"""
            return {
                "algorithms": [
                    {
                        "name": algo,
                        **details
                    }
                    for algo, details in self.algorithms.items()
                ],
                "count": len(self.algorithms)
            }

        @self.app.post("/api/v1/keys/generate")
        async def generate_key(req: KeyGenerationRequest):
            """Generate a new PQC key pair"""
            start = time.time()

            if req.algorithm not in self.algorithms:
                raise HTTPException(status_code=400, detail="Unsupported algorithm")

            algo_info = self.algorithms[req.algorithm]
            if req.usage == "signing" and algo_info["type"] != "signature":
                raise HTTPException(status_code=400, detail="Algorithm not suitable for signing")
            if req.usage == "encryption" and algo_info["type"] != "kem":
                raise HTTPException(status_code=400, detail="Algorithm not suitable for encryption")

            # Generate key pair (simulated)
            key_id = f"pqc-key-{secrets.token_hex(8)}"
            public_key = secrets.token_hex(algo_info.get("key_size", 2048) // 8)
            private_key = secrets.token_hex(algo_info.get("key_size", 2048) // 8)

            key = CryptoKey(
                key_id=key_id,
                algorithm=req.algorithm,
                public_key=public_key,
                private_key=private_key,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=req.validity_days) if req.validity_days else None,
                key_size=algo_info.get("key_size", 2048),
                usage=req.usage
            )

            self.keys[key_id] = key

            # Update metrics
            keys_generated.labels(
                algorithm=req.algorithm,
                usage=req.usage
            ).inc()
            active_keys.labels(algorithm=req.algorithm).inc()

            duration = time.time() - start
            crypto_operation_duration.labels(
                operation="keygen",
                algorithm=req.algorithm
            ).observe(duration)

            return {
                "key_id": key_id,
                "algorithm": req.algorithm,
                "public_key": public_key,
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "mode": req.mode,
                "duration_ms": duration * 1000
            }

        @self.app.get("/api/v1/keys")
        async def list_keys():
            """List all PQC keys"""
            keys = []
            for key in self.keys.values():
                key_dict = asdict(key)
                key_dict.pop("private_key")  # Don't expose private keys
                key_dict["created_at"] = key.created_at.isoformat()
                if key.expires_at:
                    key_dict["expires_at"] = key.expires_at.isoformat()
                keys.append(key_dict)

            return {
                "keys": keys,
                "count": len(keys)
            }

        @self.app.get("/api/v1/keys/{key_id}")
        async def get_key(key_id: str):
            """Get specific key details"""
            if key_id not in self.keys:
                raise HTTPException(status_code=404, detail="Key not found")

            key = self.keys[key_id]
            key_dict = asdict(key)
            key_dict.pop("private_key")  # Don't expose private key
            key_dict["created_at"] = key.created_at.isoformat()
            if key.expires_at:
                key_dict["expires_at"] = key.expires_at.isoformat()

            return key_dict

        @self.app.post("/api/v1/sign")
        async def sign_data(req: SignRequest):
            """Sign data with PQC signature"""
            start = time.time()

            if req.key_id not in self.keys:
                raise HTTPException(status_code=404, detail="Key not found")

            key = self.keys[req.key_id]
            if key.usage != "signing":
                raise HTTPException(status_code=400, detail="Key not suitable for signing")

            algo_info = self.algorithms[key.algorithm]

            # Create signature (simulated)
            signature_id = f"sig-{secrets.token_hex(8)}"
            data_hash = hashlib.sha256(req.data.encode()).hexdigest()
            signature_data = secrets.token_hex(algo_info.get("signature_size", 3000) // 8)

            signature = Signature(
                signature_id=signature_id,
                algorithm=key.algorithm,
                signature=signature_data,
                signed_data_hash=data_hash,
                timestamp=datetime.utcnow(),
                key_id=req.key_id
            )

            self.signatures[signature_id] = signature

            # Update metrics
            signatures_created.labels(algorithm=key.algorithm).inc()

            duration = time.time() - start
            crypto_operation_duration.labels(
                operation="sign",
                algorithm=key.algorithm
            ).observe(duration)

            return {
                "signature_id": signature_id,
                "algorithm": key.algorithm,
                "signature": signature_data,
                "data_hash": data_hash,
                "timestamp": signature.timestamp.isoformat(),
                "mode": req.mode,
                "duration_ms": duration * 1000
            }

        @self.app.post("/api/v1/verify")
        async def verify_signature(req: VerifyRequest):
            """Verify PQC signature"""
            start = time.time()

            if req.signature_id not in self.signatures:
                raise HTTPException(status_code=404, detail="Signature not found")

            signature = self.signatures[req.signature_id]
            data_hash = hashlib.sha256(req.data.encode()).hexdigest()

            # Verify signature (simulated - always returns true for matching hash)
            valid = (data_hash == signature.signed_data_hash)

            duration = time.time() - start
            crypto_operation_duration.labels(
                operation="verify",
                algorithm=signature.algorithm
            ).observe(duration)

            return {
                "valid": valid,
                "signature_id": req.signature_id,
                "algorithm": signature.algorithm,
                "duration_ms": duration * 1000
            }

        @self.app.post("/api/v1/encrypt")
        async def encrypt_data(req: EncryptRequest):
            """Encrypt data with PQC"""
            start = time.time()

            if req.recipient_key_id not in self.keys:
                raise HTTPException(status_code=404, detail="Recipient key not found")

            key = self.keys[req.recipient_key_id]
            if key.usage != "encryption":
                raise HTTPException(status_code=400, detail="Key not suitable for encryption")

            algo_info = self.algorithms[key.algorithm]

            # Encrypt data (simulated)
            encryption_id = f"enc-{secrets.token_hex(8)}"
            ciphertext = secrets.token_hex(len(req.data))
            encapsulated_key = secrets.token_hex(algo_info.get("ciphertext_size", 1568) // 8)
            nonce = secrets.token_hex(16)

            encrypted = EncryptedData(
                encryption_id=encryption_id,
                algorithm=key.algorithm,
                ciphertext=ciphertext,
                encapsulated_key=encapsulated_key,
                nonce=nonce,
                timestamp=datetime.utcnow()
            )

            self.encrypted_data[encryption_id] = encrypted

            # Update metrics
            encryptions_performed.labels(algorithm=key.algorithm).inc()

            duration = time.time() - start
            crypto_operation_duration.labels(
                operation="encrypt",
                algorithm=key.algorithm
            ).observe(duration)

            return {
                "encryption_id": encryption_id,
                "algorithm": key.algorithm,
                "ciphertext": ciphertext,
                "encapsulated_key": encapsulated_key,
                "nonce": nonce,
                "mode": req.mode,
                "duration_ms": duration * 1000
            }

        @self.app.post("/api/v1/decrypt")
        async def decrypt_data(req: DecryptRequest):
            """Decrypt PQC encrypted data"""
            start = time.time()

            if req.encryption_id not in self.encrypted_data:
                raise HTTPException(status_code=404, detail="Encrypted data not found")

            if req.private_key_id not in self.keys:
                raise HTTPException(status_code=404, detail="Private key not found")

            encrypted = self.encrypted_data[req.encryption_id]

            # Decrypt data (simulated)
            plaintext = f"Decrypted data from {req.encryption_id}"

            duration = time.time() - start
            crypto_operation_duration.labels(
                operation="decrypt",
                algorithm=encrypted.algorithm
            ).observe(duration)

            return {
                "plaintext": plaintext,
                "algorithm": encrypted.algorithm,
                "duration_ms": duration * 1000
            }

        @self.app.post("/api/v1/migrate")
        async def migrate_keys(req: MigrationRequest):
            """Migrate classical keys to PQC"""
            migrated = []

            for key_id in req.key_ids:
                if key_id not in self.keys:
                    continue

                old_key = self.keys[key_id]

                # Generate new PQC key
                new_key_id = f"pqc-migrated-{secrets.token_hex(8)}"
                algo_info = self.algorithms[req.target_algorithm]

                new_key = CryptoKey(
                    key_id=new_key_id,
                    algorithm=req.target_algorithm,
                    public_key=secrets.token_hex(algo_info.get("key_size", 2048) // 8),
                    private_key=secrets.token_hex(algo_info.get("key_size", 2048) // 8),
                    created_at=datetime.utcnow(),
                    expires_at=old_key.expires_at,
                    key_size=algo_info.get("key_size", 2048),
                    usage=old_key.usage
                )

                self.keys[new_key_id] = new_key

                migrated.append({
                    "old_key_id": key_id,
                    "new_key_id": new_key_id,
                    "algorithm": req.target_algorithm
                })

                # Mark old key as migrated
                if not req.preserve_classical:
                    del self.keys[key_id]

            return {
                "migrated": migrated,
                "count": len(migrated),
                "preserved_classical": req.preserve_classical
            }

        @self.app.get("/api/v1/quantum-readiness")
        async def check_quantum_readiness():
            """Check quantum readiness status"""
            pqc_keys = sum(1 for k in self.keys.values()
                          if self.algorithms[k.algorithm]["nist_approved"])
            total_keys = len(self.keys)

            readiness_score = (pqc_keys / total_keys * 100) if total_keys > 0 else 0

            return {
                "readiness_score": readiness_score,
                "total_keys": total_keys,
                "pqc_keys": pqc_keys,
                "classical_keys": total_keys - pqc_keys,
                "nist_approved_algorithms": sum(
                    1 for a in self.algorithms.values() if a["nist_approved"]
                ),
                "status": "quantum_ready" if readiness_score >= 80 else "migration_needed"
            }

        # Add Prometheus metrics endpoint
        metrics_app = make_asgi_app()
        self.app.mount("/metrics", metrics_app)

    def run(self, host: str = "0.0.0.0", port: int = 8086):
        """Run the service"""
        uvicorn.run(self.app, host=host, port=port)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8086"))
    service = QuantumCryptoService()
    service.run(port=port)
