import os
from flask import Blueprint, current_app, send_from_directory
from flask import render_template

from common.login_required import sms_login_required, staff_login_required
from common.user import current_user, User
from common.email_utils import send_mail
from . import predication_model
from flask import request
from flask import flash, Response
from flask import session
from flask import redirect
from flask import url_for
import json


from db.db import get_connection,getCursor

import json

staff = Blueprint("staff", __name__, template_folder="templates")

# Common functions for student's routes
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

# Get all projects
def get_all_projects():
    cursor = getCursor()
    query = "SELECT project_id, project_name FROM Projects"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# Get all students
def get_all_students():
    cursor = getCursor()
    query = "SELECT student_id, formal_name FROM Students"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# Get staff id
def get_staff_id(user_id):
    cursor = getCursor()
    query = "SELECT staff_id FROM Staff WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0]

# Get projects skills list
def get_project_skills(project_id):
    cursor = getCursor()
    query = """SELECT
                s.skill_name
            FROM Skills AS s
            INNER JOIN Project_skills AS ps ON s.skill_id = ps.skill_id
            WHERE ps.project_id =%s;"""
    cursor.execute(query, (project_id,))
    result = cursor.fetchall()
    cursor.close()
    return result

# Get mentor by id
def get_mentor_by_id(mentor_id):
    cursor = getCursor()
    query = "SELECT mentor_name, mentor_email FROM Mentors WHERE mentor_id = %s"
    cursor.execute(query, (mentor_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

# Get student by id 
def get_student_by_id(student_id):
    cursor = getCursor()
    query = "SELECT formal_name, email FROM Students WHERE student_id = %s"
    cursor.execute(query, (student_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

# Get project by id
def get_project_by_id(project_id):
    cursor = getCursor()
    query = "SELECT project_name, project_description FROM Projects WHERE project_id = %s"
    cursor.execute(query, (project_id,))
    result = cursor.fetchone()
    cursor.close()
    return result


@staff.route("/dashboard",endpoint="dashboard")
# @staff_login_required
def dashboard():
    user = User.get_user(session["user_id"])

    return render_template(f"staff_dashboard.html", user=user)

# Get all mentors
def get_all_mentors():
    cursor = getCursor()
    query = """SELECT * FROM Mentors where company_id is null;"""
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# get skills for project
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

@staff.route("/dashboard/viewStudent", methods=['GET', 'POST'], endpoint="view_student")
def view_student():
    # Get the user object
    user = User.get_user(session["user_id"])
    sql = ""
    if request.method == "GET":
        sql = "SELECT student_id ,formal_name,alternative_name,preferred_name,email,phone,placement_status from Students"
        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        cursor.execute(sql)
        students = cursor.fetchall()
        return render_template("student_table.html", user=user, students=students)
    elif request.method == "POST":
        student_id = request.form.get('student_id')
        formal_name = request.form.get('formal_name')
        alternative_name = request.form.get('alternative_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        placement_status=request.form.get('placement_status')

        sql = "SELECT student_id,formal_name,alternative_name,preferred_name,email,phone, placement_status from Students where student_id like '%s'and formal_name like '%s' and alternative_name like '%s' and Email like '%s' and phone like '%s' " % (
            "%" + student_id + "%", "%" + formal_name + "%", "%" + alternative_name + "%", "%" + email + "%",
            "%" + phone + "%"+placement_status+"%")
        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        cursor.execute(sql)
        students = cursor.fetchall()
        print(students)
        return render_template("student_table.html", user=user, students=students, student_id=student_id,
                               formal_name=formal_name, alternative_name=alternative_name, email=email, phone=phone)



@staff.route('/download_cv')
@staff_login_required
def download_cv():
    student_id = request.args.get("student_id")
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    # Check if the student has uploaded a CV
    query = "SELECT cv_link FROM students WHERE student_id = %s"
    cursor.execute(query, (student_id,))
    cv_link = cursor.fetchone()
    if not cv_link or not cv_link[0]:
        flash('No CV uploaded for this student', 'error')
        return redirect(url_for('staff.view_student'))
    # Get the CV file path
    filename = cv_link[0].split('/')[-1]
    # cv_path = os.path.join(current_app.root_path, cv_link[0])
    UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
    cv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    print(cv_path)
    if not os.path.exists(cv_path):
        flash('CV file not found', 'error')
        return redirect(url_for('staff.view_student'))
    # Send the CV file for download
    return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], path=filename, as_attachment=True)


@staff.route("/dashboard/student_profile")
def student_profile():
    user = User.get_user(session["user_id"])
    student_id = request.args.get("student_id")
    return redirect(url_for('student.profile', student_id=student_id, role='staff'))



@staff.route("/dashboard/view_student_survey", endpoint="view_student_survey")
def veiw_student_survey():
    user = User.get_user(session["user_id"])
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    sql = "SELECT student_id,survey_response_json from survey_response"

    # try:
    cursor.execute(sql)

    survey_response = cursor.fetchall()
    data = []
    for item in survey_response:
        temp = []
        temp.append(item[0])
        temp.append(json.loads(item[1]))
        data.append(temp)

    print(survey_response)
    return render_template("student_survey.html",data=data, user=user)
    # except Exception as e:
    #     return ("Exception，detail：" + str(e))

    # finally:
    #    mysqldb.close()


@staff.route("/dashboard/view_project_list", endpoint="view_project-list")
@sms_login_required
def veiw_project_list():
    #user = User.get_user(session["user_id"])
    id = request.args.get('id')
    cursor = getCursor()
    sql = "select a.project_name,b.student_id,c.formal_name, c.cv_link,a.placement_status from projects as a join placement as b on a.project_id=b.project_id join students c on b.student_id=c.student_id where a.project_id=%s" % id
    cursor.execute(sql)
    project = cursor.fetchone()
    return render_template("staff_view_project.html", project=project)

@staff.route("/dashboard/add_company", endpoint="add_company", methods=['GET', 'POST'])
@staff_login_required
def add_company():
    user = User.get_user(session["user_id"])
   
    if request.method == "GET":
        #result = find_skills_compaies()
        all_mentors = get_all_mentors()
        if(all_mentors== None):
            all_mentors = []

        return render_template("staff_add_company.html", user=user,all_mentors=all_mentors)
    elif request.method == "POST":

        rec = request.form
        name = rec.get('name')
        detail = rec.get('detail')
        website = rec.get('website')
        mentors = rec.getlist('mentor')

        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        try:
           #add new company into company table
            sql = "Insert into Companies (company_name, company_detail, website) values (%s,%s,%s)"
            cursor.execute(sql,(name,detail,website))
            mysqldb.commit()

           #get id of new company
            sql = "Select company_id from Companies where company_name=%s" 
            cursor.execute(sql,(name,))
            companyid = cursor.fetchone()[0]
            print(companyid)
            mysqldb.commit()

            #update companyid in mentor table
            for mentor in mentors:
                sql = "update mentors set company_id=%s where mentor_id=%s"
                cursor.execute(sql,(companyid,int(mentor.strip(),)))
                mysqldb.commit()

            return redirect(url_for('staff.view-com'))
        except Exception as e:
            mysqldb.rollback()
            return str(e)
        finally:
            mysqldb.close()

@staff.route("/dashboard/view_companylist", methods=['GET', 'POST'], endpoint="view-com")
def view_companylist():
    user = User.get_user(session["user_id"])
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    sql = "SELECT c.company_id, c.company_name, c.company_detail, c.website, GROUP_CONCAT(m.mentor_name) as mentors FROM Companies c LEFT JOIN Mentors m ON c.company_id = m.company_id GROUP BY c.company_id"
    cursor.execute(sql)
    companies = cursor.fetchall()
    print (companies)
    return render_template("staff_view_company.html",companies=companies,user=user)


@staff.route("/dashboard/project_detail", endpoint="project_detail")
@sms_login_required
def project_detail():
    user = User.get_user(session["user_id"])
    company_id = request.args.get('company_id')
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
    sql = """select projects.project_id, projects.project_name, projects.project_description, mentors.mentor_name
             from projects join mentors on projects.mentor_id = mentors.mentor_id 
             where projects.company_id = %s""" 
    cursor.execute(sql,(company_id,))
    projects = cursor.fetchall()

    return render_template("project_detail.html", projects=projects, flag=1, user=user)


@staff.route("/dashboard/view_project", endpoint="view_project")
@sms_login_required
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


    return render_template("staff_view_project.html", result=result, user=user)


@staff.route("/dashboard/edit_company",methods=['GET', 'POST'], endpoint="edit-com")
@staff_login_required
def view_editcompany():
    user = User.get_user(session["user_id"])
    company_id = request.args.get('company_id')
    mysqldb = get_connection()
    cursor = mysqldb.cursor()
   
    #get company information
    sql = "select * from companies where company_id=%s" 
    cursor.execute(sql,(company_id,))
    companies = cursor.fetchone()

    all_mentors = get_all_mentors()
    if(all_mentors== None):
          all_mentors = []
    
    #get mentor information
    sql = "select mentor_name from Mentors where company_id=%s order by mentor_name "
    cursor.execute(sql,(company_id,))
    mentors = cursor.fetchall()
   
    if(mentors == None):
       mentors = []
    else:
        mentors = [item for sublist in mentors for item in sublist] 
    print(mentors)
   # "mentor": mentors

    return render_template("staff_edit_company.html",companies=companies, mentors=mentors, all_mentors=all_mentors, user=user)

@staff.route("/dashboard/update_company", endpoint="update_company", methods=['GET', 'POST'])
@staff_login_required
def update_company():
    user = User.get_user(session["user_id"])
    company_id = request.form.get('companyid')
    print(company_id)
    if request.method == "GET":
        return render_template("staff_edit_company.html", user=user)
    elif request.method == "POST":

        rec = request.form
        name = rec.get('name')
        detail = rec.get('detail')
        website = rec.get('website')

        all_mentors = get_all_mentors()
        if(all_mentors== None):
            all_mentors = []

        mysqldb = get_connection()
        cursor = mysqldb.cursor()
        try:

            sql = "Update Companies set Company_name = %s,company_detail = %s, website=%s where company_id=%s"

            cursor.execute(sql,(name,detail,website,company_id,))

            mysqldb.commit()
            return redirect(url_for('staff.view-com'))
        except Exception as e:
            mysqldb.rollback()
            return str(e)
        finally:
            mysqldb.close()

# Student selection machine learning model
@staff.route("/project_selection", endpoint="project_selection")
@staff_login_required
def student_selection():
    
    predication_model.skill_based_prediction()
    
    
    user = {
        "username": session["username"],
        "role": session["role"]
    }
    # Get all the students
    cursor = getCursor()
    query = """
        SELECT
            Students.student_id,
            Students.formal_name,
            Students.alternative_name,
            Students.preferred_name,
            Students.email,
            Students.phone,
            GROUP_CONCAT(Projects.project_name SEPARATOR ', ') AS preferred_projects
        FROM Students
        LEFT JOIN Placement ON Students.student_id = Placement.student_id
        LEFT JOIN Projects ON Placement.project_id = Projects.project_id
        GROUP BY
            Students.student_id, Students.formal_name,
            Students.alternative_name,
            Students.preferred_name,
            Students.email,
            Students.phone;
    """
    cursor.execute(query)
    students = cursor.fetchall()
    
    projects_tuple = get_all_projects()
    # Convert the tuple array to a list of dictionaries
    projects = [{'id': item[0], 'name': item[1]} for item in projects_tuple]
    return render_template('project_selection.html', students=students, user=user, projects=projects)

@staff.route("/project_auto_selection", methods=['Get','POST'], endpoint="project_auto_selection")
@staff_login_required
def student_auto_selection():
    if request.method == "GET":
        # Get student id from the request
        student_id = request.args.get('studentId')
        try:
            # Get student skills
            student_skills = get_student_skills(student_id)

            if(student_skills == None):
                student_skills = []
            else:
                student_skills = [item for sublist in student_skills for item in sublist]
            
            # student project selection simulation - Skill based
            projects_auto_selected = predication_model.student_project_selection(student_skills)
             # student project selection - Event based
            projects_event_base_selection = predication_model.speed_event_based_prediction_for_student()
            
            # Get student's ids
            projects_id = []
            for item in projects_event_base_selection:
                if item['student_id'] == student_id:
                    projects_id.append(item['projects'])
            
            # Get student details
            projects_event_based_details = []
            for project_id in projects_id[0]:
                project = get_project_by_id(project_id)
                print('Project: ', project)
                if project == None:
                    continue
                projects_event_based_details.append({
                    "name": project[0],
                    "id": project_id
                })

            response_data = {
                'message': 'Received studentId successfully',
                'studentId': student_id,
                'projects_auto_selected': projects_event_based_details,
                'student_skills': student_skills
            }
            json_data = json.dumps(response_data)
            return Response(json_data, mimetype='application/json', status=200)
        except Exception as e:
            return Response(json_data, mimetype='application/json', status=500)
    elif request.method == "POST":
        # Get data from form submission
        student_id = request.form.get("student_id_auto")
        projects = request.form.getlist('projects_auto')
        staff_user_id = session["user_id"]
        staff_id = get_staff_id(staff_user_id)
        
        # Remove all the projects for the student
        cursor = getCursor()
        query = "DELETE FROM Placement WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        cursor.close()
        
        # create a list data structure to store the data
        for project in projects:
            # Insert the data into the database
            cursor = getCursor()
            query = "INSERT INTO Placement (student_id, project_id, staff_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (student_id, project, staff_id))
            cursor.close()
        
        
        # Return the response with appropriate headers
        return redirect(url_for("staff.project_selection"))
    
@staff.route("/project_manual_selection", methods=['POST'], endpoint="project_manual_selection")
@staff_login_required
def student_manual_selection():
    if request.method == "POST":
        # Get data from form submission
        student_id = request.form.get("student_id_manual")
        projects = request.form.getlist('projects_manual')
        staff_user_id = session["user_id"]
        staff_id = get_staff_id(staff_user_id)
        
        # Remove all the projects for the student
        cursor = getCursor()
        query = "DELETE FROM Placement WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        cursor.close()
        
        # create a list data structure to store the data
        for project in projects:
            # Insert the data into the database
            cursor = getCursor()
            query = "INSERT INTO Placement (student_id, staff_id, project_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (student_id, staff_id, project))
            cursor.close()
        
        
        # Return the response with appropriate headers
        return redirect(url_for("staff.project_selection"))


# Project selection machine learning model
@staff.route("/student_selection", endpoint="student_selection")
@staff_login_required



def project_selection():
    user = {
        "username": session["username"],
        "role": session["role"]
    }
    # Get all the students
    cursor = getCursor()
    query = """
        SELECT 
            p.project_id,
            p.project_name,
            p.project_description,
            c.company_name,
            m.mentor_name,
            m.mentor_id,
            m.mentor_email,
            GROUP_CONCAT(Students.formal_name SEPARATOR ', ') AS preferred_students
        FROM Projects AS p
        LEFT JOIN Companies AS c ON c.company_id = p.company_id
        LEFT JOIN Placement ON p.project_id = Placement.project_id
        LEFT JOIN Students ON Placement.student_id = Students.student_id
        LEFT JOIN Mentors AS m ON m.mentor_id = p.mentor_id
        GROUP BY
			p.project_id,
            p.project_name,
            p.project_description,
            c.company_name,
            m.mentor_name,
            m.mentor_id,
            m.mentor_email
    """
    cursor.execute(query)
    projects = cursor.fetchall()
    
    students_tuple = get_all_students()
    # Convert the tuple array to a list of dictionaries
    students = [{'id': item[0], 'name': item[1]} for item in students_tuple]
    return render_template('student_selection.html', students=students, user=user, projects=projects)

@staff.route("/student_auto_selection", methods=['Get','POST'], endpoint="student_auto_selection")
@staff_login_required
def project_auto_selection():
    if request.method == "GET":
        # Get student id from the request
        project_id = request.args.get('projectId')
        print('Project id: ', project_id)
        try:
            # Get student skills
            project_skills = get_project_skills(project_id)

            if(project_skills == None):
                project_skills = []
            else:
                project_skills = [item for sublist in project_skills for item in sublist]
            
            # student project selection - Skill based
            students_auto_selected = predication_model.skill_based_prediction()
            # student project selection - Event based
            students_event_base_selection = predication_model.speed_event_based_prediction_for_project()
            
            # Get student's ids
            students_id = []
            for item in students_event_base_selection:
                if item['project_id'] == project_id:
                    students_id.append(item['students'])
            
            # Get student details
            students_event_based_details = []
            for student_id in students_id[0]:
                student = get_student_by_id(student_id)
                print('Student: ', student)
                if student == None:
                    continue
                students_event_based_details.append({
                    "name": student[0],
                    "id": student_id
                })

            response_data = {
                'message': 'Received studentId successfully',
                'projectId': project_id,
                'students_auto_selected': students_event_based_details,
                'project_skills': project_skills
            }
            json_data = json.dumps(response_data)
            return Response(json_data, mimetype='application/json', status=200)
        except Exception as e:
            return Response(json_data, mimetype='application/json', status=500)
    elif request.method == "POST":
         # Get data from form submission
        project_id = request.form.get("project_id_auto")
        students = request.form.getlist('students_auto')
        staff_user_id = session["user_id"]
        staff_id = get_staff_id(staff_user_id)
        
        # Remove all the projects for the student
        cursor = getCursor()
        query = "DELETE FROM Placement WHERE project_id = %s"
        cursor.execute(query, (project_id,))
        cursor.close()
        
        # create a list data structure to store the data
        for student in students:
            # Insert the data into the database
            cursor = getCursor()
            query = "INSERT INTO Placement (student_id, staff_id, project_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (student, staff_id, project_id))
            cursor.close()
        
        
        # Return the response with appropriate headers
        return redirect(url_for("staff.student_selection"))
    
@staff.route("/student_manual_selection", methods=['POST'], endpoint="student_manual_selection")
@staff_login_required
def project_manual_selection():
    if request.method == "POST":
        # Get data from form submission
        project_id = request.form.get("project_id_manual")
        students = request.form.getlist('students_manual')
        staff_user_id = session["user_id"]
        staff_id = get_staff_id(staff_user_id)
        
        # Remove all the projects for the student
        cursor = getCursor()
        query = "DELETE FROM Placement WHERE project_id = %s"
        cursor.execute(query, (project_id,))
        cursor.close()
        
        # create a list data structure to store the data
        for student in students:
            # Insert the data into the database
            cursor = getCursor()
            query = "INSERT INTO Placement (student_id, staff_id, project_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (student, staff_id, project_id))
            cursor.close()
        
        
        # Return the response with appropriate headers
        return redirect(url_for("staff.student_selection"))
    
@staff.route("/notify_mentor", methods=['POST'], endpoint="notify_mentor")
@staff_login_required
def notify_mentor():
   if request.method == "POST":
        # Get data from form submission
        mentor_id = request.form.get("mentor_id")
        subject = request.form.get("subject")
        message = request.form.get("message")
        
        mentor = get_mentor_by_id(mentor_id)
        
        if (mentor == None):
            error = "Mentor not found"
            flash(error, "error")
            return redirect(url_for("staff.student_selection"))
        
        # Send email to the mentor
        send_mail(subject, mentor[1], message)
        
        # Return the response with appropriate headers
        return redirect(url_for("staff.student_selection"))

@staff.route("/speed_networking_preference", methods=['GET', 'POST'], endpoint="speed_networking_preference")
def student_speed_event_data():
    if request.method == "GET":
        student_id = request.args.get("studentId")
        print('Student id: ', student_id)
        # Get candidate preference from the database
        cursor = getCursor()
        query = "SELECT project_id, score FROM Candidate_Preference WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        # retun json data
        cadiadate_preference = cursor.fetchall()
        
        print(cadiadate_preference)
        cursor.close()
        return [{"project_id": item[0], "score": item[1]} for item in cadiadate_preference]
    if request.method == "POST":
        # Get data from form submission
        student_id = request.form.get("student_id")
        # project_id = request.form.get("project_id")
        # score = request.form.get("score")
        
        scores = []
        for key, value in request.form.items():
            print(key, value)
            if key.startswith('project_'):
                project_id = int(key.split('_')[1])
                score = int(value)
                scores.append({'student_id': student_id, 'project_id': project_id, 'score': score})
        # Process the scores as needed
        # Prepare the SQL statement for inserting data into the table
        cursor = getCursor()
        insert_query = '''
            INSERT INTO Candidate_Preference (student_id, project_id, score)
            VALUES (%s, %s, %s)
        '''
        
        # Prepare the SQL statement for updating data in the table
        update_query = '''
            UPDATE Candidate_Preference
            SET score = %s
            WHERE student_id = %s AND project_id = %s
        '''
        # Insert the data into the table
        for entry in scores:
            student_id = entry['student_id']
            project_id = entry['project_id']
            score = entry['score']
            
            # Check if the record already exists in the table
            select_query = '''
                SELECT COUNT(*) FROM Candidate_Preference
                WHERE student_id = %s AND project_id = %s
            '''
            
            cursor.execute(select_query, (student_id, project_id))
            record_exists = cursor.fetchone()[0]
            
            if record_exists:
                # Update the existing record
                cursor.execute(update_query, (score, student_id, project_id))
                print(f"Record updated: student_id={student_id}, project_id={project_id}, score={score}")
            else:
                # Insert a new record
                cursor.execute(insert_query, (student_id, project_id, score))
                print(f"Record inserted: student_id={student_id}, project_id={project_id}, score={score}")

            
        cursor.close()
    
        # Return the response with appropriate headers
        return redirect(url_for("staff.project_selection"))