# Security Policy

## Reporting a vulnerability

ThreatMind AI is a security product and we take vulnerabilities seriously. Please
report suspected issues privately (do not open a public issue): open a GitHub
security advisory or contact the maintainers directly. We aim to acknowledge
within 72 hours.

## Scope & posture

The platform's own security model is documented in
[`docs/06-security-model.md`](docs/06-security-model.md). Highlights:

- JWT access/refresh with rotation + reuse detection; Argon2id password hashing.
- OAuth2/OIDC SSO and TOTP MFA.
- RBAC (deny-by-default) enforced at the API and use-case layers.
- Encryption in transit (TLS) and at rest (Fernet for sensitive fields).
- Append-only audit logging; per-client rate limiting; security headers.
- No secrets in source; configuration via environment / secret manager.

## Supply chain

- Dependencies are open-source and free; no paid/hosted AI services.
- CI runs `bandit` (SAST), `pip-audit`, and `npm audit`.
- Pin and review new dependencies before adding them.

## Hardening

See the production hardening checklist in
[`docs/11-deployment-guide.md`](docs/11-deployment-guide.md#8-production-hardening-checklist).
