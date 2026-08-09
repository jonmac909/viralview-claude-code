# Viral View for Codex and Claude Code

This is the public agent skill pack for running [Viral View](https://app.viralview.io) from Codex and Claude Code.

The finished workspace will let an agent search the Viral View ad library, scan a product page, clone a viral ad, guide character and scene choices, estimate usage, and export the final video.

## Status

The Viral View public API is still being finalized. This repository currently contains the public project shell only. Generation scripts and skills will be added after the API is deployed and smoke-tested against its published contract.

No generation commands are included yet.

## Security

Never commit credentials to this repository.

- Keep your Viral View API key in a local `.env` file.
- Never add upstream provider keys, session cookies, authorization headers, account data, or private media.
- `.env`, local context, logs, and reference media are ignored by Git.
- Examples use placeholders only.

If a credential is committed, revoke it immediately and follow [SECURITY.md](SECURITY.md).

## Planned skills

- `clone-viral-ad`
- `search-library`
- `product-scan`
- `export-video`
- `character-options`
- `remix-script`
- `usage-costs`

Every paid image or video generation batch will require an explicit yes from the user before the API call is made. Character selection and detected scene cuts will also stop for user approval.

## Local configuration

The skill pack will use these local variables:

```dotenv
VIRALVIEW_API_KEY=your_viralview_api_key_here
VIRALVIEW_BASE_URL=https://app.viralview.io
```

Copy `.env.example` to `.env` when setup instructions are published. The `.env` file stays on your machine and is never committed.

## License

[MIT](LICENSE)
