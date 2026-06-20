import pytest
from fastapi import HTTPException
from unittest.mock import patch
from backend.security.encryption import (
    generate_encryption_key,
    encrypt_value,
    decrypt_value,
)
from backend.security.rate_limiter import rate_limit, _rate_limits
from backend.security.secrets_manager import SecretsManager

# ---------------------------------------------------------
# Test Encryption & Decryption
# ---------------------------------------------------------
def test_encryption_decryption_symmetry():
    key = generate_encryption_key()
    original_text = "my-secret-credentials-123"

    encrypted = encrypt_value(key, original_text)
    assert encrypted != original_text

    decrypted = decrypt_value(key, encrypted)
    assert decrypted == original_text


# ---------------------------------------------------------
# Test Rate Limiting
# ---------------------------------------------------------
def test_rate_limiter_allows_requests():
    _rate_limits.clear()
    # Call within threshold
    rate_limit(key="user-ip-1", limit=3, window_seconds=60)
    rate_limit(key="user-ip-1", limit=3, window_seconds=60)
    rate_limit(key="user-ip-1", limit=3, window_seconds=60)
    # 3 calls are allowed. The 4th should fail.
    with pytest.raises(HTTPException) as exc:
        rate_limit(key="user-ip-1", limit=3, window_seconds=60)
    assert exc.value.status_code == 429
    assert exc.value.detail == "Rate limit exceeded"


# ---------------------------------------------------------
# Test Secrets Manager
# ---------------------------------------------------------
def test_secrets_manager_set_and_get():
    SecretsManager.set_secret("CUSTOM_SECRET_API", "abc-xyz-789")
    val = SecretsManager.get_secret("CUSTOM_SECRET_API")
    assert val == "abc-xyz-789"


@patch("backend.security.secrets_manager.os.getenv")
def test_secrets_manager_get_openai_key(mock_getenv):
    mock_getenv.return_value = "mocked-openai-key-value"
    val = SecretsManager.get_openai_api_key()
    assert val == "mocked-openai-key-value"
    mock_getenv.assert_called_with("OPENAI_API_KEY")
