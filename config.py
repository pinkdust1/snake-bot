# Configuration file for Snake_bot

# Telegram Bot
BOT_TOKEN = "8482763885:AAEAeuIBkacJp2h89Ule7QtMxV3_hD4SCLQ"

# XAMAN API (for wallet connection only)
XAMAN_API_KEY = "96cf825f-ea1f-4b8c-87be-361776fef2ae"
XAMAN_API_SECRET = "43381612-7230-4ac8-9097-89c497bde295"
XAMAN_API_URL = "https://xumm.app/api/v1/platform"

# XRP Settings
MAIN_WALLET_SECRET = "sEd7ArkaAzAPkFWstvKc8MNnN8gvpRj"  # Your wallet seed
MAIN_WALLET = "rDsEH84xWaJycg341gzfx2ZMW7KrnBsVsy"  # Address from seed (автоматически определится)
JSON_RPC_URL = "https://s1.ripple.com:51234"

MIN_REWARD = 0.0001
MAX_REWARD = 0.01
CURRENT_REWARD = 0.0001  # Fixed for now

# Lottery Settings
LOTTERY_MIN = 0.001
LOTTERY_MAX = 0.0001

# Referral Settings
REFERRAL_BONUS = 0.00001  # 10% from referral's claim
NEW_USER_BONUS = 0.0001

# Bot Settings
CLAIM_COOLDOWN = 3600  # 1 hour in seconds
LOTTERY_COOLDOWN = 3600  # 1 hour in seconds
DATABASE_NAME = "snake_bot.db"

# Channel Settings
CHANNEL_USERNAME = "shakertest"
CHANNEL_URL = "https://t.me/shakertest"
CHECK_SUBSCRIPTION = True

# Messages
WELCOME_MESSAGE = """👋 Welcome to the Snake Faucet, @{username}!

Claim free XRP every hour or join the lottery to win up to 1 XRP!

How it works:
✔️ Log in via the XAMAN wallet.

💧 Claim 0.0001–0.01 XRP
- Click to receive a random reward from 0.0001 to 0.01 XRP.
- Available once every hour.

🏆 Try to Win 1 XRP
- Join the lottery: a 1 in 50,000 chance to win 1 XRP.
- You can try once every hour.

👥 Referrals & Your Link
- Invite friends with your referral link and earn more XRP!"""

XAMAN_CONNECT_MESSAGE = """🔐 Connect your XAMAN Wallet
Scan the QR code or click the link below to log in."""

WALLET_NOT_ACTIVATED = """Looks like your account {address} is not activated.
Use /login to log in with another account."""

LOGIN_SUCCESS = "✅ Logged in to {address}"

CLAIM_SUCCESS = "💧 Success! You received {amount} XRP to your wallet."

CLAIM_COOLDOWN_MESSAGE = """⏳ Next time you will be able to click only after {time}.
- Total clicks: {clicks}
- Total profit: {profit} XRP
- Referral profit: {ref_profit} XRP"""

CAPTCHA_MESSAGE = """Answer the question to receive a reward

{question}"""

INCORRECT_ANSWER = "❌ Incorrect answer. Try again!"

TRANSACTION_ERROR = "❌ Transaction failed. Please try again later."

SUBSCRIPTION_REQUIRED = """🔔 To use the Snake Faucet, please subscribe to our channel:
{channel_url}

After subscribing, click "✅ I Subscribed" """

LOTTERY_PRIZE = """🎉 Your prize: {amount} XRP
Try your luck again in {time}."""

REFERRAL_INFO = """At the moment, you have invited {count} participants.

📩 Your personal invitation link:
{link}

Get 10% of your referrals' clicks!"""

NEW_USER_REWARD = "🎁 Welcome bonus! You received {amount} XRP as a new user!"