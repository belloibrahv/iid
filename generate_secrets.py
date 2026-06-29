#!/usr/bin/env python3
"""
Generate secure random keys for production deployment.
Run this script to generate SECRET_KEY and API_KEY for your .env file.
"""
import secrets

def generate_secret():
    """Generate a cryptographically secure random key."""
    return secrets.token_hex(32)

if __name__ == "__main__":
    print("=== Production Secrets Generator ===\n")
    print("Add these to your .env file:\n")
    print(f"SECRET_KEY={generate_secret()}")
    print(f"API_KEY={generate_secret()}")
    print("\nMake sure to keep these secret and never commit them to version control.")
