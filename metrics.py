import numpy as np


def calculate_entropy(image):
    """Shannon entropy using pure numpy (replaces skimage.measure.shannon_entropy)."""
    arr = np.asarray(image).flatten()
    counts = np.bincount(arr.astype(np.uint8), minlength=256)
    probs = counts / counts.sum()
    # Avoid log(0)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def npcr(img1, img2):
    return np.sum(img1 != img2) / img1.size * 100


def uaci(img1, img2):
    return np.mean(np.abs(img1.astype(np.float32) - img2.astype(np.float32))) / 255 * 100