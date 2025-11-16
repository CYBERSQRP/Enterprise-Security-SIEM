# Blockchain Audit Service

Immutable audit trails using blockchain technology for tamper-proof security event logging.

## Overview

Provides blockchain-based audit logging to ensure:
- **Immutability** - Records cannot be altered or deleted
- **Verification** - Cryptographic proof of integrity
- **Transparency** - Complete audit trail history
- **Tamper Detection** - Immediate detection of any modifications

## Features

### Blockchain Architecture
- Private blockchain for security events
- Proof of Work consensus
- Merkle tree for transaction verification
- SHA-256 cryptographic hashing
- Block mining and validation

### Audit Events
- User authentication events
- Access control decisions
- Data access and modifications
- System configuration changes
- Security incidents
- Policy changes
- Incident response actions

### Verification
- Transaction integrity verification
- Block hash verification
- Merkle root validation
- Full chain validation
- Multi-level cryptographic proofs

## API Endpoints

### Recording
- `POST /api/v1/audit/record` - Record audit event

### Retrieval
- `GET /api/v1/audit/transactions/:id` - Get transaction
- `GET /api/v1/audit/search` - Search audit trail

### Verification
- `POST /api/v1/audit/verify` - Verify transaction
- `POST /api/v1/audit/verify-chain` - Verify blockchain

### Chain Management
- `GET /api/v1/chain` - Get full blockchain
- `GET /api/v1/chain/blocks/:index` - Get specific block
- `POST /api/v1/chain/mine` - Force block creation

### Statistics
- `GET /api/v1/stats` - Get blockchain statistics

## Usage Examples

```bash
# Record an audit event
curl -X POST http://localhost:8088/api/v1/audit/record \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_login",
    "user": "admin@company.com",
    "action": "login",
    "resource": "/api/admin",
    "details": {"method": "password", "mfa": true},
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "outcome": "success"
  }'

# Verify a transaction
curl -X POST http://localhost:8088/api/v1/audit/verify \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "tx-1699999999-abc12345"
  }'

# Search audit trail
curl "http://localhost:8088/api/v1/audit/search?user=admin@company.com&event_type=user_login"

# Verify blockchain integrity
curl -X POST http://localhost:8088/api/v1/audit/verify-chain \
  -H "Content-Type: application/json" \
  -d '{
    "start_block": 0,
    "end_block": null
  }'
```

## Blockchain Structure

```
Block {
  index: 0,
  timestamp: 1699999999.123,
  transactions: [
    {
      transaction_id: "tx-...",
      event_type: "user_login",
      user: "admin@company.com",
      action: "login",
      ...
    }
  ],
  proof: 35293,
  previous_hash: "0000abc...",
  hash: "0000def...",
  merkle_root: "xyz123..."
}
```

## Security Features

- **Cryptographic Hashing**: SHA-256 for all hashes
- **Merkle Trees**: Efficient transaction verification
- **Proof of Work**: Computational cost for block creation
- **Chain Linking**: Each block references previous
- **Signature Validation**: Transaction authenticity
- **Immutability**: Tampering immediately detected

## Use Cases

1. **Compliance Auditing** - Prove compliance to auditors
2. **Forensic Investigations** - Tamper-proof evidence
3. **Regulatory Reporting** - Immutable records for regulators
4. **Incident Response** - Trusted timeline of events
5. **Access Control Auditing** - Complete access history
6. **Change Management** - Verifiable change records

## Performance

- Block creation: ~1-5 seconds (depending on proof of work)
- Transaction recording: <100ms
- Verification: <50ms
- Search: Depends on chain size (indexed for performance)

## Compliance

Meets requirements for:
- SOX (Sarbanes-Oxley)
- HIPAA audit trails
- PCI-DSS logging requirements
- GDPR accountability
- ISO 27001 audit logging

## License

Proprietary - Enterprise SIEM Platform
