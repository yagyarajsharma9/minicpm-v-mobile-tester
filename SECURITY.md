# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. Do **not** open a public GitHub Issue for security vulnerabilities.
2. Check the project README for a direct contact method or use GitHub private vulnerability reporting if available.

## API Keys

This project does **not** include any API keys. Configuration for web search providers (Tavily, TinyFish) is handled via `local.properties` in the Android project, which is excluded from version control.

## Security Considerations

- The web server (`app.py`) binds to `127.0.0.1` by default — it is not exposed to the network.
- The PWA shell (`mobile_app/`) communicates only with the local server.
- Do not expose the server port (7860) to public networks.
- The Android APK includes API key fields in `BuildConfig` for local testing only — never use production keys directly in an APK.

## Dependency Security

- Run `pip audit` in the `.venv` environment periodically.
- Keep `requirements.txt` dependencies up to date.