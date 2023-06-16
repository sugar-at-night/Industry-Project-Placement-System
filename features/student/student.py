from flask import Blueprint, send_from_directory
from flask import render_template

from common.login_required import student_login_required, sms_login_required
from common.email_utils import send_mail
from common.user import User
from common.user import current_user
from flask import request
from flask import flash
from flask import session
from flask import redirect
from flask import url_for

from db.db import getCursor
import hashlib
import common

from flask import current_app
from flask import Response
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import json

student = Blueprint("student", __name__, template_folder="templates")

# Common functions for student's routes
# Get Student's details
def get_student_details(user_id):
    cursor = getCursor()
    query = """SELECT
                s.student_id,
                s.formal_name,
                s.alternative_name,
                s.preferred_name,
                s.email,
                s.phone,
                s.city,
                s.project_preference,
                s.cv_link,
                p.placement_status
            FROM Users AS u
            INNER JOIN Students AS s ON u.user_id = s.user_id
            LEFT JOIN Placement AS p ON p.student_id = s.student_id 
            WHERE u.user_id =%s;"""
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

# Get student's details by student_id
def get_student_details_by_student_id(student_id):
    cursor = getCursor()
    query = """SELECT
                s.student_id,
                s.formal_name,
                s.alternative_name,
                s.preferred_name,
                s.email,
                s.phone,
                s.city,
                s.project_preference,
                s.cv_link,
                p.placement_status
            FROM Students AS s
            LEFT JOIN Placement AS p ON p.student_id = s.student_id 
            WHERE s.student_id =%s;"""
    cursor.execute(query, (student_id,))
    result = cursor.fetchone()
    cursor.close()
    return result


# Get all skills
def get_all_skills():
    cursor = getCursor()
    query = """SELECT * FROM Skills;"""
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# Get student's skills list
def get_student_skills (student_id):
    cursor = getCursor()
    query = """SELECT
                s.skill_name
            FROM Skills AS s
            INNER JOIN Student_skills AS ss ON s.skill_id = ss.skill_id
            WHERE ss.student_id =%s;"""
    cursor.execute(query, (student_id,))
    result = cursor.fetchall()
    cursor.close()
    return result

# Get student's survey
def get_student_survey(student_id, survey_id):
    cursor = getCursor()
    query = """SELECT
                survey_response_id,
                survey_id,
                survey_response_json
            FROM Survey_Response WHERE survey_id = %s AND student_id = %s;"""
    cursor.execute(query, (survey_id, student_id))
    result = cursor.fetchone()
    cursor.close()
    return result

# Get student's offers
def get_student_offers(student_id):
    cursor = getCursor()
    query = """SELECT ps.ps_id, ps.status, c.company_name, p.project_type, p.project_name FROM PreferredStudents AS ps
    LEFT JOIN Projects AS p ON ps.project_id = p.project_id
    LEFT JOIN Companies AS c ON p.company_id = c.company_id
    WHERE ps.student_id = %s;"""

    cursor.execute(query, (student_id,))
    result = cursor.fetchall()
    offers = []
    for row in result:
        offer = {
            'id': row[0],
            'status': row[1],
            'company_name': row[2],
            'project_type': row[3],
            'project_name': row[4]
        }
        offers.append(offer)
    cursor.close()
    print("offeres", offers)
    return offers
    

@student.route("/dashboard",endpoint='dashboard')
@student_login_required
def dashboard():
    user = {
        "username": session["username"],
        "role": session["role"]
    }
    return render_template(f"student_dashboard.html", user=user)


@student.route("/change_password", methods=["GET", "POST"])
@student_login_required
def student_change_password():
    # Get the user object
    user = User.get_user(session["user_id"])
    if request.method == "POST":
        # Get the form data
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        # Verify that the current password is correct
        hashed_current_password = hashlib.sha256(current_password.encode('utf-8')).hexdigest()
        if hashed_current_password != user.password:
            error = "Incorrect current password"
            flash(error, "error")
            return render_template("change_password.html", user=user)
        # Verify that the new password and confirm password match
        if new_password != confirm_password:
            error = "New password and confirm password do not match"
            flash(error, "error")
            return render_template("change_password.html", user=user)
        # Hash the new password and update the user's password in the database
        hashed_new_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        user.update_password(current_password, new_password)
        # Display success message
        flash("Password changed successfully", "success")
        return redirect(url_for("student.dashboard"))
    # If GET request, display the change password form
    return render_template("change_password.html", user=user)


