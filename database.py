import sqlite3
from datetime import datetime
import config

class Database:
    def __init__(self, db_name=config.DATABASE_NAME):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        """Initialize database with users and transactions tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                xrp_address TEXT,
                is_authorized INTEGER DEFAULT 0,
                last_claim_time TEXT,
                last_lottery_time TEXT,
                total_clicks INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0.0,
                referrer_id INTEGER,
                referral_profit REAL DEFAULT 0.0,
                subscribed INTEGER DEFAULT 0,
                registration_date TEXT
            )
        ''')
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                timestamp TEXT,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')
        
        # Check and add missing columns for existing databases
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_lottery_time' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN last_lottery_time TEXT')
            print("Added column: last_lottery_time")
        
        if 'referrer_id' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
            print("Added column: referrer_id")
        
        if 'subscribed' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN subscribed INTEGER DEFAULT 0')
            print("Added column: subscribed")
        
        conn.commit()
        conn.close()
    
    def user_exists(self, telegram_id):
        """Check if user exists in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def add_user(self, telegram_id, username, referrer_id=None):
        """Add new user to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        registration_date = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (telegram_id, username, referrer_id, registration_date)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, username, referrer_id, registration_date))
        
        conn.commit()
        conn.close()
    
    def update_user_wallet(self, telegram_id, xrp_address):
        """Update user's XRP wallet address and authorization status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET xrp_address = ?, is_authorized = 1
            WHERE telegram_id = ?
        ''', (xrp_address, telegram_id))
        
        conn.commit()
        conn.close()
    
    def get_user(self, telegram_id):
        """Get user data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, username, xrp_address, is_authorized, 
                   last_claim_time, last_lottery_time, total_clicks, total_profit,
                   referrer_id, referral_profit, subscribed, registration_date
            FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'telegram_id': result[0],
                'username': result[1],
                'xrp_address': result[2],
                'is_authorized': result[3],
                'last_claim_time': result[4],
                'last_lottery_time': result[5],
                'total_clicks': result[6],
                'total_profit': result[7],
                'referrer_id': result[8],
                'referral_profit': result[9],
                'subscribed': result[10],
                'registration_date': result[11]
            }
        return None
    
    def update_claim(self, telegram_id, amount):
        """Update user's claim data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        claim_time = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE users 
            SET last_claim_time = ?,
                total_clicks = total_clicks + 1,
                total_profit = total_profit + ?
            WHERE telegram_id = ?
        ''', (claim_time, amount, telegram_id))
        
        conn.commit()
        conn.close()
    
    def get_last_claim_time(self, telegram_id):
        """Get user's last claim time"""
        user = self.get_user(telegram_id)
        if user and user['last_claim_time']:
            return datetime.fromisoformat(user['last_claim_time'])
        return None
    
    def get_last_lottery_time(self, telegram_id):
        """Get user's last lottery time"""
        user = self.get_user(telegram_id)
        if user and user['last_lottery_time']:
            return datetime.fromisoformat(user['last_lottery_time'])
        return None
    
    def update_lottery(self, telegram_id, amount):
        """Update user's lottery data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        lottery_time = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE users 
            SET last_lottery_time = ?,
                total_profit = total_profit + ?
            WHERE telegram_id = ?
        ''', (lottery_time, amount, telegram_id))
        
        conn.commit()
        conn.close()
    
    def update_subscription_status(self, telegram_id, subscribed):
        """Update user's subscription status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET subscribed = ?
            WHERE telegram_id = ?
        ''', (1 if subscribed else 0, telegram_id))
        
        conn.commit()
        conn.close()
    
    def add_transaction(self, user_id, amount, trans_type, status):
        """Add transaction to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, timestamp, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, trans_type, timestamp, status))
        
        conn.commit()
        conn.close()
    
    def get_referral_count(self, telegram_id):
        """Get count of user's referrals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM users WHERE referrer_id = ?
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def add_referral_profit(self, telegram_id, amount):
        """Add profit to referrer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET referral_profit = referral_profit + ?,
                total_profit = total_profit + ?
            WHERE telegram_id = ?
        ''', (amount, amount, telegram_id))
        
        conn.commit()
        conn.close()