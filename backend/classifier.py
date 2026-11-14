def scale(x, lo, hi):
    """Map x from [lo, hi] onto [0, 1], clamped."""
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def classify_water(f):
    """
    Rule-based classifier. `f` is the feature dict from vision.analyze_image.
    Returns (classification, confidence 0-100).

    These thresholds were tuned on a tiny dataset (12 images). They are a
    stopgap until the TensorFlow model replaces them.
    """

    green = f["green_frac"]
    blue = f["blue_frac"]
    brown = f["brown_frac"]
    entropy = f["hue_entropy"]
    specks = f["specks"]

    # 1. Oil sheen: lots of different vivid hues plus fine texture.
    if entropy > 3.3 and specks > 12:
        return "pollution", round(55 + 40 * scale(entropy, 3.3, 4.0))

    # 2. Algae: mostly green water (not a rocky, multicolored scene).
    if green >= 0.45 and entropy < 2.6:
        return "algae", round(55 + 40 * scale(green, 0.45, 0.70))

    # 3. Brown water: sediment, unless it's full of floating debris.
    if brown >= 0.30:
        if specks >= 25:
            return "pollution", round(55 + 40 * scale(specks, 25, 40))
        return "sediment", round(55 + 40 * scale(brown, 0.30, 0.65))

    # 4. Clear water: blue/teal and not brown.
    if blue >= 0.20 and brown < 0.15:
        return "clear_water", round(55 + 40 * scale(blue, 0.20, 0.70))

    # Nothing matched clearly: say so with low confidence.
    return "clear_water", 50