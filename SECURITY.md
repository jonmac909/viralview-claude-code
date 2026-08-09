# Security policy

## Keep credentials out of Git

This public repository must never contain API keys, provider credentials, session cookies, authorization headers, private account data, or customer media.

Store your Viral View API key only in `.env`. That file is ignored by Git. Documentation and tests must use obvious placeholders that cannot authenticate.

## If a secret is exposed

1. Revoke or rotate the credential immediately.
2. Remove it from the working tree and Git history.
3. Open a private GitHub security advisory for this repository with the affected path and commit.
4. Do not paste the credential into an issue, pull request, discussion, or chat transcript.

## Report a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not open a public issue for credential exposure or a security flaw.
