import asyncio
import random
from datetime import datetime, timedelta
import requests
import io
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import qrcode

# XRP Ledger imports
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops
from xrpl.models.requests import AccountInfo
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.transaction import submit_and_wait as async_submit_and_wait
from xrpl.asyncio.clients import AsyncJsonRpcClient


import config
from database import Database

# Initialize bot and database
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Initialize XRP wallet (sync - only for address)
main_wallet = Wallet.from_seed(config.MAIN_WALLET_SECRET)

# Update config with actual wallet address if mismatch
if main_wallet.classic_address != config.MAIN_WALLET:
    print(f"⚠️ WARNING: Updating MAIN_WALLET in config to match seed")
    print(f"  Old: {config.MAIN_WALLET}")
    print(f"  New: {main_wallet.classic_address}")
    config.MAIN_WALLET = main_wallet.classic_address
else:
    print(f"✅ Wallet address matches: {main_wallet.classic_address}")

# Store active captcha sessions
captcha_sessions = {}
# Store XAMAN payload sessions
xaman_sessions = {}

def create_main_keyboard(authorized=False):
    """Create main keyboard based on authorization status"""
    if not authorized:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Register", callback_data="register")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💧 Claim 0.0001–0.01 XRP", callback_data="claim")],
            [InlineKeyboardButton(text="🏆 Try to Win 1 XRP", callback_data="lottery")],
            [InlineKeyboardButton(text="⏳ Next Claim in: --:--", callback_data="timer")],
            [InlineKeyboardButton(text="👥 Referrals & Your Link", callback_data="referrals")]
        ])
    return keyboard

