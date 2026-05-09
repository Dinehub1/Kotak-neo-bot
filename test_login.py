import logging
from broker import KotakBroker

logging.basicConfig(level=logging.INFO)

def test():
    broker = KotakBroker()
    if broker.login():
        print("✅ SUCCESS: Auto-login with TOTP secret worked perfectly!")
    else:
        print("❌ FAILED: Auto-login failed.")

if __name__ == "__main__":
    test()
