"""
Create encrypted credentials file programmatically
"""
import sys
from pathlib import Path

# Add parent directory to path to import credentials_manager
sys.path.insert(0, str(Path(__file__).parent))

from credentials_manager import CredentialsManager

# Credentials to encrypt
credentials = {
    'FrameworkDefaultPass': 'password',
    'FrameworkDefaultUser': 'root',
    'DANTA_DB_PASSWORD': 'Keepingtrack2',
    'SSH_PASSWORD': ''  # Empty, will be filled if needed
}

# Create credentials manager
cm = CredentialsManager()

# Save credentials with NO password (so installer can auto-load without prompt)
print("Creating encrypted credentials file...")
print("Using NO password protection for automatic loading...")

# Save without password (pass None)
cm.save_credentials(credentials, password=None)

print("\n" + "="*70)
print("✓ Credentials encrypted successfully!")
print("="*70)
print(f"\nFiles created in keys/ folder:")
print(f"  - {cm.credentials_file}")
print(f"  - {cm.key_file}")
print("\nThese files are saved in the keys/ folder and can be distributed")
print("with the installer package. The installer will automatically load")
print("credentials without prompts.")
print("\n⚠ Keep these files secure and do NOT commit to Git")
print("="*70)
