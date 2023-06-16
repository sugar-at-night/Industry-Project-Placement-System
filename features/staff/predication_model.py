import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

from db.db import get_connection,getCursor


def student_project_selection(candidate_skills):
    # Load the JSON dataset
    with open('features/staff/datasets/project_dataset.json', 'r') as f:
        candidate_data = json.load(f)

    # New candidate skills - ['Python', 'Java']
    new_candidate_skills = candidate_skills

    # Define the threshold for suitability
    threshold = 0.1

    # Predict suitable projects for the new candidate
    suitable_projects = predict_project_suitability(new_candidate_skills, candidate_data, threshold)
        
    return suitable_projects

def convert_suitability_to_label(suitability, threshold):
    # Convert suitability values to binary labels
    return [1 if s >= threshold else 0 for s in suitability]

def predict_project_suitability(candidate_skills, candidate_data, threshold):
    # Step 1: Prepare the data
    project_skills = {}
    candidate_skill_set = set(candidate_skills)

    for candidate in candidate_data:
        skills = set(candidate['skills'])
        project = candidate['project']['name']
        project_id = candidate['project']['id']

        if project in project_skills:
            project_skills[project]['skills'] |= skills
        else:
            project_skills[project] = {'skills': skills, 'id': project_id}

    # Step 2: Calculate the similarity score
    similarity_scores = []
    for project, project_info in project_skills.items():
        skills = project_info['skills']
        project_id = project_info['id']

        similarity = len(candidate_skill_set.intersection(skills)) / len(candidate_skill_set.union(skills))
        similarity_scores.append({'project': project, 'similarity': similarity, 'id': project_id})

    # Step 3: Sort the projects by similarity score in descending order
    sorted_projects = sorted(similarity_scores, key=lambda x: x['similarity'], reverse=True)

    # Step 4: Filter the projects based on the suitability threshold
    suitable_projects = [{'name': project['project'], 'id': project['id']} for project in sorted_projects if project['similarity'] >= threshold]

    return suitable_projects

def predict_candidates(candidate_data, model):
    # Prepare the data
    candidates = []
    skills = []

    for candidate in candidate_data:
        candidates.append(candidate['name'])
        skills.append(','.join(candidate['skills']))

    # Create a DataFrame
    df = pd.DataFrame({'Candidate': candidates, 'Skills': skills})

    # Convert skills into dummy variables
    df = pd.get_dummies(df, columns=['Skills'])

    # Predict suitability using the trained model
    X = df.drop('Candidate', axis=1)
    suitability = model.predict(X)

    # Assign suitability to each candidate
    df['Suitability'] = suitability

    # Sort the candidates by suitability in descending order
    sorted_candidates = df.sort_values('Suitability', ascending=False)

    # Get the top 5 suitable candidates
    top_candidates = sorted_candidates.head(5)

    return top_candidates['Candidate'].tolist()


def skill_based_prediction():
    # Load project and candidate data
    with open('features/staff/datasets/project_dataset.json', 'r') as projects_file:
        projects_data = json.load(projects_file)

    with open('features/staff/datasets/candidate_dataset.json', 'r') as candidate_file:
        candidate_data = json.load(candidate_file)

    # Extract project skills and suitability into separate lists
    project_skills = []
    project_suitability = []

    for project in projects_data:
        skills = ' '.join(project['skills'])
        project_skills.append(skills)
        project_suitability.append(project['suitability'])

    # Create a DataFrame for project data
    project_df = pd.DataFrame({'skills': project_skills, 'suitability': project_suitability})

    # Create a CountVectorizer object
    vectorizer = CountVectorizer()

    # Fit and transform the project skills into a skill matrix
    skill_matrix = vectorizer.fit_transform(project_df['skills'])

    # Train the model using the skill matrix and project suitability
    model = LinearRegression()
    model.fit(skill_matrix, project_df['suitability'])

    # Iterate over each candidate and find the cosine similarity with project skills
    suitability_scores = []
    for candidate in candidate_data:
        candidate_skills = ' '.join(candidate['skills'])
        candidate_matrix = vectorizer.transform([candidate_skills])
        similarity = cosine_similarity(candidate_matrix, skill_matrix)[0]
        predicted_suitability = model.predict(candidate_matrix)
        suitability_scores.append({'candidate': candidate['name'], 'suitability': predicted_suitability[0], 'similarity': similarity})

    # Sort the candidates based on suitability score in descending order
    sorted_candidates = sorted(suitability_scores, key=lambda x: x['suitability'], reverse=True)

    # Get the top 5 suitable candidates
    top_candidates = sorted_candidates[:5]

    candidates = []
    # Print the top suitable candidates
    i = 1
    for candidate in top_candidates:
        print(candidate['candidate'])
        candidates.append({
            'name': candidate['candidate'],
            'id': str(i)
            })
        i += 1
        
    return candidates

