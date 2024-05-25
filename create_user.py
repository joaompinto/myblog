# create_user.py
from sqlmodel import Session
from db import engine, Users

def create_user(email: str, name: str, password: str):
    # Create a new user instance
    new_user = Users(email=email, name=name, password=password)

    # Hash the user's password
    new_user.hash_password()

    # Open a database session
    with Session(engine) as session:
        # Add the new user to the session
        session.add(new_user)

        # Commit the session to save the new user to the database
        session.commit()

        print(f"User {name} with email {email} created successfully!")

if __name__ == "__main__":
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Create a new user.")
    parser.add_argument("email", type=str, help="The email of the new user.")
    parser.add_argument("name", type=str, help="The name of the new user.")
    parser.add_argument("password", type=str, help="The password for the new user.")

    args = parser.parse_args()

    # Create the user with the provided arguments
    create_user(args.email, args.name, args.password)
