"""
Initial database setup script.

Creates database tables and initial superadmin users.
Run this script once to initialize the authentication system.
"""

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.auth.database import SessionLocal, init_db
from src.auth.models import User


def create_initial_superadmins():
    """
    Create initial 2 superadmin users.

    WARNING: Default passwords MUST be changed on first login!
    """
    init_db()  # Create tables

    db = SessionLocal()

    try:
        # Check if superadmins already exist
        existing_admins = db.query(User).filter(User.role == "superadmin").count()

        if existing_admins > 0:
            print(f"WARNING: {existing_admins} superadmin(s) already exist. Skipping creation.")
            return

        # Create Superadmin 1
        admin1 = User(username="admin1", email="admin1@empresa.com.br", role="superadmin", is_active=True)
        admin1.set_password("Admin@123!")  # MUST change on first login

        # Create Superadmin 2
        admin2 = User(username="admin2", email="admin2@empresa.com.br", role="superadmin", is_active=True)
        admin2.set_password("Admin@456!")  # MUST change on first login

        db.add_all([admin1, admin2])
        db.commit()

        print("SUCCESS: Initial superadmins created successfully!")
        print("")
        print("Created users:")
        print("  1. Username: admin1, Password: Admin@123!")
        print("  2. Username: admin2, Password: Admin@456!")
        print("")
        print("WARNING: Change these default passwords immediately after first login!")
        print("")
        print("Security reminder:")
        print("  - Use strong passwords (min 8 chars, uppercase, lowercase, numbers, symbols)")
        print("  - Do not share passwords")
        print("  - Change passwords regularly")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Error creating superadmins: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing authentication database...")
    print("")
    create_initial_superadmins()
