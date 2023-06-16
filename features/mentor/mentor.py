import os
from flask import Blueprint, current_app, send_from_directory
from flask import render_template

from common.login_required import mentor_login_required, sms_login_required
from common.email_utils import send_mail
from common.user import current_user, User
from common.email_utils import send_mail
from flask import request
from flask import flash, Response
from flask import session
from flask import redirect
from flask import url_for
import json

from db.db import getCursor, get_connection

mentor = Blueprint("mentor", __name__, template_folder="templates")

# Common functions for mentor's routes
# Get mentor by user id
def get_mentor_by_user_id(user_id):
    cursor = getCursor()
    query = """SELECT
                m.mentor_id,
                m.mentor_name,
                m.user_id,
                m.company_id,
                c.company_name
             FROM mentors as m
             INNER JOIN companies as c on m.company_id = c.company_id
             WHERE user_id =%s;"""
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    mentor = {
        'id': result[0],
        'name': result[1],
        'user_id': result[2],
        'company_id': result[3],
        'company_name': result[4]
    }
    return mentor

# Get mentor's projects
def get_mentor_projects(mentor_id):
    cursor = getCursor()
    query = """SELECT
                p.project_id,
                p.project_name,
                p.project_description,
                p.num_students_required,
                p.placement_status,
                c.company_name,
                p.project_type,
                p.project_location
             FROM projects as p
             INNER JOIN companies as c on p.company_id = c.company_id
             WHERE mentor_id =%s;"""
    cursor.execute(query, (mentor_id,))
    result = cursor.fetchall()
    projects = []
    for row in result:
        project = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'num_students_required': row[3],
            'placement_status': row[4],
            'company_name': row[5],
            'project_type': row[6],
            'project_location': row[7]
        }
        projects.append(project)
    return projects

# Get students by project id
def get_students_by_project_id(project_id):
    cursor = getCursor()
    query = """SELECT
                s.student_id,
                s.preferred_name,
                s.email
            FROM Placement AS p
            INNER JOIN Students AS s on s.student_id = p.student_id
            WHERE project_id =%s;"""
    cursor.execute(query, (project_id,))
    result = cursor.fetchall()
    students = []
    for row in result:
        student = {
            'id': row[0],
            'formal_name': row[1],
            'email': row[2]
        }
        students.append(student)
    return students

# Check if student is preferred status
def get_student_preferred_status(student_id, project_id):
    # Check student already in preferred table
    # Only return non approved students
    cursor = getCursor()
    qurery = """SELECT status FROM PreferredStudents WHERE student_id = %s AND project_id = %s;"""
    cursor.execute(qurery, (student_id, project_id))
    result = cursor.fetchone()
    return result[0] if result else None

# Get student by id
def get_student_by_id(student_id):
    cursor = getCursor()
    query = """SELECT
                s.student_id,
                s.formal_name,
                s.alternative_name,
                s.preferred_name,
                s.email,
                s.phone,
                s.city
             from students as s
    
            WHERE student_id =%s;"""
    cursor.execute(query, (student_id,))
    result = cursor.fetchone()
    student = {
        'id': result[0],
        'formal_name': result[1],
        'alternative_name': result[2],
        'preferred_name': result[3],
        'email': result[4],
        'phone': result[5],
        'city': result[6]
    }
    return student

@mentor.route("/dashboard", endpoint="dashboard")
@mentor_login_required
def dashboard():
    user = User.get_user(session["user_id"])

    return render_template("mentor_dashboard.html", user=user)



def find_skills_compaies():
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    sql = "SELECT skill_id,skill_name FROM skills ORDER BY skill_id"
    cursor.execute(sql)
    skills = cursor.fetchall()

    sql = "SELECT company_id,company_name FROM companies ORDER BY company_id"
    cursor.execute(sql)
    companies = cursor.fetchall()

    sql = "SELECT mentor_id,mentor_name FROM mentors ORDER BY mentor_id"
    cursor.execute(sql)
    mentors = cursor.fetchall()

    result = {"skills": skills, "companies": companies, "mentors": mentors}
    return result


