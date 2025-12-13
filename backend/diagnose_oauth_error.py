"""
Diagnose OAuth 400 error by checking Google OAuth service
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_oauth_service():
    """Test the Google OAuth service configuration"""
    print("=" * 60)
    print("Google OAuth Service Diagnostic")
    print("=" * 60)
    
    try:
        from app.services.google_oauth_hr import get_google_oauth_hr_service
        
        service = get_google_oauth_hr_service()
        
        print("\n✅ OAuth service initialized")
        print(f"   Client ID: {service.client_id[:20]}...")
        print(f"   Redirect URI: {service.redirect_uri}")
        
        # Test authorization URL generation
        auth_url = service.get_authorization_url()
        print(f"\n✅ Authorization URL generated")
        print(f"   URL: {auth_url[:100]}...")
        
        # Check if redirect_uri is in the URL
        if service.redirect_uri in auth_url:
            print(f"\n✅ Redirect URI is correctly included in auth URL")
        else:
            print(f"\n❌ Redirect URI NOT found in auth URL")
            print(f"   Expected: {service.redirect_uri}")
        
        print("\n" + "=" * 60)
        print("Common 400 Error Causes:")
        print("=" * 60)
        print("\n1. ❌ Redirect URI not in Google Console")
        print(f"   Add this to Google Console: {service.redirect_uri}")
        print("\n2. ❌ OAuth code expired (10 min limit)")
        print("   Solution: Try fresh login")
        print("\n3. ❌ OAuth code already used")
        print("   Solution: Don't refresh callback page")
        print("\n4. ❌ Client ID/Secret mismatch")
        print("   Solution: Verify credentials in Google Console")
        
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("\n1. Go to: https://console.cloud.google.com/apis/credentials")
        print(f"2. Find OAuth Client: {service.client_id[:20]}...")
        print("3. Click Edit")
        print("4. Verify 'Authorized redirect URIs' includes:")
        print(f"   {service.redirect_uri}")
        print("5. If not, add it and save")
        print("6. Wait 5 minutes")
        print("7. Try fresh Google login")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_oauth_service())
