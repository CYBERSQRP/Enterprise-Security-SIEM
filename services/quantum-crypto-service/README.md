# Quantum-Ready Security Service

Post-quantum cryptography service providing quantum-resistant security using NIST-approved algorithms.

## Overview

Implements post-quantum cryptographic algorithms to protect against quantum computer attacks:
- **CRYSTALS-Dilithium** - Digital signatures (NIST selected)
- **CRYSTALS-Kyber** - Key encapsulation (NIST selected)
- **FALCON** - Compact signatures (NIST selected)
- **SPHINCS+** - Hash-based signatures (NIST selected)
- **NTRU** - Lattice-based encryption
- **SABER** - Module-LWR KEM

## Features

- Key generation for PQC algorithms
- Digital signatures with quantum resistance
- Encryption/decryption with PQC
- Hybrid classical/quantum cryptography
- Key migration from classical to PQC
- Quantum readiness assessment

## API Endpoints

### Algorithms
- `GET /api/v1/algorithms` - List supported PQC algorithms

### Key Management
- `POST /api/v1/keys/generate` - Generate PQC key pair
- `GET /api/v1/keys` - List all keys
- `GET /api/v1/keys/:id` - Get specific key

### Cryptographic Operations
- `POST /api/v1/sign` - Sign data with PQC
- `POST /api/v1/verify` - Verify PQC signature
- `POST /api/v1/encrypt` - Encrypt with PQC
- `POST /api/v1/decrypt` - Decrypt PQC data

### Migration
- `POST /api/v1/migrate` - Migrate classical keys to PQC
- `GET /api/v1/quantum-readiness` - Check quantum readiness

## Usage Examples

```bash
# Generate a PQC key for signing
curl -X POST http://localhost:8086/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "CRYSTALS-Dilithium",
    "usage": "signing",
    "mode": "quantum_only",
    "validity_days": 365
  }'

# Sign data
curl -X POST http://localhost:8086/api/v1/sign \
  -H "Content-Type: application/json" \
  -d '{
    "key_id": "pqc-key-abc123",
    "data": "Important security message",
    "mode": "quantum_only"
  }'

# Check quantum readiness
curl http://localhost:8086/api/v1/quantum-readiness
```

## Quantum Threat Timeline

- **2025-2030**: NISQ (Noisy Intermediate-Scale Quantum) computers
- **2030-2035**: Cryptographically relevant quantum computers possible
- **Now**: Harvest now, decrypt later attacks possible

## Migration Strategy

1. **Assessment**: Evaluate current cryptographic inventory
2. **Planning**: Identify critical systems for PQC migration
3. **Hybrid Mode**: Deploy hybrid classical/quantum crypto
4. **Full Migration**: Transition to quantum-only mode
5. **Decommission**: Remove classical cryptography

## Performance

Typical operation times:
- Key generation: 1-5ms
- Signing: 0.5-2ms
- Verification: 0.5-1.5ms
- Encryption: 1-3ms
- Decryption: 1-3ms

## Security Considerations

- All algorithms are NIST-approved or candidates
- Key material stored securely (production would use HSM)
- Constant-time implementations
- Side-channel attack resistant
- Hybrid mode provides defense-in-depth

## License

Proprietary - Enterprise SIEM Platform
