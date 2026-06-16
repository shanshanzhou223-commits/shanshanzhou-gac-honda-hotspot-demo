"""
车型图片预处理脚本
把 images/ 下的原图统一裁剪+留白成 4:3 尺寸，让页面更整齐。
"""
import os
from PIL import Image, ImageFilter

SRC_DIR = os.path.join(os.path.dirname(__file__), "images")
OUT_DIR = os.path.join(SRC_DIR, "processed")
TARGET_SIZE = (600, 450)  # 4:3，展示卡片更整齐

os.makedirs(OUT_DIR, exist_ok=True)


def estimate_bg_color(im: Image.Image) -> tuple:
    """
    估算图片背景色：缩小后取平均色，再模糊一下，
    让填充边距和原图背景更融合。
    """
    small = im.copy()
    small.thumbnail((80, 80), Image.Resampling.LANCZOS)
    # 轻微模糊，避免被车身的鲜艳颜色主导
    small = small.filter(ImageFilter.GaussianBlur(radius=3))
    pixels = list(small.getdata())
    if not pixels:
        return (255, 255, 255)
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)
    # 提亮一点，避免太深
    def lighten(c):
        return min(255, int(c * 1.15 + 20))
    return (lighten(r), lighten(g), lighten(b))


for fname in sorted(os.listdir(SRC_DIR)):
    if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        continue
    src_path = os.path.join(SRC_DIR, fname)
    out_path = os.path.join(OUT_DIR, fname)

    with Image.open(src_path) as im:
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGBA")
            # 先估算背景（用缩略图），再预乘
            bg_color = estimate_bg_color(im)
            bg = Image.new("RGBA", im.size, bg_color + (255,))
            im = Image.alpha_composite(bg, im).convert("RGB")
        else:
            im = im.convert("RGB")
            bg_color = estimate_bg_color(im)

        # 等比缩放，让图片完全放进目标框内
        im.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)

        # 新建目标尺寸画布，居中粘贴
        canvas = Image.new("RGB", TARGET_SIZE, bg_color)
        x = (TARGET_SIZE[0] - im.width) // 2
        y = (TARGET_SIZE[1] - im.height) // 2
        canvas.paste(im, (x, y))

        canvas.save(out_path, quality=95)
        print(f"Processed {fname}: {canvas.size}, bg={bg_color}")

print("Done. Processed images are in images/processed/")
