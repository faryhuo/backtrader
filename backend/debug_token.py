"""
Debug utility to decode and inspect JWT tokens
Usage: python debug_token.py <token>
"""

import sys
import json
from jose import jwt

def decode_token_unsafe(token):
    """Decode token without verification to inspect claims"""
    try:
        # Decode without verification to see what's inside
        unverified = jwt.get_unverified_claims(token)
        header = jwt.get_unverified_header(token)

        print("=" * 80)
        print("JWT TOKEN ANALYSIS")
        print("=" * 80)

        print("\n📋 HEADER:")
        print(json.dumps(header, indent=2))

        print("\n📋 CLAIMS (Payload):")
        print(json.dumps(unverified, indent=2))

        print("\n🔍 IMPORTANT CLAIMS:")
        print(f"  Issuer (iss):    {unverified.get('iss', 'N/A')}")
        print(f"  Audience (aud):  {unverified.get('aud', 'N/A')}")
        print(f"  Subject (sub):   {unverified.get('sub', 'N/A')}")
        print(f"  Expires (exp):   {unverified.get('exp', 'N/A')}")
        print(f"  Issued At (iat): {unverified.get('iat', 'N/A')}")

        # Check expiration
        import time
        exp = unverified.get('exp')
        if exp:
            current_time = time.time()
            if current_time > exp:
                print(f"\n⚠️  TOKEN IS EXPIRED! (expired {int(current_time - exp)} seconds ago)")
            else:
                print(f"\n✅ Token is valid for {int(exp - current_time)} more seconds")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        print("\nToken might be malformed or invalid.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_token.py <token>")
        print("\nExample:")
        print("  python debug_token.py eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
        sys.exit(1)

    token = sys.argv[1]
    decode_token_unsafe(token)
