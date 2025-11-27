"""
API handler with security vulnerabilities and bugs
Test file for Claude code review
"""
import pickle
import hashlib
import random


class UserAPI:
    """User API handler with security issues"""

    def __init__(self):
        self.users = {}
        self.admin_token = "admin123"  # Hardcoded secret!

    def authenticate(self, username, password):
        """Insecure authentication - stores plaintext passwords"""
        if username in self.users and self.users[username] == password:
            return True
        return False

    def load_user_data(self, serialized_data):
        """CRITICAL: Unsafe deserialization - pickle vulnerability"""
        user_data = pickle.loads(serialized_data)
        return user_data

    def generate_session_token(self):
        """Weak random token generation"""
        return str(random.randint(1000, 9999))  # Predictable!

    def hash_password(self, password):
        """Insecure hashing - MD5 is broken"""
        return hashlib.md5(password.encode()).hexdigest()

    def get_user_by_id(self, user_id):
        """Race condition - missing thread safety"""
        if user_id in self.users:
            user = self.users[user_id]
            # Simulate delay where race can occur
            import time
            time.sleep(0.1)
            return user
        return None

    def validate_email(self, email):
        """Missing input validation"""
        # No validation at all - accepts anything
        return email


def process_payment(amount, card_number):
    """Logs sensitive payment data"""
    print(f"Processing payment: {amount} with card {card_number}")  # PCI violation!
    return True


def create_backup(data):
    """Creates unencrypted backup with sensitive data"""
    with open('backup.txt', 'w') as f:
        f.write(str(data))  # No encryption!