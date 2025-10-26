"""
Quick test script for Snake_bot XRP functionality
Run this before starting the bot to verify everything works
"""

import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountInfo
import config

async def test_wallet_and_balance():
    """Test wallet creation and balance check"""
    print("="*60)
    print("🧪 QUICK XRP FUNCTIONALITY TEST")
    print("="*60)
    
    # Test 1: Create wallet from seed
    print("\n1️⃣  Testing wallet creation from seed...")
    try:
        wallet = Wallet.from_seed(config.MAIN_WALLET_SECRET)
        print(f"   ✅ Wallet created")
        print(f"   Address: {wallet.classic_address}")
        
        if wallet.classic_address == config.MAIN_WALLET:
            print(f"   ✅ Address matches config")
        else:
            print(f"   ⚠️  Address mismatch!")
            print(f"      Config: {config.MAIN_WALLET}")
            print(f"      Actual: {wallet.classic_address}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Connect to RPC node
    print(f"\n2️⃣  Testing connection to {config.JSON_RPC_URL}...")
    try:
        async with AsyncJsonRpcClient(config.JSON_RPC_URL) as client:
            print(f"   ✅ Connected to RPC node")
            
            # Test 3: Check balance
            print(f"\n3️⃣  Checking wallet balance...")
            account_info = AccountInfo(
                account=wallet.classic_address,
                ledger_index="validated"
            )
            response = await client.request(account_info)
            
            if response.is_successful():
                balance_drops = int(response.result['account_data']['Balance'])
                balance_xrp = balance_drops / 1000000
                print(f"   ✅ Balance retrieved")
                print(f"   Balance: {balance_xrp:.6f} XRP")
                
                if balance_xrp < 0.01:
                    print(f"   ⚠️  Balance very low! Bot needs XRP to send transactions")
                elif balance_xrp < 1:
                    print(f"   ⚠️  Balance low. Consider adding more XRP")
                else:
                    print(f"   ✅ Balance sufficient")
                
                return True
            else:
                print(f"   ❌ Failed to get balance")
                print(f"   Response: {response.result}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def test_wallet_activation(test_address):
    """Test checking if a wallet is activated"""
    print(f"\n4️⃣  Testing wallet activation check...")
    print(f"   Test address: {test_address}")
    
    try:
        async with AsyncJsonRpcClient(config.JSON_RPC_URL) as client:
            account_info = AccountInfo(
                account=test_address,
                ledger_index="validated"
            )
            response = await client.request(account_info)
            
            if response.is_successful():
                print(f"   ✅ Wallet is activated")
                return True
            else:
                print(f"   ⚠️  Wallet not activated or doesn't exist")
                return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def main():
    """Run all tests"""
    print("\n")
    
    # Main tests
    success = await test_wallet_and_balance()
    
    # Test activation check with a known address
    if success:
        await test_wallet_activation(config.MAIN_WALLET)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("\nYou can now start the bot:")
        print("  python main.py")
    else:
        print("❌ TESTS FAILED!")
        print("\nPlease fix the errors above before starting the bot")
    print("="*60)
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()