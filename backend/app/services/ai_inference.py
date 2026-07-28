"""
app/services/ai_inference.py

AI inference service — loads U-Net weights and runs segmentation on a
preprocessed 512x512 float32 NumPy array.

Singleton pattern: model is loaded once and reused across Celery tasks.
"""
import functools
import os
from typing import Any

import cv2
import numpy as np
import torch

from app.config import settings
from ml.model import UNet

# ── Paths ──────────────────────────────────────────────────────────────────────
WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "ml_weights", "best_model.pth"
)
MASK_DIR    = os.path.join(settings.PREPROCESSED_DIR, "masks")
OVERLAY_DIR = os.path.join(settings.PREPROCESSED_DIR, "overlays")

# ── Threshold for binary mask ──────────────────────────────────────────────────
MASK_THRESHOLD = 0.45


# ── Model loader (singleton) ───────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _get_model() -> tuple[UNet, torch.device]:
    """Load U-Net weights once; cache for lifetime of the worker process."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = UNet(in_channels=1, out_channels=1).to(device)

    weights_path = os.path.abspath(WEIGHTS_PATH)
    if os.path.exists(weights_path):
        ckpt = torch.load(weights_path, map_location=device)
        model.load_state_dict(ckpt["model_state"])
    else:
        # No weights file — use random init (demo mode)
        import warnings
        warnings.warn(
            f"No weights found at {weights_path}. "
            "Using random init (demo mode). "
            "Run: python ml/export_weights.py",
            stacklevel=2,
        )

    model.eval()
    return model, device


# ── Inference ─────────────────────────────────────────────────────────────────

def run_inference(array: np.ndarray) -> dict[str, Any]:
    """
    Run U-Net segmentation on a preprocessed (512, 512) float32 array.

    Returns:
        mask:          np.ndarray (512, 512) binary float32
        bboxes:        list of {x, y, w, h, confidence, area_px}
        confidence:    float — max per-region confidence score
        findings_json: structured dict ready for DB storage
    """
    model, device = _get_model()

    # Prepare input tensor: (1, 1, 512, 512)
    tensor = torch.from_numpy(array).unsqueeze(0).unsqueeze(0).to(device)

    with torch.no_grad():
        raw: torch.Tensor = model(tensor)   # (1, 1, 512, 512)

    prob_map = raw.squeeze().cpu().numpy()           # (512, 512) probabilities
    binary   = (prob_map > MASK_THRESHOLD).astype(np.uint8)

    # ── Extract bounding boxes from contours ───────────────────────────────────
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bboxes: list[dict] = []
    for cnt in contours:
        area = float(cv2.contourArea(cnt))
        if area < 50:           # skip tiny noise artifacts
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        # Confidence = mean probability inside the bounding box
        roi_prob = prob_map[y : y + h, x : x + w]
        conf     = float(roi_prob.mean())
        bboxes.append({"x": x, "y": y, "w": w, "h": h,
                       "confidence": round(conf, 4),
                       "area_px": int(area)})

    # Sort by confidence desc
    bboxes.sort(key=lambda b: b["confidence"], reverse=True)
    max_conf = bboxes[0]["confidence"] if bboxes else 0.0

    findings = {
        "num_regions":   len(bboxes),
        "bboxes":        bboxes,
        "max_confidence": max_conf,
        "summary":       _summarise(len(bboxes), max_conf),
    }

    return {
        "mask":          binary.astype(np.float32),
        "prob_map":      prob_map,
        "bboxes":        bboxes,
        "confidence":    max_conf,
        "findings_json": findings,
    }


def _summarise(n_regions: int, confidence: float) -> str:
    if n_regions == 0:
        return "No significant findings detected."
    severity = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"
    return (
        f"{n_regions} region(s) of interest detected "
        f"(max confidence {confidence:.0%}, severity: {severity})."
    )


# ── Overlay generation ────────────────────────────────────────────────────────

def save_overlay(array: np.ndarray, mask: np.ndarray, scan_id: str) -> str:
    """
    Blend the original grayscale scan with a red segmentation mask.
    Saves as PNG and returns the file path.
    """
    os.makedirs(OVERLAY_DIR, exist_ok=True)

    # Convert grayscale [0,1] → BGR uint8
    gray_uint8 = (array * 255).astype(np.uint8)
    bgr        = cv2.cvtColor(gray_uint8, cv2.COLOR_GRAY2BGR)

    # Red overlay where mask=1
    overlay        = bgr.copy()
    mask_bool      = mask.astype(bool)
    overlay[mask_bool] = [0, 0, 220]    # bright red in BGR

    # Semi-transparent blend
    blended = cv2.addWeighted(bgr, 0.65, overlay, 0.35, 0)

    out_path = os.path.join(OVERLAY_DIR, f"{scan_id}.png")
    cv2.imwrite(out_path, blended)
    return out_path


def save_mask(mask: np.ndarray, scan_id: str) -> str:
    """Save binary mask as .npy and return path."""
    os.makedirs(MASK_DIR, exist_ok=True)
    out_path = os.path.join(MASK_DIR, f"{scan_id}.npy")
    np.save(out_path, mask)
    return out_path
