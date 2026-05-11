import sys
import os
import argparse
import cv2
import numpy as np
import torch
from PIL import Image

# Add LaMa source to path
_LAMA_SRC = os.path.join(os.path.dirname(__file__), "assets", "lama")
if _LAMA_SRC not in sys.path:
    sys.path.insert(0, _LAMA_SRC)

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Depth-based foreground/background separation pipeline."
    )

    # Required inputs (now with defaults pointing to script directory)
    parser.add_argument(
        "--image",
        type=str,
        default=os.path.join(script_dir, "input.png"),
        help="Path to original RGB image (JPEG/PNG).",
    )
    parser.add_argument(
        "--depth",
        type=str,
        default=os.path.join(script_dir, "output_depthpro.png"),
        help="Path to depth map image (INFERNO colormap output of run_depth_pro.py).",
    )

    # Output paths
    parser.add_argument(
        "--foreground-out",
        type=str,
        default=os.path.join(script_dir, "foreground.png"),
        help="Output path for foreground PNG.",
    )
    parser.add_argument(
        "--background-out",
        type=str,
        default=os.path.join(script_dir, "background.png"),
        help="Output path for background PNG.",
    )
    parser.add_argument(
        "--mask-out",
        type=str,
        default=os.path.join(script_dir, "mask.png"),
        help="Path to save the binary mask for inspection.",
    )

    # Processing parameters
    parser.add_argument(
        "--threshold",
        type=int,
        default=200,
        help="Depth threshold 0–255; pixels above threshold = foreground (default: 200).",
    )
    parser.add_argument(
        "--kernel-size",
        type=int,
        default=7,
        help="Morphological kernel size; must be odd and ≥ 1 (default: 7).",
    )
    parser.add_argument(
        "--dilation",
        type=int,
        default=0,
        help="Extra dilation iterations on the inpainting mask (default: 0).",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to use for inference: 'cuda' or 'cpu' (default: auto-detected).",
    )
    parser.add_argument(
        "--invert-mask",
        action="store_true",
        help="Invert the binary mask before extraction.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Image loading
# ---------------------------------------------------------------------------

def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        print(f"Error: Could not read image file '{path}'. Check that the file exists and is a valid image.")
        sys.exit(1)
    return img


def load_depth_map(path: str, target_size: tuple) -> np.ndarray:
    depth = cv2.imread(path)
    if depth is None:
        print(f"Error: Could not read depth map file '{path}'. Check that the file exists and is a valid image.")
        sys.exit(1)
    # target_size is (width, height); cv2.imread gives shape (H, W, C)
    w, h = target_size
    if depth.shape[1] != w or depth.shape[0] != h:
        depth = cv2.resize(depth, target_size)
    return depth


# ---------------------------------------------------------------------------
# Depth channel extraction and normalization
# ---------------------------------------------------------------------------

def extract_depth_channel(depth_inferno: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(depth_inferno, cv2.COLOR_BGR2HSV)
    return hsv[:, :, 2]


def normalize_depth(channel: np.ndarray) -> np.ndarray:
    min_val = channel.min()
    max_val = channel.max()
    if min_val == max_val:
        raise ValueError("Depth map has no variation; cannot normalize uniform depth channel.")
    return ((channel.astype(np.float32) - min_val) / (max_val - min_val) * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Mask generation
# ---------------------------------------------------------------------------

def generate_mask(depth_channel: np.ndarray, threshold: int, kernel_size: int) -> np.ndarray:
    # Threshold: pixels above threshold → 255 (foreground), others → 0
    _, mask = cv2.threshold(depth_channel, threshold, 255, cv2.THRESH_BINARY)

    # Build elliptical structuring element for morphological ops
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )

    # Close first (fill small holes), then open (remove small noise blobs)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    return mask


def validate_mask(mask: np.ndarray) -> str:
    """Return 'empty' if no foreground pixels, 'full' if all pixels are foreground, else 'ok'."""
    if not np.any(mask == 255):
        return "empty"
    if np.all(mask == 255):
        return "full"
    return "ok"


# ---------------------------------------------------------------------------
# Foreground extraction
# ---------------------------------------------------------------------------

def extract_foreground(image_bgr: np.ndarray, mask: np.ndarray) -> Image.Image:
    # Convert BGR → RGB
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    # Create PIL RGBA image from RGB data
    pil_rgba = Image.fromarray(image_rgb).convert("RGBA")

    # Split into channels, replace alpha with mask, then merge back
    r, g, b, _ = pil_rgba.split()
    alpha = Image.fromarray(mask, mode="L")
    pil_rgba = Image.merge("RGBA", (r, g, b, alpha))

    return pil_rgba


# ---------------------------------------------------------------------------
# LaMa model loading
# ---------------------------------------------------------------------------

def load_lama_model(checkpoint_dir: str, device: str) -> torch.nn.Module:
    """Load the LaMa model from a big-lama checkpoint directory.

    Args:
        checkpoint_dir: Path to the big-lama directory containing config.yaml
                        and models/best.ckpt.
        device: Target device string ('cuda' or 'cpu').

    Returns:
        The loaded LaMa model ready for inference.
    """
    ckpt_path = os.path.join(checkpoint_dir, "models", "best.ckpt")
    config_path = os.path.join(checkpoint_dir, "config.yaml")

    if not os.path.isfile(ckpt_path):
        print(
            "Error: LaMa checkpoint not found at models/checkpoints/big-lama/. "
            "Download from https://huggingface.co/smartywu/big-lama/tree/main"
        )
        sys.exit(1)

    min_valid_size_bytes = 1024
    if os.path.getsize(ckpt_path) < min_valid_size_bytes:
        print(
            "Error: LaMa checkpoint not found at models/checkpoints/big-lama/. "
            "Download from https://huggingface.co/smartywu/big-lama/tree/main"
        )
        sys.exit(1)

    try:
        from omegaconf import OmegaConf
        from saicinpainting.training.trainers import load_checkpoint

        train_config = OmegaConf.load(config_path)
        train_config.training_model.predict_only = True
        train_config.visualizer.kind = "noop"

        model = load_checkpoint(train_config, ckpt_path, strict=False, map_location=device)
        model.eval()
        model.to(device)
        return model
    except Exception as e:
        print(f"Error: LaMa model failed to load — {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Background inpainting
# ---------------------------------------------------------------------------

def inpaint_background(image_bgr: np.ndarray, mask: np.ndarray, model: torch.nn.Module, device: str) -> np.ndarray:
    """Inpaint the background region using the local LaMa model."""
    try:
        # Convert BGR → RGB and normalize to [0, 1]
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image_float = image_rgb.astype(np.float32) / 255.0

        orig_h, orig_w = image_float.shape[:2]

        # Pad to nearest multiple of 32 (LaMa requirement)
        def pad_to_multiple(x, multiple=32):
            return (multiple - x % multiple) % multiple

        pad_h = pad_to_multiple(orig_h)
        pad_w = pad_to_multiple(orig_w)

        if pad_h > 0 or pad_w > 0:
            image_float = np.pad(image_float, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
            mask_float_pad = np.pad(mask.astype(np.float32) / 255.0, ((0, pad_h), (0, pad_w)), mode='reflect')
        else:
            mask_float_pad = mask.astype(np.float32) / 255.0

        # Prepare tensors
        image_tensor = torch.from_numpy(image_float).permute(2, 0, 1).unsqueeze(0).to(device)
        mask_tensor = torch.from_numpy(mask_float_pad).unsqueeze(0).unsqueeze(0).to(device)

        batch = {"image": image_tensor, "mask": mask_tensor}

        with torch.no_grad():
            batch = model(batch)

        output_tensor = batch["inpainted"]
        output_np = output_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
        output_np = np.clip(output_np, 0.0, 1.0)

        # Crop back to original size
        output_np = output_np[:orig_h, :orig_w]
        output_uint8 = (output_np * 255.0).astype(np.uint8)

        return output_uint8

    except Exception as e:
        print(f"Error: LaMa inpainting failed — {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # --- Parameter range validation ---
    if not (0 <= args.threshold <= 255):
        print("Error: --threshold must be in range [0, 255]")
        sys.exit(1)

    if args.kernel_size < 1 or args.kernel_size % 2 == 0:
        print("Error: --kernel-size must be ≥ 1 and odd")
        sys.exit(1)

    if args.dilation < 0:
        print("Error: --dilation must be ≥ 0")
        sys.exit(1)

    # --- Write permission checks (before any processing) ---
    output_paths = [args.foreground_out, args.background_out]
    if args.mask_out is not None:
        output_paths.append(args.mask_out)

    for out_path in output_paths:
        dir_path = os.path.dirname(os.path.abspath(out_path))
        if not os.access(dir_path, os.W_OK):
            print(f"Error: No write permission for {dir_path}.")
            sys.exit(1)

    print(f"[INFO] Using device: {args.device}")

    # --- Load inputs ---
    print("[INFO] Loading inputs...")
    image_bgr = load_image(args.image)
    h, w = image_bgr.shape[:2]
    depth_bgr = load_depth_map(args.depth, (w, h))

    # --- Extract and normalize depth channel ---
    print("[INFO] Extracting depth channel from INFERNO colormap...")
    depth_channel = extract_depth_channel(depth_bgr)
    try:
        depth_channel = normalize_depth(depth_channel)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # --- Generate foreground mask ---
    print(f"[INFO] Generating foreground mask (threshold={args.threshold}, kernel={args.kernel_size})...")
    mask = generate_mask(depth_channel, args.threshold, args.kernel_size)

    # --- Optional mask inversion ---
    if args.invert_mask:
        mask = cv2.bitwise_not(mask)

    # --- Optional mask dilation (superset: only adds pixels, never removes) ---
    if args.dilation > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (args.kernel_size, args.kernel_size)
        )
        mask = cv2.dilate(mask, kernel, iterations=args.dilation)

    # --- Validate mask ---
    mask_status = validate_mask(mask)
    if mask_status == "empty":
        print("[WARN] No foreground detected, skipping foreground extraction")
    if mask_status == "full":
        print("[WARN] No background detected, skipping inpainting")

    # --- Save mask if requested ---
    if args.mask_out is not None:
        try:
            success = cv2.imwrite(args.mask_out, mask)
            if not success:
                print(f"Error: Failed to write {args.mask_out}. Check write permissions.")
                sys.exit(1)
        except Exception:
            print(f"Error: Failed to write {args.mask_out}. Check write permissions.")
            sys.exit(1)

    # --- Extract foreground ---
    if mask_status != "empty":
        print("[INFO] Extracting foreground...")
        foreground = extract_foreground(image_bgr, mask)

    # --- Inpaint background ---
    if mask_status != "full":
        print("[INFO] Loading LaMa model from local checkpoint...")
        checkpoint_dir = os.path.join(os.path.dirname(__file__), "checkpoints", "big-lama")
        lama_model = load_lama_model(checkpoint_dir, args.device)
        print("[INFO] Running LaMa inpainting...")
        background = inpaint_background(image_bgr, mask, lama_model, args.device)

    # --- Save outputs ---
    print("[INFO] Saving outputs...")
    if mask_status != "empty":
        try:
            foreground.save(args.foreground_out)
        except Exception:
            print(f"Error: Failed to write {args.foreground_out}. Check write permissions.")
            sys.exit(1)

    if mask_status != "full":
        try:
            bg_image = Image.fromarray(background)
            bg_image.save(args.background_out)
        except Exception:
            print(f"Error: Failed to write {args.background_out}. Check write permissions.")
            sys.exit(1)

    saved = []
    if mask_status != "empty":
        saved.append(args.foreground_out)
    if mask_status != "full":
        saved.append(args.background_out)
    print(f"[INFO] Done. {', '.join(saved)}")


if __name__ == "__main__":
    main()
