import sys
import os
import cv2
import numpy as np
import torch
import torch.nn.functional as F

# ---------------------------------------------------------------------------
# Load input image with error handling
# ---------------------------------------------------------------------------
img = cv2.imread("input.jpeg")
if img is None:
    print("Error: Could not read input.jpeg. Ensure the file exists and is a valid image.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] Using device: {device}")

# ---------------------------------------------------------------------------
# Load MiDaS model from local checkpoint (offline)
# ---------------------------------------------------------------------------
model_path = os.path.join(os.path.dirname(__file__), "checkpoints", "midas_small.pth")
if not os.path.exists(model_path):
    raise FileNotFoundError(
        f"MiDaS model checkpoint not found: {model_path}\n"
        "Run: python3 -c \"import torch; torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')\""
    )

print(f"[INFO] Loading MiDaS_small from {model_path}")
model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

# Load MiDaS transforms
print("[INFO] Loading MiDaS transforms...")
midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.small_transform  # must match MiDaS_small

# ---------------------------------------------------------------------------
# Preprocess, run inference, interpolate back to original size
# ---------------------------------------------------------------------------
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

input_batch = transform(img_rgb).to(device)

print("[INFO] Running inference...")
with torch.no_grad():
    prediction = model(input_batch)

# Interpolate output to original image dimensions (H, W)
original_h, original_w = img.shape[:2]
prediction = F.interpolate(
    prediction.unsqueeze(1),
    size=(original_h, original_w),
    mode="bicubic",
    align_corners=False,
).squeeze()

# ---------------------------------------------------------------------------
# Normalize, apply COLORMAP_INFERNO
# ---------------------------------------------------------------------------
depth = prediction.cpu().numpy()

depth_min = depth.min()
depth_max = depth.max()
if depth_max == depth_min:
    depth_normalized = np.zeros_like(depth, dtype=np.uint8)
else:
    depth_normalized = ((depth - depth_min) / (depth_max - depth_min) * 255).astype(np.uint8)

colorized = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_INFERNO)

# ---------------------------------------------------------------------------
# Save output with error handling
# ---------------------------------------------------------------------------
success = cv2.imwrite("output_midas_small.png", colorized)
if not success:
    print("Error: Failed to write output_midas_small.png. Check that the current directory is writable.")
    sys.exit(1)

print("Saved output_midas_small.png")
