from werkzeug.security import generate_password_hash

# Prompt for the new admin password
new_password = input("Enter the new admin password: ")

# Hash the new password
hashed_password = generate_password_hash(new_password)

# Output the hashed password
print("The hashed password is:", hashed_password)