@mentor.route("/dashboard/add_project", endpoint="add_project", methods=['GET', 'POST'])
# @mentor_login_required
def add_project():
    user = User.get_user(session["user_id"])
    print(user.user_id)
    if request.method == "GET":
        cursor = getCursor()
        sql = "select * from projects where company_id=(SELECT company_id from mentors WHERE user_id=%s)" % user.user_id
        cursor.execute(sql)
        projects = cursor.fetchall()
        result = find_skills_compaies()

        return render_template("mentor_add_project.html", projects=projects, result=result, user=user)
    elif request.method == "POST":
        user_id = session["user_id"]
        rec = request.form
        title = rec.get('title')
        summary = rec.get('summary')
        number = int(rec.get('number'))
        skills = rec.getlist('skills')
        other = rec.get('other')
        #company_id = int(rec.get('company_id'))
        project_type = rec.get('project-type')
        location = rec.get('location')
        placement_status = rec.get('placement_status')

        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        try:
            
            sql = "SELECT mentor_id,company_id FROM mentors WHERE user_id=%s"
            cursor.execute(sql, (user.user_id,))
            mentor = cursor.fetchone()
            mentor_id = int(mentor[0])
            company_id = int(mentor[1])
            sql = """Insert into projects (project_name, project_type, project_description, project_location, 
                 company_id,mentor_id, num_students_required, placement_status) 
                    values ('%s','%s','%s','%s',%d,%d,%d,'%s')""" % (title, project_type, summary, location,company_id,
                                                                      mentor_id, number, placement_status)

            cursor.execute(sql)
            cursor.execute("select project_id from projects where project_name='%s'" % title)
            id = cursor.fetchone()[0]

            if other:
                sql = "select skill_id,skill_name from skills"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                for index, value in enumerate(data_list):

                    print("==", value[1], other)
                    if value[1] == other:
                        skills.append(value[0])
                        break

                    if index == len(data_list) - 1:
                        sql = "insert into skills (skill_name) value ('%s')" % other
                        print(sql)
                        cursor.execute(sql)
                        sql = "select skill_id from skills where skill_name='%s'" % other
                        cursor.execute(sql)
                        other_id = cursor.fetchone()[0]
                        skills.append(other_id)
            for skill in skills:
                sql = "insert into project_skills (project_id,skill_id) values (%d,%d)" % (id, int(skill))
                print(sql)
                cursor.execute(sql)
            mysqldb.commit()
            return redirect(url_for('mentor.project_detail'))
        except Exception as e:
            mysqldb.rollback()
            return str(e)
        finally:
            mysqldb.close()


@mentor.route("/dashboard/project_detail", endpoint="project_detail")
@mentor_login_required
def project_detail():
    user = User.get_user(session["user_id"])
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    sql = "select company_id from mentors where user_id = %s" % (user.user_id)
    cursor.execute(sql)
    company = cursor.fetchone()
    company_id = company[0]
    print (company_id)
    sql = """select project_id,project_name,project_description,m.mentor_name from projects p 
                inner join mentors m on p.mentor_id = m.mentor_id 
                where p.company_id = %s"""
    cursor.execute(sql, (company_id,))
    projects = cursor.fetchall()

    return render_template("project_detail.html", projects=projects, flag=1, user=user)


@mentor.route("/dashboard/view_project", endpoint="view_project")
@mentor_login_required
def view_project():
    user = User.get_user(session["user_id"])
    id = request.args.get('id')
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
   
    sql = """SELECT project_id,project_name,project_description,num_students_required,
                company_id,mentor_id,project_type,project_location 
                FROM projects p WHERE project_id=%s"""
    cursor.execute(sql, (id,))
    project = cursor.fetchone()

    sql = "SELECT skill_id FROM project_skills WHERE project_id = %s"
    cursor.execute(sql, (id,))
    skill_ids = cursor.fetchall()
    skill_id_list = []
    for skill_id in skill_ids:
        skill_id_list.append(skill_id[0])

    result = find_skills_compaies()
    print(result)
    result['project'] = project
    result['skill_id_list'] = skill_id_list


    return render_template("mentor_view_project.html", result=result, user=user)


