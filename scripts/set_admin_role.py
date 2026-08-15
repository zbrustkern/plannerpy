#!/usr/bin/env python3
import sys
import os
import argparse
import firebase_admin
from firebase_admin import auth, credentials

def main():
    parser = argparse.ArgumentParser(description="Securely assign Firebase Auth Custom Claims (Admin/Paid) to a user email.")
    parser.add_argument("email", help="The email address of the user to update")
    parser.add_argument("--role", choices=["admin", "paid", "free"], default="admin", help="Role to assign (default: admin)")
    parser.add_argument("--project", default="tophat-financial", help="Firebase Project ID (default: tophat-financial)")
    
    args = parser.parse_args()

    print(f"🔒 Initializing Firebase Admin SDK for project '{args.project}'...")
    
    # Initialize Firebase Admin app if not initialized
    if not firebase_admin._apps:
        try:
            # First try Application Default Credentials (gcloud auth application-default login)
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {'projectId': args.project})
        except Exception as e:
            print(f"Warning: Default credentials fallback, attempting bare init: {e}")
            firebase_admin.initialize_app(options={'projectId': args.project})

    try:
        user = auth.get_user_by_email(args.email)
        print(f"Found User UID: {user.uid} ({user.email})")

        # Set custom claims on Google's Auth servers
        claims = {'role': args.role}
        auth.set_custom_user_claims(user.uid, claims)

        print(f"✅ SUCCESS: Custom claim {claims} assigned to user '{args.email}' (UID: {user.uid}).")
        print("Note: The user will need to log out and log back in (or refresh their token) for the new claim to take effect in their JWT token.")

    except auth.UserNotFoundError:
        print(f"❌ ERROR: User with email '{args.email}' not found in Firebase Auth for project '{args.project}'.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR assigning custom claim: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
