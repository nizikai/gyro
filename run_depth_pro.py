import sys
import os

# ---------------------------------------------------------------------------
# 4.3  Add ml-depth-pro/src to sys.path, import create_model_and_transforms
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "assets", "ml-depth-pro", "src"))
from depth_pro import create_model_and_transforms

import numpy as np
import cv2
import torch
from PIL import Image, UnidentifiedImageError

# ---------------------------------------------------------------------------
# 4.1  Load input image with error handling (PIL-based)
# ---------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "input.png")

try:
    image = Image.open(input_path).convert("RGB")
except FileNotFoundError:
    print(f"Error: Could not find input.png at {input_path}. Ensure the file exists.")
    sys.exit(1)
except UnidentifiedImageError:
    print(f"Error: Could not decode input.png at {input_path}. Ensure the file is a valid image.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 4.2  Device selection
# ---------------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------------------------------------------------------------------
# 4.4  Load model and transform, load checkpoint weights
# ---------------------------------------------------------------------------
model, transform = create_model_and_transforms(device=device)

checkpoint_path = os.path.join(
    os.path.dirname(__file__), "checkpoints", "depth_pro.pt"
)
state_dict = torch.load(checkpoint_path, map_location=device)
model.load_state_dict(state_dict)
model.eval()

# ---------------------------------------------------------------------------
# 4.5  Apply DepthPro transform, run inference, extract prediction["depth"]
# ---------------------------------------------------------------------------
image_tensor = transform(image).to(device)
with torch.no_grad():
    prediction = model.infer(image_tensor)
depth_tensor = prediction["depth"]

# ---------------------------------------------------------------------------
# 4.6  Convert to 2D float numpy array, normalize (inlined), apply
#      COLORMAP_INFERNO, save as output_depthpro.png with error handling
# ---------------------------------------------------------------------------
depth = depth_tensor.squeeze().cpu().numpy()

depth_min = depth.min()
depth_max = depth.max()
if depth_max == depth_min:
    depth_normalized = np.zeros_like(depth, dtype=np.uint8)
else:
    depth_normalized = ((depth - depth_min) / (depth_max - depth_min) * 255).astype(np.uint8)

colorized = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_INFERNO)

output_path = os.path.join(script_dir, "output_depthpro.png")
success = cv2.imwrite(output_path, colorized)
if not success:
    print(f"Error: Failed to write {output_path}. Check that the directory is writable.")
    sys.exit(1)

print(f"Saved {output_path}")
