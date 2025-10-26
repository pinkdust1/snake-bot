"""
Admin utilities for Snake_bot
Provides functions for monitoring and managing the bot
"""

import sqlite3
from datetime import datetime, timedelta
from database import Database
import config

db = Database()

def get_bot_statistics():
    """Get overall bot statistics"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Authorized users
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_authorized = 1')
    authorized_users = cursor.fetchone()[0]
    
    # Subscribed users
    cursor.execute('SELECT COUNT(*) FROM users WHERE subscribed = 1')
    subscribed_users = cursor.fetchone()[0]
    
    # Total transactions
    cursor.execute('SELECT COUNT(*), SUM(amount) FROM transactions WHERE status = "success"')
    trans_data = cursor.fetchone()
    total_transactions = trans_data[0] or 0
    total_amount = trans_data[1] or 0.0
    
    # Failed transactions
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE status = "failed"')
    failed_transactions = cursor.fetchone()[0]
    
    # Transactions by type
    cursor.execute('''
        SELECT type, COUNT(*), SUM(amount) 
        FROM transactions 
        WHERE status = "success" 
        GROUP BY type
    ''')
    trans_by_type = cursor.fetchall()
    
    # New users last 24h
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    cursor.execute('SELECT COUNT(*) FROM users WHERE registration_date > ?', (yesterday,))
    new_users_24h = cursor.fetchone()[0]
    
    # Active users last 24h (had any claim/lottery)
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) 
        FROM transactions 
        WHERE timestamp > ?
    ''', (yesterday,))
    active_users_24h = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'authorized_users': authorized_users,
        'subscribed_users': subscribed_users,
        'total_transactions': total_transactions,
        'total_amount_sent': total_amount,
        'failed_transactions': failed_transactions,
        'transactions_by_type': trans_by_type,
        'new_users_24h': new_users_24h,
        'active_users_24h': active_users_24h
    }

def get_top_users(limit=10, sort_by='total_profit'):
    """Get top users by various metrics"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    valid_columns = ['total_profit', 'total_clicks', 'referral_profit']
    if sort_by not in valid_columns:
        sort_by = 'total_profit'
    
    cursor.execute(f'''
        SELECT telegram_id, username, xrp_address, 
               total_clicks, total_profit, referral_profit
        FROM users
        WHERE is_authorized = 1
        ORDER BY {sort_by} DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    users = []
    for row in results:
        users.append({
            'telegram_id': row[0],
            'username': row[1],
            'xrp_address': row[2],
            'total_clicks': row[3],
            'total_profit': row[4],
            'referral_profit': row[5]
        })
    
    return users

def get_top_referrers(limit=10):
    """Get users with most referrals"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.telegram_id, u.username, u.referral_profit,
               COUNT(r.telegram_id) as referral_count
        FROM users u
        LEFT JOIN users r ON u.telegram_id = r.referrer_id
        WHERE u.is_authorized = 1
        GROUP BY u.telegram_id
        HAVING referral_count > 0
        ORDER BY referral_count DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    referrers = []
    for row in results:
        referrers.append({
            'telegram_id': row[0],
            'username': row[1],
            'referral_profit': row[2],
            'referral_count': row[3]
        })
    
    return referrers

def get_recent_transactions(limit=20, status='success'):
    """Get recent transactions"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.id, t.user_id, u.username, t.amount, t.type, t.timestamp, t.status
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.telegram_id
        WHERE t.status = ?
        ORDER BY t.timestamp DESC
        LIMIT ?
    ''', (status, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    transactions = []
    for row in results:
        transactions.append({
            'id': row[0],
            'user_id': row[1],
            'username': row[2],
            'amount': row[3],
            'type': row[4],
            'timestamp': row[5],
            'status': row[6]
        })
    
    return transactions

def get_user_details(telegram_id):
    """Get detailed information about a user"""
    user = db.get_user(telegram_id)
    if not user:
        return None
    
    # Get referral count
    referral_count = db.get_referral_count(telegram_id)
    
    # Get user's transactions
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, COUNT(*), SUM(amount)
        FROM transactions
        WHERE user_id = ? AND status = "success"
        GROUP BY type
    ''', (telegram_id,))
    
    trans_by_type = cursor.fetchall()
    
    # Get referrer info if exists
    referrer_info = None
    if user['referrer_id']:
        referrer_info = db.get_user(user['referrer_id'])
    
    conn.close()
    
    return {
        'user': user,
        'referral_count': referral_count,
        'transactions_by_type': trans_by_type,
        'referrer': referrer_info
    }

def export_statistics_to_text():
    """Export bot statistics to formatted text"""
    stats = get_bot_statistics()
    
    text = "📊 SNAKE BOT STATISTICS\n"
    text += "=" * 40 + "\n\n"
    
    text += "👥 USERS\n"
    text += f"Total Users: {stats['total_users']}\n"
    text += f"Authorized Users: {stats['authorized_users']}\n"
    text += f"Subscribed Users: {stats['subscribed_users']}\n"
    text += f"New Users (24h): {stats['new_users_24h']}\n"
    text += f"Active Users (24h): {stats['active_users_24h']}\n\n"
    
    text += "💰 TRANSACTIONS\n"
    text += f"Total Transactions: {stats['total_transactions']}\n"
    text += f"Failed Transactions: {stats['failed_transactions']}\n"
    text += f"Total XRP Sent: {stats['total_amount_sent']:.6f} XRP\n\n"
    
    text += "📈 BY TYPE\n"
    for trans_type, count, amount in stats['transactions_by_type']:
        text += f"{trans_type.capitalize()}: {count} txs, {amount:.6f} XRP\n"
    
    text += "\n" + "=" * 40 + "\n"
    text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return text

def check_wallet_balance():
    """Check main wallet balance (requires running event loop)"""
    import asyncio
    from xrpl.asyncio.clients import AsyncJsonRpcClient
    from xrpl.models.requests import AccountInfo
    from xrpl.wallet import Wallet
    
    async def _check():
        wallet = Wallet.from_seed(config.MAIN_WALLET_SECRET)
        async with AsyncJsonRpcClient(config.JSON_RPC_URL) as client:
            account_info = AccountInfo(
                account=wallet.classic_address,
                ledger_index="validated"
            )
            response = await client.request(account_info)
            
            if response.is_successful():
                balance_drops = int(response.result['account_data']['Balance'])
                balance = float(balance_drops) / 1000000
                return {
                    'success': True,
                    'balance': balance,
                    'address': wallet.classic_address
                }
            return {'success': False, 'error': 'Invalid response'}
    
    try:
        # Try to get existing event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an event loop, create a task
            return asyncio.create_task(_check())
        except RuntimeError:
            # No running loop, create new one
            return asyncio.run(_check())
    except Exception as e:
        return {'success': False, 'error': str(e)}

def cleanup_old_sessions():
    """Clean up old captcha sessions (call periodically)"""
    # This would need to be implemented in main.py
    # to clean up the captcha_sessions dictionary
    pass

def generate_report(report_type='daily'):
    """Generate various reports"""
    if report_type == 'daily':
        period = timedelta(days=1)
    elif report_type == 'weekly':
        period = timedelta(days=7)
    elif report_type == 'monthly':
        period = timedelta(days=30)
    else:
        period = timedelta(days=1)
    
    start_date = (datetime.now() - period).isoformat()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # New users in period
    cursor.execute('SELECT COUNT(*) FROM users WHERE registration_date > ?', (start_date,))
    new_users = cursor.fetchone()[0]
    
    # Transactions in period
    cursor.execute('''
        SELECT COUNT(*), SUM(amount)
        FROM transactions
        WHERE timestamp > ? AND status = "success"
    ''', (start_date,))
    trans_data = cursor.fetchone()
    
    # Active users in period
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id)
        FROM transactions
        WHERE timestamp > ?
    ''', (start_date,))
    active_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'period': report_type,
        'new_users': new_users,
        'active_users': active_users,
        'total_transactions': trans_data[0] or 0,
        'total_amount': trans_data[1] or 0.0
    }

if __name__ == "__main__":
    # Example usage
    print(export_statistics_to_text())
    print("\n" + "=" * 40 + "\n")
    
    print("🏆 TOP 10 USERS BY PROFIT:")
    top_users = get_top_users(10, 'total_profit')
    for i, user in enumerate(top_users, 1):
        print(f"{i}. @{user['username']}: {user['total_profit']:.6f} XRP")
    
    print("\n" + "=" * 40 + "\n")
    
    print("👥 TOP 10 REFERRERS:")
    top_refs = get_top_referrers(10)
    for i, ref in enumerate(top_refs, 1):
        print(f"{i}. @{ref['username']}: {ref['referral_count']} referrals, {ref['referral_profit']:.6f} XRP")
    
    print("\n" + "=" * 40 + "\n")
    
    balance = check_wallet_balance()
    if balance['success']:
        print(f"💰 MAIN WALLET BALANCE: {balance['balance']:.6f} XRP")
    else:
        print(f"❌ Error checking balance: {balance['error']}")