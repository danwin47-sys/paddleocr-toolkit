# -*- coding: utf-8 -*-
"""
API Dependencies and Shared Utilities
"""
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from paddleocr_toolkit.utils.logger import logger

# Rate limiting storage
rate_limits: Dict[str, List[float]] = defaultdict(list)

# Constants
RATE_LIMIT = 10  # Requests per minute
RATE_LIMIT_BATCH = 3  # Batch requests per minute
RATE_WINDOW = 60  # Time window in seconds
MAX_IMAGE_SIDE = 2500  # Maximum image dimension in pixels


def check_rate_limit(client_ip: str, limit: int = RATE_LIMIT) -> bool:
    """
    Check if client has exceeded rate limit

    Args:
        client_ip: Client IP address
        limit: Request limit (default 10/minute)

    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()

    # Clean old records
    rate_limits[client_ip] = [
        t for t in rate_limits[client_ip] if now - t < RATE_WINDOW
    ]

    # Check if limit exceeded
    if len(rate_limits[client_ip]) >= limit:
        return False

    # Record request
    rate_limits[client_ip].append(now)
    return True


def resize_image_if_needed(file_path: str, max_side: int = MAX_IMAGE_SIDE) -> str:
    """
    Resize large images to avoid OCR memory issues

    Args:
        file_path: Image file path
        max_side: Maximum side length (default 2500px)

    Returns:
        Processed image path (resized or original)
    """
    try:
        from PIL import Image

        with Image.open(file_path) as img:
            width, height = img.size
            max_dim = max(width, height)

            if max_dim <= max_side:
                logger.debug(
                    "Image size %dx%d within limits, no resize needed", width, height
                )
                return file_path

            # Calculate scale
            scale = max_side / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)

            logger.info(
                "Image too large (%dx%d), resizing to %dx%d",
                width,
                height,
                new_width,
                new_height,
            )

            # Resize image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save to new file
            path = Path(file_path)
            new_path = path.parent / f"{path.stem}_resized{path.suffix}"
            resized_img.save(str(new_path), quality=95)

            logger.info("Resized image saved: %s", new_path)
            return str(new_path)

    except Exception as e:
        logger.error("Error resizing image: %s, using original", e)
        return file_path
