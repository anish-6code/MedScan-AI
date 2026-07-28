"""
app/services/dicom_processor.py

Full DICOM preprocessing pipeline:
  1. Load DICOM via pydicom (from local path or S3 key)
  2. Apply CT windowing/leveling (Hounsfield units) or min-max for other modalities
  3. Denoise with OpenCV (Gaussian for CT, median for MR/other)
  4. Resize + zero-pad to a fixed 512×512 output
  5. Return a float32 NumPy array in [0, 1] + metadata dict
"""
import io
import os
from typing import Any

import cv2
import numpy as np
import pydicom
from pydicom.dataset import Dataset

from app.config import settings


# ── Target output shape ────────────────────────────────────────────────────────
TARGET_SIZE = (512, 512)


# ── Step 1: Load ───────────────────────────────────────────────────────────────

def _load_bytes(file_path: str) -> bytes:
    """Read raw file bytes — local disk or S3 depending on STORAGE_BACKEND."""
    if settings.STORAGE_BACKEND == "s3":
        import boto3
        client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        obj = client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=file_path)
        return obj["Body"].read()
    else:
        with open(file_path, "rb") as f:
            return f.read()


def load_dicom(file_path: str) -> Dataset:
    """Load a DICOM Dataset from a file path (local or S3 key)."""
    raw = _load_bytes(file_path)
    ds = pydicom.dcmread(io.BytesIO(raw), force=True)
    return ds


def extract_metadata(ds: Dataset) -> dict[str, Any]:
    """Pull relevant DICOM metadata tags into a plain dict."""
    def safe(tag, default=None):
        try:
            return getattr(ds, tag)
        except AttributeError:
            return default

    return {
        "modality":          safe("Modality", "UNKNOWN"),
        "window_center":     safe("WindowCenter"),
        "window_width":      safe("WindowWidth"),
        "rescale_intercept": float(safe("RescaleIntercept", 0)),
        "rescale_slope":     float(safe("RescaleSlope", 1)),
        "slice_thickness":   safe("SliceThickness"),
        "patient_position":  safe("PatientPosition"),
        "rows":              safe("Rows"),
        "columns":           safe("Columns"),
    }


# ── Step 2: Windowing / normalization ──────────────────────────────────────────

def apply_windowing(pixel_array: np.ndarray, meta: dict[str, Any]) -> np.ndarray:
    """
    For CT: convert raw values to Hounsfield Units, then apply window/level.
    For other modalities: simple min-max normalization to [0, 1].
    Always returns float32 in [0, 1].
    """
    arr = pixel_array.astype(np.float32)

    if meta["modality"] == "CT":
        # 1. Rescale to HU
        arr = arr * meta["rescale_slope"] + meta["rescale_intercept"]

        # 2. Get window center/width (may be a list for multi-window DICOMs)
        wc = meta["window_center"]
        ww = meta["window_width"]
        if isinstance(wc, pydicom.multival.MultiValue):
            wc = float(wc[0])
        if isinstance(ww, pydicom.multival.MultiValue):
            ww = float(ww[0])

        # Fallback to common soft-tissue window if tags are missing
        if wc is None or ww is None:
            wc, ww = 40.0, 400.0

        lower = wc - ww / 2.0
        upper = wc + ww / 2.0
        arr = np.clip(arr, lower, upper)
        arr = (arr - lower) / (upper - lower)   # → [0, 1]
    else:
        mn, mx = arr.min(), arr.max()
        if mx > mn:
            arr = (arr - mn) / (mx - mn)
        else:
            arr = np.zeros_like(arr, dtype=np.float32)

    return arr.astype(np.float32)


# ── Step 3: Denoising ─────────────────────────────────────────────────────────

def denoise(arr: np.ndarray, modality: str) -> np.ndarray:
    """
    OpenCV denoising — convert to uint8 for processing, back to float32.
    CT: Gaussian blur (3×3, σ=0) — smooths Gaussian noise from detector.
    MR/other: median blur (3×3) — better for salt-and-pepper artifacts.
    """
    uint8 = (arr * 255).astype(np.uint8)
    if modality == "CT":
        filtered = cv2.GaussianBlur(uint8, (3, 3), 0)
    else:
        filtered = cv2.medianBlur(uint8, 3)
    return (filtered / 255.0).astype(np.float32)


# ── Step 4: Resize + pad ──────────────────────────────────────────────────────

def resize_and_pad(arr: np.ndarray, target: tuple[int, int] = TARGET_SIZE) -> np.ndarray:
    """
    Resize image to fit inside target while preserving aspect ratio,
    then zero-pad to exactly target shape.
    """
    th, tw = target
    h, w = arr.shape[:2]
    scale = min(tw / w, th / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(arr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((th, tw), dtype=np.float32)
    y_off = (th - new_h) // 2
    x_off = (tw - new_w) // 2
    canvas[y_off : y_off + new_h, x_off : x_off + new_w] = resized
    return canvas


# ── Full pipeline ─────────────────────────────────────────────────────────────

def preprocess(file_path: str, scan_id: str) -> dict[str, Any]:
    """
    Full end-to-end DICOM preprocessing pipeline.

    Args:
        file_path: local path or S3 key (from scans.file_path)
        scan_id:   UUID string — used for output filename

    Returns:
        {
            "scan_id":       str,
            "array":         np.ndarray  shape (512, 512) float32 [0,1],
            "output_path":   str,        where .npy was saved
            "modality":      str,
            "shape":         tuple,
            "window_center": float | None,
            "window_width":  float | None,
        }
    """
    # Load
    ds = load_dicom(file_path)
    meta = extract_metadata(ds)
    pixel_array = ds.pixel_array

    # Handle multi-frame (take middle slice)
    if pixel_array.ndim == 3:
        mid = pixel_array.shape[0] // 2
        pixel_array = pixel_array[mid]

    # Process
    arr = apply_windowing(pixel_array, meta)
    arr = denoise(arr, meta["modality"])
    arr = resize_and_pad(arr)

    # Save as .npy for fast loading by the AI inference step
    os.makedirs(settings.PREPROCESSED_DIR, exist_ok=True)
    output_path = os.path.join(settings.PREPROCESSED_DIR, f"{scan_id}.npy")
    np.save(output_path, arr)

    return {
        "scan_id":       scan_id,
        "array":         arr,
        "output_path":   output_path,
        "modality":      meta["modality"],
        "shape":         arr.shape,
        "window_center": meta["window_center"],
        "window_width":  meta["window_width"],
    }
