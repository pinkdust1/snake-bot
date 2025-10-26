"""
Get XRP address from seed
Use this to find the correct address for your seed
"""

from xrpl.wallet import Wallet

print("="*60)
print("🔑 Get XRP Address from Seed")
print("="*60)

seed = input("\nEnter your seed (starts with 's'): ").strip()

if not seed:
    print("❌ No seed provided")
    exit(1)

if not seed.startswith('s'):
    print("⚠️  Warning: Seed should start with 's'")
    proceed = input("Continue anyway? (yes/no): ")
    if proceed.lower() != 'yes':
        exit(1)

try:
    print("\n🔐 Creating wallet from seed...")
    wallet = Wallet.from_seed(seed)
    
    print("\n" + "="*60)
    print("✅ SUCCESS!")
    print("="*60)
    print(f"\nYour XRP Address: {wallet.classic_address}")
    print(f"\nAdd this to your config.py:")
    print(f'MAIN_WALLET_SECRET = "{seed}"')
    print(f'MAIN_WALLET = "{wallet.classic_address}"')
    print("\n" + "="*60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure your seed is valid!")