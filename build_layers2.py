import numpy as np
import cv2
from PIL import Image

SRC = r"C:\Users\Doori\Documents\Vibe Code Apps\Bioglow logo\Picture3.png"
OUT = r"C:\Users\Doori\Documents\Vibe Code Apps\Bioglow logo"
SCRATCH = r"C:\Users\Doori\AppData\Local\Temp\claude\C--Users-Doori-Documents-Vibe-Code-Apps-Bioglow-logo\a808b6bc-5cb9-421f-9bf1-ba1636607a23\scratchpad"

im = Image.open(SRC).convert('RGBA')
arr = np.array(im)
H, W = arr.shape[:2]
rgb = arr[:, :, :3].astype(int)
alpha = arr[:, :, 3]
bg = np.array([193, 221, 139])
nonbg = ((np.abs(rgb - bg).sum(axis=2) > 20) & (alpha > 0)).astype(np.uint8)

leaf_mask_core_src = np.array(Image.open(SCRATCH + r"\leaf_mask2.png"))  # already dilated leaf mask (margin 16)

# ---- rebuild the 3 circuit blobs (outside leaf, text, border) ----
remainder = nonbg.copy()
remainder[leaf_mask_core_src > 0] = 0
remainder[1300:, :] = 0
remainder[:, :40] = 0
remainder[:, 1670:] = 0
remainder[:40, :] = 0
remainder[1670:, :] = 0

n, labels, stats, centroids = cv2.connectedComponentsWithStats(remainder, connectivity=8)
big = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 5000]
assert len(big) == 3, f"expected 3 circuit components, got {len(big)}"

MARGIN = 16
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MARGIN * 2 + 1, MARGIN * 2 + 1))


def disk(cx, cy, r):
    m = np.zeros((H, W), dtype=np.uint8)
    cv2.circle(m, (cx, cy), r, 255, -1)
    return m > 0


# classify the 3 components by centroid position
comp_info = []
for i in big:
    x, y, w, h, area = stats[i]
    comp_info.append((i, centroids[i], (x, y, w, h)))

def nearest(pt):
    return min(comp_info, key=lambda c: (c[1][0]-pt[0])**2 + (c[1][1]-pt[1])**2)

DOT3, DOT4 = (1298, 603), (1254, 967)
lbl_tendril1_dot3 = nearest(DOT3)[0]
lbl_root2_dot4 = nearest(DOT4)[0]
lbl_root1 = [c[0] for c in comp_info if c[0] not in (lbl_tendril1_dot3, lbl_root2_dot4)][0]

R_OUT = 79
dot3_disk = disk(*DOT3, R_OUT)
dot4_disk = disk(*DOT4, R_OUT)

blob_td3 = (labels == lbl_tendril1_dot3)
blob_rd4 = (labels == lbl_root2_dot4)
blob_r1 = (labels == lbl_root1)

tendril1_core = blob_td3 & ~dot3_disk
dot3_core = blob_td3 & dot3_disk
root2_core = blob_rd4 & ~dot4_disk
dot4_core = blob_rd4 & dot4_disk
root1_core = blob_r1

# ---- inner leaf dots ----
DOT1, DOT2 = (1042, 530), (1020, 783)
R_IN = 76
dot1_disk = disk(*DOT1, R_IN)
dot2_disk = disk(*DOT2, R_IN)
leaf_full_mask = leaf_mask_core_src > 0
dot1_core = leaf_full_mask & dot1_disk
dot2_core = leaf_full_mask & dot2_disk
leaf_base_core = leaf_full_mask & ~dot1_disk & ~dot2_disk

# ---- dilate each independent object's OUTER boundary for sprite padding ----
def dilate(mask_bool):
    return cv2.dilate(mask_bool.astype(np.uint8) * 255, kernel) > 0

tendril1_mask = dilate(tendril1_core)
root2_mask = dilate(root2_core)
root1_mask = dilate(root1_core)
# dots and leaf_base keep exact (no extra dilation) so internal seams stay tight;
# their outer edge already came from the leaf/blob dilation done earlier.
dot3_mask = dot3_core
dot4_mask = dot4_core
dot1_mask = dot1_core
dot2_mask = dot2_core
leaf_base_mask = leaf_base_core

LAYERS = {
    'layer_leaf_base': leaf_base_mask,
    'layer_dot1': dot1_mask,
    'layer_dot2': dot2_mask,
    'layer_tendril1': tendril1_mask,
    'layer_dot3': dot3_mask,
    'layer_root1': root1_mask,
    'layer_root2': root2_mask,
    'layer_dot4': dot4_mask,
}

all_moving = np.zeros((H, W), dtype=bool)
for m in LAYERS.values():
    all_moving |= m

# background layer = original with every moving region flattened to bg color
bg_layer = arr.copy()
bg_layer[all_moving, 0] = bg[0]
bg_layer[all_moving, 1] = bg[1]
bg_layer[all_moving, 2] = bg[2]
bg_layer[all_moving, 3] = 255
Image.fromarray(bg_layer).save(OUT + r"\layer_background.png")

# each moving sprite = real original pixels within its mask, transparent elsewhere
composite = bg_layer.copy().astype(int)
for name, m in LAYERS.items():
    sprite = arr.copy()
    sprite[:, :, 3] = np.where(m, alpha, 0)
    Image.fromarray(sprite).save(OUT + f"\\{name}.png")
    composite[m] = arr[m]

comp_img = Image.fromarray(composite.astype(np.uint8))
comp_img.save(SCRATCH + r"\composite_check2.png")

diff = np.abs(composite.astype(int) - arr.astype(int))
print("max diff vs original:", diff.max())
print("differing px:", (diff.sum(axis=2) > 0).sum(), "/", H * W)

for name, m in LAYERS.items():
    print(name, "area:", m.sum())
