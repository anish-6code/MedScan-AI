"""
ml/export_weights.py

Utility: initialise a fresh U-Net and save it as best_model.pth.
This creates a DEMO / DUMMY weight file so the inference pipeline
works end-to-end without a GPU training run.

For production: replace best_model.pth with real trained weights.

Usage:
    python ml/export_weights.py
    python ml/export_weights.py --output app/ml_weights/best_model.pth
"""
import argparse
import os

import torch

from ml.model import UNet


def export(output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    model = UNet(in_channels=1, out_channels=1)
    # Random init — produces plausible-looking (noisy) masks for demo purposes
    torch.save({
        "epoch":       0,
        "model_state": model.state_dict(),
        "val_dice":    0.0,
        "note":        "DEMO weights — replace with trained best_model.pth",
    }, output_path)
    print(f"Demo weights saved → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="app/ml_weights/best_model.pth")
    args = parser.parse_args()
    export(args.output)
