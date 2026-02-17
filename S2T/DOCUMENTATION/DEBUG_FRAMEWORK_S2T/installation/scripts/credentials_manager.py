"""
Encrypted Credentials Manager for Debug Framework
==================================================
Version: 1.7.1
Date: February 17, 2026
Author: Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

This module manages encrypted credential storage for the Debug Framework installer.
Credentials are stored in an encrypted file (credentials.enc) that is NOT committed to Git.

Security Features:
- AES-256 encryption using cryptography library (Fernet)
- Machine-specific key derivation (optional)
- Password-based key derivation (PBKDF2)
- Encrypted file is excluded from Git via .gitignore

Usage:
    # Create encrypted credentials file
    python credentials_manager.py create

    # Read credentials
    python credentials_manager.py read

    # Programmatic usage
    from credentials_manager import CredentialsManager
    cm = CredentialsManager()
    creds = cm.load_credentials()
"""

import json
import base64
import getpass
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠ Warning: cryptography library not installed")
    print("Install with: pip install cryptography")


class CredentialsManager:
    """Manages encrypted credential storage"""

    def __init__(self, credentials_file: Optional[Path] = None, key_file: Optional[Path] = None):
        """
        Initialize credentials manager

        Args:
            credentials_file: Path to encrypted credentials file (default: ../keys/credentials.enc)
            key_file: Path to encryption key file (default: ../keys/credentials.key)
        """
        self.script_dir = Path(__file__).parent
        # Default location is keys folder in installation root (one level up from scripts)
        keys_dir = self.script_dir.parent / "keys"
        self.credentials_file = credentials_file or (keys_dir / "credentials.enc")
        self.key_file = key_file or (keys_dir / "credentials.key")

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2HMAC"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _get_or_create_key(self, password: Optional[str] = None) -> bytes:
        """
        Get encryption key from file or create new one

        Args:
            password: Optional password for key derivation

        Returns:
            Encryption key as bytes
        """
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key_data = f.read()

            # Check if it's a password-derived key (has salt prefix)
            if key_data.startswith(b'SALT:'):
                if not password:
                    raise ValueError("Password required to decrypt credentials")
                # Extract salt and derive key
                salt = key_data[5:37]  # SALT: + 32 bytes
                return self._derive_key_from_password(password, salt)
            else:
                # Direct key
                return key_data
        else:
            # Create new key
            if password:
                # Use password-based key derivation
                salt = os.urandom(32)
                key = self._derive_key_from_password(password, salt)
                # Store salt with key file
                with open(self.key_file, 'wb') as f:
                    f.write(b'SALT:' + salt)
                print(f"✓ Created password-based encryption key: {self.key_file}")
            else:
                # Generate random key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                print(f"✓ Created encryption key: {self.key_file}")

            return key

    def create_credentials(self, interactive: bool = True) -> Dict[str, str]:
        """
        Create encrypted credentials file interactively or programmatically

        Args:
            interactive: If True, prompt user for credentials

        Returns:
            Dictionary of credentials
        """
        if not CRYPTO_AVAILABLE:
            print("✗ Error: cryptography library not available")
            print("Install with: pip install cryptography")
            sys.exit(1)

        print("\n" + "="*70)
        print("Debug Framework - Encrypted Credentials Setup")
        print("="*70)
        print("\nThis utility creates an encrypted credentials file for the installer.")
        print("The encrypted file will be stored locally and NOT committed to Git.")
        print("\n⚠ SECURITY: Keep the credentials.enc and credentials.key files secure.")
        print("These files should be distributed to end users through secure channels.\n")

        if interactive:
            # Get encryption password
            print("Step 1: Set encryption password")
            print("-" * 70)
            use_password = input("Use password-based encryption? (y/n, default=y): ").strip().lower()
            use_password = use_password != 'n'

            password = None
            if use_password:
                while True:
                    password = getpass.getpass("Enter encryption password: ")
                    password_confirm = getpass.getpass("Confirm password: ")
                    if password == password_confirm:
                        break
                    print("✗ Passwords don't match. Try again.")

            # Get credentials
            print("\nStep 2: Enter framework credentials")
            print("-" * 70)
            print("Contact your team lead if you don't know these values.")
            print("")

            credentials = {}
            credentials['FrameworkDefaultPass'] = getpass.getpass("FrameworkDefaultPass: ")
            credentials['FrameworkDefaultUser'] = input("FrameworkDefaultUser (default=root): ").strip() or 'root'
            credentials['DANTA_DB_PASSWORD'] = getpass.getpass("DANTA_DB_PASSWORD: ")

            # Optional: Add more credentials
            print("\nOptional: SSH Password for EFI transfer")
            ssh_pass = getpass.getpass("SSH Password (press Enter to skip): ")
            if ssh_pass:
                credentials['SSH_PASSWORD'] = ssh_pass
        else:
            # Non-interactive mode - return empty dict to be filled programmatically
            credentials = {
                'FrameworkDefaultPass': '',
                'FrameworkDefaultUser': 'root',
                'DANTA_DB_PASSWORD': '',
                'SSH_PASSWORD': ''
            }
            password = None

        # Encrypt and save
        self.save_credentials(credentials, password)

        print("\n" + "="*70)
        print("✓ Credentials encrypted successfully!")
        print("="*70)
        print(f"\nFiles created:")
        print(f"  - {self.credentials_file} (encrypted credentials)")
        print(f"  - {self.key_file} (encryption key)")
        print("\n⚠ IMPORTANT:")
        print("  1. Keep these files secure and do NOT commit to Git")
        print("  2. Distribute to end users through secure channels only")
        print("  3. .gitignore should exclude: credentials.enc, credentials.key")
        print(f"  4. To decrypt: python credentials_manager.py read")
        print("")

        return credentials

    def save_credentials(self, credentials: Dict[str, str], password: Optional[str] = None):
        """
        Save credentials to encrypted file

        Args:
            credentials: Dictionary of credential key-value pairs
            password: Optional password for encryption
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        # Get or create encryption key
        key = self._get_or_create_key(password)
        fernet = Fernet(key)

        # Serialize credentials to JSON
        credentials_json = json.dumps(credentials, indent=2)

        # Encrypt
        encrypted_data = fernet.encrypt(credentials_json.encode())

        # Save to file
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted_data)

        print(f"✓ Encrypted credentials saved to: {self.credentials_file}")

    def load_credentials(self, password: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Load and decrypt credentials from file

        Args:
            password: Optional password for decryption

        Returns:
            Dictionary of credentials or None if file doesn't exist
        """
        if not self.credentials_file.exists():
            return None

        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        try:
            # Get encryption key
            key = self._get_or_create_key(password)
            fernet = Fernet(key)

            # Read encrypted file
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt
            decrypted_data = fernet.decrypt(encrypted_data)

            # Parse JSON
            credentials = json.loads(decrypted_data.decode())

            return credentials

        except Exception as e:
            print(f"✗ Error loading credentials: {e}")
            print("  Possible causes:")
            print("  - Wrong password")
            print("  - Corrupted credentials file")
            print("  - Missing or wrong key file")
            return None

    def credentials_exist(self) -> bool:
        """Check if encrypted credentials file exists"""
        return self.credentials_file.exists()


