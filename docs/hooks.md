# Envault Hooks

Envault supports **pre/post operation hooks** — shell scripts that run automatically before or after key vault operations.

## Supported Events

| Event        | Triggered                          |
|--------------|------------------------------------|
| `pre-lock`   | Before encrypting the `.env` file  |
| `post-lock`  | After encrypting the `.env` file   |
| `pre-unlock` | Before decrypting the vault        |
| `post-unlock`| After decrypting the vault         |
| `pre-sync`   | Before syncing the vault           |
| `post-sync`  | After syncing the vault            |

## Registering a Hook

Create a shell script and register it for an event:

```bash
# Create a hook script
cat > notify.sh << 'EOF'
#!/bin/sh
echo "Vault locked at $(date)" >> ~/.envault_activity.log
EOF
chmod +x notify.sh

# Register it
envault hooks register post-lock ./notify.sh
```

## Listing Hooks

```bash
envault hooks list
```

## Removing a Hook

```bash
envault hooks remove post-lock
```

## Hook Storage

Hooks are stored in `.envault/hooks/` by default. Each event maps to a single executable file named after the event (e.g., `.envault/hooks/post-lock`).

Add `.envault/hooks/` to version control to share hooks with your team.

## Error Handling

If a hook script exits with a non-zero status, the envault operation will be **aborted** and an error message displayed. Hooks must complete within **30 seconds**.

## Example: Slack Notification on Sync

```bash
#!/bin/sh
curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-type: application/json' \
  --data '{"text":"envault: vault synced by '"$USER"'"}'
```
