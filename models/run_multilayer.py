import sys
import os
import cv2
import numpy as np
from PIL import Image
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

# ---------------------------------------------------------------------------
# Config — edit these as needed
# ---------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))

IMAGE_PATH = os.path.join(script_dir, "input.png")
DEPTH_PATH = os.path.join(script_dir, "output_depthpro.png")
OUTPUT_DIR = os.path.join(script_dir, "layers")

# Parallax layer strategy:
# - Always extract the closest object cluster as foreground (layer 1)
# - Always extract the farthest region as deep background (layer N)
# - Auto-split the middle range into 1+ layers based on histogram peaks
MIN_LAYERS = 6  # Minimum total layers (foreground + middle + background)

# Minimum % of pixels a layer must contain to be kept
MIN_LAYER_COVERAGE = 0.03  # 3%

# Foreground detection: top X% brightest pixels form the foreground cluster
FOREGROUND_PERCENTILE = 95  # Top 5% brightest = foreground

# Smoothing for histogram analysis
HISTOGRAM_SIGMA = 3.0

# Morphological cleanup kernel size
KERNEL_SIZE = 7


# ---------------------------------------------------------------------------
# Depth channel extraction (same as run_separation.py)
# ---------------------------------------------------------------------------
def extract_depth_channel(depth_inferno: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(depth_inferno, cv2.COLOR_BGR2HSV)
    channel = hsv[:, :, 2]
    min_val, max_val = channel.min(), channel.max()
    if min_val == max_val:
        return channel
    return ((channel.astype(np.float32) - min_val) / (max_val - min_val) * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Parallax-aware layer segmentation using adaptive clustering
# ---------------------------------------------------------------------------
def analyze_depth_for_parallax(depth_channel: np.ndarray, sigma=3.0, min_coverage=0.03, min_layers=3):
    """
    Analyze the depth map and return layer boundaries optimized for parallax.
    Uses histogram peak detection to find natural object clusters.
    
    Returns list of (lo, hi, label) tuples ordered front-to-back.
    """
    total_pixels = depth_channel.size
    hist, bin_edges = np.histogram(depth_channel.flatten(), bins=256, range=(0, 255))
    hist_smooth = gaussian_filter1d(hist.astype(float), sigma=sigma)
    
    # Find all significant peaks (object clusters) in the histogram
    peaks, properties = find_peaks(
        hist_smooth,
        prominence=hist_smooth.max() * 0.05,  # Must be at least 5% of max peak
        distance=15,  # Peaks must be at least 15 bins apart
        width=3,  # Must have some width (not just noise)
    )
    
    if len(peaks) == 0:
        # No clear peaks — fall back to percentile-based split
        print("  [WARN] No clear depth clusters found, using percentile split")
        p33 = int(np.percentile(depth_channel, 33))
        p67 = int(np.percentile(depth_channel, 67))
        layers = [
            (p67, 255, "foreground"),
            (p33, p67 - 1, "midground_1"),
            (0, p33 - 1, "background"),
        ]
        return layers, hist_smooth, p67, p33
    
    # Sort peaks by depth (brightest to darkest = closest to farthest)
    peaks = sorted(peaks, reverse=True)
    
    print(f"  Found {len(peaks)} depth clusters at: {peaks}")
    
    # Find valleys (boundaries) between peaks
    valleys = []
    for i in range(len(peaks) - 1):
        # Search for minimum between consecutive peaks
        left = peaks[i + 1]
        right = peaks[i]
        segment = hist_smooth[left:right]
        if len(segment) > 0:
            valley_idx = left + np.argmin(segment)
            valleys.append(valley_idx)
    
    # Build layer boundaries from valleys
    # valleys split the depth range into regions around each peak
    boundaries = [0] + sorted(valleys) + [255]
    
    # Create layers from boundaries
    raw_layers = []
    for i in range(len(boundaries) - 1):
        lo = boundaries[i]
        hi = boundaries[i + 1]
        
        # Check if this layer has enough pixels
        mask = (depth_channel >= lo) & (depth_channel <= hi)
        coverage = mask.sum() / total_pixels
        
        if coverage >= min_coverage:
            raw_layers.append((lo, hi))
    
    # Ensure we have at least min_layers
    while len(raw_layers) < min_layers:
        # Split the largest layer
        largest_idx = max(range(len(raw_layers)), key=lambda i: (
            (depth_channel >= raw_layers[i][0]) & (depth_channel <= raw_layers[i][1])
        ).sum())
        lo, hi = raw_layers[largest_idx]
        mid = (lo + hi) // 2
        raw_layers[largest_idx] = (mid + 1, hi)
        raw_layers.insert(largest_idx + 1, (lo, mid))
    
    # Sort front to back (high depth to low depth)
    raw_layers = sorted(raw_layers, key=lambda x: x[0], reverse=True)
    
    # Label layers
    labeled = []
    for i, (lo, hi) in enumerate(raw_layers):
        if i == 0:
            label = "foreground"
        elif i == len(raw_layers) - 1:
            label = "background"
        else:
            label = f"midground_{i}"
        labeled.append((lo, hi, label))
    
    # Return boundaries for visualization
    fg_boundary = raw_layers[0][0] if raw_layers else 200
    bg_boundary = raw_layers[-1][1] if raw_layers else 50
    
    return labeled, hist_smooth, fg_boundary, bg_boundary


# ---------------------------------------------------------------------------
# Extract a single layer as RGBA
# ---------------------------------------------------------------------------
def extract_layer(image_bgr: np.ndarray, depth_channel: np.ndarray, lo: int, hi: int) -> Image.Image:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    mask = np.zeros(depth_channel.shape, dtype=np.uint8)
    mask[(depth_channel >= lo) & (depth_channel <= hi)] = 255

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (KERNEL_SIZE, KERNEL_SIZE))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    pil_rgba = Image.fromarray(image_rgb).convert("RGBA")
    r, g, b, _ = pil_rgba.split()
    alpha = Image.fromarray(mask, mode="L")
    return Image.merge("RGBA", (r, g, b, alpha))


# ---------------------------------------------------------------------------
# Save histogram visualization
# ---------------------------------------------------------------------------
def save_histogram(hist_smooth: np.ndarray, layers: list, fg_boundary: int, bg_boundary: int, output_path: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(hist_smooth, color="#444", linewidth=1.5, label="Depth histogram (smoothed)")

    # Color layers front-to-back: warm → cool
    layer_colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6", "#1abc9c"]
    for i, (lo, hi, label) in enumerate(layers):
        color = layer_colors[i % len(layer_colors)]
        ax.axvspan(lo, hi, alpha=0.3, color=color, label=f"Layer {i+1}: {label} ({lo}–{hi})")

    ax.axvline(fg_boundary, color="red", linestyle="--", linewidth=1, alpha=0.7, label=f"FG boundary ({fg_boundary})")
    ax.axvline(bg_boundary, color="blue", linestyle="--", linewidth=1, alpha=0.7, label=f"BG boundary ({bg_boundary})")

    ax.set_xlabel("Depth value  (255 = closest,  0 = farthest)")
    ax.set_ylabel("Pixel count")
    ax.set_title("Depth histogram — parallax layer segmentation")
    ax.legend(loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Saved histogram → {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load inputs
    image_bgr = cv2.imread(IMAGE_PATH)
    if image_bgr is None:
        print(f"Error: Could not read image at {IMAGE_PATH}")
        sys.exit(1)

    depth_bgr = cv2.imread(DEPTH_PATH)
    if depth_bgr is None:
        print(f"Error: Could not read depth map at {DEPTH_PATH}")
        sys.exit(1)

    # Resize depth to match image if needed
    h, w = image_bgr.shape[:2]
    if depth_bgr.shape[:2] != (h, w):
        depth_bgr = cv2.resize(depth_bgr, (w, h))

    # Extract normalized depth channel
    depth_channel = extract_depth_channel(depth_bgr)

    # Analyze depth map for parallax layers
    print("\n[INFO] Analyzing depth map for parallax layer segmentation...")
    layers, hist_smooth, fg_boundary, bg_boundary = analyze_depth_for_parallax(
        depth_channel,
        sigma=HISTOGRAM_SIGMA,
        min_coverage=MIN_LAYER_COVERAGE,
        min_layers=MIN_LAYERS,
    )

    print(f"\n[INFO] Detected {len(layers)} parallax layers (front → back):")
    print(f"  {'#':<4} {'Label':<18} {'Depth range':<16} {'Coverage':>8}  {'Role'}")
    print(f"  {'-'*60}")
    for i, (lo, hi, label) in enumerate(layers):
        mask = (depth_channel >= lo) & (depth_channel <= hi)
        coverage = mask.sum() / depth_channel.size * 100
        role = "← closest to camera" if i == 0 else ("← farthest from camera" if i == len(layers) - 1 else "")
        print(f"  {i+1:<4} {label:<18} {lo:>3}–{hi:<3}           {coverage:>6.1f}%  {role}")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save histogram visualization
    print(f"\n[INFO] Saving histogram → {OUTPUT_DIR}/depth_histogram.png")
    save_histogram(hist_smooth, layers, fg_boundary, bg_boundary,
                   os.path.join(OUTPUT_DIR, "depth_histogram.png"))

    # Extract and save each layer as RGBA PNG
    print(f"\n[INFO] Extracting layers → {OUTPUT_DIR}/")
    for i, (lo, hi, label) in enumerate(layers):
        layer_img = extract_layer(image_bgr, depth_channel, lo, hi)
        
        # Debug: count non-transparent pixels
        layer_np = np.array(layer_img)
        alpha = layer_np[:, :, 3]
        visible_pixels = (alpha > 0).sum()
        coverage_pct = visible_pixels / alpha.size * 100
        
        out_name = f"layer_{i+1:02d}_{label}.png"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        layer_img.save(out_path)
        print(f"  [{i+1}/{len(layers)}] {label:<18} → {out_name}  ({coverage_pct:.1f}% visible)")

    print(f"\n[DONE] {len(layers)} layers saved to {OUTPUT_DIR}/")
    print("  Stack them in your parallax viewer from layer_01 (front) to the last (back).")


if __name__ == "__main__":
    main()
