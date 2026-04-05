import sys
from database import execute_query
from werkzeug.security import generate_password_hash

def create_admin_manual(username, email, password):
    # Check if exists
    exists = execute_query("SELECT id FROM auth_user WHERE username = %s OR email = %s", (username, email), fetchone=True)
    if exists:
        print(f"Error: User '{username}' or email '{email}' already exists.")
        return

    hashed = generate_password_hash(password, method='pbkdf2:sha256')
    
    # 1. Create Auth User with superuser permissions
    user_id = execute_query("""
        INSERT INTO auth_user (username, email, password, is_superuser, is_staff, is_active, date_joined, first_name, last_name)
        VALUES (%s, %s, %s, 1, 1, 1, NOW(), 'System', 'Admin')
    """, (username, email, hashed), commit=True)
    
    if user_id:
        # 2. Create Profile
        execute_query("""
            INSERT INTO user_management_app_profile (user_id, occupational_status, is_approved)
            VALUES (%s, 'Admin', 1)
        """, (user_id,), commit=True)
        print(f"✅ Success! Admin account '{username}' created successfully.")
    else:
        print("❌ Error: Failed to create admin account.")

if __name__ == "__main__":
    print("--- e-Learny | Administrative Account Generator ---")
    u = input("Enter Admin Username: ")
    e = input("Enter Admin Email: ")
    p = input("Enter Admin Password: ")
    create_admin_manual(u, e, p)
