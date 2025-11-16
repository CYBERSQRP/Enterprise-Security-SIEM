"""
Training Pipeline for Threat Detection Models

This module provides the training infrastructure for deep learning threat detection models.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Optional, Tuple, Callable
import numpy as np
from pathlib import Path
import json
import logging
from dataclasses import dataclass
from tqdm import tqdm
import wandb

from .model import (
    ThreatDetectionTransformer,
    LSTMThreatDetector,
    CNNThreatDetector,
    EnsembleThreatDetector
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    model_type: str = 'transformer'  # 'transformer', 'lstm', 'cnn', 'ensemble'
    vocab_size: int = 50000
    embedding_dim: int = 512
    num_threat_classes: int = 20
    max_seq_length: int = 512

    # Training parameters
    batch_size: int = 32
    num_epochs: int = 50
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    warmup_steps: int = 1000
    gradient_clip: float = 1.0

    # Optimization
    optimizer: str = 'adamw'  # 'adam', 'adamw', 'sgd'
    scheduler: str = 'cosine'  # 'cosine', 'linear', 'step'
    label_smoothing: float = 0.1

    # Regularization
    dropout: float = 0.1
    use_mixup: bool = True
    mixup_alpha: float = 0.2

    # Early stopping
    patience: int = 10
    min_delta: float = 0.001

    # Checkpointing
    checkpoint_dir: str = './checkpoints'
    save_every_n_epochs: int = 5

    # Logging
    use_wandb: bool = False
    wandb_project: str = 'siem-threat-detection'
    log_every_n_steps: int = 100


class ThreatDetectionDataset(Dataset):
    """Dataset for threat detection training."""

    def __init__(
        self,
        data_path: str,
        max_seq_length: int = 512,
        tokenizer: Optional[Callable] = None
    ):
        self.data_path = Path(data_path)
        self.max_seq_length = max_seq_length
        self.tokenizer = tokenizer or self._default_tokenizer

        # Load data
        self.samples = self._load_data()

    def _load_data(self) -> List[Dict]:
        """Load training data from disk."""
        samples = []

        # Load from JSONL format
        if self.data_path.suffix == '.jsonl':
            with open(self.data_path, 'r') as f:
                for line in f:
                    sample = json.loads(line)
                    samples.append(sample)

        logger.info(f"Loaded {len(samples)} samples from {self.data_path}")
        return samples

    def _default_tokenizer(self, text: str) -> List[int]:
        """Simple whitespace tokenizer (replace with actual tokenizer)."""
        tokens = text.lower().split()
        # Convert to IDs (simplified)
        return [hash(token) % 50000 for token in tokens]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]

        # Tokenize log event
        log_text = sample['log_text']
        token_ids = self.tokenizer(log_text)

        # Truncate or pad to max_seq_length
        if len(token_ids) > self.max_seq_length:
            token_ids = token_ids[:self.max_seq_length]
        else:
            token_ids = token_ids + [0] * (self.max_seq_length - len(token_ids))

        # Create attention mask
        attention_mask = [1 if tid != 0 else 0 for tid in token_ids]

        return {
            'input_ids': torch.tensor(token_ids, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'label': torch.tensor(sample['label'], dtype=torch.long),
            'is_anomaly': torch.tensor(sample.get('is_anomaly', 0), dtype=torch.float)
        }


class FocalLoss(nn.Module):
    """Focal Loss for handling class imbalance in threat detection."""

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_loss = nn.functional.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss.mean()


class ThreatDetectionTrainer:
    """Trainer for threat detection models."""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Initialize model
        self.model = self._create_model()
        self.model.to(self.device)

        # Loss functions
        self.classification_loss = FocalLoss()
        self.anomaly_loss = nn.BCELoss()

        # Optimizer
        self.optimizer = self._create_optimizer()

        # Learning rate scheduler
        self.scheduler = None

        # Metrics tracking
        self.best_val_loss = float('inf')
        self.patience_counter = 0

        # Initialize wandb if enabled
        if config.use_wandb:
            wandb.init(project=config.wandb_project, config=config.__dict__)

    def _create_model(self) -> nn.Module:
        """Create model based on configuration."""
        model_config = {
            'vocab_size': self.config.vocab_size,
            'num_threat_classes': self.config.num_threat_classes,
            'embedding_dim': self.config.embedding_dim,
            'dropout': self.config.dropout
        }

        if self.config.model_type == 'transformer':
            return ThreatDetectionTransformer(**model_config)
        elif self.config.model_type == 'lstm':
            return LSTMThreatDetector(**model_config)
        elif self.config.model_type == 'cnn':
            return CNNThreatDetector(**model_config)
        elif self.config.model_type == 'ensemble':
            return EnsembleThreatDetector(**model_config)
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")

    def _create_optimizer(self) -> optim.Optimizer:
        """Create optimizer."""
        if self.config.optimizer == 'adam':
            return optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        elif self.config.optimizer == 'adamw':
            return optim.AdamW(
                self.model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        elif self.config.optimizer == 'sgd':
            return optim.SGD(
                self.model.parameters(),
                lr=self.config.learning_rate,
                momentum=0.9,
                weight_decay=self.config.weight_decay
            )
        else:
            raise ValueError(f"Unknown optimizer: {self.config.optimizer}")

    def _create_scheduler(self, num_training_steps: int):
        """Create learning rate scheduler."""
        if self.config.scheduler == 'cosine':
            self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=num_training_steps
            )
        elif self.config.scheduler == 'linear':
            self.scheduler = optim.lr_scheduler.LinearLR(
                self.optimizer,
                start_factor=0.1,
                total_iters=self.config.warmup_steps
            )
        elif self.config.scheduler == 'step':
            self.scheduler = optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=10,
                gamma=0.1
            )

    def _mixup_data(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
        alpha: float = 0.2
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, float]:
        """Apply mixup augmentation."""
        if alpha > 0:
            lam = np.random.beta(alpha, alpha)
        else:
            lam = 1

        batch_size = x.size(0)
        index = torch.randperm(batch_size).to(x.device)

        mixed_x = lam * x + (1 - lam) * x[index, :]
        y_a, y_b = y, y[index]

        return mixed_x, y_a, y_b, lam

    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        total_class_loss = 0
        total_anomaly_loss = 0
        correct = 0
        total = 0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch}")

        for batch_idx, batch in enumerate(pbar):
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['label'].to(self.device)
            is_anomaly = batch['is_anomaly'].to(self.device)

            # Apply mixup if enabled
            if self.config.use_mixup and np.random.random() < 0.5:
                input_ids, labels_a, labels_b, lam = self._mixup_data(
                    input_ids,
                    labels,
                    self.config.mixup_alpha
                )

            # Forward pass
            outputs = self.model(input_ids, attention_mask)
            threat_logits = outputs['threat_logits']

            # Calculate loss
            if self.config.use_mixup and 'labels_a' in locals():
                class_loss = lam * self.classification_loss(threat_logits, labels_a) + \
                           (1 - lam) * self.classification_loss(threat_logits, labels_b)
            else:
                class_loss = self.classification_loss(threat_logits, labels)

            # Anomaly detection loss (if available)
            anomaly_loss = 0
            if 'anomaly_score' in outputs:
                anomaly_loss = self.anomaly_loss(
                    outputs['anomaly_score'].squeeze(),
                    is_anomaly
                )

            # Total loss
            loss = class_loss + 0.3 * anomaly_loss

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            if self.config.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config.gradient_clip
                )

            self.optimizer.step()

            if self.scheduler:
                self.scheduler.step()

            # Metrics
            total_loss += loss.item()
            total_class_loss += class_loss.item()
            if isinstance(anomaly_loss, torch.Tensor):
                total_anomaly_loss += anomaly_loss.item()

            _, predicted = threat_logits.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            # Update progress bar
            pbar.set_postfix({
                'loss': f"{loss.item():.4f}",
                'acc': f"{100. * correct / total:.2f}%"
            })

            # Log to wandb
            if self.config.use_wandb and batch_idx % self.config.log_every_n_steps == 0:
                wandb.log({
                    'train/loss': loss.item(),
                    'train/class_loss': class_loss.item(),
                    'train/accuracy': 100. * correct / total,
                    'train/lr': self.optimizer.param_groups[0]['lr']
                })

        return {
            'loss': total_loss / len(train_loader),
            'class_loss': total_class_loss / len(train_loader),
            'anomaly_loss': total_anomaly_loss / len(train_loader),
            'accuracy': 100. * correct / total
        }

    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """Validate the model."""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)
                is_anomaly = batch['is_anomaly'].to(self.device)

                outputs = self.model(input_ids, attention_mask)
                threat_logits = outputs['threat_logits']

                loss = self.classification_loss(threat_logits, labels)

                if 'anomaly_score' in outputs:
                    anomaly_loss = self.anomaly_loss(
                        outputs['anomaly_score'].squeeze(),
                        is_anomaly
                    )
                    loss += 0.3 * anomaly_loss

                total_loss += loss.item()

                _, predicted = threat_logits.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        return {
            'loss': total_loss / len(val_loader),
            'accuracy': 100. * correct / total
        }

    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset
    ):
        """Full training loop."""
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )

        # Create scheduler
        num_training_steps = len(train_loader) * self.config.num_epochs
        self._create_scheduler(num_training_steps)

        # Create checkpoint directory
        Path(self.config.checkpoint_dir).mkdir(parents=True, exist_ok=True)

        # Training loop
        for epoch in range(1, self.config.num_epochs + 1):
            logger.info(f"\n{'=' * 50}")
            logger.info(f"Epoch {epoch}/{self.config.num_epochs}")
            logger.info(f"{'=' * 50}")

            # Train
            train_metrics = self.train_epoch(train_loader, epoch)
            logger.info(f"Train - Loss: {train_metrics['loss']:.4f}, "
                       f"Acc: {train_metrics['accuracy']:.2f}%")

            # Validate
            val_metrics = self.validate(val_loader)
            logger.info(f"Val   - Loss: {val_metrics['loss']:.4f}, "
                       f"Acc: {val_metrics['accuracy']:.2f}%")

            # Log to wandb
            if self.config.use_wandb:
                wandb.log({
                    'epoch': epoch,
                    'val/loss': val_metrics['loss'],
                    'val/accuracy': val_metrics['accuracy']
                })

            # Save checkpoint
            if epoch % self.config.save_every_n_epochs == 0:
                self._save_checkpoint(epoch, val_metrics['loss'])

            # Early stopping
            if val_metrics['loss'] < self.best_val_loss - self.config.min_delta:
                self.best_val_loss = val_metrics['loss']
                self.patience_counter = 0
                self._save_checkpoint(epoch, val_metrics['loss'], is_best=True)
            else:
                self.patience_counter += 1

            if self.patience_counter >= self.config.patience:
                logger.info(f"Early stopping triggered after {epoch} epochs")
                break

        logger.info("\nTraining completed!")

    def _save_checkpoint(self, epoch: int, val_loss: float, is_best: bool = False):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'config': self.config.__dict__
        }

        if is_best:
            path = Path(self.config.checkpoint_dir) / 'best_model.pt'
            torch.save(checkpoint, path)
            logger.info(f"Saved best model checkpoint to {path}")
        else:
            path = Path(self.config.checkpoint_dir) / f'checkpoint_epoch_{epoch}.pt'
            torch.save(checkpoint, path)
            logger.info(f"Saved checkpoint to {path}")
