# Phase 5 Quick Start Guide

Get started with Phase 5 AI/ML and optimization features in 15 minutes.

## Prerequisites

- Kubernetes cluster running Phase 1-4 components
- kubectl configured
- Python 3.11+ (for ML training)
- Node.js 18+ (for visualization components)

## Step 1: Deploy AI/ML Services (5 minutes)

### Deploy ML Models

```bash
# Navigate to project root
cd /path/to/Enterprise-Security-SIEM

# Create ML namespace
kubectl create namespace siem-ml

# Deploy threat detection models
kubectl apply -f infrastructure/kubernetes/ml-models/

# Verify deployment
kubectl get pods -n siem-ml
```

### Deploy AI Analyst Assistant

```bash
# Deploy AI analyst service
kubectl apply -f infrastructure/kubernetes/ai-services/

# Check status
kubectl get svc -n siem-platform | grep ai-analyst
```

## Step 2: Train Initial ML Models (5 minutes)

### Prepare Training Data

```bash
# Export training data from existing events
python scripts/export_training_data.py \
  --output /data/training/ \
  --days 90 \
  --min-events 1000
```

### Train Threat Detection Model

```python
# train_threat_model.py
from ml_models.threat_detection.trainer import ThreatDetectionTrainer, TrainingConfig
from ml_models.threat_detection.trainer import ThreatDetectionDataset

# Configure training
config = TrainingConfig(
    model_type='transformer',
    num_epochs=10,  # Quick training
    batch_size=32,
    learning_rate=1e-4,
    checkpoint_dir='./checkpoints'
)

# Load datasets
train_dataset = ThreatDetectionDataset('/data/training/train.jsonl')
val_dataset = ThreatDetectionDataset('/data/training/val.jsonl')

# Train model
trainer = ThreatDetectionTrainer(config)
trainer.train(train_dataset, val_dataset)
```

Run training:
```bash
python train_threat_model.py
```

## Step 3: Enable AI Features (2 minutes)

### Update Configuration

```bash
# Enable AI analyst
kubectl set env deployment/api-gateway AI_ANALYST_ENABLED=true

# Enable alert prioritization
kubectl set env deployment/alert-manager AI_PRIORITIZATION_ENABLED=true

# Enable NLP log analysis
kubectl set env deployment/log-processor NLP_ANALYSIS_ENABLED=true
```

### Verify AI Services

```bash
# Check AI analyst health
curl https://siem.example.com/api/ai/health

# Expected output:
# {
#   "status": "healthy",
#   "models_loaded": true,
#   "version": "1.0.0"
# }
```

## Step 4: Test AI Features (3 minutes)

### Test AI Analyst Assistant

```python
from siem_sdk import SIEMClient

client = SIEMClient(
    api_url="https://siem.example.com/api",
    api_key="your-api-key"
)

# Get a recent alert
alerts = client.alerts.list(limit=1)
alert = alerts[0]

# Analyze with AI
analysis = client.ai.analyze_alert(alert.alert_id)

print("Risk Assessment:", analysis['risk_assessment'])
print("Recommendations:", analysis['recommendations'])
print("Next Steps:", analysis['next_steps'])
```

### Test NLP Log Analysis

```python
from ml_models.nlp_analysis.log_analyzer import NLPLogAnalyzer

analyzer = NLPLogAnalyzer()

log = "Failed SSH login from 192.168.1.100 for user root"
result = analyzer.analyze_log(log)

print("Entities:", result['entities'])
print("Template:", result['template'])
```

### Test Alert Prioritization

```python
from services.alert_prioritization.prioritizer import IntelligentAlertPrioritizer
from services.alert_prioritization.prioritizer import Alert
from datetime import datetime

prioritizer = IntelligentAlertPrioritizer()

alert = Alert(
    alert_id="test-123",
    timestamp=datetime.utcnow(),
    alert_type="brute_force",
    severity="high",
    source_ip="10.0.0.5"
)

result = prioritizer.prioritize_alert(alert)
print(f"Priority: {result.priority.name}")
print(f"Score: {result.priority_score:.2f}")
print(f"SLA: {result.recommended_sla}")
```

## Step 5: Deploy Visualizations (Optional)

```bash
# Build visualization components
cd web-ui
npm install
npm run build

# Deploy to Kubernetes
kubectl apply -f infrastructure/kubernetes/web-ui/

# Access visualizations
# Navigate to: https://siem.example.com/visualizations
```

## Common Tasks

### View AI Analyst Recommendations

```bash
# Using Python SDK
python -c "
from siem_sdk import SIEMClient
client = SIEMClient(api_url='...', api_key='...')
alerts = client.alerts.list(status='open')
for alert in alerts[:5]:
    analysis = client.ai.analyze_alert(alert.alert_id)
    print(f'Alert: {alert.title}')
    print(f'Priority: {analysis[\"triage_decision\"][\"priority\"]}')
    print('---')
"
```

