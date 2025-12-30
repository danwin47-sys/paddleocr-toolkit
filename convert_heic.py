#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF opener with Pillow
register_heif_opener()

def convert_heic_to_jpg(input_dir='input'):
    targets = ['1', '2']
    
    # Ensure input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Directory '{input_dir}' not found.")
        return

    print(f"Checking '{input_dir}' for HEIC files...")
    
    for filename in os.listdir(input_dir):
        name, ext = os.path.splitext(filename)
        if ext.lower() == '.heic' and name in targets:
            heic_path = os.path.join(input_dir, filename)
            jpg_path = os.path.join(input_dir, f"{name}.jpg")
            
            try:
                print(f"Converting {filename} to JPG...")
                image = Image.open(heic_path)
                image.convert('RGB').save(jpg_path, "JPEG")
                print(f"Saved to {jpg_path}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    convert_heic_to_jpg()