@mentor.route("/dashboard/edit_project", endpoint="edit_project", methods=['GET', 'POST'])
@mentor_login_required
def edit_project():
    if request.method == "GET":
        id = request.args.get('id')
        user = User.get_user(session["user_id"])
        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        sql = """SELECT project_id,project_name,project_description,num_students_required,company_id,project_type,
                    project_location,placement_status FROM projects p WHERE project_id=%s"""
        cursor.execute(sql, (id,))
        project = cursor.fetchone()

        sql = "SELECT skill_id FROM project_skills WHERE project_id = %s"
        cursor.execute(sql, (id,))
        skill_ids = cursor.fetchall()
        skill_id_list = []
        for skill_id in skill_ids:
            skill_id_list.append(skill_id[0])

        result = find_skills_compaies()
        result['project'] = project
        result['skill_id_list'] = skill_id_list

        return render_template("mentor_edit_project.html", result=result, user=user)
    
    elif request.method == "POST":
        user = User.get_user(session["user_id"])

        rec = request.form
        id = int(rec.get('id'))
        title = rec.get('title')
        summary = rec.get('summary')
        number = int(rec.get('number'))
        skills = rec.getlist('skills')
        other = rec.get('other')
        #company_id = int(rec.get('company_id'))
        project_type = rec.get('project-type')
        location = rec.get('location')
        placement_status = rec.get('placement_status')

        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        try:

            #update project details in projects table
            sql = "SELECT mentor_id FROM mentors WHERE user_id='%s'"
            cursor.execute(sql, (user.user_id,))
            mentor_id = cursor.fetchone()[0]

            sql = """UPDATE projects SET project_name='%s', project_type='%s', project_description='%s', 
                    project_location='%s', mentor_id=%d, num_students_required=%d, placement_status='%s' 
                    WHERE project_id=%d""" % (title, project_type, summary, location, mentor_id, number,
                                              placement_status, id)
            cursor.execute(sql)
            
            #create skills list
            if other:
                sql = "select skill_id,skill_name from skills"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                for index, value in enumerate(data_list):
                    print("==", value[1], other)
                    if value[1] == other:
                        skills.append(value[0])
                        break
                    if index == len(data_list) - 1:
                        sql = "insert into skills (skill_name) value ('%s')" % other
                        print(sql)
                        cursor.execute(sql)
                        sql = "select skill_id from skills where skill_name='%s'" % other
                        cursor.execute(sql)
                        other_id = cursor.fetchone()[0]
                        skills.append(other_id)
            
            #delete previous skills
            sql = "DELETE FROM project_skills WHERE project_id=%d" % id
            cursor.execute(sql)

            #add new selected skills
            for skill in skills:
                sql = "insert into project_skills (project_id,skill_id) values (%d,%d)" % (id, int(skill))
                print(sql)
                cursor.execute(sql)
            mysqldb.commit()
            return redirect(url_for('mentor.project_detail'))
        
        except Exception as e:
            mysqldb.rollback()
            return str(e)
        finally:
            mysqldb.close()


@mentor.route("/dashboard/remove_project", endpoint="remove_project")
# @mentor_login_required
def remove_project():
    id = int(request.args.get('id'))

    mysqldb = get_connection()
    cursor = mysqldb.cursor()

    # sql="DELETE FROM placement where project_id=%s"%id
    # cursor.execute(sql)
    sql = "DELETE FROM project_skills WHERE project_id = %s" % id
    cursor.execute(sql)
    mysqldb.commit()
    sql = "DELETE FROM projects WHERE project_id = %s" % id
    cursor.execute(sql)
    mysqldb.commit()
    return redirect(url_for('mentor.project_detail'))


