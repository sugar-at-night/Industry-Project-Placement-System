from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app
from flask_cors import CORS
from common.login_required import login_required
from common.user import User, clear_session
from common.email_utils import configure_mail, send_mail
from features.student.student import student
from features.mentor.mentor import mentor
from features.staff.staff import staff
import common.user
from db.db import getCursor
import hashlib
import random
import string
from flask_mail import Mail, Message
import re

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

configure_mail(app)
CORS(app)



app.register_blueprint(student, url_prefix="/student")
app.register_blueprint(mentor, url_prefix="/mentor")
app.register_blueprint(staff, url_prefix="/staff")

user = None


@app.route("/", methods=["GET"])
@login_required
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Authenticate the user
        user = User.authenticate(username, password)
        if user:
            # Set the session variables
            session["is_authenticated"] = True
            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = user.role
            if user.role == "student":
                return redirect(url_for("student.dashboard"))
            if user.role == "mentor":
                return redirect(url_for("mentor.dashboard"))
            if user.role == "staff":
                return redirect(url_for("staff.dashboard"))
        else:
            error = "Invalid username or password"
            flash(error, "error")
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    # Clear the session variables and redirect to the login page
    clear_session()
    return redirect(url_for("login"))


# Validates if a phone number is in the format of a New Zealand mobile number.
def validate_nz_mobile_number(phone_number):
    # Regular expression pattern for New Zealand mobile numbers
    nz_mobile_pattern = r"^(\+?64|0)[2-9]\d{7,9}$"
    return re.match(nz_mobile_pattern, phone_number)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Get the form data
        username = request.form.get("username")
        recovery_email = request.form.get("recovery_email")
        password = request.form.get("password")
        role = request.form.get("role")
        # Hash the password
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        # Check if the username and recovery_email already exist in the database
        cursor = getCursor()
        query = "SELECT * FROM Users WHERE username=%s OR recovery_email=%s"
        cursor.execute(query, (username, recovery_email))
        result = cursor.fetchone()
        if result:
            error = "Username or recovery email already exists"
            flash(error, "error")
            return render_template("signup.html")
        else:
            # Insert the new user into the database
            query = "INSERT INTO Users (username, password, role, recovery_email) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (username, hashed_password, role, recovery_email))
            user_id = cursor.lastrowid

            # Handle additional fields for Mentor and Staff
            if role == "mentor":
                mentor_email = request.form.get("contact_email")
                mentor_name = request.form.get("formal_name")
                mentor_phone = request.form.get("phone_number")
                # Check if mentor_email or mentor_phone already exist in Mentors table
                query = "SELECT * FROM Mentors WHERE mentor_email=%s OR mentor_phone=%s"
                cursor.execute(query, (mentor_email, mentor_phone))
                result = cursor.fetchone()
                if result:
                    error = "Contact email or phone number already exists for a mentor"
                    flash(error, "error")
                    return render_template("signup.html")
                if not validate_nz_mobile_number(mentor_phone):
                    error = "Invalid New Zealand mobile number"
                    flash(error, "error")
                    return render_template("signup.html")
                # Insert the new mentor into the database
                query = "INSERT INTO Mentors (user_id, mentor_name, mentor_email, mentor_phone) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (user_id, mentor_name, mentor_email, mentor_phone))

            elif role == "staff":
                staff_email = request.form.get("contact_email_staff")
                staff_name = request.form.get("formal_name_staff")
                # Check if staff_email already exists in Staff table
                query = "SELECT * FROM Staff WHERE email=%s"
                cursor.execute(query, (staff_email,))
                result = cursor.fetchone()
                if result:
                    error = "Email already exists for a staff member"
                    flash(error, "error")
                    return render_template("signup.html")
                # Insert the new staff member into the database
                query = "INSERT INTO Staff (user_id, email, staff_name) VALUES (%s, %s, %s)"
                cursor.execute(query, (user_id, staff_email, staff_name))

            cursor.close()
            # Create a new User object and set the session variables
            user = User(username, role, user_id, recovery_email, password)
            session["is_authenticated"] = True
            session["user_id"] = user_id
            flash("Account created successfully", "success")
            return redirect(url_for("login"))
    else:
        return render_template("signup.html")


def generate_random_password(length=10):
    # Generates a random password of the specified length
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


def send_password_reset_recovery_email(recovery_email, new_password):
    # Sends a recovery email to the user with their new password
    subject = 'Password Reset'
    body = f'Your new password is: {new_password}'
    send_mail(subject, recovery_email, body)


@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        # Get form data
        recovery_email = request.form.get("recovery_email")
        # Check if user exists in the database
        cursor = getCursor()
        query = "SELECT * FROM Users WHERE recovery_email=%s"
        cursor.execute(query, (recovery_email,))
        result = cursor.fetchone()
        if result:
            # Generate a new random password
            new_password = generate_random_password()
            # Hash the new password
            hashed_password = hashlib.sha256(
                new_password.encode('utf-8')).hexdigest()
            # Update the user's password in the database
            query = "UPDATE Users SET password=%s WHERE recovery_email=%s"
            cursor.execute(query, (hashed_password, recovery_email))
            # Send the new password to the user's recovery email
            send_password_reset_recovery_email(recovery_email, new_password)
            # Display success message
            flash(
                "Your password has been reset. Check your recovery email for the new password.", "success")
            return redirect(url_for("login"))
        else:
            # Display error message
            flash("Invalid recovery email address. Please try again.", "error")
            return redirect(url_for("reset"))
    # If GET request, display the password reset form
    return render_template("reset.html")





