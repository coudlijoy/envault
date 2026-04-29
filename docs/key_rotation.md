# Key Rotation

envault supports rotating the shared encryption key without losing access to your `.env` data.

## Why Rotate Keys?

- A team member leaves and you want to revoke access
- Periodic security hygiene
- A key may have been accidentally exposed

## Rotating a Key

### Auto-generate a new key

```bash
envault rotation rotate .env.vault --key $ENVAULT_KEY
```

This will print the new key. **Share it securely with your team.**

### Rotate to a specific key

```bash
envault rotation rotate .env.vault --key $ENVAULT_KEY --new-key <NEW_KEY>
```

### Using environment variable

```bash
export ENVAULT_KEY=your-current-key
envault rotation rotate .env.vault
```

## Viewing Rotation History

```bash
envault rotation history .env.vault
```

Example output:

```
Rotation history for .env.vault:
  1. 2024-06-01T10:32:11.123456
  2. 2024-07-15T08:14:55.654321
```

Rotation events are stored in `.envault_rotation_log.json` alongside your vault file.

> **Note:** Add `.envault_rotation_log.json` to `.gitignore` if you do not want to track rotation history in version control.

## After Rotation

1. The vault is re-encrypted with the new key immediately.
2. All team members must update their `ENVAULT_KEY` environment variable.
3. The old key will no longer decrypt the vault.