#mentor can view and update their own company profile
@mentor.route("/dashboard/company_profile", endpoint="company_profile", methods=['GET', 'POST'])
def company_profile():
    # Get the user object
    user = User.get_user(session["user_id"])
    user_id = session['user_id']
    if request.method == "GET":
        query = "SELECT company_id, company_name, company_detail, website FROM Companies WHERE company_id = (SELECT company_id FROM Mentors WHERE user_id = %s)"
        cursor = getCursor()
        cursor.execute(query, (user_id,))
        company = cursor.fetchone()
        if company:
            company_id, company_name, company_detail, website = company
            # Render the company profile view with the retrieved data
            return render_template("company_profile.html", user=user, company_id=company_id, company_name=company_name, company_detail=company_detail, website=website)
        else:
            # No company profile found for the mentor
            return flash("Company profile not found. Please contact Staff", "warning")
            
    elif request.method == "POST":
        company_name = request.form.get("company_name")
        company_detail = request.form.get("company_detail")
        website = request.form.get("website")
        # Update the company profile in the database
        query = "UPDATE Companies SET company_name = %s, company_detail = %s, website = %s WHERE company_id = (SELECT company_id FROM Mentors WHERE user_id = %s)"
        cursor = getCursor()
        cursor.execute(query, (company_name, company_detail, website, user_id))
        flash("Company profile updated successfully!", "success")
        # Redirect to the company profile page after updating
        return redirect(url_for("mentor.company_profile"))



@mentor.route("/profile", endpoint="student_profile", methods=["GET", "POST"])
@mentor_login_required
def profile():
    id = request.args.get("id")
    return redirect(url_for('student.profile', student_id=id, role='staff'))


@mentor.route("/student_list", methods=["GET", "POST"], endpoint="student_list")
@mentor_login_required
def student_list():
    user = User.get_user(session["user_id"])
    cursor = getCursor()
    sql = "select student_id,formal_name,phone,email,project_preference from students"
    cursor.execute(sql)
    student = cursor.fetchall()
    return render_template("student_list.html", student=student, user=user)


@mentor.route('/download_cv')
@mentor_login_required
def download_cv():
    student_id = request.args.get("id")
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    # Check if the student has uploaded a CV
    query = "SELECT cv_link FROM students WHERE student_id = %s"
    cursor.execute(query, (student_id,))
    cv_link = cursor.fetchone()
    if not cv_link or not cv_link[0]:
        flash('No CV uploaded for this student', 'error')
        return redirect(url_for('mentor.student_list'))
    # Get the CV file path
    filename = cv_link[0].split('/')[-1]
    # cv_path = os.path.join(current_app.root_path, cv_link[0])
    UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
    cv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    print(cv_path)
    if not os.path.exists(cv_path):
        flash('CV file not found', 'error')
        return redirect(url_for('mentor.student_list'))
    # Send the CV file for download
    return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], path=filename, as_attachment=True)

@mentor.route("/student_preferred", methods=["GET", "POST"])
@mentor_login_required
def student_preferred():
    # Get logged in user
    user = {
        "username": session["username"],
        "role": session["role"]
    }

    try:
        # Get logged in user
        mentor_user_id = session["user_id"]
        
        # Get mentor's details
        mentor = get_mentor_by_user_id(mentor_user_id)
        
        # Get mentor's projects
        mentor_projects = get_mentor_projects(mentor["id"])
        
        # Project's students placement
        students = []
        for project in mentor_projects:
            project_students = get_students_by_project_id(project["id"])
            print(project_students)
            for student in project_students:
                # Get student's preferred status
                preferred_status = get_student_preferred_status(student["id"], project["id"])
                if (preferred_status == None):
                    preferred_status = "NotSele"
                print(preferred_status)
                student["project_name"] = project["name"]
                student["project_id"] = project["id"]
                student["project_description"] = project["description"]
                student["project_type"] = project["project_type"]
                student["project_location"] = project["project_location"]
                student["company_name"] = project["company_name"]
                student["placement_status"] = project["placement_status"]
                student["preferred_status"] = preferred_status
                student["email"] = student["email"]
                students.append(student)
        print(students)
        return render_template("student_preferred.html", user=user, students=students)
    except Exception as e:
        flash("You are not a mentor")
        return redirect(url_for("login"))

