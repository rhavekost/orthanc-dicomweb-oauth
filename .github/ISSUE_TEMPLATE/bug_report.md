---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce

1.
2.
3.
4.

## Expected Behavior

<!-- What you expected to happen -->

## Actual Behavior

<!-- What actually happened -->

## Environment

**Orthanc Version:**
<!-- e.g., 1.12.1 -->

**Plugin Version:**
<!-- e.g., 2.0.0 -->

**Python Version:**
<!-- e.g., 3.11.4 -->

**Deployment Method:**
- [ ] Docker
- [ ] Manual installation
- [ ] Other (please specify):

**Operating System:**
<!-- e.g., Ubuntu 22.04, macOS 14.2, Windows Server 2022 -->

**OAuth Provider:**
- [ ] Azure Entra ID
- [ ] Google Cloud
- [ ] Keycloak
- [ ] Auth0
- [ ] Okta
- [ ] Other (please specify):

## Configuration

<!-- Share relevant configuration (redact secrets!) -->

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "my-server": {
        "Url": "https://...",
        "TokenEndpoint": "https://...",
        ...
      }
    }
  }
}
```

## Logs

<!-- Include relevant log output (redact secrets and tokens!) -->

```
[Paste logs here]
```

## Error Messages

<!-- Full error message and stack trace if available -->

```
[Paste error here]
```

## Screenshots

<!-- If applicable, add screenshots to help explain the problem -->

## Additional Context

<!-- Add any other context about the problem here -->

## Possible Solution

<!-- Optional: Suggest a fix or reason for the bug -->

## Security Concern

- [ ] This bug has security implications
- [ ] This should be reported privately (see SECURITY.md)

---

**Checklist:**
- [ ] I have searched existing issues for duplicates
- [ ] I have redacted all secrets and tokens
- [ ] I have provided all required environment information
- [ ] I can reproduce this consistently
