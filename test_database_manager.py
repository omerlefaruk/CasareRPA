"""
Database manager with resource leaks and concurrency bugs
Test file for Claude code review
"""
import sqlite3
import threading
import os


class DatabaseManager:
    """Database manager with resource management issues"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        self.cache = {}

    def connect(self):
        """Opens connection but never closes it - RESOURCE LEAK"""
        self.connection = sqlite3.connect(self.db_path)
        return self.connection

    def execute_query(self, query, params=None):
        """SQL query without proper error handling"""
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()  # Cursor never closed!

    def get_cached_data(self, key):
        """Race condition on shared cache"""
        if key not in self.cache:
            # Another thread could modify cache here
            data = self.fetch_from_db(key)
            self.cache[key] = data  # RACE CONDITION!
        return self.cache[key]

    def fetch_from_db(self, key):
        """Simulated database fetch"""
        return f"data_for_{key}"

    def bulk_insert(self, records):
        """Missing transaction - partial failures leave DB inconsistent"""
        for record in records:
            query = f"INSERT INTO users VALUES ({record['id']}, '{record['name']}')"
            self.execute_query(query)  # No transaction, no rollback!

    def delete_old_records(self, days):
        """Integer overflow risk"""
        milliseconds = days * 24 * 60 * 60 * 1000
        # For large 'days' values, this could overflow
        query = f"DELETE FROM logs WHERE timestamp < {milliseconds}"
        self.execute_query(query)


class ConnectionPool:
    """Connection pool with deadlock potential"""

    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get_connection(self):
        """Potential deadlock - lock held while waiting"""
        self.lock.acquire()
        if len(self.connections) < self.max_connections:
            conn = sqlite3.connect('test.db')
            self.connections.append(conn)
            self.lock.release()
            return conn
        else:
            # Holding lock while waiting - DEADLOCK RISK!
            while len(self.connections) >= self.max_connections:
                pass  # Busy wait with lock held!
            self.lock.release()

    def release_connection(self, conn):
        """Missing lock - RACE CONDITION"""
        # Should acquire lock before modifying shared list
        self.connections.remove(conn)  # Thread-unsafe!


def process_file(filepath):
    """File handle leak - no context manager"""
    f = open(filepath, 'r')
    data = f.read()
    # File never closed if exception occurs!
    if len(data) > 1000:
        raise ValueError("File too large")
    return data


def unsafe_temp_file():
    """Security: Predictable temp file name"""
    temp_path = "/tmp/myapp_temp_123.txt"  # Predictable, race condition
    with open(temp_path, 'w') as f:
        f.write("sensitive data")
    return temp_path