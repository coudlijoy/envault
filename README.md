# envault

> A CLI tool for encrypting and syncing `.env` files across team members using a shared key.

---

## Installation

```bash
pip install envault
```

Or with pipx for isolated installs:

```bash
pipx install envault
```

---

## Usage

**Initialize envault in your project:**

```bash
envault init
```

**Encrypt your `.env` file and push to the shared vault:**

```bash
envault push --file .env
```

**Pull and decrypt the latest `.env` for your team:**

```bash
envault pull --out .env
```

**Rotate the shared key:**

```bash
envault rotate-key
```

> 💡 Store your shared key in a secure secrets manager or share it with teammates via a secure channel. Never commit it to version control.

---

## How It Works

1. `envault init` generates a shared encryption key (AES-256).
2. `envault push` encrypts your `.env` and uploads the ciphertext to a configured backend (local, S3, or a shared URL).
3. `envault pull` fetches the latest encrypted file and decrypts it locally using the shared key.

---

## Configuration

Set your shared key as an environment variable:

```bash
export ENVAULT_KEY="your-base64-encoded-key"
```

Or store it in `.envault.toml`:

```toml
[vault]
key_env = "ENVAULT_KEY"
backend = "s3"
bucket = "my-team-vault"
```

---

## License

[MIT](LICENSE) © 2024 envault contributors