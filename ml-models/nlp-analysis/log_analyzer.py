"""
NLP-Based Log Analysis Service

This module provides natural language processing capabilities for analyzing
security logs, extracting entities, and understanding semantic patterns.
"""

import torch
import torch.nn as nn
from transformers import (
    BertModel,
    BertTokenizer,
    RobertaModel,
    RobertaTokenizer,
    AutoModel,
    AutoTokenizer
)
from typing import Dict, List, Tuple, Optional, Set
import re
import json
from dataclasses import dataclass
from enum import Enum
import numpy as np


class EntityType(Enum):
    """Types of entities that can be extracted from logs."""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    USERNAME = "username"
    PROCESS_NAME = "process_name"
    FILE_PATH = "file_path"
    HASH = "hash"
    PORT = "port"
    CVE = "cve"
    COMMAND = "command"
    REGISTRY_KEY = "registry_key"
    MAC_ADDRESS = "mac_address"


@dataclass
class Entity:
    """Represents an extracted entity from a log."""
    text: str
    entity_type: EntityType
    confidence: float
    start_pos: int
    end_pos: int
    context: str


@dataclass
class LogIntent:
    """Represents the intent/purpose of a log message."""
    intent_type: str  # e.g., "authentication_failure", "file_access", "network_connection"
    confidence: float
    attributes: Dict[str, any]


class LogEntityExtractor:
    """Extracts security-relevant entities from log messages using regex and NLP."""

    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[EntityType, re.Pattern]:
        """Compile regex patterns for entity extraction."""
        return {
            EntityType.IP_ADDRESS: re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),
            EntityType.DOMAIN: re.compile(
                r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
            ),
            EntityType.URL: re.compile(
                r'https?://(?:[-\w.])+(?::\d+)?(?:/[^\s]*)?'
            ),
            EntityType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            EntityType.FILE_PATH: re.compile(
                r'(?:[A-Za-z]:\\|/)[^\s:;,<>"|?*]+'
            ),
            EntityType.HASH: re.compile(
                r'\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b'
            ),
            EntityType.PORT: re.compile(
                r'\b(?:port[:\s]+)?(\d{1,5})\b'
            ),
            EntityType.CVE: re.compile(
                r'\bCVE-\d{4}-\d{4,}\b'
            ),
            EntityType.MAC_ADDRESS: re.compile(
                r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'
            ),
        }

    def extract_entities(self, log_text: str) -> List[Entity]:
        """Extract all entities from a log message."""
        entities = []

        for entity_type, pattern in self.patterns.items():
            for match in pattern.finditer(log_text):
                entity = Entity(
                    text=match.group(),
                    entity_type=entity_type,
                    confidence=1.0,  # Regex-based extraction has high confidence
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=log_text[max(0, match.start() - 50):match.end() + 50]
                )
                entities.append(entity)

        return entities


class BERTLogClassifier(nn.Module):
    """BERT-based classifier for log intent classification."""

    def __init__(
        self,
        model_name: str = 'bert-base-uncased',
        num_intents: int = 50,
        dropout: float = 0.1
    ):
        super(BERTLogClassifier, self).__init__()

        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_intents)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass for log classification.

        Args:
            input_ids: Token IDs [batch_size, seq_length]
            attention_mask: Attention mask [batch_size, seq_length]

        Returns:
            Intent logits [batch_size, num_intents]
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        # Use [CLS] token representation
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)

        logits = self.classifier(pooled_output)
        return logits


