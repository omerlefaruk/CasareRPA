"""
Validation module with input validation bugs and logic errors
Test file for Claude code review
"""
import re
import json


class UserValidator:
    """User input validator with missing validation"""

    def validate_age(self, age):
        """Missing upper bound check"""
        if age < 0:
            return False
        return True  # Accepts age=999999!

    def validate_email(self, email):
        """Weak regex - accepts invalid emails"""
        return '@' in email  # Too simple! Accepts "a@" or "@b"

    def validate_password(self, password):
        """No complexity requirements"""
        return len(password) > 0  # Accepts "1" as valid password!

    def validate_phone(self, phone):
        """No format validation"""
        return True  # Accepts anything!

    def sanitize_html(self, html):
        """Incomplete XSS protection"""
        return html.replace("<script>", "")  # Only removes exact match!
        # Bypassed by: <Script>, <scr<script>ipt>, etc.


class DataProcessor:
    """Data processing with logic errors"""

    def calculate_discount(self, price, discount_percent):
        """Logic error - can result in negative prices"""
        discount = price * discount_percent / 100
        return price - discount  # No check for discount > 100%!

    def merge_user_data(self, user1, user2):
        """Loses data - last write wins"""
        merged = {}
        merged.update(user1)
        merged.update(user2)  # Silently overwrites user1 data!
        return merged

    def process_batch(self, items):
        """Off-by-one error"""
        results = []
        for i in range(len(items) - 1):  # Skips last item!
            results.append(items[i])
        return results

    def calculate_average(self, numbers):
        """Division by zero not handled"""
        total = sum(numbers)
        return total / len(numbers)  # Crashes on empty list!

    def parse_json_safe(self, json_string):
        """Catches exception but returns None - loses error info"""
        try:
            return json.loads(json_string)
        except:
            return None  # Silent failure - no logging!


class PermissionChecker:
    """Authorization with logic flaws"""

    def __init__(self):
        self.admin_users = ['admin']

    def is_admin(self, username):
        """Case-sensitive comparison - security bypass"""
        return username in self.admin_users  # "Admin" != "admin"

    def can_delete_user(self, actor, target):
        """Missing check - users can delete themselves"""
        if self.is_admin(actor):
            return True
        # Should check if actor == target!
        return False

    def has_permission(self, user, resource, action):
        """Always returns True - broken authorization!"""
        # TODO: Implement permission check
        return True  # CRITICAL BUG!


def process_payment_amount(amount_str):
    """Type conversion without validation"""
    amount = float(amount_str)  # No validation - accepts negative!
    return amount  # Can process negative payments!


def get_user_by_index(users, index):
    """No bounds checking"""
    return users[index]  # IndexError if index >= len(users)


def copy_file_contents(src, dest):
    """Missing error handling"""
    with open(src, 'r') as f:
        data = f.read()
    with open(dest, 'w') as f:
        f.write(data)
    # No error handling for missing files, permission errors, disk full, etc.


def format_currency(amount):
    """Precision loss with float"""
    return f"${amount:.2f}"  # Float precision issues for large amounts