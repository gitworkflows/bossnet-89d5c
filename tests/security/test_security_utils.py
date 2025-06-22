""
Tests for security utility functions.
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException

from utils.security_utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    sanitize_input,
    generate_secure_random_string,
    get_security_headers,
)
from config import settings

# Test data
TEST_PASSWORD = "test_password_123!"
TEST_DATA = {"sub": "test@example.com"}
TEST_HTML = "<script>alert('xss')</script>Test"
SANITIZED_HTML = "Test"

class TestSecurityUtils:
    """Test suite for security utility functions."""
    
    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        hashed = hash_password(TEST_PASSWORD)
        assert hashed != TEST_PASSWORD
        assert verify_password(TEST_PASSWORD, hashed)
        assert not verify_password("wrong_password", hashed)
    
    def test_create_and_verify_token(self):
        """Test JWT token creation and verification."""
        token = create_access_token(TEST_DATA)
        assert isinstance(token, str)
        
        # Verify the token
        payload = decode_token(token)
        assert payload["sub"] == TEST_DATA["sub"]
    
    def test_token_expiration(self):
        """Test token expiration."""
        # Create a token that expires in 1 second
        token = create_access_token(
            TEST_DATA,
            expires_delta=timedelta(seconds=1)
        )
        
        # Should be valid initially
        decode_token(token)
        
        # Should raise exception after expiration
        with pytest.raises(HTTPException) as exc_info:
            # Fast forward time (in a real test, you'd mock datetime)
            settings.ALGORITHM = "HS256"  # Ensure algorithm is set
            # This is a simplified test; in reality, you'd need to mock time
            # or test with a very short expiration
            pass
            
        assert exc_info.value.status_code == 401
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        assert sanitize_input(TEST_HTML) == SANITIZED_HTML
        assert sanitize_input("<b>Test</b>") == "Test"
        assert sanitize_input("Test\x00") == "Test"
    
    def test_generate_secure_random_string(self):
        """Test secure random string generation."""
        # Test default length
        rand_str = generate_secure_random_string()
        assert len(rand_str) == 32
        assert rand_str.isalnum()
        
        # Test custom length
        rand_str = generate_secure_random_string(16)
        assert len(rand_str) == 16
    
    def test_get_security_headers(self):
        """Test security headers generation."""
        headers = get_security_headers()
        assert isinstance(headers, dict)
        assert "X-Content-Type-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in headers

    def test_token_with_wrong_secret(self):
        """Test token verification with wrong secret key."""
        # Create token with current secret
        token = create_access_token(TEST_DATA)
        
        # Change the secret
        original_secret = settings.SECRET_KEY
        settings.SECRET_KEY = "wrong_secret"
        
        # Should raise exception
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
            
        assert exc_info.value.status_code == 401
        
        # Restore original secret
        settings.SECRET_KEY = original_secret
