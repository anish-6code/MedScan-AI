"""
ml/train.py

Standalone training script for the U-Net segmentation model.
Run on a GPU machine:
    python ml/train.py --data /path/to/dataset --epochs 50 --batch-size 8

Requirements (install separately on GPU machine):
    pip install torch torchvision tqdm
"""
import argparse
import os

import torch
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from ml.model import BCEDiceLoss, UNet
from ml.dataset import DicomSegDataset
from ml.evaluate import dice_score, iou_score


def train(args: argparse.Namespace) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device}")

    # Datasets
    train_ds = DicomSegDataset(args.data, split="train", augment=True)
    val_ds   = DicomSegDataset(args.data, split="val",   augment=False)
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                          num_workers=4, pin_memory=True)
    val_dl   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False,
                          num_workers=2, pin_memory=True)

    # Model
    model     = UNet(in_channels=1, out_channels=1).to(device)
    criterion = BCEDiceLoss(bce_weight=0.5)
    optimizer = Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode="max", patience=5, factor=0.5)

    # AMP for faster training on CUDA
    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")

    best_dice = 0.0
    os.makedirs(args.output, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        # ── Train ─────────────────────────────────────────────────────────────
        model.train()
        train_loss = 0.0
        for images, masks in train_dl:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
                preds = model(images)
                loss  = criterion(preds, masks)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            train_loss += loss.item()

        # ── Validate ───────────────────────────────────────────────────────────
        model.eval()
        val_dice, val_iou = 0.0, 0.0
        with torch.no_grad():
            for images, masks in val_dl:
                images, masks = images.to(device), masks.to(device)
                with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
                    preds = model(images)
                val_dice += dice_score(preds, masks)
                val_iou  += iou_score(preds, masks)

        val_dice /= len(val_dl)
        val_iou  /= len(val_dl)
        scheduler.step(val_dice)

        print(
            f"Epoch {epoch:03d}/{args.epochs} | "
            f"loss={train_loss/len(train_dl):.4f} | "
            f"dice={val_dice:.4f} | iou={val_iou:.4f}"
        )

        # Save best checkpoint
        if val_dice > best_dice:
            best_dice = val_dice
            ckpt_path = os.path.join(args.output, "best_model.pth")
            torch.save({
                "epoch":      epoch,
                "model_state": model.state_dict(),
                "optimizer":  optimizer.state_dict(),
                "val_dice":   val_dice,
            }, ckpt_path)
            print(f"  ✓ Saved checkpoint → {ckpt_path}  (dice={val_dice:.4f})")

    print(f"\nTraining complete. Best Dice: {best_dice:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train U-Net on DICOM segmentation data")
    parser.add_argument("--data",       required=True,       help="Dataset root dir (images/ + masks/ subdirs)")
    parser.add_argument("--output",     default="app/ml_weights", help="Where to save best_model.pth")
    parser.add_argument("--epochs",     type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr",         type=float, default=1e-4)
    args = parser.parse_args()
    train(args)