# Helper function
ALLOWED_EXTENSIONS = {'pdf'}  # allowed file extensions
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # max file size in bytes (5MB)

# Create a directory for storing uploaded files
@student.record
def on_load(state):
    app = state.app
    with app.app_context():
        UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom error handler for RequestEntityTooLarge error
@student.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(error):
    # Get the user object
    user = User.get_user(session["user_id"])
    flash('File too large. Maximum file size is 5MB.', 'error')
    return render_template('upload_cv.html', user=user)


@student.route('/upload_cv', methods=['GET', 'POST'])
@student_login_required
def upload_cv():
    # Get the user object
    user = User.get_user(session["user_id"])
    user_id = session["user_id"]
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return render_template('upload_cv.html', user=user)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return render_template('upload_cv.html', user=user)
        if not allowed_file(file.filename):
            flash('Invalid file type. Only PDF files are allowed.', 'error')
            return render_template('upload_cv.html', user=user)
        try:
            # rename file to user_id.pdf
            filename = secure_filename(f"{user_id}.pdf")  
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            print(filepath)
            if os.path.exists(filepath):
                # If a file with the same name already exists, replace it with the new file
                os.remove(filepath)
                flash('Your CV has been replaced', 'success')
            file.save(filepath)
            # cv_link = url_for('static', filename=f"uploads/{filename}")
            cv_link = f"/uploads/{filename}"  # Generate the cv_link without app root
            print(cv_link)
            with getCursor() as cursor:
                cursor.execute("UPDATE Students SET cv_link=%s WHERE user_id=%s", (cv_link, user_id))
            flash('File uploaded successfully', 'success')
            return render_template('upload_cv.html', user=user)
        except RequestEntityTooLarge:
            flash('File too large. Maximum file size is 5MB.', 'error')
            return render_template('upload_cv.html', user=user)
    return render_template('upload_cv.html', user=user)


@student.route('/view_cv')
@student_login_required
def view_cv():
    # Get the user object
    user = User.get_user(session["user_id"])
    user_id = session["user_id"]
    filename = f"{user_id}.pdf"
    cv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(cv_path):
        with open(cv_path, 'rb') as f:
            file_contents = f.read()
        return Response(file_contents, mimetype='application/pdf')
    flash('No CV uploaded', 'error')
    return render_template('upload_cv.html', user=user)




@student.route('/download_cv')
@student_login_required
def download_cv():
    # Get the user object
    user = User.get_user(session["user_id"])
    user_id = session["user_id"]
    filename = f"{user_id}.pdf"
    cv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(cv_path):
        return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], path=filename, as_attachment=True)
    flash('No CV uploaded', 'error')
    return render_template('upload_cv.html', user=user)


