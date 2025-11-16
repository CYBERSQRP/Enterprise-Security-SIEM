# Machine Learning Models

This directory contains all machine learning models and related infrastructure for the Enterprise SIEM platform.

## Phase 3: Advanced Analytics Components

### Overview
Phase 3 introduces advanced machine learning capabilities, user behavior analytics, and threat hunting features to enhance the SIEM platform's detection and analysis capabilities.

## Directory Structure

```
ml-models/
├── anomaly-detection/       # Anomaly detection models
├── threat-classification/   # Threat classification models
├── training-pipeline/       # Model training infrastructure
└── uba-models/             # User Behavior Analytics models
```

## Components

### 1. Anomaly Detection Models
- Network traffic anomaly detection
- Authentication anomaly detection
- Process execution anomaly detection
- Statistical baseline models

### 2. Threat Classification
- ML-based threat categorization
- Attack pattern recognition
- Malware classification

### 3. Training Pipeline
- Automated model training
- Feature engineering
- Model versioning and deployment
- Performance monitoring

### 4. UBA Models
- User behavior profiling
- Baseline behavior models
- Peer group analysis
- Risk scoring models

## Technology Stack

- **ML Framework**: PyTorch, TensorFlow, scikit-learn
- **Feature Store**: Feast
- **Model Registry**: MLflow
- **Training**: Kubernetes with GPU support
- **Serving**: TensorFlow Serving, TorchServe

## Getting Started

See individual component README files for detailed setup and usage instructions.
