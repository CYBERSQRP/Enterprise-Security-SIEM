#!/usr/bin/env python3
"""
Predictive Analytics Engine

This service provides AI-powered threat forecasting, risk prediction,
attack path prediction, and resource optimization using machine learning.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictionType(str, Enum):
    """Types of predictions"""
    THREAT_TREND = "threat_trend"
    RISK_SCORE = "risk_score"
    ATTACK_PATH = "attack_path"
    CAPACITY = "capacity"
    ALERT_VOLUME = "alert_volume"


class ThreatCategory(str, Enum):
    """Threat categories"""
    MALWARE = "malware"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    DDOS = "ddos"
    DATA_BREACH = "data_breach"
    INSIDER_THREAT = "insider_threat"
    APT = "apt"


@dataclass
class ThreatForecast:
    """Threat trend forecast"""
    threat_category: ThreatCategory
    forecast_period: str  # daily, weekly, monthly
    predictions: List[Dict]  # timestamp, predicted_count, confidence
    trend: str  # increasing, decreasing, stable
    confidence: float
    generated_at: datetime


@dataclass
class RiskPrediction:
    """Asset or user risk prediction"""
    entity_id: str
    entity_type: str  # asset, user
    current_risk: float
    predicted_risk: float
    risk_change: float
    time_horizon: int  # days
    contributing_factors: Dict[str, float]
    recommendations: List[str]
    confidence: float


@dataclass
class AttackPathPrediction:
    """Predicted attack path"""
    incident_id: str
    current_stage: str
    predicted_stages: List[Dict]
    next_targets: List[str]
    probability: float
    estimated_time_to_next_stage: int  # minutes
    recommended_actions: List[str]


@dataclass
class CapacityForecast:
    """Infrastructure capacity forecast"""
    resource_type: str  # storage, compute, network
    current_usage: float
    predicted_usage: List[Dict]  # timestamp, usage, confidence
    capacity_limit: float
    estimated_time_to_limit: Optional[int]  # days
    recommendations: List[str]


# Pydantic models for API
class ThreatForecastRequest(BaseModel):
    threat_category: ThreatCategory
    forecast_period: str = "daily"
    days_ahead: int = 30


class RiskPredictionRequest(BaseModel):
    entity_id: str
    entity_type: str
    time_horizon: int = 7  # days


class AttackPathRequest(BaseModel):
    incident_id: str
    current_indicators: List[str]


class CapacityForecastRequest(BaseModel):
    resource_type: str
    days_ahead: int = 30


# Prometheus metrics
metrics_predictions_generated = Counter(
    'predictive_analytics_predictions_generated_total',
    'Total predictions generated',
    ['prediction_type']
)

metrics_model_accuracy = Gauge(
    'predictive_analytics_model_accuracy',
    'ML model accuracy',
    ['model_name']
)

metrics_prediction_latency = Histogram(
    'predictive_analytics_prediction_latency_seconds',
    'Prediction generation latency',
    ['prediction_type']
)

metrics_active_models = Gauge(
    'predictive_analytics_active_models',
    'Number of active ML models'
)


class PredictiveAnalyticsEngine:
    """Main predictive analytics service"""

    def __init__(self):
        self.running = False
        self.models = {}

        self.config = {
            'model_update_interval': int(os.getenv('MODEL_UPDATE_INTERVAL', '86400')),  # 24 hours
            'min_confidence_threshold': float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.7')),
            'max_forecast_days': int(os.getenv('MAX_FORECAST_DAYS', '90')),
        }

    async def start(self):
        """Start the analytics service"""
        logger.info("Starting Predictive Analytics Engine...")

        # Initialize ML models
        await self.initialize_models()

        self.running = True

        # Start background tasks
        asyncio.create_task(self.model_training_worker())
        asyncio.create_task(self.accuracy_monitoring_worker())

        logger.info("Predictive Analytics Engine started successfully")

    async def stop(self):
        """Stop the analytics service"""
        logger.info("Stopping Predictive Analytics Engine...")
        self.running = False
        logger.info("Predictive Analytics Engine stopped")

    async def initialize_models(self):
        """Initialize ML models"""
        # In production, load actual models from storage
        # For now, initialize placeholders

        self.models = {
            'threat_forecaster': {
                'name': 'threat_forecaster',
                'type': 'time_series',
                'accuracy': 0.87,
                'last_trained': datetime.utcnow(),
            },
            'risk_predictor': {
                'name': 'risk_predictor',
                'type': 'gradient_boosting',
                'accuracy': 0.85,
                'last_trained': datetime.utcnow(),
            },
            'attack_path_predictor': {
                'name': 'attack_path_predictor',
                'type': 'neural_network',
                'accuracy': 0.82,
                'last_trained': datetime.utcnow(),
            },
            'capacity_forecaster': {
                'name': 'capacity_forecaster',
                'type': 'prophet',
                'accuracy': 0.90,
                'last_trained': datetime.utcnow(),
            },
        }

        metrics_active_models.set(len(self.models))

        for model_name, model_info in self.models.items():
            metrics_model_accuracy.labels(model_name=model_name).set(model_info['accuracy'])
            logger.info(f"Initialized model: {model_name} (accuracy: {model_info['accuracy']:.2f})")

    async def model_training_worker(self):
        """Background worker for model retraining"""
        while self.running:
            try:
                await asyncio.sleep(self.config['model_update_interval'])

                logger.info("Starting model retraining cycle...")

                # In production, retrain models with new data
                # For now, simulate training
                for model_name in self.models:
                    self.models[model_name]['last_trained'] = datetime.utcnow()
                    # Simulate accuracy improvement
                    current_acc = self.models[model_name]['accuracy']
                    new_acc = min(0.95, current_acc + np.random.uniform(-0.02, 0.03))
                    self.models[model_name]['accuracy'] = new_acc
                    metrics_model_accuracy.labels(model_name=model_name).set(new_acc)

                logger.info("Model retraining cycle completed")

            except Exception as e:
                logger.error(f"Error in model training worker: {e}")
                await asyncio.sleep(3600)

    async def accuracy_monitoring_worker(self):
        """Monitor and log model accuracy"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Check every hour

                for model_name, model_info in self.models.items():
                    if model_info['accuracy'] < self.config['min_confidence_threshold']:
                        logger.warning(
                            f"Model {model_name} accuracy below threshold: "
                            f"{model_info['accuracy']:.2f}"
                        )

            except Exception as e:
                logger.error(f"Error in accuracy monitoring: {e}")
                await asyncio.sleep(600)

    async def forecast_threats(self, request: ThreatForecastRequest) -> ThreatForecast:
        """Forecast threat trends"""
        logger.info(
            f"Generating threat forecast for {request.threat_category.value} "
            f"({request.days_ahead} days ahead)"
        )

        # Simulate time series prediction
        # In production, use actual ARIMA/Prophet models

        base_count = np.random.randint(50, 200)
        trend_factor = np.random.choice([0.95, 1.0, 1.05])  # decreasing, stable, increasing

        predictions = []
        current_date = datetime.utcnow()

        for i in range(request.days_ahead):
            date = current_date + timedelta(days=i)
            count = int(base_count * (trend_factor ** i) + np.random.normal(0, 10))
            confidence = max(0.6, 0.95 - (i * 0.01))  # Confidence decreases over time

            predictions.append({
                'timestamp': date.isoformat(),
                'predicted_count': max(0, count),
                'confidence': round(confidence, 2)
            })

        # Determine trend
        if trend_factor > 1.02:
            trend = "increasing"
        elif trend_factor < 0.98:
            trend = "decreasing"
        else:
            trend = "stable"

        forecast = ThreatForecast(
            threat_category=request.threat_category,
            forecast_period=request.forecast_period,
            predictions=predictions,
            trend=trend,
            confidence=self.models['threat_forecaster']['accuracy'],
            generated_at=datetime.utcnow()
        )

        metrics_predictions_generated.labels(
            prediction_type=PredictionType.THREAT_TREND.value
        ).inc()

        return forecast

    async def predict_risk(self, request: RiskPredictionRequest) -> RiskPrediction:
        """Predict future risk for an entity"""
        logger.info(
            f"Predicting risk for {request.entity_type} {request.entity_id} "
            f"({request.time_horizon} days ahead)"
        )

        # Simulate risk prediction
        # In production, use actual ML models

        current_risk = np.random.uniform(20, 80)
        risk_change = np.random.normal(0, 15)
        predicted_risk = np.clip(current_risk + risk_change, 0, 100)

        # Generate contributing factors
        factors = {
            'vulnerability_score': np.random.uniform(0, 30),
            'threat_exposure': np.random.uniform(0, 25),
            'user_behavior': np.random.uniform(0, 20),
            'network_position': np.random.uniform(0, 15),
            'patch_status': np.random.uniform(0, 10),
        }

        # Generate recommendations
        recommendations = []
        if factors['vulnerability_score'] > 20:
            recommendations.append("Apply security patches immediately")
        if factors['threat_exposure'] > 15:
            recommendations.append("Increase monitoring frequency")
        if factors['user_behavior'] > 15:
            recommendations.append("Provide security awareness training")

        prediction = RiskPrediction(
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            current_risk=round(current_risk, 2),
            predicted_risk=round(predicted_risk, 2),
            risk_change=round(risk_change, 2),
            time_horizon=request.time_horizon,
            contributing_factors=factors,
            recommendations=recommendations,
            confidence=self.models['risk_predictor']['accuracy']
        )

        metrics_predictions_generated.labels(
            prediction_type=PredictionType.RISK_SCORE.value
        ).inc()

        return prediction

    async def predict_attack_path(self, request: AttackPathRequest) -> AttackPathPrediction:
        """Predict next steps in an attack"""
        logger.info(f"Predicting attack path for incident {request.incident_id}")

        # Simulate attack path prediction
        # In production, use actual kill chain analysis and ML models

        attack_stages = [
            {"stage": "reconnaissance", "probability": 1.0, "completed": True},
            {"stage": "weaponization", "probability": 0.9, "completed": True},
            {"stage": "delivery", "probability": 0.85, "completed": True},
            {"stage": "exploitation", "probability": 0.75, "completed": False},
            {"stage": "installation", "probability": 0.60, "completed": False},
            {"stage": "command_and_control", "probability": 0.45, "completed": False},
            {"stage": "actions_on_objectives", "probability": 0.30, "completed": False},
        ]

        current_stage = "delivery"
        predicted_stages = [s for s in attack_stages if not s['completed']]

        next_targets = [
            "web-server-01",
            "database-prod-02",
            "file-server-05"
        ]

        recommended_actions = [
            "Isolate potentially compromised hosts",
            "Block outbound connections to suspicious IPs",
            "Enable enhanced logging on critical systems",
            "Deploy decoy credentials (honeytokens)",
        ]

        prediction = AttackPathPrediction(
            incident_id=request.incident_id,
            current_stage=current_stage,
            predicted_stages=predicted_stages,
            next_targets=next_targets,
            probability=0.75,
            estimated_time_to_next_stage=45,  # minutes
            recommended_actions=recommended_actions
        )

        metrics_predictions_generated.labels(
            prediction_type=PredictionType.ATTACK_PATH.value
        ).inc()

        return prediction

    async def forecast_capacity(self, request: CapacityForecastRequest) -> CapacityForecast:
        """Forecast infrastructure capacity needs"""
        logger.info(
            f"Forecasting {request.resource_type} capacity "
            f"({request.days_ahead} days ahead)"
        )

        # Simulate capacity forecasting
        # In production, use Prophet or similar time series models

        current_usage = np.random.uniform(40, 70)  # Percentage
        capacity_limit = 100.0
        growth_rate = 1.02  # 2% daily growth

        predictions = []
        current_date = datetime.utcnow()

        for i in range(request.days_ahead):
            date = current_date + timedelta(days=i)
            usage = current_usage * (growth_rate ** i) + np.random.normal(0, 2)
            confidence = max(0.7, 0.95 - (i * 0.008))

            predictions.append({
                'timestamp': date.isoformat(),
                'usage': round(min(usage, 100), 2),
                'confidence': round(confidence, 2)
            })

        # Calculate time to capacity limit
        estimated_days = None
        for i, pred in enumerate(predictions):
            if pred['usage'] >= 90:  # 90% threshold
                estimated_days = i
                break

        recommendations = []
        if estimated_days and estimated_days < 30:
            recommendations.append(f"Capacity limit will be reached in ~{estimated_days} days")
            recommendations.append(f"Plan capacity expansion for {request.resource_type}")
        if estimated_days and estimated_days < 14:
            recommendations.append("URGENT: Immediate capacity planning required")

        forecast = CapacityForecast(
            resource_type=request.resource_type,
            current_usage=round(current_usage, 2),
            predicted_usage=predictions,
            capacity_limit=capacity_limit,
            estimated_time_to_limit=estimated_days,
            recommendations=recommendations
        )

        metrics_predictions_generated.labels(
            prediction_type=PredictionType.CAPACITY.value
        ).inc()

        return forecast


