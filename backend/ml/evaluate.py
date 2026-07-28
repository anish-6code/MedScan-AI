"""
ml/evaluate.py

Evaluation metrics for binary segmentation.
Used during training (validation loop) and for standalone evaluation.
"""
import torch


def dice_score(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Dice coefficient (F1) — higher is better, max 1.0."""
    pred   = (pred   > threshold).float()
    target = (target > threshold).float()
    smooth = 1e-6
    intersection = (pred * target).sum()
    return ((2.0 * intersection + smooth) / (pred.sum() + target.sum() + smooth)).item()


def iou_score(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Intersection over Union (Jaccard index) — higher is better, max 1.0."""
    pred   = (pred   > threshold).float()
    target = (target > threshold).float()
    smooth = 1e-6
    intersection = (pred * target).sum()
    union        = pred.sum() + target.sum() - intersection
    return ((intersection + smooth) / (union + smooth)).item()


def pixel_accuracy(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Fraction of correctly classified pixels."""
    pred   = (pred   > threshold).float()
    target = (target > threshold).float()
    correct = (pred == target).float().sum()
    total   = target.numel()
    return (correct / total).item()
