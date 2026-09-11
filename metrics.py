import numpy as np
from skimage.measure import shannon_entropy

def calculate_entropy(image):
    return shannon_entropy(image)

def npcr(img1, img2):
    return np.sum(img1 != img2) / img1.size * 100

def uaci(img1, img2):
    return np.mean(np.abs(img1 - img2)) / 255 * 100