def generate_xaman_payload(user_address=None):
    """Generate XAMAN sign-in request"""
    headers = {
        "X-API-Key": config.XAMAN_API_KEY,
        "X-API-Secret": config.XAMAN_API_SECRET,
        "Content-Type": "application/json"
    }
    
    payload = {
        "txjson": {
            "TransactionType": "SignIn"
        }
    }
    
    try:
        response = requests.post(
            f"{config.XAMAN_API_URL}/payload",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error creating XAMAN payload: {e}")
        return None

def check_xaman_payload_status(payload_uuid):
    """Check XAMAN payload status"""
    headers = {
        "X-API-Key": config.XAMAN_API_KEY,
        "X-API-Secret": config.XAMAN_API_SECRET
    }
    
    try:
        response = requests.get(
            f"{config.XAMAN_API_URL}/payload/{payload_uuid}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error checking payload status: {e}")
        return None

# Change this function to be asynchronous
async def check_wallet_activation(address):
    """Check if XRP wallet is activated using async xrpl-py"""
    try:
        account_info = AccountInfo(
            account=address,
            ledger_index="validated"
        )
        # Use async client for the request
        async_client = AsyncJsonRpcClient(config.JSON_RPC_URL)
        response = await async_client.request(account_info)
        
        if response.is_successful():
            return True
        return False
    except Exception as e:
        print(f"Error checking wallet activation: {e}")
        return False

async def send_xrp_transaction(destination, amount):
    """
    Send XRP transaction using async xrpl-py
    """
    try:
        print(f"💰 Sending {amount} XRP to {destination}")
        
        # Validate destination address
        if not destination or not destination.startswith('r'):
            return {
                'success': False,
                'hash': None,
                'error': 'Invalid destination address',
                'validated': False
            }
        
        # Create payment transaction
        payment = Payment(
            account=main_wallet.classic_address,
            amount=xrp_to_drops(amount),
            destination=destination,
        )
        
        print(f"📤 Submitting transaction from {main_wallet.classic_address}...")
        
        # Use async client and async submission
        async_client = AsyncJsonRpcClient(config.JSON_RPC_URL)
        
        # Submit and wait for validation (async)
        response = await async_submit_and_wait(payment, async_client, main_wallet)
        
        # Check if transaction was successful
        if response.is_successful():
            tx_hash = response.result.get('hash', 'unknown')
            print(f"✅ Transaction successful! Hash: {tx_hash}")
            
            return {
                'success': True,
                'hash': tx_hash,
                'error': None,
                'validated': True
            }
        else:
            error_msg = response.result.get('engine_result_message', 'Transaction failed')
            print(f"❌ Transaction failed: {error_msg}")
            
            return {
                'success': False,
                'hash': None,
                'error': error_msg,
                'validated': False
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error sending XRP: {error_msg}")
        
        return {
            'success': False,
            'hash': None,
            'error': error_msg,
            'validated': False
        }
        
def check_wallet_balance():
    """Check main wallet balance"""
    try:
        account_info = AccountInfo(
            account=main_wallet.classic_address,
            ledger_index="validated"
        )
        response = xrp_client.request(account_info)
        
        if response.is_successful():
            balance_drops = int(response.result['account_data']['Balance'])
            balance_xrp = balance_drops / 1000000
            return {
                'success': True,
                'balance': balance_xrp,
                'address': main_wallet.classic_address
            }
        else:
            return {
                'success': False,
                'error': 'Failed to get account info'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def generate_qr_code(data):
    """Generate QR code image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

def format_time_remaining(seconds):
    """Format seconds to 'XX min XX sec'"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes} min {secs:02d} sec"

def get_time_until_next_claim(telegram_id):
    """Calculate time until next claim is available"""
    last_claim = db.get_last_claim_time(telegram_id)
    if not last_claim:
        return 0
    
    next_claim = last_claim + timedelta(seconds=config.CLAIM_COOLDOWN)
    now = datetime.now()
    
    if now >= next_claim:
        return 0
    
    remaining = (next_claim - now).total_seconds()
    return int(remaining)

def get_time_until_next_lottery(telegram_id):
    """Calculate time until next lottery is available"""
    last_lottery = db.get_last_lottery_time(telegram_id)
    if not last_lottery:
        return 0
    
    next_lottery = last_lottery + timedelta(seconds=config.LOTTERY_COOLDOWN)
    now = datetime.now()
    
    if now >= next_lottery:
        return 0
    
    remaining = (next_lottery - now).total_seconds()
    return int(remaining)

def generate_captcha():
    """Generate simple math captcha"""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    correct_answer = num1 + num2
    
    # Generate wrong answers
    answers = [correct_answer]
    while len(answers) < 3:
        wrong = correct_answer + random.randint(-5, 5)
        if wrong > 0 and wrong not in answers:
            answers.append(wrong)
    
    random.shuffle(answers)
    
    return {
        'question': f"{num1} + {num2} = ???",
        'correct': correct_answer,
        'options': answers
    }

async def check_subscription(user_id):
    """Check if user is subscribed to all required channels"""
    if not config.CHECK_SUBSCRIPTION:
        print(f"Subscription check disabled for user {user_id}")
        return True
    
    channels_to_check = [
        config.CHANNEL_USERNAME,
        config.CHANNEL_USERNAME_2
    ]
    
    for channel in channels_to_check:
        try:
            print(f"Checking subscription for user {user_id} in @{channel}")
            member = await bot.get_chat_member(f"@{channel}", user_id)
            print(f"User {user_id} status in @{channel}: {member.status}")
            is_subscribed = member.status in ['member', 'administrator', 'creator']
            
            if not is_subscribed:
                print(f"User {user_id} is NOT subscribed to @{channel}")
                return False
                
        except TelegramBadRequest as e:
            print(f"TelegramBadRequest checking subscription for {user_id} in @{channel}: {e}")
            # If bot is not admin in channel or channel not found, return True to not block users
            continue
        except Exception as e:
            print(f"Error checking subscription for {user_id} in @{channel}: {e}")
            # On error, allow access to not block legitimate users
            continue
    
    print(f"User {user_id} is subscribed to all required channels")
    return True

async def require_subscription(callback: types.CallbackQuery):
    """Check subscription and show message if not subscribed"""
    is_subscribed = await check_subscription(callback.from_user.id)
    
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Subscribe to Snake666wrb", url=config.CHANNEL_URL)],
            [InlineKeyboardButton(text="📢 Subscribe to shakertest", url=config.CHANNEL_URL_2)],
            [InlineKeyboardButton(text="✅ I Subscribed", callback_data="check_subscription")]
        ])
        
        subscription_message = (
            "📢 To use this bot, you need to subscribe to our channels:\n\n"
            f"1. @{config.CHANNEL_USERNAME}\n"
            f"2. @{config.CHANNEL_USERNAME_2}\n\n"
            "After subscribing, click the button below to verify."
        )
        
        await callback.message.answer(
            subscription_message,
            reply_markup=keyboard
        )
        return False
    
    db.update_subscription_status(callback.from_user.id, True)
    return True

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    telegram_id = message.from_user.id
    username = message.from_user.username or "User"
    
    # Check for referral link
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
            if referrer_id == telegram_id:
                referrer_id = None  # Can't refer yourself
        except ValueError:
            pass
    
    if not db.user_exists(telegram_id):
        db.add_user(telegram_id, username, referrer_id)
    
    user = db.get_user(telegram_id)
    is_authorized = user['is_authorized'] == 1
    
    welcome_text = config.WELCOME_MESSAGE.format(username=username)
    keyboard = create_main_keyboard(authorized=is_authorized)
    
    await message.answer(welcome_text, reply_markup=keyboard)

@dp.message(Command("login"))
async def cmd_login(message: types.Message):
    """Handle /login command"""
    await handle_xaman_login(message.from_user.id, message.chat.id)

async def handle_xaman_login(user_id, chat_id):
    """Handle XAMAN wallet login process"""
    payload_data = generate_xaman_payload()
    
    if not payload_data:
        await bot.send_message(chat_id, config.TRANSACTION_ERROR)
        return
    
    payload_uuid = payload_data['uuid']
    xaman_url = payload_data['next']['always']
    
    # Generate QR code
    qr_image = generate_qr_code(xaman_url)
    
    await bot.send_photo(
        chat_id,
        photo=types.BufferedInputFile(qr_image.read(), filename="qr.png"),
        caption=f"{config.XAMAN_CONNECT_MESSAGE}\n\n{xaman_url}"
    )
    
    # Wait for user to sign in (poll for status)
    for _ in range(60):  # Wait up to 5 minutes
        await asyncio.sleep(5)
        status = check_xaman_payload_status(payload_uuid)
        
        if status and status['meta']['signed']:
            user_address = status['response']['account']
            
            # Check if wallet is activated (async)
            if not await check_wallet_activation(user_address):
                await bot.send_message(
                    chat_id,
                    config.WALLET_NOT_ACTIVATED.format(address=user_address)
                )
                return
            
            # Save wallet address
            db.update_user_wallet(user_id, user_address)
            
            # Send success message with main keyboard
            keyboard = create_main_keyboard(authorized=True)
            await bot.send_message(
                chat_id,
                config.LOGIN_SUCCESS.format(address=user_address),
                reply_markup=keyboard
            )
            return
    
    await bot.send_message(chat_id, config.TRANSACTION_ERROR)

@dp.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: types.CallbackQuery):
    """Handle subscription check button"""
    print(f"User {callback.from_user.id} clicked 'I Subscribed'")
    
    await callback.answer("Checking your subscription...", show_alert=False)
    
    is_subscribed = await check_subscription(callback.from_user.id)
    
    if is_subscribed:
        db.update_subscription_status(callback.from_user.id, True)
        print(f"User {callback.from_user.id} subscription confirmed")
        
        user = db.get_user(callback.from_user.id)
        keyboard = create_main_keyboard(authorized=user['is_authorized'] == 1)
        
        await callback.message.answer(
            "✅ Subscription confirmed! You can now use the bot.",
            reply_markup=keyboard
        )
    else:
        print(f"User {callback.from_user.id} not subscribed to all channels yet")
        
        # Show which channels are missing
        channels_to_check = [config.CHANNEL_USERNAME, config.CHANNEL_USERNAME_2]
        missing_channels = []
        
        for channel in channels_to_check:
            try:
                member = await bot.get_chat_member(f"@{channel}", callback.from_user.id)
                is_subscribed = member.status in ['member', 'administrator', 'creator']
                if not is_subscribed:
                    missing_channels.append(f"@{channel}")
            except Exception as e:
                print(f"Error checking channel {channel}: {e}")
                missing_channels.append(f"@{channel}")
        
        if missing_channels:
            missing_text = "\n".join(missing_channels)
            await callback.answer(
                f"❌ You are not subscribed to:\n{missing_text}\n\nPlease subscribe and try again.",
                show_alert=True
            )
        else:
            await callback.answer(
                "❌ Subscription check failed. Please try again.",
                show_alert=True
            )

