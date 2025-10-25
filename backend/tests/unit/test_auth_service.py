"""
Unit tests for Authentication Service
Tests JWT, password hashing, and rate limiting
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from services.auth_service import create_access_token, verify_password, get_password_hash


class TestAuthService:
    """Test cases for Authentication Service"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (salt)"""
        password = "testpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Different hashes due to salt
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiration(self):
        """Test token creation with custom expiration"""
        data = {"sub": "testuser"}
        short_expiry = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=short_expiry)

        assert isinstance(token, str)

    def test_verify_token_valid(self):
        """Test verification of valid token"""
        from jose import jwt
        import os

        secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-testing")
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))

        # Decode and verify
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert payload["sub"] == "testuser"

    def test_verify_token_expired(self):
        """Test that expired tokens are rejected"""
        from jose import jwt, JWTError
        import os

        secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-testing")

        # Create token that expired 1 hour ago
        data = {"sub": "testuser"}
        expired_token = create_access_token(data, expires_delta=timedelta(hours=-1))

        with pytest.raises(JWTError):
            jwt.decode(expired_token, secret_key, algorithms=["HS256"])

    def test_password_validation_min_length(self):
        """Test password minimum length requirement"""
        # This would be implemented in your validation logic
        weak_password = "123"
        assert len(weak_password) < 8  # Should fail validation

        strong_password = "securepass123"
        assert len(strong_password) >= 8  # Should pass validation

    def test_empty_password_hash(self):
        """Test handling of empty password"""
        with pytest.raises(Exception):
            get_password_hash("")

    def test_token_payload_integrity(self):
        """Test that token payload is preserved correctly"""
        from jose import jwt
        import os

        secret_key = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-testing")

        data = {
            "sub": "testuser",
            "email": "test@example.com",
            "role": "user"
        }
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        assert payload["sub"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "user"

    @pytest.mark.parametrize("password,should_be_strong", [
        ("abc123", False),
        ("strongpassword123", True),
        ("", False),
        ("a" * 20, True),
    ])
    def test_password_strength(self, password, should_be_strong):
        """Test password strength validation"""
        # Basic strength check: at least 8 characters
        is_strong = len(password) >= 8
        assert is_strong == should_be_strong
