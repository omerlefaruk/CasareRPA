"""
Test file to trigger Claude code review
This file intentionally contains potential bugs and security issues
"""
import os
import subprocess


def execute_user_command(user_input):
    """Execute a shell command from user input - SECURITY RISK!"""
    # This is vulnerable to command injection
    result = subprocess.run(user_input, shell=True, capture_output=True)
    return result.stdout


def divide_numbers(a, b):
    """Divide two numbers - BUG: no zero check"""
    return a / b  # Potential division by zero


def read_file(filename):
    """Read a file - SECURITY RISK: path traversal"""
    # No validation of filename - could be ../../../etc/passwd
    with open(filename, 'r') as f:
        return f.read()


def generate_sql_query(user_id):
    """Generate SQL query - SQL INJECTION RISK!"""
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query


if __name__ == "__main__":
    # Test the functions
    print(divide_numbers(10, 0))  # This will crash
    print(execute_user_command("ls"))  # Command injection risk
    print(read_file("../../../etc/passwd"))  # Path traversal
    print(generate_sql_query("1 OR 1=1"))  # SQL injection