# LuckLoom Docs

Static public documentation pages for the LuckLoom app.

## Pages

- `index.html` - combined support and privacy overview
- `privacy.html` - privacy policy
- `terms.html` - terms of service
- `account-deletion.html` - account deletion instructions

## Local Verification

Run the static site check before publishing changes:

```bash
python3 scripts/check_static_site.py
```

The checker validates required HTML metadata and local links.
