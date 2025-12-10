"""
Configuration Verification Script
Checks if all Logto configurations are correct
"""

import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_backend_env():
    """Check backend .env configuration"""
    print("🔍 Checking Backend Configuration...")
    print("=" * 80)

    backend_env = Path(__file__).parent / "backend" / ".env"

    if not backend_env.exists():
        print("❌ backend/.env file not found!")
        return False

    required_vars = {
        'LOGTO_ENDPOINT': None,
        'LOGTO_APP_ID': None,
        'LOGTO_APP_SECRET': None,
        'LOGTO_AUDIENCE': None
    }

    with open(backend_env, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key in required_vars:
                        required_vars[key] = value

    all_ok = True
    for key, value in required_vars.items():
        if value:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: NOT SET")
            all_ok = False

    # Check specific values
    if required_vars.get('LOGTO_AUDIENCE'):
        audience = required_vars['LOGTO_AUDIENCE']
        if audience.endswith('/api'):
            print(f"\n⚠️  WARNING: LOGTO_AUDIENCE should be 'http://localhost:8000' not '{audience}'")
            print("   The '/api' suffix should NOT be included!")
            all_ok = False
        elif audience == 'http://localhost:8000':
            print(f"\n✅ LOGTO_AUDIENCE is correctly set")
        else:
            print(f"\n⚠️  LOGTO_AUDIENCE is '{audience}' (expected 'http://localhost:8000')")

    return all_ok

def check_frontend_env():
    """Check frontend .env configuration"""
    print("\n🔍 Checking Frontend Configuration...")
    print("=" * 80)

    frontend_env = Path(__file__).parent / "frontend" / ".env"

    if not frontend_env.exists():
        print("❌ frontend/.env file not found!")
        return False

    required_vars = {
        'VITE_LOGTO_ENDPOINT': None,
        'VITE_LOGTO_APP_ID': None,
        'VITE_LOGTO_REDIRECT_URI': None,
        'VITE_LOGTO_POST_LOGOUT_REDIRECT_URI': None,
        'VITE_API_RESOURCE': None
    }

    with open(frontend_env, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key in required_vars:
                        required_vars[key] = value

    all_ok = True
    for key, value in required_vars.items():
        if value:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: NOT SET")
            all_ok = False

    # Check specific values
    print("\n🔍 Validating specific values...")

    api_resource = required_vars.get('VITE_API_RESOURCE')
    if api_resource:
        if api_resource.endswith('/api'):
            print(f"❌ VITE_API_RESOURCE should be 'http://localhost:8000' not '{api_resource}'")
            print("   The '/api' suffix should NOT be included!")
            all_ok = False
        elif api_resource == 'http://localhost:8000':
            print(f"✅ VITE_API_RESOURCE is correctly set")

    redirect_uri = required_vars.get('VITE_LOGTO_REDIRECT_URI')
    if redirect_uri and redirect_uri != 'http://localhost:8000/callback':
        print(f"⚠️  VITE_LOGTO_REDIRECT_URI is '{redirect_uri}'")
        print("   Expected: 'http://localhost:8000/callback'")

    post_logout_uri = required_vars.get('VITE_LOGTO_POST_LOGOUT_REDIRECT_URI')
    if post_logout_uri:
        if 'logto.fary.chat' in post_logout_uri:
            print(f"❌ VITE_LOGTO_POST_LOGOUT_REDIRECT_URI should be 'http://localhost:8000'")
            print(f"   Current value: {post_logout_uri}")
            all_ok = False
        elif post_logout_uri == 'http://localhost:8000':
            print(f"✅ VITE_LOGTO_POST_LOGOUT_REDIRECT_URI is correctly set")

    return all_ok

def check_audience_match():
    """Check if backend and frontend audience match"""
    print("\n🔍 Checking Audience Consistency...")
    print("=" * 80)

    backend_env = Path(__file__).parent / "backend" / ".env"
    frontend_env = Path(__file__).parent / "frontend" / ".env"

    backend_audience = None
    frontend_resource = None

    with open(backend_env, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('LOGTO_AUDIENCE='):
                backend_audience = line.split('=', 1)[1].strip()

    with open(frontend_env, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('VITE_API_RESOURCE='):
                frontend_resource = line.split('=', 1)[1].strip()

    if backend_audience and frontend_resource:
        if backend_audience == frontend_resource:
            print(f"✅ Backend LOGTO_AUDIENCE and Frontend VITE_API_RESOURCE MATCH")
            print(f"   Both are: {backend_audience}")
            return True
        else:
            print(f"❌ MISMATCH DETECTED!")
            print(f"   Backend LOGTO_AUDIENCE:      {backend_audience}")
            print(f"   Frontend VITE_API_RESOURCE:  {frontend_resource}")
            print(f"\n   These MUST be identical!")
            return False
    else:
        print("❌ Could not read one or both configurations")
        return False

def main():
    print("\n" + "=" * 80)
    print("LOGTO CONFIGURATION VERIFICATION")
    print("=" * 80 + "\n")

    backend_ok = check_backend_env()
    frontend_ok = check_frontend_env()
    audience_ok = check_audience_match()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if backend_ok and frontend_ok and audience_ok:
        print("✅ All configurations are correct!")
        print("\n📝 Next steps:")
        print("   1. Restart the backend server: cd backend && python main.py")
        print("   2. Clear browser cache and re-login")
        print("   3. Check Logto Console:")
        print("      - API Resource exists with identifier: http://localhost:8000")
        print("      - Frontend app (ro4uk4fd2czd7cyx3wcbm) is linked to this API Resource")
        return 0
    else:
        print("❌ Configuration issues found!")
        print("\n📝 Please fix the issues above and run this script again.")
        print("   After fixing, you need to:")
        print("   1. Restart the backend server")
        print("   2. Rebuild the frontend: cd frontend && npm run build")
        print("   3. Clear browser cache and re-login")
        return 1

if __name__ == "__main__":
    sys.exit(main())
