# Anomaly Detection Models

Machine learning models for detecting anomalous behavior in security events.

## Models

### 1. Network Traffic Anomaly Detection
**Purpose**: Detect unusual network traffic patterns

**Features**:
- Packet size distribution
- Protocol usage patterns
- Connection frequency
- Port usage anomalies
- Geographic location anomalies

**Algorithm**: Isolation Forest, Autoencoder

**Use Cases**:
- Data exfiltration detection
- C2 communication detection
- Port scanning detection
- DDoS attack detection

### 2. Authentication Anomaly Detection
**Purpose**: Detect unusual authentication patterns

**Features**:
- Login time patterns
- Login location
- Failed login attempts
- User agent patterns
- Session duration

**Algorithm**: LSTM-based time series analysis, One-Class SVM

**Use Cases**:
- Brute force attack detection
- Credential stuffing detection
- Account takeover detection
- Impossible travel detection

### 3. Process Execution Anomaly Detection
**Purpose**: Detect unusual process execution behavior

**Features**:
- Process execution frequency
- Parent-child process relationships
- Command line arguments
- File access patterns
- Network connections from processes

**Algorithm**: Random Forest, Graph Neural Networks

**Use Cases**:
- Malware execution detection
- Living-off-the-land (LOL) binary abuse
- Privilege escalation detection
- Lateral movement detection

### 4. Statistical Baseline Models
**Purpose**: Establish behavioral baselines for anomaly detection

**Features**:
- Time-series decomposition
- Statistical threshold calculation
- Seasonal pattern identification
- Trend analysis

**Algorithm**: ARIMA, Prophet, STL decomposition

**Use Cases**:
- Volume anomaly detection
- Periodicity detection
- Baseline establishment

## Architecture

```
┌─────────────────┐
│  Event Stream   │
│    (Kafka)      │
└────────┬────────┘
         │
┌────────▼────────┐
│Feature Extractor│
└────────┬────────┘
         │
┌────────▼────────┐
│  Model Serving  │
│  (Ensemble of   │
│   all models)   │
└────────┬────────┘
         │
┌────────▼────────┐
│ Anomaly Scores  │
│   & Alerts      │
└─────────────────┘
```

## Files

- `network_anomaly/` - Network traffic anomaly detection
  - `model.py` - Model implementation
  - `features.py` - Feature engineering
  - `train.py` - Training script
- `auth_anomaly/` - Authentication anomaly detection
- `process_anomaly/` - Process execution anomaly detection
- `baseline/` - Statistical baseline models
- `config/` - Model configurations
- `notebooks/` - Jupyter notebooks for experimentation

## Training

Each model can be trained independently:

```bash
# Network anomaly detection
python network_anomaly/train.py --config config/network.yaml

# Authentication anomaly detection
python auth_anomaly/train.py --config config/auth.yaml

# Process anomaly detection
python process_anomaly/train.py --config config/process.yaml
```

## Inference

Models are served via the ML service and can be queried via API:

```bash
POST /api/v1/ml/predict/network-anomaly
{
  "events": [...]
}
```

## Performance Metrics

- **Network Anomaly**: 95% precision, 92% recall
- **Auth Anomaly**: 93% precision, 90% recall
- **Process Anomaly**: 91% precision, 88% recall

## Model Updates

Models are retrained:
- Weekly with new data
- When performance degrades below threshold
- When data drift is detected