# Speed Event based prediction of project for each student.
def speed_event_based_prediction_for_student():
    # Load the JSON datasets
    # TODO - Load the data from the database
    with open('features/staff/datasets/candidate_preferrence.json', 'r') as f:
        candidate_preference = json.load(f)
    
    # print(candidate_preference)
    # print(get_candidate_preferences())
    candidate_preference = get_candidate_preferences()

    # TODO - Load the data from the database
    with open('features/staff/datasets/host_preferrence.json', 'r') as f:
        project_preference = json.load(f)
        
    print(project_preference)
    print(get_host_preferences())
    project_preference = get_host_preferences()
    
    
    # Create DataFrames from the candidate and project preference data
    # return find_matching_projects(candidate_preference, project_preference)
    return select_projects(candidate_preference, project_preference)

# Speed Event based prediction of student for each project.
def speed_event_based_prediction_for_project():
    # Load the JSON datasets
    # TODO - Load the data from the database
    with open('features/staff/datasets/candidate_preferrence.json', 'r') as f:
        candidate_preference = json.load(f)

    # TODO - Load the data from the database
    with open('features/staff/datasets/host_preferrence.json', 'r') as f:
        project_preference = json.load(f)
        
    # Create DataFrames from the candidate and project preference data
    # return find_matching_students(candidate_preference, project_preference)
    return select_students(candidate_preference, project_preference)


def find_matching_projects(student_preferences, host_preferences):
    matching_projects = []

    # Iterate over each student's preferences
    for student_pref in student_preferences:
        student_id = student_pref["student_id"]
        preferences = student_pref["preferences"]

        # Sort the student's preferences based on the score in descending order
        sorted_preferences = sorted(preferences, key=lambda x: x["score"], reverse=True)

        # Keep track of the number of projects matched for the student
        projects_matched = 0
        projects_for_student = []  # List to store projects for the student

        # Iterate over each preference and find matching hosts
        for pref in sorted_preferences:
            if projects_matched >= 3:
                break  # Stop matching projects if the student has already been matched with 3 projects

            project_id = pref["project_id"]
            score = pref["score"]

            # Find the host preferences for the current project
            host_pref = next((h for h in host_preferences if h["project_id"] == project_id), None)
            if host_pref is None:
                continue

            # Find the host with the highest score among the preferences
            max_score = 0
            max_host_id = None
            for host in host_pref["preferences"]:
                host_id = host["student_id"]
                host_score = host["score"]
                if host_score > max_score:
                    max_score = host_score
                    max_host_id = host_id

            # Add the matching project to the list
            if max_host_id == student_id:
                projects_for_student.append(project_id)
                projects_matched += 1

        # Add the student and their matched projects to the final list
        if projects_for_student:
            matching_projects.append({"student_id": student_id, "projects": projects_for_student})
            
    return matching_projects

# Find matching students for each project
def find_matching_students(student_preferences, host_preferences):
    matching_projects = []

    # Iterate over each project's preferences
    for host_pref in host_preferences:
        project_id = host_pref["project_id"]
        preferences = host_pref["preferences"]

        # Sort the project's preferences based on the score in descending order
        sorted_preferences = sorted(preferences, key=lambda x: x["score"], reverse=True)

        # Keep track of the number of students matched for the project
        students_matched = 0

        # Iterate over each preference and find matching students
        for pref in sorted_preferences:
            if students_matched >= 5:
                break  # Stop matching students if the project has already been matched with 5 students

            student_id = pref["student_id"]
            score = pref["score"]

            # Find the student preferences for the current student
            student_pref = next((s for s in student_preferences if s["student_id"] == student_id), None)
            if student_pref is None:
                continue

            # Find the student with the highest score among the preferences
            max_score = 0
            max_student_id = None
            for student in student_pref["preferences"]:
                student_project_id = student["project_id"]
                student_score = student["score"]
                if student_score > max_score:
                    max_score = student_score
                    max_student_id = student_project_id

            # Add the matching project to the list
            if max_student_id == project_id:
                matching_projects.append({"project_id": project_id, "students": []})
                students_matched += 1

    # Iterate over each project and add the matched students to the respective project
    for project in matching_projects:
        project_id = project["project_id"]

        # Iterate over the student preferences and find the matching students for the project
        for student_pref in student_preferences:
            student_id = student_pref["student_id"]

            # Find the highest scored project in the student preferences
            max_score = 0
            max_project_id = None
            for student in student_pref["preferences"]:
                student_project_id = student["project_id"]
                student_score = student["score"]
                if student_score > max_score:
                    max_score = student_score
                    max_project_id = student_project_id

            # Add the student to the project if it matches
            if max_project_id == project_id:
                project["students"].append(student_id)
    return matching_projects

