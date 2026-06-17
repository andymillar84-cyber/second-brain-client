"""Exchange an oauth_token cookie value for a Google master token.

Usage:
    .venv/bin/python exchange_token.py <oauth_token_value>

The oauth_token comes from the cookie set after signing in at
https://accounts.google.com/EmbeddedSetup.

The master token is saved to .secrets/master_token (chmod 600), never
printed to stdout, so it doesn't leak via terminal scrollback or chat.
"""
import os
import sys
import secrets
import gpsoauth
from pathlib import Path

EMAIL = os.environ.get("GKEEP_EMAIL", "")
SECRETS_DIR = Path(__file__).parent / ".secrets"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 1

    oauth_token = sys.argv[1].strip()
    android_id = secrets.token_hex(8)

    print(f"Email: {EMAIL}")
    print(f"Android ID: {android_id}")
    print("Exchanging oauth_token for master token...")

    response = gpsoauth.exchange_token(EMAIL, oauth_token, android_id)

    if "Token" not in response:
        print("\nFAILED. Full response:", file=sys.stderr)
        for k, v in response.items():
            print(f"  {k}: {v}", file=sys.stderr)
        return 2

    master_token = response["Token"]

    SECRETS_DIR.mkdir(exist_ok=True)
    os.chmod(SECRETS_DIR, 0o700)

    token_path = SECRETS_DIR / "master_token"
    token_path.write_text(master_token)
    os.chmod(token_path, 0o600)

    android_path = SECRETS_DIR / "android_id"
    android_path.write_text(android_id)
    os.chmod(android_path, 0o600)

    print(f"\nSUCCESS")
    print(f"Master token written to: {token_path}")
    print(f"Android ID written to:   {android_path}")
    print(f"Token length: {len(master_token)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
