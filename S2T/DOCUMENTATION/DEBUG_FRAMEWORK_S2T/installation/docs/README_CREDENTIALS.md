# Encrypted Credentials Quick Start

**For Administrators distributing the installer package**

## Creating Encrypted Credentials File

1. **Install cryptography library**:
   ```powershell
   pip install --proxy http://proxy-dmz.intel.com:911 cryptography
   ```

2. **Create encrypted credentials**:
   ```powershell
   cd installation
   python credentials_manager.py create
   ```

3. **Follow the prompts** to enter:
   - Encryption password (recommended)
   - FrameworkDefaultPass
   - DANTA_DB_PASSWORD
   - SSH Password (optional)

4. **Package for distribution**:
   - `keys/credentials.enc` (encrypted credentials)
   - `keys/credentials.key` (encryption key)
   - All installer files

5. **Distribute securely** through approved Intel channels

## For End Users

The credentials are located in the `installation/keys/` folder. The installer automatically detects `keys/credentials.enc` and `keys/credentials.key` - No manual password entry needed!

## Commands

```powershell
# Create new credentials
python credentials_manager.py create

# Read/test credentials
python credentials_manager.py read

# Check if credentials exist
python credentials_manager.py check
```

## Security

- ✅ Files in keys/ folder excluded from Git (.gitignore)
- ✅ AES-256 encryption (Fernet)
- ✅ Optional password-based encryption
- ⚠️ Keep keys/credentials.enc and keys/credentials.key secure
- ⚠️ Distribute only through secure channels

## Troubleshooting

**"cryptography not found"**
```powershell
pip install cryptography
```

**"Failed to decrypt"**
- Check password is correct
- Verify both .enc and .key files present
- Try recreating files

For detailed documentation, see [CREDENTIALS_SETUP.md](CREDENTIALS_SETUP.md)
