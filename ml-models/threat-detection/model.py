"""
Deep Learning-based Threat Detection Model

This module implements a transformer-based neural network for detecting
security threats from log events and network traffic patterns.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np


class ThreatDetectionTransformer(nn.Module):
    """
    Transformer-based model for threat detection using attention mechanisms
    to identify complex attack patterns across temporal sequences.
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        embedding_dim: int = 512,
        num_heads: int = 8,
        num_layers: int = 6,
        ff_dim: int = 2048,
        max_seq_length: int = 512,
        num_threat_classes: int = 20,
        dropout: float = 0.1
    ):
        super(ThreatDetectionTransformer, self).__init__()

        self.embedding_dim = embedding_dim
        self.max_seq_length = max_seq_length

        # Token embedding layer
        self.token_embedding = nn.Embedding(vocab_size, embedding_dim)

        # Positional encoding
        self.positional_encoding = self._create_positional_encoding(
            max_seq_length, embedding_dim
        )

        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=ff_dim,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, ff_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim // 2, num_threat_classes)
        )

        # Anomaly score head (for unsupervised detection)
        self.anomaly_detector = nn.Sequential(
            nn.Linear(embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def _create_positional_encoding(
        self, max_seq_length: int, embedding_dim: int
    ) -> torch.Tensor:
        """Create sinusoidal positional encoding."""
        position = torch.arange(max_seq_length).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, embedding_dim, 2) *
            -(np.log(10000.0) / embedding_dim)
        )

        pos_encoding = torch.zeros(max_seq_length, embedding_dim)
        pos_encoding[:, 0::2] = torch.sin(position * div_term)
        pos_encoding[:, 1::2] = torch.cos(position * div_term)

        return pos_encoding.unsqueeze(0)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the threat detection model.

        Args:
            input_ids: Token IDs [batch_size, seq_length]
            attention_mask: Attention mask [batch_size, seq_length]

        Returns:
            Dictionary containing:
                - threat_logits: Classification logits [batch_size, num_classes]
                - anomaly_score: Anomaly detection score [batch_size, 1]
                - embeddings: Contextual embeddings [batch_size, seq_length, embedding_dim]
        """
        batch_size, seq_length = input_ids.shape

        # Token embeddings
        embeddings = self.token_embedding(input_ids)

        # Add positional encoding
        pos_encoding = self.positional_encoding[:, :seq_length, :].to(embeddings.device)
        embeddings = embeddings + pos_encoding

        # Create attention mask for transformer
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        # Transformer expects mask in different format (True for positions to mask)
        transformer_mask = (attention_mask == 0)

        # Apply transformer encoder
        encoded = self.transformer_encoder(
            embeddings,
            src_key_padding_mask=transformer_mask
        )

        # Use [CLS] token representation (first token) for classification
        cls_representation = encoded[:, 0, :]

        # Threat classification
        threat_logits = self.classifier(cls_representation)

        # Anomaly detection
        anomaly_score = self.anomaly_detector(cls_representation)

        return {
            'threat_logits': threat_logits,
            'anomaly_score': anomaly_score,
            'embeddings': encoded
        }


class LSTMThreatDetector(nn.Module):
    """
    LSTM-based threat detection model for sequence analysis.
    Useful for temporal pattern detection in log sequences.
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        embedding_dim: int = 256,
        hidden_dim: int = 512,
        num_layers: int = 3,
        num_threat_classes: int = 20,
        dropout: float = 0.3,
        bidirectional: bool = True
    ):
        super(LSTMThreatDetector, self).__init__()

        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # LSTM layer
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )

        # Attention mechanism
        lstm_output_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.attention = nn.Sequential(
            nn.Linear(lstm_output_dim, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

        # Classification layers
        self.classifier = nn.Sequential(
            nn.Linear(lstm_output_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_threat_classes)
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        sequence_lengths: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through LSTM threat detector.

        Args:
            input_ids: Token IDs [batch_size, seq_length]
            sequence_lengths: Actual sequence lengths [batch_size]

        Returns:
            Dictionary with threat_logits and attention_weights
        """
        batch_size, seq_length = input_ids.shape

        # Embedding
        embedded = self.embedding(input_ids)

        # Pack sequences if lengths provided
        if sequence_lengths is not None:
            embedded = nn.utils.rnn.pack_padded_sequence(
                embedded,
                sequence_lengths.cpu(),
                batch_first=True,
                enforce_sorted=False
            )

        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(embedded)

        # Unpack if packed
        if sequence_lengths is not None:
            lstm_out, _ = nn.utils.rnn.pad_packed_sequence(
                lstm_out,
                batch_first=True
            )

        # Apply attention mechanism
        attention_scores = self.attention(lstm_out)  # [batch, seq_len, 1]
        attention_weights = F.softmax(attention_scores, dim=1)

        # Weighted sum of LSTM outputs
        context_vector = torch.sum(attention_weights * lstm_out, dim=1)

        # Classification
        threat_logits = self.classifier(context_vector)

        return {
            'threat_logits': threat_logits,
            'attention_weights': attention_weights.squeeze(-1)
        }


class CNNThreatDetector(nn.Module):
    """
    CNN-based threat detection for capturing local patterns in log sequences.
    Effective for detecting signature-based threats.
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        embedding_dim: int = 256,
        num_filters: int = 256,
        filter_sizes: List[int] = [3, 4, 5, 7],
        num_threat_classes: int = 20,
        dropout: float = 0.5
    ):
        super(CNNThreatDetector, self).__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_dim)

        # Multiple parallel convolutional layers with different kernel sizes
        self.convs = nn.ModuleList([
            nn.Conv1d(
                in_channels=embedding_dim,
                out_channels=num_filters,
                kernel_size=fs
            )
            for fs in filter_sizes
        ])

        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Linear(len(filter_sizes) * num_filters, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_threat_classes)
        )

    def forward(self, input_ids: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through CNN threat detector.

        Args:
            input_ids: Token IDs [batch_size, seq_length]

        Returns:
            Dictionary with threat_logits
        """
        # Embedding: [batch, seq_len, embedding_dim]
        embedded = self.embedding(input_ids)

        # Transpose for Conv1d: [batch, embedding_dim, seq_len]
        embedded = embedded.transpose(1, 2)

        # Apply convolutions and max pooling
        conv_outputs = []
        for conv in self.convs:
            conv_out = F.relu(conv(embedded))  # [batch, num_filters, seq_len - kernel_size + 1]
            pooled = F.max_pool1d(conv_out, conv_out.size(2))  # [batch, num_filters, 1]
            conv_outputs.append(pooled.squeeze(2))

        # Concatenate all filter outputs
        concatenated = torch.cat(conv_outputs, dim=1)  # [batch, num_filters * len(filter_sizes)]

        # Classification
        threat_logits = self.fc(concatenated)

        return {
            'threat_logits': threat_logits
        }


class EnsembleThreatDetector(nn.Module):
    """
    Ensemble model combining Transformer, LSTM, and CNN for robust threat detection.
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        num_threat_classes: int = 20,
        embedding_dim: int = 256
    ):
        super(EnsembleThreatDetector, self).__init__()

        # Individual models
        self.transformer = ThreatDetectionTransformer(
            vocab_size=vocab_size,
            embedding_dim=embedding_dim,
            num_threat_classes=num_threat_classes
        )

        self.lstm = LSTMThreatDetector(
            vocab_size=vocab_size,
            embedding_dim=embedding_dim,
            num_threat_classes=num_threat_classes
        )

        self.cnn = CNNThreatDetector(
            vocab_size=vocab_size,
            embedding_dim=embedding_dim,
            num_threat_classes=num_threat_classes
        )

        # Ensemble fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(num_threat_classes * 3, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_threat_classes)
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through ensemble model.
        """
        # Get predictions from all models
        transformer_out = self.transformer(input_ids, attention_mask)
        lstm_out = self.lstm(input_ids)
        cnn_out = self.cnn(input_ids)

        # Concatenate logits
        combined_logits = torch.cat([
            transformer_out['threat_logits'],
            lstm_out['threat_logits'],
            cnn_out['threat_logits']
        ], dim=1)

        # Fuse predictions
        final_logits = self.fusion(combined_logits)

        return {
            'threat_logits': final_logits,
            'transformer_logits': transformer_out['threat_logits'],
            'lstm_logits': lstm_out['threat_logits'],
            'cnn_logits': cnn_out['threat_logits'],
            'anomaly_score': transformer_out['anomaly_score']
        }
