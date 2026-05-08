import os
from dotenv import load_dotenv
from neo_api_client import NeoAPI

# Load environment variables from .env file
load_dotenv()

# Fetch credentials from environment
CONSUMER_KEY = os.getenv("NEO_CONSUMER_KEY")
MOBILE_NUMBER = os.getenv("NEO_MOBILE_NUMBER")
UCC = os.getenv("NEO_UCC")
MPIN = os.getenv("NEO_MPIN")

def test_login():
    print("Initializing NeoAPI Client...")
    # Initialize the client
    client = NeoAPI(
        environment='prod', 
        access_token=None, 
        neo_fin_key=None, 
        consumer_key=CONSUMER_KEY
    )
    
    # Read TOTP from standard input since it changes every 30 seconds
    totp_code = input(f"\n🔑 Enter current 6-digit TOTP code for {UCC}: ").strip()
    
    print("\nStarting TOTP Login...")
    try:
        # Step 1: Login with TOTP
        login_resp = client.totp_login(
            mobile_number=MOBILE_NUMBER, 
            ucc=UCC, 
            totp=totp_code
        )
        print("✅ TOTP Login Response:", login_resp)
        if type(login_resp) is dict and ('error' in login_resp or 'Error Message' in login_resp):
            raise Exception("TOTP Login failed based on response.")

        # Step 2: Validate MPIN
        print("\nValidating MPIN...")
        validate_resp = client.totp_validate(mpin=MPIN)
        print("✅ MPIN Validation Response:", validate_resp)
        if type(validate_resp) is dict and ('error' in validate_resp or 'Error Message' in validate_resp):
            raise Exception("MPIN Validation failed based on response.")
        
        # Step 3: Test a simple API call to verify we are authenticated
        print("\nFetching account limits to verify connection...")
        limits = client.limits()
        print("✅ Limits Response:")
        print(limits)
        if type(limits) is dict and ('error' in limits or 'Error Message' in limits):
            raise Exception("Failed to fetch limits. You may not be fully authenticated.")
        
        print("\n🎉 Successfully authenticated and verified connection! You are ready to trade.")
        
    except Exception as e:
        print("\n❌ Login or verification failed!")
        print("Error details:", str(e))

if __name__ == "__main__":
    # Check if all required environment variables are present
    if not all([CONSUMER_KEY, MOBILE_NUMBER, UCC, MPIN]):
        print("❌ Missing credentials! Please ensure your .env file is set up correctly with:")
        print("NEO_CONSUMER_KEY, NEO_MOBILE_NUMBER, NEO_UCC, and NEO_MPIN")
    else:
        test_login()