### Enable Query Optimization

```python
from services.performance_optimizer.optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer()

# Analyze your queries
query = {
    'filters': {'event_type': 'failed_login'},
    'time_range': {'gte': '2024-01-01', 'lte': '2024-12-31'}
}

analysis = optimizer.query_optimizer.analyze_query(query)
optimized = optimizer.query_optimizer.optimize_query(query)

print("Original:", query)
print("Optimized:", optimized)
print("Improvements:", analysis['optimizations'])
```

### Start Forensic Investigation

```python
from services.forensics.investigator import ForensicInvestigator

investigator = ForensicInvestigator()

# Create case
case = investigator.create_case(
    case_name="Suspicious Login Investigation",
    incident_id="INC-2024-001",
    investigator="analyst@company.com"
)

# Collect evidence
results = await investigator.conduct_investigation(
    case,
    target_systems=["web-server-01"]
)

print(f"Evidence collected: {results['evidence_count']}")
print(f"Findings: {results['findings_count']}")
```

## Performance Tuning

### Optimize Query Cache

```bash
# Increase cache size
kubectl set env deployment/api-gateway \
  QUERY_CACHE_SIZE=20000 \
  QUERY_CACHE_TTL=600
```

### Enable GPU for ML Models

```bash
# Update deployment to use GPU
kubectl patch deployment threat-detector \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"threat-detector","resources":{"limits":{"nvidia.com/gpu":"1"}}}]}}}}'
```

### Configure Data Tiering

```python
from services.performance_optimizer.optimizer import DataTieringManager

tier_manager = DataTieringManager()

# Configure tier policies
tier_manager.tier_policies['hot']['max_age_days'] = 7
tier_manager.tier_policies['warm']['max_age_days'] = 30

# Analyze current tiering
analysis = tier_manager.analyze_tiering_efficiency()
print(analysis['recommendations'])
```

## Monitoring

### Check ML Model Performance

```bash
# View model metrics
kubectl logs -n siem-ml deployment/threat-detector --tail=100

# Check inference latency
curl https://siem.example.com/api/metrics/ml | jq '.inference_latency_ms'
```

### Monitor Query Performance

```python
from services.performance_optimizer.optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer()

# Get slow queries
slow_queries = optimizer.query_optimizer.get_slow_queries(10)
for query in slow_queries:
    print(f"Hash: {query.query_hash}")
    print(f"Time: {query.execution_time_ms}ms")
    print(f"Rows: {query.rows_scanned}")
```

### View Cache Statistics

```python
from services.performance_optimizer.optimizer import QueryCache

cache = QueryCache()
stats = cache.get_stats()

print(f"Hit Rate: {stats['hit_rate']:.2%}")
print(f"Size: {stats['size']}/{stats['max_size']}")
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
```

## Troubleshooting

### AI Analyst Not Working

```bash
# Check logs
kubectl logs -n siem-platform deployment/ai-analyst --tail=50

# Verify model is loaded
kubectl exec -it deployment/ai-analyst -- python -c "
import torch
print('CUDA available:', torch.cuda.is_available())
"
```

### Slow ML Inference

```bash
# Enable batch inference
kubectl set env deployment/threat-detector BATCH_INFERENCE=true BATCH_SIZE=64

# Use GPU
kubectl patch deployment threat-detector \
  --patch '{"spec":{"template":{"spec":{"nodeSelector":{"gpu":"true"}}}}}'
```

### High Memory Usage

```bash
# Reduce cache size
kubectl set env deployment/api-gateway QUERY_CACHE_SIZE=5000

# Enable data tiering
kubectl set env deployment/data-tier-manager AUTO_TIER=true
```

## Next Steps

1. **Explore Advanced Features**
   - Set up automated playbooks
   - Configure custom ML models
   - Build custom visualizations

2. **Integrate with Existing Tools**
   - SOAR platform integration
   - Ticketing system integration
   - Chat ops (Slack, Teams)

3. **Customize for Your Environment**
   - Train models on your data
   - Customize alert prioritization rules
   - Build custom dashboards

4. **Scale Up**
   - Add more GPU nodes
   - Increase cache sizes
   - Configure auto-scaling

## Resources

- [Full Phase 5 Documentation](PHASE5_README.md)
- [API Reference](../api/API_SPECIFICATION.md)
- [Python SDK Documentation](../../sdk/python/README.md)
- [JavaScript SDK Documentation](../../sdk/javascript/README.md)

## Support

Need help?
- Check the [troubleshooting guide](PHASE5_README.md#troubleshooting)
- Open an issue on GitHub
- Contact support@enterprise-siem.com

---

**Congratulations! You've successfully deployed Phase 5 AI/ML features. Your SIEM is now powered by cutting-edge artificial intelligence.**