# Student profile.
@student.route("/profile", methods=["GET", "POST"])
# Staff, mentor or student login required
@sms_login_required
def profile():
    if request.method == "POST":
        user_id = session["user_id"]
        student_id = request.form.get("student_id")
        formal_name = request.form.get("formal_name")
        preferred_name = request.form.get("preferred_name")
        alternative_name = request.form.get("alternative_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        city = request.form.get("city")
        project_preference = request.form.get("project_preference")
        skills = request.form.getlist('skills')
        
        # If student_id is not provided, then it is a new student
        if (student_id):
            cursor = getCursor()
            # Update student details
            query = "UPDATE Students SET formal_name=%s, preferred_name=%s, alternative_name=%s, email=%s, phone=%s, city=%s, project_preference=%s WHERE student_id=%s"
            cursor.execute(query, (formal_name, preferred_name, alternative_name, email, phone, city, project_preference, student_id))
            
            # Drop existing skills
            query = "DELETE FROM Student_Skills WHERE student_id=%s"
            cursor.execute(query, (student_id,))
                
            # Update student skills
            for skill in skills:
                # Insert new skills
                query = """INSERT INTO Student_Skills (student_id, skill_id)
                            SELECT %s, %s
                            WHERE NOT EXISTS (
                                SELECT 1
                                FROM Student_Skills
                                WHERE student_id = %s
                                AND skill_id = %s
                        );"""
                cursor.execute(query, (student_id, int(skill.strip()), student_id, int(skill.strip())))
                
            cursor.close()
            
            # Display success message
            flash("Student updated successfully", "success")
            return redirect(url_for("student.profile"))
    else:
        # Get logged in user's role
        login_user_role = session["role"]
        cursor = getCursor()
        # Identify the user's role
        if login_user_role == "student":
            # Get student details
            result = get_student_details(session["user_id"])
            if(result == None):
                user = {
                    "username": session["username"],
                    "role": session["role"]
                }
                return render_template('create_profile.html', user=user)
            else:
                # Get all skills
                all_skills = get_all_skills()
                if(all_skills == None):
                    all_skills = []
                    
                # Get student skills
                student_skills = get_student_skills(result[0])
                if(student_skills == None):
                    student_skills = []
                else:
                    student_skills = [item for sublist in student_skills for item in sublist]
                    
                # Does the user have a survey response?
                student_survey = get_student_survey(result[0], 1)
                is_survey_complete = 1
                print(student_survey)
                if(student_survey == None):
                    is_survey_complete = 0
                
                user_profile = {
                    "username": session["username"],
                    "student_id": result[0],
                    "name": result[1],
                    "role": session["role"],
                    "email": result[4],
                    "phone": result[5],
                    "preferred_name": result[3],
                    "city": result[6],
                    "skills": student_skills,
                    "is_survey_complete": is_survey_complete,
                    "project_preference": result[7] if result[7] else "",
                    "cv_link": result[8] if result[8] else "",
                    "placement_status": result[9] if result[9] else ""
                }
                
                # Get offers
                offers = get_student_offers(result[0])
                if(offers == None):
                    offers = []
                
                return render_template('profile.html', user=user_profile, all_skills=all_skills, offers=offers)
        else:
            # Get url parameter
            student_id = request.args.get('student_id')
            role = request.args.get('role')
            result = get_student_details_by_student_id(student_id)
            print("Loging user role isn snot student")
            print(student_id)
            print(role)
            print(result)
            if(result == None):
                flash("Student does not exist", "error")
                if(role == "staff"):
                    return redirect(url_for("staff.dashboard"))
                elif(role == "mentor"):
                    return redirect(url_for("mentor.dashboard"))
                
                # Got to landing page
                return render_template('index.html')
            else:
                # Get all skills
                all_skills = get_all_skills()
                if(all_skills == None):
                    all_skills = []
                    
                # Get student skills
                student_skills = get_student_skills(result[0])
                if(student_skills == None):
                    student_skills = []
                else:
                    student_skills = [item for sublist in student_skills for item in sublist]
                    
                # Does the user have a survey response?
                student_survey = get_student_survey(result[0], 1)
                is_survey_complete = 1
                print(student_survey)
                if(student_survey == None):
                    is_survey_complete = 0
                
                user_profile = {
                    "username": session["username"],
                    "student_id": result[0],
                    "name": result[1],
                    "role": session["role"],
                    "email": result[4],
                    "phone": result[5],
                    "preferred_name": result[3],
                    "city": result[6],
                    "skills": student_skills,
                    "is_survey_complete": is_survey_complete,
                    "project_preference": result[7] if result[7] else "",
                    "cv_link": result[8] if result[8] else "",
                    "placement_status": result[9] if result[9] else ""
                }
                
                offers = get_student_offers(result[0])
                if(offers == None):
                    offers = []
                
                return render_template('profile.html', user=user_profile, all_skills=all_skills, offers=offers)
            
# Profile page. Only accessible to logged in users.
@student.route("/create_profile", methods=["GET", "POST"])
@student_login_required
def create_profile():
    if request.method == "POST":
        user_id = session["user_id"]
        student_id = request.form.get("student_id")
        formal_name = request.form.get("formal_name")
        preferred_name = request.form.get("preferred_name")
        alternative_name = request.form.get("alternative_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        city = request.form.get("city")
        
        # Insert the new student into the database
        cursor = getCursor()
        query = "INSERT INTO Students (student_id, user_id, formal_name, preferred_name, alternative_name, email, phone, city) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (student_id, user_id, formal_name, preferred_name, alternative_name, email, phone, city))
        student_id = cursor.lastrowid
        cursor.close()
        # Display success message
        flash("Student added successfully", "success")
        return redirect(url_for("student.profile"))
    else:
        return render_template('create_profile.html')

# Survey routes
@student.route("/survey", methods=["GET", "POST"])
@sms_login_required
def survey():
    user = {
        "username": session["username"],
        "role": session["role"],
        "is_survey_complete": 1
    }
    if request.method == "POST":
        # Get Json request data
        request_data = request.get_json()
        user_id = session["user_id"]
        print(request_data)
        
        # Get student details
        student_details = get_student_details(user_id)
        if(student_details == None):
             return render_template('create_profile.html')
        
        survey_id = request_data["survey_id"]
        survey_response_id = request_data["survey_response_id"]
        if (survey_response_id == '{}'):
            # Insert the new survey response into the database
            cursor = getCursor()
            query = "INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (%s, %s, %s)"
            cursor.execute(query, (survey_id, student_details[0], json.dumps(request_data["data"])))
            survey_response_id = cursor.lastrowid
            cursor.close()
            return render_template('profile.html', user=user)
        survey_response_data = request_data["data"]
        query = "UPDATE Survey_Response SET survey_response_json=%s WHERE survey_response_id=%s and survey_id=%s and student_id=%s"
        cursor = getCursor()
        cursor.execute(query, (json.dumps(survey_response_data), survey_response_id, survey_id, student_details[0]))
        cursor.close()
        return render_template('profile.html', user=user)
    else:
        # Get student_id from url params
        student_id = request.args.get('student_id')
        user_details = get_student_details_by_student_id(student_id)
        if(user_details == None):
            user = {
                "username": session["username"],
                "role": session["role"]
            }
            return render_template('create_profile.html', user=user)
        else: 
            # Get student skills
            student_skills = get_student_skills(user_details[0])
            if(student_skills == None):
                student_skills = []
            else:
                student_skills = [item for sublist in student_skills for item in sublist]
                
            user = {
                'username': session["username"],
                'student_id': user_details[0],
                'name': user_details[1],
                'role': session["role"],
                'email': user_details[4],
                'phone': user_details[5],
                'preferred_name': user_details[3],
                'city': user_details[6],
                'skills': student_skills
            }

            # Get questions json
            cursor = getCursor()
            question_query = """SELECT 
                        survey_id, 
                        survey_name, 
                        survey_description, 
                        survey_question_json
                    FROM Survey WHERE survey_id = 1"""
            cursor.execute(question_query)
            questions_result = cursor.fetchone()
            if questions_result is None:
                flash("Survey not found", "error")
                return redirect(url_for("student.profile"))
            
            # Get answers json
            query = """SELECT
                        survey_response_id,
                        survey_id,
                        survey_response_json
                    FROM Survey_Response WHERE survey_id = %s AND student_id = %s;"""
            cursor.execute(query, (questions_result[0], user["student_id"]))
            answers = cursor.fetchone()
            if answers is None:
                answers = {}
        return render_template("survey.html", user=user, questions=questions_result, answers=answers)


@student.route("/project_detail", endpoint="project_detail")
@sms_login_required
def project_detail():
    # Get the user object
    user = User.get_user(session["user_id"])
    cursor = getCursor()
    sql = """select projects.project_id, projects.project_name, projects.project_description, mentors.mentor_name
             from projects join mentors on projects.mentor_id = mentors.mentor_id"""
    cursor.execute(sql)
    projects = cursor.fetchall()
    return render_template("project_detail.html", user=user, projects=projects)


# Helper function to retrieve project details
def get_project_details(project_id):
    # Connect to the MySQL database
    cursor = getCursor()
    # Retrieve the project details from the database
    query = "SELECT project_name, project_description, placement_status FROM Projects WHERE project_id = %s"
    cursor.execute(query, (project_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        project_name, project_description, placement_status = row
        project = {
            'project_id': project_id,
            'project_name': project_name,
            'project_description': project_description,
            'placement_status': placement_status
        }
        return project
    else:
        return None

# Helper function to retrieve student ID using user ID
def get_student_id(user_id):
    query = "SELECT student_id FROM Students WHERE user_id = %s"
    cursor = getCursor()
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return None


@student.route('/add_to_wishlist', methods=['GET'])
@student_login_required
def add_to_wishlist():
    project_id = int(request.args.get('id'))  # Get the project ID from the URL query parameter
    user_id = session['user_id']
    student_id = get_student_id(user_id)
    print(student_id, project_id) 
    # Check if the project is already in the student's wishlist
    query = "SELECT COUNT(wish_id) FROM WishList WHERE student_id = %s AND project_id = %s"
    cursor = getCursor()
    cursor.execute(query, (student_id, project_id))
    count = cursor.fetchone()[0]
    if count > 0:
        flash('Project already in wishlist', 'error')
        cursor.close()
        return redirect(url_for('student.project_detail'))
    # Get the highest rank in the student's wishlist
    query = "SELECT MAX(`rank`) AS max_rank FROM WishList WHERE student_id = %s"
    cursor.execute(query, (student_id,))
    max_rank = cursor.fetchone()[0]
    if max_rank is None:
        rank = 1  # First project in the wishlist
    else:
        rank = max_rank + 1
    # Insert the project into the wishlist
    insert_query = "INSERT INTO WishList (student_id, project_id, `rank`) VALUES (%s, %s, %s)"
    try:
        cursor.execute(insert_query, (student_id, project_id, rank))
        flash('Project added to wishlist', 'success')
    except Exception as err:
        flash(f"Error adding project to wishlist: {str(err)}", 'error')
    cursor.close()
    return redirect(url_for('student.project_detail'))


@student.route('/wishlist')
@student_login_required
def wishlist():
    # Get the user object
    user = User.get_user(session["user_id"])
    user_id = session['user_id']
    student_id = get_student_id(user_id)
    # Check if the student has any items in their wishlist
    query = "SELECT COUNT(*) FROM WishList WHERE student_id = %s"
    cursor = getCursor()
    cursor.execute(query, (student_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    if count == 0:
        flash('Your wishlist is empty. Go to project list to add some.', 'warning')
        return render_template('wishlist.html', user=user, wishlist=[])
    # Retrieve the student's wishlist from the database
    query = "SELECT project_id, `rank` FROM WishList WHERE student_id = %s ORDER BY `rank`"
    cursor = getCursor()
    cursor.execute(query, (student_id,))
    rows = cursor.fetchall()
    cursor.close()
    wishlist = []
    for row in rows:
        project_id, rank = row
        project = get_project_details(project_id)
        if project:
            wishlist.append({
                'project_id': project_id,
                'project_name': project['project_name'],
                'project_description': project['project_description'],
                'rank': rank
            })
            # Check if any projects in the wishlist have been placed or are no longer available
            if project['placement_status'] in ['Not Looking', 'Placed']:
                # Retrieve the emails of all students who have selected the project in their wishlist
                query = """
                    SELECT students.email
                    FROM Users
                    INNER JOIN Students ON Users.user_id = Students.user_id
                    INNER JOIN WishList ON Students.student_id = WishList.student_id
                    WHERE WishList.project_id = %s
                """
                cursor = getCursor()
                cursor.execute(query, (project_id,))
                student_emails = cursor.fetchall()
                cursor.close()

                # Send emails to the all affected students
                for student_email in student_emails:
                    email_subject = "Wishlist Project Unavailable"
                    email_body = f"The project {project['project_name']} in your wishlist is no longer available."
                    send_mail(email_subject, student_email[0], email_body)

                # Remove the project from the wishlists of all students who had it in their wishlist
                query = "DELETE FROM WishList WHERE project_id = %s"
                cursor = getCursor()
                cursor.execute(query, (project_id,))
                cursor.close()

    return render_template('wishlist.html', user=user, wishlist=wishlist)


@student.route('/save_ranks', methods=['POST'])
@student_login_required
def save_ranks():
    user_id = session['user_id']
    student_id = get_student_id(user_id)
    project_ids = request.form.getlist('project_id[]')
    ranks = request.form.getlist('rank[]')
    # Check for duplicate ranks
    if len(set(ranks)) != len(ranks):
        flash('Each project must have a unique rank', 'error')
        return redirect(url_for('student.wishlist'))
    # Check for ranks less than or equal to 0
    if any(int(rank) <= 0 for rank in ranks):
        flash('Ranks must be greater than 0', 'error')
        return redirect(url_for('student.wishlist'))
    cursor = getCursor()
    try:
        cursor.execute("START TRANSACTION")
        for i, project_id in enumerate(project_ids):
            desired_rank = int(ranks[i])
            # Update the rank of the project to the desired rank
            update_query = "UPDATE WishList SET `rank` = %s WHERE student_id = %s AND project_id = %s"
            cursor.execute(update_query, (desired_rank, student_id, project_id))
        cursor.execute("COMMIT")
        flash('Project ranks updated', 'success')
    except Exception as e:
        cursor.execute("ROLLBACK")
        flash('An error occurred while updating the project ranks', 'error')
    finally:
        cursor.close()
    return redirect(url_for('student.wishlist'))


@student.route('/remove_from_wishlist/<int:project_id>', methods=['GET', 'POST'])
@student_login_required
def remove_from_wishlist(project_id):
    user_id = session['user_id']
    student_id = get_student_id(user_id)
    # Remove the project from the student's wishlist
    query = "DELETE FROM WishList WHERE student_id = %s AND project_id = %s"
    cursor = getCursor()
    cursor.execute(query, (student_id, project_id))
    flash('Project removed from wishlist', 'success')
    cursor.close()
    return redirect(url_for('student.wishlist'))

@student.route("/student/contact_staff", methods=['GET', 'POST'], endpoint="contact_staff")
@student_login_required
def contact_staff():
   user = User.get_user(session["user_id"])
   user_id = session['user_id']
   sql = "select email from students where user_id = %s"
   cursor = getCursor()
   cursor.execute(sql,(user_id,))
   sender = cursor.fetchone()
   sender = sender[0]

   if request.method == "GET":
      return render_template("mentor_contact_staff.html", user=user)
   elif request.method == "POST": 
       #find email from staff table
        sql = "select email from staff"
        cursor = getCursor()
        cursor.execute(sql)
        email = cursor.fetchall()
        
        # Get data from form submission

        subject = request.form.get("subject")
        message = request.form.get("message")

        if (email == None):
           error = "Staff email address not found"
           flash(error, "error")
           return redirect(url_for("student.dashboard"))
        if (sender == None):
           error = "Student email address not found"
           flash(error, "error")
           return redirect(url_for("student.dashboard"))
        
        # Send email to the staff
        for mail in email:
            send_mail(subject, mail[0], message,sender)

        message = "Message sent"
        flash(message, "success")
        
        # Return the response with appropriate headers
        return redirect(url_for("student.dashboard"))

# Accept a project offer
@student.route('/accept_offer', methods=['POST'])
@student_login_required
def accept_offer():
    # Get project id from the form
    project_id = request.form.get('project_id')
    # Get the student's id from the session
    student_id = get_student_id(session['user_id'])
    
    print('project_id', project_id)
    print('student_id', student_id)
    
    # Update PreferredStudents table to indicate that the student has accepted the offer
    cursor = getCursor()
    query = """
        UPDATE PreferredStudents SET status = 'Accepted' WHERE student_id = %s AND project_id = %s;
    """
    cursor.execute(query, (student_id, project_id))
    cursor.close()
    
    # All other offers for the student are automatically rejected
    cursor = getCursor()
    query = """ UPDATE PreferredStudents SET status = 'Declined' WHERE student_id = %s AND project_id <> %s AND status = 'Preferred'; """
    cursor.execute(query, (student_id, project_id))
    cursor.close()
    
    # For all other status, set them Not available.
    cursor = getCursor()
    query = """ UPDATE PreferredStudents SET status = 'NotAvl' WHERE student_id = %s AND project_id <> %s AND status not in ('Declined', 'Accepted'); """
    cursor.execute(query, (student_id, project_id))
    cursor.close()
    
    # Update the project's placement status to 'Approved'
    cursor = getCursor()
    query = """ UPDATE Placement SET placement_status = 'approved' WHERE project_id = %s AND student_id = %s; """
    cursor.execute(query, (project_id, student_id))
    
    cursor.close()
    
    # Display success message
    flash("Updated successfully", "success")
    return redirect(url_for("student.profile"))
    
# Reject a project offer
@student.route('/reject_offer', methods=['POST'])
@student_login_required
def reject_offer():
    # Get project id from the form
    project_id = request.form.get('project_id')
    # Get the student's id from the session
    student_id = get_student_id(session['user_id'])
    
    print('project_id', project_id) 
    print('student_id', student_id)
    
    # Update PreferredStudents table to indicate that the student has accepted the offer
    cursor = getCursor()
    query = """
        UPDATE PreferredStudents SET status = 'Declined' WHERE student_id = %s AND project_id = %s;
    """
    cursor.execute(query, (student_id, project_id))
    cursor.close()
    flash("Updated successfully", "success")
    return redirect(url_for("student.profile"))
    
    
