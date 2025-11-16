# ML Training Pipeline

Infrastructure for training, evaluating, and deploying machine learning models.

## Components

### 1. Feature Engineering Pipeline
- Data extraction from Elasticsearch
- Feature transformation and normalization
- Time-series feature generation
- Feature store integration

### 2. Model Training Framework
- Distributed training support
- Hyperparameter tuning (Optuna)
- Cross-validation
- Model versioning

### 3. Model Deployment Pipeline
- Automated model validation
- A/B testing framework
- Canary deployments
- Model serving infrastructure

### 4. Model Monitoring
- Performance metrics tracking
- Data drift detection
- Model degradation alerts
- Retraining triggers

## Architecture

```
┌─────────────────┐
│  Data Sources   │
│ (Elasticsearch) │
└────────┬────────┘
         │
┌────────▼────────┐
│Feature Engineer │
│   Pipeline      │
└────────┬────────┘
         │
┌────────▼────────┐
│  Feature Store  │
│     (Feast)     │
└────────┬────────┘
         │
┌────────▼────────┐
│ Training Engine │
│   (Kubeflow)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Model Registry  │
│    (MLflow)     │
└────────┬────────┘
         │
┌────────▼────────┐
│ Model Serving   │
│ (TF Serving)    │
└─────────────────┘
```

## Files

- `feature_engineering.py` - Feature extraction and transformation
- `trainer.py` - Model training orchestration
- `evaluator.py` - Model evaluation and validation
- `deployment.py` - Model deployment automation
- `monitoring.py` - Model performance monitoring
- `config/` - Training configurations
- `scripts/` - Utility scripts

## Usage

### Training a New Model

```bash
python trainer.py --model anomaly_detection \
  --data-start 2024-01-01 \
  --data-end 2024-03-31 \
  --config config/anomaly_detection.yaml
```

### Deploying a Model

```bash
python deployment.py --model-id model_v1.2.3 \
  --strategy canary \
  --canary-percentage 10
```

### Monitoring Models

```bash
python monitoring.py --model anomaly_detection \
  --check-drift \
  --alert-threshold 0.15
```

## Configuration

See `config/` directory for example configurations.