# Select the top 5 projects for each student
def select_projects(student_preferences, project_preferences):
    selected_projects = []
    
    # Iterate over each student's preferences
    for student_pref in student_preferences:
        student_id = student_pref["student_id"]
        preferences = student_pref["preferences"]

        # Sort the student's preferences based on the score in descending order
        sorted_student_preferences = sorted(preferences, key=lambda x: x["score"], reverse=True)
        
        project_scores = get_project_scores(project_preferences, student_id)

        merged_dict = {}

        # Merge the arrays
        for item in sorted_student_preferences + project_scores:
            project_id = item['project_id']
            score = item['score']
            if project_id in merged_dict:
                # Add the scores together if the project ID already exists
                merged_dict[project_id] += score
            else:
                # Initialize the score if the project ID is new
                merged_dict[project_id] = score

        # Sort the dictionary based on score in descending order
        sorted_dict = sorted(merged_dict.items(), key=lambda x: x[1], reverse=True)
        # Output the top 5 project IDs and scores
        project_ids = []
        for project_id, score in sorted_dict[:5]:
            project_ids.append(project_id)
            
        selected_projects.append({ "student_id": student_id, "projects": project_ids})
        
    return selected_projects

# Get the project scores for a student
def get_project_scores(data, student_id):
    project_scores = []
    
    for project in data:
        project_id = project["project_id"]
        preferences = project["preferences"]
        
        for preference in preferences:
            if preference["student_id"] == student_id:
                score = preference["score"]
                project_scores.append({ "project_id": project_id, "score": score})
    
    return project_scores


def select_students(student_preferences, project_preferences):
    selected_students = []
    
    for project_pref in project_preferences:
        project_id = project_pref["project_id"]
        preferences = project_pref["preferences"]

        # Sort the project's preferences based on the score in descending order
        sorted_project_preferences = sorted(preferences, key=lambda x: x["score"], reverse=True)
        
        student_scores = get_student_scores(student_preferences, project_id)

        merged_dict = {}

        # Merge the arrays
        for item in sorted_project_preferences + student_scores:
            student_id = item['student_id']
            score = item['score']
            if student_id in merged_dict:
                # Add the scores together if the student ID already exists
                merged_dict[student_id] += score
            else:
                # Initialize the score if the student ID is new
                merged_dict[student_id] = score

        # Sort the dictionary based on score in descending order
        sorted_dict = sorted(merged_dict.items(), key=lambda x: x[1], reverse=True)
        # Output the top 5 project IDs and scores
        student_ids = []
        for student_id, score in sorted_dict[:5]:
            student_ids.append(student_id)
            
        selected_students.append({ "project_id": project_id, "students": student_ids})
    print(selected_students)
    return selected_students

# Get the project scores for a student
def get_student_scores(data, project_id):
    student_scores = []
    
    for student in data:
        student_id = student["student_id"]
        preferences = student["preferences"]
        
        for preference in preferences:
            if preference["project_id"] == project_id:
                score = preference["score"]
                student_scores.append({ "student_id": student_id, "score": score})
        
    
    return student_scores

#  Get the candidate preferences for each project form db
def get_candidate_preferences():
    query = """
    SELECT cp.student_id, cp.project_id, cp.score
    FROM Candidate_Preference cp
    ORDER BY cp.student_id
    """
    cursor = getCursor()
    cursor.execute(query)
    results = cursor.fetchall()

    # Create a dictionary to store the output
    output = []

    # Iterate over the query results and build the output structure
    current_student_id = None
    current_preferences = []

    for row in results:
        if current_student_id is None:
            current_student_id = row[0]  # Assuming student_id is the first column
        elif current_student_id != row[0]:
            output.append({"student_id": str(current_student_id), "preferences": current_preferences})
            current_preferences = []
            current_student_id = row[0]

        current_preferences.append({"project_id": str(row[1]), "score": row[2]})  # Assuming project_id is the second column and score is the third column

    # Add the last student's preferences to the output
    if current_student_id is not None:
        output.append({"student_id": str(current_student_id), "preferences": current_preferences})

    # Convert the output to JSON
    # output_json = json.dumps(output, indent=2)

    # Print the output
    return output


#  Get the host preferences for each project form db
def get_host_preferences():
    # Query the database to get the host preferences
    query = """
    SELECT hp.project_id, hp.student_id, hp.score
    FROM Host_Preference hp
    ORDER BY hp.project_id
    """
    cursor = getCursor()
    cursor.execute(query)
    results = cursor.fetchall()

    # Create a dictionary to store the output
    output = []

    # Iterate over the query results and build the output structure
    current_project_id = None
    current_preferences = []

    for row in results:
        if current_project_id is None:
            current_project_id = row[0]  # Assuming project_id is the first column
        elif current_project_id != row[0]:
            output.append({"project_id": str(current_project_id), "preferences": current_preferences})
            current_preferences = []
            current_project_id = row[0]

        current_preferences.append({"student_id": str(row[1]), "score": row[2]})  # Assuming student_id is the second column and score is the third column

    # Add the last project's preferences to the output
    if current_project_id is not None:
        output.append({"project_id": str(current_project_id), "preferences": current_preferences})

    # Convert the output to JSON
    # output_json = json.dumps(output, indent=2)

    # Print the output
    return output



