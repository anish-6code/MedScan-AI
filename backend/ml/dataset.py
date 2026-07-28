"""
ml/dataset.py

Dataset loader for LUNA16-compatible numpy arrays.
Expects a directory of paired files:
  images/{scan_id}.npy   — preprocessed float32 (512, 512)
  masks/{scan_id}.npy    — binary float32 annotation (512, 512)
"""
import os
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


class DicomSegDataset(Dataset):
    """
    Loads preprocessed DICOM numpy arrays and their corresponding masks.

    Args:
        data_dir:   root dir containing images/ and masks/ subdirs
        split:      "train" | "val" | "test"
        val_split:  fraction of data used for validation
        augment:    apply random horizontal/vertical flips
        seed:       random seed for reproducible splits
    """
    def __init__(
        self,
        data_dir: str,
        split: str = "train",
        val_split: float = 0.1,
        augment: bool = False,
        seed: int = 42,
    ):
        self.images_dir = Path(data_dir) / "images"
        self.masks_dir  = Path(data_dir) / "masks"
        self.augment    = augment

        all_ids = sorted([
            f.stem for f in self.images_dir.glob("*.npy")
            if (self.masks_dir / f.name).exists()
        ])

        rng = np.random.default_rng(seed)
        rng.shuffle(all_ids)

        n_val = max(1, int(len(all_ids) * val_split))
        if split == "train":
            self.ids = all_ids[n_val:]
        elif split == "val":
            self.ids = all_ids[:n_val]
        else:  # test — use all
            self.ids = all_ids

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        sid = self.ids[idx]
        image = np.load(self.images_dir / f"{sid}.npy").astype(np.float32)
        mask  = np.load(self.masks_dir  / f"{sid}.npy").astype(np.float32)

        # Ensure binary mask
        mask = (mask > 0.5).astype(np.float32)

        # Random augmentation (train only)
        if self.augment:
            if np.random.rand() > 0.5:
                image = np.fliplr(image).copy()
                mask  = np.fliplr(mask).copy()
            if np.random.rand() > 0.5:
                image = np.flipud(image).copy()
                mask  = np.flipud(mask).copy()

        # Add channel dim: (H, W) → (1, H, W)
        image = torch.from_numpy(image).unsqueeze(0)
        mask  = torch.from_numpy(mask).unsqueeze(0)
        return image, mask
