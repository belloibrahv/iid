"""
Authentication Module.
Handles login, logout, session management, and password hashing.
Implements FR-AUTH-01 through FR-AUTH-05.
"""
from flask import session, redirect, url_for, flash
from functools import wraps
from flask_bcrypt import Bcrypt
from typing import Optional

from core.database import Database


bcrypt = Bcrypt()
db = Database()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        password_hash: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.check_password_hash(password_hash, password)


def login_user(username: str, password: str) -> bool:
    """
    Authenticate a user and create a session.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        True if login successful, False otherwise
    """
    user = db.get_user_by_username(username)
    
    if user and verify_password(password, user['password_hash']):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = False
        return True
    
    return False


def logout_user():
    """
    Clear the session and log out the user.
    """
    session.clear()


def is_authenticated() -> bool:
    """
    Check if a user is currently authenticated.
    
    Returns:
        True if user is logged in, False otherwise
    """
    return 'user_id' in session


def get_current_user() -> Optional[dict]:
    """
    Get the current authenticated user.
    
    Returns:
        User dictionary if authenticated, None otherwise
    """
    if is_authenticated():
        return {
            'id': session['user_id'],
            'username': session['username']
        }
    return None


def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Redirects to login page if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('dashboard.login'))
        return f(*args, **kwargs)
    return decorated_function


def init_admin_user(username: str = 'admin', password: str = 'admin123'):
    """
    Initialize the default admin user if it doesn't exist.
    
    Args:
        username: Admin username
        password: Admin password
    """
    existing_user = db.get_user_by_username(username)
    
    if not existing_user:
        password_hash = hash_password(password)
        user_id = db.create_user(username, password_hash)
        print(f"Created admin user: {username} with ID: {user_id}")
        print(f"Default password: {password}")
        print("Please change this password after first login!")
    else:
        print(f"Admin user '{username}' already exists.")


if __name__ == '__main__':
    # Test authentication functions
    print("Testing password hashing...")
    password = "test_password"
    hashed = hash_password(password)
    print(f"Hashed: {hashed}")
    
    print("\nTesting password verification...")
    is_valid = verify_password(password, hashed)
    print(f"Verification result: {is_valid}")
    
    print("\nTesting admin user initialization...")
    init_admin_user()
