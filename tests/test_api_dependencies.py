# -*- coding: utf-8 -*-
"""
API Dependencies Tests
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from paddleocr_toolkit.api.dependencies import (
    check_rate_limit,
    resize_image_if_needed,
    rate_limits,
    RATE_LIMIT,
    MAX_IMAGE_SIDE,
)


class TestDependencies:
    def test_check_rate_limit_within_limit(self):
        """Test rate limiting when within limit"""
        ip = "192.168.1.1"
        rate_limits[ip] = []  # Reset

        # Should allow up to RATE_LIMIT requests
        for i in range(RATE_LIMIT):
            assert check_rate_limit(ip) is True

        # Next request should be blocked
        assert check_rate_limit(ip) is False

    def test_check_rate_limit_custom_limit(self):
        """Test rate limiting with custom limit"""
        ip = "192.168.1.2"
        rate_limits[ip] = []

        custom_limit = 3
        for i in range(custom_limit):
            assert check_rate_limit(ip, limit=custom_limit) is True

        assert check_rate_limit(ip, limit=custom_limit) is False

    def test_check_rate_limit_window_expiry(self):
        """Test that old requests are cleaned up"""
        ip = "192.168.1.3"

        # Mock time to simulate old requests
        with patch("paddleocr_toolkit.api.dependencies.time") as mock_time:
            # Set initial time
            mock_time.time.return_value = 1000.0
            rate_limits[ip] = []

            # Fill up the limit
            for _ in range(RATE_LIMIT):
                check_rate_limit(ip)

            # Advance time beyond window (60 seconds)
            mock_time.time.return_value = 1070.0

            # Should allow new requests after window expires
            assert check_rate_limit(ip) is True

    @patch("PIL.Image")
    def test_resize_image_within_limits(self, mock_pil):
        """Test that small images are not resized"""
        mock_img = Mock()
        mock_img.size = (1000, 800)  # Within MAX_IMAGE_SIDE
        mock_pil.open.return_value.__enter__.return_value = mock_img

        result = resize_image_if_needed("test.jpg")
        assert result == "test.jpg"
        mock_img.resize.assert_not_called()

    @patch("PIL.Image")
    def test_resize_image_exceeds_limits(self, mock_pil):
        """Test that large images are resized"""
        mock_img = Mock()
        mock_img.size = (3000, 2000)  # Exceeds MAX_IMAGE_SIDE
        mock_resized = Mock()
        mock_img.resize.return_value = mock_resized
        mock_pil.open.return_value.__enter__.return_value = mock_img
        mock_pil.Resampling.LANCZOS = 1

        with patch("paddleocr_toolkit.api.dependencies.Path") as mock_path:
            mock_path.return_value.parent = Path("/tmp")
            mock_path.return_value.stem = "test"
            mock_path.return_value.suffix = ".jpg"

            result = resize_image_if_needed("/tmp/test.jpg")

            # Should return resized path
            assert "resized" in result
            mock_img.resize.assert_called_once()
            mock_resized.save.assert_called_once()

    def test_resize_image_error_handling(self):
        """Test that errors are handled gracefully"""
        # Non-existent file should return original path
        result = resize_image_if_needed("/nonexistent/file.jpg")
        assert result == "/nonexistent/file.jpg"
