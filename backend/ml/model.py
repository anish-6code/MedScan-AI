"""
ml/model.py

U-Net for binary medical image segmentation.
Input:  (B, 1, 512, 512)  float32 normalised to [0, 1]
Output: (B, 1, 512, 512)  float32 probability mask via Sigmoid
"""
import torch
import torch.nn as nn


# ── Building blocks ────────────────────────────────────────────────────────────

class DoubleConv(nn.Module):
    """Two consecutive Conv2d → BatchNorm → ReLU blocks."""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class Down(nn.Module):
    """MaxPool → DoubleConv (encoder step)."""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.net = nn.Sequential(nn.MaxPool2d(2), DoubleConv(in_ch, out_ch))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class Up(nn.Module):
    """Bilinear upsample + DoubleConv (decoder step with skip connections)."""
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.up   = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        self.conv = DoubleConv(in_ch, out_ch)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        # Pad if spatial dims don't match (edge case for non-power-of-2 inputs)
        dh = skip.size(2) - x.size(2)
        dw = skip.size(3) - x.size(3)
        if dh > 0 or dw > 0:
            x = nn.functional.pad(x, [dw // 2, dw - dw // 2, dh // 2, dh - dh // 2])
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)


# ── U-Net ──────────────────────────────────────────────────────────────────────

class UNet(nn.Module):
    """
    5-level U-Net.
    Channels: 1 → 64 → 128 → 256 → 512 → 1024 (bottleneck) → back up.
    """
    def __init__(self, in_channels: int = 1, out_channels: int = 1):
        super().__init__()
        # Encoder
        self.inc   = DoubleConv(in_channels, 64)
        self.down1 = Down(64,  128)
        self.down2 = Down(128, 256)
        self.down3 = Down(256, 512)
        self.down4 = Down(512, 1024)

        # Decoder
        self.up1 = Up(1024 + 512, 512)
        self.up2 = Up(512  + 256, 256)
        self.up3 = Up(256  + 128, 128)
        self.up4 = Up(128  + 64,   64)

        # Output
        self.outc = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        # Decoder with skip connections
        x = self.up1(x5, x4)
        x = self.up2(x,  x3)
        x = self.up3(x,  x2)
        x = self.up4(x,  x1)

        return torch.sigmoid(self.outc(x))


# ── Loss ───────────────────────────────────────────────────────────────────────

class BCEDiceLoss(nn.Module):
    """Combined BCE + Dice loss — robust for class-imbalanced segmentation."""
    def __init__(self, bce_weight: float = 0.5):
        super().__init__()
        self.bce_weight = bce_weight
        self.bce = nn.BCELoss()

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        bce = self.bce(pred, target)
        smooth = 1e-6
        pred_flat   = pred.view(-1)
        target_flat = target.view(-1)
        intersection = (pred_flat * target_flat).sum()
        dice = 1 - (2 * intersection + smooth) / (pred_flat.sum() + target_flat.sum() + smooth)
        return self.bce_weight * bce + (1 - self.bce_weight) * dice