def main():
    """Command-line interface for credentials management"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python credentials_manager.py create    - Create encrypted credentials")
        print("  python credentials_manager.py read      - Read and display credentials")
        print("  python credentials_manager.py check     - Check if credentials exist")
        sys.exit(1)

    command = sys.argv[1].lower()
    cm = CredentialsManager()

    if command == 'create':
        cm.create_credentials(interactive=True)

    elif command == 'read':
        if not cm.credentials_exist():
            print("✗ Credentials file not found")
            print(f"   Expected: {cm.credentials_file}")
            print("\nRun: python credentials_manager.py create")
            sys.exit(1)

        # Check if password-based
        password = None
        if cm.key_file.exists():
            with open(cm.key_file, 'rb') as f:
                key_data = f.read()
            if key_data.startswith(b'SALT:'):
                password = getpass.getpass("Enter decryption password: ")

        credentials = cm.load_credentials(password)

        if credentials:
            print("\n" + "="*70)
            print("Decrypted Credentials")
            print("="*70)
            for key, value in credentials.items():
                # Mask password values
                if 'PASS' in key.upper() or 'PASSWORD' in key.upper():
                    display_value = '*' * len(value) if value else '(not set)'
                else:
                    display_value = value
                print(f"  {key}: {display_value}")
            print("="*70)
        else:
            print("✗ Failed to decrypt credentials")
            sys.exit(1)

    elif command == 'check':
        if cm.credentials_exist():
            print(f"✓ Credentials file exists: {cm.credentials_file}")
            if cm.key_file.exists():
                print(f"✓ Key file exists: {cm.key_file}")
            else:
                print(f"✗ Key file missing: {cm.key_file}")
        else:
            print(f"✗ Credentials file not found: {cm.credentials_file}")
            print("\nRun: python credentials_manager.py create")

    else:
        print(f"✗ Unknown command: {command}")
        print("Valid commands: create, read, check")
        sys.exit(1)


if __name__ == '__main__':
    import os
    main()
