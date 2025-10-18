#!/usr/bin/env python3
"""
Simplify circuit board tree for favicon by making lines thicker and more visible
"""

from PIL import Image, ImageDraw, ImageFilter, ImageOps
import os

# Paths
input_path = os.path.expanduser("~/Downloads/favicon_io/android-chrome-512x512.png")
output_dir = os.path.expanduser("~/Documents/Ancient Free Will Database/frontend/public/")

def simplify_and_create_favicons(input_image_path):
    """Simplify the tree design and create favicon sizes"""

    # Load the original image
    img = Image.open(input_image_path).convert('RGBA')

    # Get the dimensions
    width, height = img.size

    # Create a simplified version by:
    # 1. Increasing contrast
    # 2. Making lines thicker using morphological operations

    # Extract alpha channel
    r, g, b, a = img.split()

    # Dilate to make lines thicker (repeat for more thickness)
    from PIL import ImageFilter

    # Convert to grayscale for processing
    gray = img.convert('L')

    # Increase contrast
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(2.0)

    # Threshold to make it binary (sharper)
    threshold = 200
    gray = gray.point(lambda x: 255 if x > threshold else 0)

    # Dilate to make lines thicker (makes small details merge and thicken)
    for i in range(2):  # Apply twice for thicker lines
        gray = gray.filter(ImageFilter.MaxFilter(3))

    # Convert back to RGBA with original colors
    # Get the red color from original
    red_layer = Image.new('RGBA', img.size, (182, 27, 33, 255))  # #b61b21

    # Use the processed grayscale as alpha mask
    gray_inverted = ImageOps.invert(gray)
    red_layer.putalpha(gray_inverted)

    # Create white/transparent background
    background = Image.new('RGBA', img.size, (255, 255, 255, 0))
    result = Image.alpha_composite(background, red_layer)

    # Generate favicon sizes
    sizes = {
        'favicon-16x16.png': 16,
        'favicon-32x32.png': 32,
        'apple-touch-icon.png': 180,
        'android-chrome-192x192.png': 192,
        'android-chrome-512x512.png': 512,
    }

    for filename, size in sizes.items():
        # Resize with high-quality downsampling
        resized = result.resize((size, size), Image.Resampling.LANCZOS)

        # For very small sizes, apply additional sharpening
        if size <= 32:
            resized = resized.filter(ImageFilter.SHARPEN)

        output_path = os.path.join(output_dir, filename)
        resized.save(output_path, 'PNG', optimize=True)
        print(f"Created: {filename} ({size}x{size})")

    # Create ICO file (multi-size)
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico_images = []
    for size in ico_sizes:
        resized = result.resize(size, Image.Resampling.LANCZOS)
        if size[0] <= 32:
            resized = resized.filter(ImageFilter.SHARPEN)
        ico_images.append(resized)

    ico_path = os.path.join(output_dir, 'favicon.ico')
    ico_images[0].save(ico_path, format='ICO', sizes=ico_sizes)
    print(f"Created: favicon.ico (multi-size)")

    print("\n✅ All simplified favicons created!")

if __name__ == "__main__":
    if not os.path.exists(input_path):
        print(f"❌ Error: Input file not found: {input_path}")
        print("Please make sure the favicon_io folder is in your Downloads")
    else:
        simplify_and_create_favicons(input_path)
