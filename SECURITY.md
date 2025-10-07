# Security Notice

## Credential Management

### IMPORTANT: Google Cloud Service Account

If you have a `translator-450208-74f3fffcc975.json` file in this directory:

1. **This file contains sensitive credentials** and should NEVER be committed to version control
2. The file is properly excluded via `.gitignore`
3. **Store credentials securely** using one of these methods:
   - Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to the file
   - Use Google Cloud Secret Manager
   - Use a secure credential management system

### API Key Security

All API keys should be stored in the `.env` file:

```env
DEEPL_API_KEY=your-deepl-key
DEEPSEEK_API_KEY=your-deepseek-key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**Never:**

- Commit `.env` files to version control
- Share API keys in code, logs, or error messages
- Use API keys in URLs or GET parameters
- Print API keys in debug output

### Reporting Security Issues

If you discover a security vulnerability, please report it privately to the repository maintainer.