class LogSemanticAnalyzer:
    """Analyzes semantic meaning and relationships in log messages."""

    def __init__(
        self,
        model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()

    def get_embedding(self, text: str) -> np.ndarray:
        """Get semantic embedding for a log message."""
        # Tokenize
        encoded = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )

        # Move to device
        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**encoded)

            # Mean pooling
            attention_mask = encoded['attention_mask']
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                input_mask_expanded.sum(1), min=1e-9
            )

        return embeddings.cpu().numpy()[0]

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two log messages."""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    def find_similar_logs(
        self,
        query_log: str,
        log_corpus: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find similar logs from a corpus."""
        query_emb = self.get_embedding(query_log)

        similarities = []
        for log in log_corpus:
            log_emb = self.get_embedding(log)
            similarity = np.dot(query_emb, log_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(log_emb)
            )
            similarities.append((log, float(similarity)))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class LogTemplateExtractor:
    """Extracts log templates and identifies variable fields."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.templates: List[Dict] = []

    def extract_template(self, log_messages: List[str]) -> List[str]:
        """Extract common templates from log messages."""
        templates = []

        for log in log_messages:
            # Tokenize
            tokens = log.split()

            # Replace variable content with placeholders
            template_tokens = []
            for token in tokens:
                if self._is_variable(token):
                    template_tokens.append('<*>')
                else:
                    template_tokens.append(token)

            template = ' '.join(template_tokens)
            templates.append(template)

        return templates

    def _is_variable(self, token: str) -> bool:
        """Determine if a token is a variable field."""
        # Check if token is a number
        if re.match(r'^\d+$', token):
            return True

        # Check if token is an IP address
        if re.match(r'^(?:\d{1,3}\.){3}\d{1,3}$', token):
            return True

        # Check if token is a timestamp
        if re.match(r'^\d{4}-\d{2}-\d{2}', token):
            return True

        # Check if token is a hash
        if re.match(r'^[a-fA-F0-9]{32,64}$', token):
            return True

        return False


class LogAnomalyDetector:
    """Detects anomalous log messages using NLP techniques."""

    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.semantic_analyzer = LogSemanticAnalyzer()
        self.normal_embeddings: Optional[np.ndarray] = None

    def fit(self, normal_logs: List[str]):
        """Fit the anomaly detector on normal log messages."""
        embeddings = []
        for log in normal_logs:
            emb = self.semantic_analyzer.get_embedding(log)
            embeddings.append(emb)

        self.normal_embeddings = np.array(embeddings)

    def predict(self, log_messages: List[str]) -> List[bool]:
        """Predict if log messages are anomalous."""
        if self.normal_embeddings is None:
            raise ValueError("Model not fitted. Call fit() first.")

        predictions = []

        for log in log_messages:
            log_emb = self.semantic_analyzer.get_embedding(log)

            # Compute distances to normal logs
            distances = np.linalg.norm(
                self.normal_embeddings - log_emb,
                axis=1
            )

            # Use percentile-based threshold
            threshold = np.percentile(distances, (1 - self.contamination) * 100)
            min_distance = np.min(distances)

            is_anomaly = min_distance > threshold
            predictions.append(is_anomaly)

        return predictions

    def get_anomaly_score(self, log_message: str) -> float:
        """Get anomaly score for a log message."""
        if self.normal_embeddings is None:
            raise ValueError("Model not fitted. Call fit() first.")

        log_emb = self.semantic_analyzer.get_embedding(log_message)

        # Compute distances to normal logs
        distances = np.linalg.norm(
            self.normal_embeddings - log_emb,
            axis=1
        )

        # Normalize score between 0 and 1
        min_distance = np.min(distances)
        max_distance = np.max(distances)

        if max_distance == min_distance:
            return 0.0

        score = (min_distance - np.min(distances)) / (max_distance - np.min(distances))
        return float(score)


class NLPLogAnalyzer:
    """Main NLP log analysis service combining all components."""

    def __init__(self):
        self.entity_extractor = LogEntityExtractor()
        self.semantic_analyzer = LogSemanticAnalyzer()
        self.template_extractor = LogTemplateExtractor()
        self.anomaly_detector = LogAnomalyDetector()

    def analyze_log(self, log_message: str) -> Dict:
        """Perform comprehensive NLP analysis on a log message."""
        # Extract entities
        entities = self.entity_extractor.extract_entities(log_message)

        # Get semantic embedding
        embedding = self.semantic_analyzer.get_embedding(log_message)

        # Extract template
        template = self.template_extractor.extract_template([log_message])[0]

        # Prepare result
        result = {
            'log_message': log_message,
            'entities': [
                {
                    'text': e.text,
                    'type': e.entity_type.value,
                    'confidence': e.confidence,
                    'position': (e.start_pos, e.end_pos)
                }
                for e in entities
            ],
            'template': template,
            'embedding': embedding.tolist(),
            'analysis_metadata': {
                'num_entities': len(entities),
                'entity_types': list(set(e.entity_type.value for e in entities))
            }
        }

        return result

    def batch_analyze(self, log_messages: List[str]) -> List[Dict]:
        """Analyze multiple log messages."""
        return [self.analyze_log(log) for log in log_messages]

    def detect_anomalies(
        self,
        log_messages: List[str],
        baseline_logs: Optional[List[str]] = None
    ) -> List[Dict]:
        """Detect anomalous logs in a batch."""
        if baseline_logs:
            self.anomaly_detector.fit(baseline_logs)

        anomaly_predictions = self.anomaly_detector.predict(log_messages)
        results = []

        for log, is_anomaly in zip(log_messages, anomaly_predictions):
            score = self.anomaly_detector.get_anomaly_score(log)
            results.append({
                'log_message': log,
                'is_anomaly': is_anomaly,
                'anomaly_score': score
            })

        return results

    def cluster_logs(
        self,
        log_messages: List[str],
        num_clusters: int = 10
    ) -> Dict[int, List[str]]:
        """Cluster similar log messages together."""
        from sklearn.cluster import KMeans

        # Get embeddings
        embeddings = []
        for log in log_messages:
            emb = self.semantic_analyzer.get_embedding(log)
            embeddings.append(emb)

        embeddings = np.array(embeddings)

        # Perform clustering
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Group logs by cluster
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(log_messages[i])

        return clusters