@dp.callback_query(F.data == "register")
async def callback_register(callback: types.CallbackQuery):
    """Handle register button"""
    await callback.answer()
    
    # Check subscription first
    if not await require_subscription(callback):
        return
    
    await handle_xaman_login(callback.from_user.id, callback.message.chat.id)

@dp.callback_query(F.data == "claim")
async def callback_claim(callback: types.CallbackQuery):
    """Handle claim button"""
    await callback.answer()
    telegram_id = callback.from_user.id
    
    # Check subscription first
    if not await require_subscription(callback):
        return
    
    user = db.get_user(telegram_id)
    
    if not user or user['is_authorized'] != 1:
        await callback.message.answer("Please login first with /login")
        return
    
    # Check cooldown
    remaining = get_time_until_next_claim(telegram_id)
    
    if remaining > 0:
        time_str = format_time_remaining(remaining)
        message = config.CLAIM_COOLDOWN_MESSAGE.format(
            time=time_str,
            clicks=user['total_clicks'],
            profit=user['total_profit'],
            ref_profit=user['referral_profit']
        )
        await callback.message.answer(message)
        return
    
    # Generate and send captcha
    captcha = generate_captcha()
    captcha_sessions[telegram_id] = {'data': captcha, 'type': 'claim'}
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(opt), callback_data=f"answer_{opt}")]
        for opt in captcha['options']
    ])
    
    await callback.message.answer(
        config.CAPTCHA_MESSAGE.format(question=captcha['question']),
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("answer_"))
async def callback_answer(callback: types.CallbackQuery):
    """Handle captcha answer"""
    await callback.answer()
    telegram_id = callback.from_user.id
    
    if telegram_id not in captcha_sessions:
        await callback.message.answer("Session expired. Please try again.")
        return
    
    # Get and remove session immediately to prevent multiple clicks
    session = captcha_sessions.pop(telegram_id)
    captcha = session['data']
    session_type = session['type']
    user_answer = int(callback.data.split("_")[1])
    
    if user_answer == captcha['correct']:
        # Correct answer
        user = db.get_user(telegram_id)
        
        if session_type == 'claim':
            # Double-check cooldown to ensure no race conditions
            remaining = get_time_until_next_claim(telegram_id)
            if remaining > 0:
                time_str = format_time_remaining(remaining)
                message = config.CLAIM_COOLDOWN_MESSAGE.format(
                    time=time_str,
                    clicks=user['total_clicks'],
                    profit=user['total_profit'],
                    ref_profit=user['referral_profit']
                )
                await callback.message.answer(message)
                return
            
            amount = config.CURRENT_REWARD
            
            # Check if this is first claim from a referred user
            is_first_claim = user['total_clicks'] == 0 and user['referrer_id']
            
            # Send XRP transaction (await async function)
            result = await send_xrp_transaction(user['xrp_address'], amount)
            
            if result['success']:
                # Update database
                db.update_claim(telegram_id, amount)
                db.add_transaction(telegram_id, amount, 'claim', 'success')
                
                # Handle referral bonus
                if user['referrer_id']:
                    referral_bonus = amount * config.REFERRAL_BONUS
                    db.add_referral_profit(user['referrer_id'], referral_bonus)
                    
                    # Send bonus to referrer
                    referrer = db.get_user(user['referrer_id'])
                    if referrer and referrer['xrp_address']:
                        bonus_result = await send_xrp_transaction(referrer['xrp_address'], referral_bonus)
                        if bonus_result['success']:
                            db.add_transaction(user['referrer_id'], referral_bonus, 'referral', 'success')
                
                # Send new user bonus if first claim
                if is_first_claim:
                    bonus_result = await send_xrp_transaction(user['xrp_address'], config.NEW_USER_BONUS)
                    if bonus_result['success']:
                        db.add_transaction(telegram_id, config.NEW_USER_BONUS, 'bonus', 'success')
                        await callback.message.answer(
                            config.NEW_USER_REWARD.format(amount=config.NEW_USER_BONUS)
                        )
                
                await callback.message.answer(
                    config.CLAIM_SUCCESS.format(amount=amount)
                )
            else:
                db.add_transaction(telegram_id, amount, 'claim', 'failed')
                await callback.message.answer(config.TRANSACTION_ERROR)
                
        elif session_type == 'lottery':
            # Double-check lottery cooldown to ensure no race conditions
            remaining = get_time_until_next_lottery(telegram_id)
            if remaining > 0:
                time_str = format_time_remaining(remaining)
                await callback.message.answer(
                    f"⏳ You can try the lottery again in {time_str}"
                )
                return
            
            # Random amount for lottery
            amount = round(random.uniform(config.LOTTERY_MIN, config.LOTTERY_MAX), 6)
            
            # Send XRP transaction (await async function)
            result = await send_xrp_transaction(user['xrp_address'], amount)
            
            if result['success']:
                # Update database
                db.update_lottery(telegram_id, amount)
                db.add_transaction(telegram_id, amount, 'lottery', 'success')
                
                remaining = get_time_until_next_lottery(telegram_id)
                time_str = format_time_remaining(remaining)
                
                await callback.message.answer(
                    config.LOTTERY_PRIZE.format(amount=amount, time=time_str)
                )
            else:
                db.add_transaction(telegram_id, amount, 'lottery', 'failed')
                await callback.message.answer(config.TRANSACTION_ERROR)
    else:
        # Wrong answer - generate new captcha
        await callback.message.answer(config.INCORRECT_ANSWER)
        
        captcha = generate_captcha()
        captcha_sessions[telegram_id] = {'data': captcha, 'type': session_type}
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=str(opt), callback_data=f"answer_{opt}")]
            for opt in captcha['options']
        ])
        
        await callback.message.answer(
            config.CAPTCHA_MESSAGE.format(question=captcha['question']),
            reply_markup=keyboard
        )

