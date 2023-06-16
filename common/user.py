from flask import session
import hashlib
from db.db import getCursor


class User():
    def __init__(self, username, role, user_id, recovery_email, password):
        self.username = username
        self.role = role
        self.user_id = user_id
        self.recovery_email = recovery_email
        self.password = password
        self.is_authenticated = True
        session["user_id"] = user_id
        session["role"] = role
        session["username"] = username

    def __str__(self):
        return f"<User(username = {self.username}, role = {self.role}, user_id = {self.user_id}, recovery_email = {self.recovery_email})>"

    @staticmethod
    def authenticate(username, password):
        # Hash the password
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        # Check if the username and hashed password match a row in the Users table
        cursor = getCursor()
        query = "SELECT * FROM Users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, hashed_password))
        result = cursor.fetchone()
        print(result)
        # If a match is found, return a new User object
        if result:
            return User(result[1], result[3], result[0], result[4], result[2])
        else:
            return None

    def update_password(self, old_password, new_password):
        # Hash the old password
        hashed_old_password = hashlib.sha256(
            old_password.encode('utf-8')).hexdigest()
        # Check if the old password matches the current password for the user
        cursor = getCursor()
        query = "SELECT * FROM Users WHERE user_id=%s AND password=%s"
        cursor.execute(query, (self.user_id, hashed_old_password))
        result = cursor.fetchone()
        if result:
            # Hash the new password
            hashed_new_password = hashlib.sha256(
                new_password.encode('utf-8')).hexdigest()
            # Update the password in the Users table
            query = "UPDATE Users SET password=%s WHERE user_id=%s"
            cursor.execute(query, (hashed_new_password, self.user_id))
            self.password = hashed_new_password  # Update the password attribute
            return True
        else:
            return False

    @staticmethod
    def get_user(user_id):
        # Look up the user in the Users table based on their user_id
        cursor = getCursor()
        query = "SELECT * FROM Users WHERE user_id=%s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        # If a match is found, return a new User object
        if result:
            return User(result[1], result[3], result[0], result[4], result[2])
        else:
            return None


def current_user():
    user_id = session.get("user_id")
    if user_id:
        return User.get_user(user_id)
    else:
        return None


def clear_session():
    session.clear()
