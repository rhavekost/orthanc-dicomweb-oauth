# Secrets Encryption in Memory

## Overview

The plugin encrypts sensitive data (client secrets, access tokens) in memory to protect against memory dumps and process inspection.

## Implementation

Secrets are encrypted using Fernet (symmetric encryption) with AES-128:

```python
from cryptography.fernet import Fernet

# Each TokenManager instance generates unique encryption key
cipher = Fernet(Fernet.generate_key())

# Client secrets encrypted on initialization
encrypted_secret = cipher.encrypt(client_secret.encode())

# Decrypted only when needed for OAuth requests
client_secret = cipher.decrypt(encrypted_secret).decode()
```

## Protected Data

- **Client secrets**: OAuth2 client credentials
- **Access tokens**: Cached JWT tokens
- **Refresh tokens**: If implemented

## Security Benefits

- **Memory dump protection**: Secrets not readable in memory dumps
- **Process inspection protection**: Secrets not visible in debuggers
- **Crash dump protection**: Secrets encrypted in crash dumps

## Automatic

Encryption is automatic and transparent:
- No configuration required
- No performance impact
- Secrets decrypted only when needed

## Limitations

- **Key in memory**: Encryption key is in memory
- **Not encryption at rest**: Only protects in-memory data
- **Single process**: Keys not shared across processes

## Recommendations

For enhanced security:
1. Use secret managers (Azure Key Vault, AWS Secrets Manager)
2. Enable memory protection features (ASLR, DEP)
3. Limit process access permissions
4. Enable audit logging for memory access
