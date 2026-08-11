import math
import numpy as np
from PIL import Image

OUT = r"C:\Users\Doori\Documents\Vibe Code Apps\Bioglow logo"

W = H = 1709

def load(name):
    return Image.open(OUT + f"\\{name}.png").convert("RGBA")

background = load("layer_background")
leaf_base = load("layer_leaf_base")
tendril1 = load("layer_tendril1")
root1 = load("layer_root1")
root2 = load("layer_root2")
dot1 = load("layer_dot1")
dot2 = load("layer_dot2")
dot3 = load("layer_dot3")
dot4 = load("layer_dot4")

LEAF_PIVOT = (628.0, 1162.9)
ROOT1_PIVOT = (628.0, 1164.8)
ROOT2_PIVOT = (702.7, 1199.6)
DOT1_C = (1042, 530)
DOT2_C = (1020, 783)
DOT3_C = (1298, 603)
DOT4_C = (1254, 967)


def rotate_about(img, angle_deg, pivot):
    if angle_deg == 0:
        return img
    return img.rotate(angle_deg, resample=Image.BICUBIC, center=pivot)


def scale_about(img, s, pivot):
    if s == 1.0:
        return img
    px, py = pivot
    inv = 1.0 / s
    coeffs = (inv, 0, px * (1 - inv), 0, inv, py * (1 - inv))
    return img.transform(img.size, Image.AFFINE, coeffs, resample=Image.BICUBIC)


def rotate_point(pt, angle_deg, pivot):
    # matches PIL Image.rotate(angle_deg, center=pivot)'s pixel mapping (empirically verified)
    a = math.radians(angle_deg)
    px, py = pivot
    dx, dy = pt[0] - px, pt[1] - py
    ca, sa = math.cos(a), math.sin(a)
    return (px + dx * ca + dy * sa, py - dx * sa + dy * ca)


N = 36
DURATION_MS = 100

LEAF_AMP = 4.0
ROOT_AMP = 3.0
PULSE_AMP = 0.14

frames = []
for i in range(N):
    t = i / N
    sway = 2 * math.pi * t
    pulse = 4 * math.pi * t  # 2 pulse cycles per loop

    leaf_angle = LEAF_AMP * math.sin(sway)
    root1_angle = ROOT_AMP * math.sin(sway + 0.5)
    root2_angle = ROOT_AMP * math.sin(sway + 1.0)

    def pulse_scale(phase_step):
        return 1.0 + PULSE_AMP * (0.5 - 0.5 * math.cos(pulse + phase_step))

    s1 = pulse_scale(0 * math.pi / 2)
    s2 = pulse_scale(1 * math.pi / 2)
    s3 = pulse_scale(2 * math.pi / 2)
    s4 = pulse_scale(3 * math.pi / 2)

    # Everything below hangs off the leaf, which hangs off nothing (its own pivot).
    # Each child is first rotated with its parent's motion (so the attachment point
    # never drifts apart), then gets its own extra motion layered on top.

    # leaf_base and its direct riders (dot1, dot2, tendril1) share leaf_angle/LEAF_PIVOT
    leaf_xform = [(leaf_angle, LEAF_PIVOT)]

    root1_xform = leaf_xform + [(root1_angle, rotate_point(ROOT1_PIVOT, leaf_angle, LEAF_PIVOT))]
    root2_pivot_after_leaf = rotate_point(ROOT2_PIVOT, leaf_angle, LEAF_PIVOT)
    root2_xform = leaf_xform + [(root2_angle, root2_pivot_after_leaf)]

    def apply_chain(img, chain):
        for ang, piv in chain:
            img = rotate_about(img, ang, piv)
        return img

    def apply_chain_point(pt, chain):
        for ang, piv in chain:
            pt = rotate_point(pt, ang, piv)
        return pt

    dot1_c = apply_chain_point(DOT1_C, leaf_xform)
    dot2_c = apply_chain_point(DOT2_C, leaf_xform)
    dot3_c = apply_chain_point(DOT3_C, leaf_xform)
    dot4_c = apply_chain_point(DOT4_C, root2_xform)

    img_dot1 = scale_about(apply_chain(dot1, leaf_xform), s1, dot1_c)
    img_dot2 = scale_about(apply_chain(dot2, leaf_xform), s2, dot2_c)
    img_dot3 = scale_about(apply_chain(dot3, leaf_xform), s3, dot3_c)
    img_dot4 = scale_about(apply_chain(dot4, root2_xform), s4, dot4_c)

    frame = background.copy()
    frame.alpha_composite(apply_chain(root1, root1_xform))
    frame.alpha_composite(apply_chain(root2, root2_xform))
    frame.alpha_composite(apply_chain(leaf_base, leaf_xform))
    frame.alpha_composite(apply_chain(tendril1, leaf_xform))
    frame.alpha_composite(img_dot1)
    frame.alpha_composite(img_dot2)
    frame.alpha_composite(img_dot3)
    frame.alpha_composite(img_dot4)

    frames.append(frame)

SCALE = 700 / W
small = [f.resize((700, 700), Image.LANCZOS).convert("RGB") for f in frames]

gif_path = OUT + r"\bioglow_animated.gif"
quantized = [f.quantize(colors=64, method=Image.MEDIANCUT) for f in small]
quantized[0].save(
    gif_path,
    save_all=True,
    append_images=quantized[1:],
    duration=DURATION_MS,
    loop=0,
    optimize=True,
)
print("saved", gif_path)
