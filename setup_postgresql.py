"""PostgreSQL database setup for CasareRPA"""

import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def setup_database():
    """Create database and user for CasareRPA"""

    # Connection parameters
    conn_params = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "postgre",
    }

    try:
        # Connect to PostgreSQL server
        print("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='casare_rpa'")
        if cursor.fetchone():
            print("✓ Database 'casare_rpa' already exists")
        else:
            # Create database
            print("Creating database 'casare_rpa'...")
            cursor.execute("CREATE DATABASE casare_rpa;")
            print("✓ Database created successfully")

        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='casare_user'")
        if cursor.fetchone():
            print("✓ User 'casare_user' already exists")
        else:
            # Create user
            print("Creating user 'casare_user'...")
            cursor.execute("CREATE USER casare_user WITH PASSWORD 'postgre';")
            print("✓ User created successfully")

        # Grant privileges
        print("Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE casare_rpa TO casare_user;")
        print("✓ Privileges granted")

        cursor.close()
        conn.close()

        # Connect to casare_rpa database and grant schema privileges
        print("\nGranting schema privileges...")
        conn_params["database"] = "casare_rpa"
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("GRANT ALL ON SCHEMA public TO casare_user;")
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO casare_user;"
        )
        cursor.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO casare_user;"
        )
        print("✓ Schema privileges granted")

        cursor.close()
        conn.close()

        print("\n" + "=" * 50)
        print("PostgreSQL setup completed successfully!")
        print("=" * 50)
        print("\nDatabase Configuration:")
        print("  Database: casare_rpa")
        print("  User: casare_user")
        print("  Password: postgre")
        print("  Host: localhost")
        print("  Port: 5432")

    except psycopg2.Error as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Verify postgres user password is 'postgre'")
        print("3. Check pg_hba.conf allows local connections")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    setup_database()