# FastAPI application
app = FastAPI(
    title="Predictive Analytics Engine",
    description="AI-powered threat forecasting and risk prediction",
    version="1.0.0"
)

# Global service instance
engine = PredictiveAnalyticsEngine()


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    await engine.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    await engine.stop()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "models_loaded": len(engine.models),
        "models": list(engine.models.keys())
    }


@app.get("/api/v1/models")
async def list_models():
    """List all ML models"""
    models_info = [
        {
            "name": info['name'],
            "type": info['type'],
            "accuracy": info['accuracy'],
            "last_trained": info['last_trained'].isoformat()
        }
        for info in engine.models.values()
    ]

    return {
        "models": models_info,
        "count": len(models_info)
    }


@app.post("/api/v1/predict/threats")
async def predict_threats(request: ThreatForecastRequest):
    """Forecast threat trends"""
    forecast = await engine.forecast_threats(request)

    return {
        "threat_category": forecast.threat_category.value,
        "forecast_period": forecast.forecast_period,
        "trend": forecast.trend,
        "predictions": forecast.predictions,
        "confidence": forecast.confidence,
        "generated_at": forecast.generated_at.isoformat()
    }


@app.post("/api/v1/predict/risk")
async def predict_risk(request: RiskPredictionRequest):
    """Predict entity risk"""
    prediction = await engine.predict_risk(request)

    return {
        "entity_id": prediction.entity_id,
        "entity_type": prediction.entity_type,
        "current_risk": prediction.current_risk,
        "predicted_risk": prediction.predicted_risk,
        "risk_change": prediction.risk_change,
        "time_horizon": prediction.time_horizon,
        "contributing_factors": prediction.contributing_factors,
        "recommendations": prediction.recommendations,
        "confidence": prediction.confidence
    }


@app.post("/api/v1/predict/attack-path")
async def predict_attack_path(request: AttackPathRequest):
    """Predict attack path"""
    prediction = await engine.predict_attack_path(request)

    return {
        "incident_id": prediction.incident_id,
        "current_stage": prediction.current_stage,
        "predicted_stages": prediction.predicted_stages,
        "next_targets": prediction.next_targets,
        "probability": prediction.probability,
        "estimated_time_to_next_stage": prediction.estimated_time_to_next_stage,
        "recommended_actions": prediction.recommended_actions
    }


@app.post("/api/v1/predict/capacity")
async def predict_capacity(request: CapacityForecastRequest):
    """Forecast capacity needs"""
    forecast = await engine.forecast_capacity(request)

    return {
        "resource_type": forecast.resource_type,
        "current_usage": forecast.current_usage,
        "predicted_usage": forecast.predicted_usage,
        "capacity_limit": forecast.capacity_limit,
        "estimated_time_to_limit": forecast.estimated_time_to_limit,
        "recommendations": forecast.recommendations
    }


# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


def main():
    """Main entry point"""
    port = int(os.getenv("PORT", "8084"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