@mentor.route("/student_preferred_update", methods=["GET", "POST"])
def student_preferred_update():
    if request.method == "POST":
        
        data = request.get_json()  # Read the JSON data from the request
        # Extract the required fields from the data
        student_id = data.get('student_id')
        project_id = data.get('project_id')
        preferred_status = data.get('preferred_status')
        cursor = getCursor()
        try:
            # Check student already in preferred table
            sql = """SELECT status FROM PreferredStudents WHERE student_id = %s AND project_id = %s;"""
            cursor.execute(sql, (student_id, project_id))
            result = cursor.fetchone()
            if (result):
                # Update preferred status
                sql = """UPDATE PreferredStudents SET status = %s WHERE student_id = %s AND project_id = %s;"""
                cursor.execute(sql, (preferred_status, student_id, project_id))
            else:
                # Insert preferred status
                sql = """INSERT INTO PreferredStudents (student_id, project_id, status) VALUES (%s, %s, %s);"""
                cursor.execute(sql, (student_id, project_id, preferred_status))
            json_data = json.dumps({"status": "success"})
            return Response(json_data, mimetype='application/json', status=200)
        except Exception as e:
            print(e)
            flash("Error updating preferred status", "error")
            return redirect(url_for("mentor.student_preferred"))

@mentor.route("/mentor/notify_student", methods=['POST'], endpoint="notify_student")
@mentor_login_required
def notify_student():
   if request.method == "POST":
        # Get data from form submission
        student_id = request.form.get("student_id")
        subject = request.form.get("subject")
        message = request.form.get("message")
        action = request.form.get("action")
        project_id = request.form.get("project_id")
        
        print('student_id', student_id)
        print('subject', subject)
        print('message', message)
        print('action', action)
        print('project_id', project_id)   
        
        student = get_student_by_id(student_id)
        
        if (student == None):
            error = "Mentor not found"
            flash(error, "error")
            return redirect(url_for("mentor.student_preferred"))
        
        # Send email to the mentor
        send_mail(subject, student['email'], message)
        
        if (action == "Interview Request"):
            # Update the mentor's preferred status
            cursor = getCursor()
            sql = """UPDATE PreferredStudents SET status = %s WHERE student_id = %s AND project_id = %s;"""
            cursor.execute(sql, ('Interview', student_id, project_id))
        
        flash("Email sent to student successfully", "success")
        # Return the response with appropriate headers
        return redirect(url_for("mentor.student_preferred"))


@mentor.route("/mentor/contact_staff", methods=['GET', 'POST'], endpoint="contact_staff")
@mentor_login_required
def contact_staff():
   user = User.get_user(session["user_id"])
   user_id = session['user_id']
   sql = "select mentor_email from mentors where user_id = %s"
   cursor = getCursor()
   cursor.execute(sql,(user_id,))
   sender = cursor.fetchone()[0]

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
           return redirect(url_for("mentor.dashboard"))
        if (sender == None):
           error = "Mentor email address not found"
           flash(error, "error")
           return redirect(url_for("mentor.dashboard"))
        
        # Send email to the staff
        for mail in email:
            send_mail(subject, mail[0], message,sender)

        message = "Message sent"
        flash(message, "success")
        
        # Return the response with appropriate headers
        return redirect(url_for("mentor.dashboard"))