@dp.callback_query(F.data == "timer")
async def callback_timer(callback: types.CallbackQuery):
    """Handle timer button"""
    telegram_id = callback.from_user.id
    remaining = get_time_until_next_claim(telegram_id)
    
    if remaining > 0:
        time_str = format_time_remaining(remaining)
        await callback.answer(f"Next claim in: {time_str}", show_alert=True)
    else:
        await callback.answer("You can claim now!", show_alert=True)

@dp.callback_query(F.data == "lottery")
async def callback_lottery(callback: types.CallbackQuery):
    """Handle lottery button"""
    await callback.answer()
    telegram_id = callback.from_user.id
    
    # Check subscription first
    if not await require_subscription(callback):
        return
    
    user = db.get_user(telegram_id)
    
    if not user or user['is_authorized'] != 1:
        await callback.message.answer("Please login first with /login")
        return
    
    # Check cooldown
    remaining = get_time_until_next_lottery(telegram_id)
    
    if remaining > 0:
        time_str = format_time_remaining(remaining)
        await callback.message.answer(
            f"⏳ You can try the lottery again in {time_str}"
        )
        return
    
    # Generate and send captcha
    captcha = generate_captcha()
    captcha_sessions[telegram_id] = {'data': captcha, 'type': 'lottery'}
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(opt), callback_data=f"answer_{opt}")]
        for opt in captcha['options']
    ])
    
    await callback.message.answer(
        config.CAPTCHA_MESSAGE.format(question=captcha['question']),
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "referrals")
async def callback_referrals(callback: types.CallbackQuery):
    """Handle referrals button"""
    await callback.answer()
    telegram_id = callback.from_user.id
    
    # Check subscription first
    if not await require_subscription(callback):
        return
    
    user = db.get_user(telegram_id)
    
    if not user or user['is_authorized'] != 1:
        await callback.message.answer("Please login first with /login")
        return
    
    # Get referral count
    referral_count = db.get_referral_count(telegram_id)
    
    # Generate referral link
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={telegram_id}"
    
    message = config.REFERRAL_INFO.format(
        count=referral_count,
        link=referral_link
    )
    
    await callback.message.answer(message)

async def main():
    """Start the bot"""
    try:
        print("="*50)
        print("🐍 SNAKE FAUCET BOT STARTING")
        print("="*50)
        
        print("\n📋 Configuration:")
        print(f"  Bot token: {config.BOT_TOKEN[:10]}...")
        print(f"  Database: {config.DATABASE_NAME}")
        print(f"  Main wallet: {main_wallet.classic_address}")
        print(f"  RPC URL: {config.JSON_RPC_URL}")
        print(f"  Check subscription: {config.CHECK_SUBSCRIPTION}")
        if config.CHECK_SUBSCRIPTION:
            print(f"  Channel 1: @{config.CHANNEL_USERNAME}")
            print(f"  Channel 2: @{config.CHANNEL_USERNAME_2}")
        
        # Test bot token
        print("\n🤖 Testing bot connection...")
        bot_info = await bot.get_me()
        print(f"  Bot: @{bot_info.username} ({bot_info.first_name})")
        
        print("\n" + "="*50)
        print("✅ BOT STARTED SUCCESSFULLY!")
        print("="*50)
        print("\n💡 Bot is running. Press Ctrl+C to stop\n")
        
        await dp.start_polling(bot)
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        print("👋 BOT STOPPED BY USER")
        print("="*50)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()