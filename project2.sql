DROP SCHEMA IF EXISTS Project2;
CREATE SCHEMA Project2;
USE Project2;

CREATE TABLE Users (
    `user_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `role` ENUM('student', 'mentor', 'staff') NOT NULL,
    `recovery_email` VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE Skills (
    `skill_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `skill_name` VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE Students (
    `student_id` INTEGER PRIMARY KEY,
    `user_id` INTEGER NOT NULL UNIQUE,
    `formal_name` VARCHAR(50) NOT NULL,
    `alternative_name` VARCHAR(50),
    `preferred_name` VARCHAR(50),
    `email` VARCHAR(255) NOT NULL,
    `phone` VARCHAR(20) NOT NULL,
    `city` VARCHAR(45) NOT NULL,
    `cv_link` VARCHAR(255),
    `project_preference` TEXT,
    `semester` ENUM('1', '2', '3') NOT NULL,
    `placement_status` ENUM('Not Looking', 'Actively Looking', 'Placed') NOT NULL,
    CONSTRAINT `fk_student_user_i` FOREIGN KEY (`user_id`) REFERENCES Users(`user_id`) ON DELETE CASCADE
);


CREATE TABLE Companies (
    `company_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `company_name` VARCHAR(255) NOT NULL,
    `company_detail` TEXT NOT NULL,
    `website` VARCHAR(255)
);

CREATE TABLE Mentors (
    `mentor_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `user_id` INTEGER NOT NULL UNIQUE,
    `company_id` INTEGER,
    `mentor_name` VARCHAR(255) NOT NULL,
    `mentor_email` VARCHAR(255) NOT NULL,
    `mentor_phone` VARCHAR(20) NOT NULL,
    CONSTRAINT `fk_mentor_user_id` FOREIGN KEY (`user_id`) REFERENCES Users(`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mentor_company_id` FOREIGN KEY (`company_id`) REFERENCES Companies(`company_id`) ON DELETE CASCADE
);

CREATE TABLE Staff (
    `staff_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `user_id` INTEGER NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL,
	`staff_name` VARCHAR(255) NOT NULL,
    CONSTRAINT `fk_staff_user_id` FOREIGN KEY (`user_id`) REFERENCES Users(`user_id`) ON DELETE CASCADE
);


CREATE TABLE Projects (
    `project_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `project_name` VARCHAR(255) NOT NULL,
    `project_type` VARCHAR(50) NOT NULL,
    `project_description` TEXT NOT NULL,
    `project_location` VARCHAR(50) NOT NULL,
    `company_id` INTEGER NOT NULL,
    `mentor_id` INTEGER NOT NULL,
    `num_students_required` INTEGER NOT NULL,
    `placement_status` ENUM('Not Looking', 'Actively Looking', 'Filled') DEFAULT 'Actively Looking' NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_project_company_id` FOREIGN KEY (`company_id`) REFERENCES `Companies`(`company_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_project_mentor_id` FOREIGN KEY (`mentor_id`) REFERENCES `Mentors`(`mentor_id`) ON DELETE CASCADE
);


CREATE TABLE Student_Skills (
    student_id INTEGER,
    skill_id INTEGER,
    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id),
    PRIMARY KEY (student_id, skill_id)
);

CREATE TABLE Project_Skills (
    project_id INTEGER,
    skill_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id),
    PRIMARY KEY (project_id, skill_id)
);

CREATE TABLE `PreferredStudents` (
    `ps_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `project_id` INTEGER NOT NULL,
    `student_id` INTEGER NOT NULL,
	`status` ENUM('Selected', 'Preferred', 'Pending', 'Interview','NotSele', 'Declined', 'Accepted', 'NotAvl') DEFAULT 'Pending' NOT NULL,
    CONSTRAINT `fk_ps_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ps_project_id` FOREIGN KEY (`project_id`) REFERENCES `Projects`(`project_id`),
    CONSTRAINT `unique_preferred_students` UNIQUE (`ps_id`, `student_id`)
);

CREATE TABLE `WishList` (
    `wish_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `student_id` INTEGER NOT NULL,
    `project_id` INTEGER NOT NULL,
    `rank` INTEGER NOT NULL,
    CONSTRAINT `fk_wish_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_wish_project_id` FOREIGN KEY (`project_id`) REFERENCES `Projects`(`project_id`) ON DELETE CASCADE,
    CONSTRAINT `unique_wish_list_rank` UNIQUE (`student_id`, `rank`)
);

CREATE TABLE `Placement` (
    `student_id` INTEGER NOT NULL,
    `project_id` INTEGER NOT NULL,
    `placement_status` ENUM('pending', 'approved', 'failed') DEFAULT 'pending' NOT NULL,
    `staff_id` INTEGER NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `pk_placement` PRIMARY KEY (`student_id`, `project_id`),
    CONSTRAINT `fk_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`),
    CONSTRAINT `fk_staff_id` FOREIGN KEY (`staff_id`) REFERENCES `Staff`(`staff_id`),
    CONSTRAINT `fk_project_id` FOREIGN KEY (`project_id`) REFERENCES `Projects`(`project_id`)
);

-- Create a survey table
CREATE TABLE `Survey` (
    `survey_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `survey_name` VARCHAR(255) NOT NULL,
    `survey_description` TEXT NOT NULL,
    `survey_question_json` Json NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `unique_survey_name` UNIQUE (`survey_name`)
);

-- Create a survey response table
CREATE TABLE `Survey_Response` (
    `survey_response_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `survey_id` INTEGER NOT NULL,
    `student_id` INTEGER NOT NULL,
    `survey_response_json` Json NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_survey_response_survey_id` FOREIGN KEY (`survey_id`) REFERENCES `Survey`(`survey_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_survey_response_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`) ON DELETE CASCADE
);

-- Create a survey completion table
CREATE TABLE `Survey_Completion` (
    `survey_completion_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
    `survey_id` INTEGER NOT NULL,
    `student_id` INTEGER NOT NULL,
    `survey_completion_status` ENUM('completed', 'incomplete') NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_survey_completion_survey_id` FOREIGN KEY (`survey_id`) REFERENCES `Survey`(`survey_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_survey_completion_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`) ON DELETE CASCADE
);

-- Initisalise the database with some data. password genarate with sha2 256 hash.
INSERT INTO Users (username, password, role, recovery_email) Values ('student1', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student1@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('student2', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student2@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('student3', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student3@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('student4', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'studnet4@example.com');

-- Initialise user for mentor. pw: student1
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor1', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor1@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor2', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor2@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor3', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor3@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor4', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor4@example.com');

-- Initialise user for staff. pw: student1
INSERT INTO Users (username, password, role, recovery_email) Values ('staff1', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'staff', 'staff1@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('staff2', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'staff', 'staff2@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('staff3', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'staff', 'staff3@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('staff4', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'staff', 'staff4@example.com');

--- Initialise the more mentor table
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor5', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor5@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor6', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor6@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor7', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor7@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor8', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor8@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor9', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor9@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('mentor10', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'mentor', 'mentor10example.com');

-- Initialise more students
INSERT INTO Users (username, password, role, recovery_email) Values ('student5', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student5@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('student6', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student6@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('student7', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student7@example.com');
INSERT INTO Users (username, password, role, recovery_email) Values ('student8', '509e87a6c45ee0a3c657bf946dd6dc43d7e5502143be195280f279002e70f7d9', 'student', 'student8@example.com');

-- Inistialise the student table
INSERT INTO Students (student_id, user_id, formal_name, alternative_name, preferred_name, email, phone, city, project_preference) VALUES (1, 1, 'Student 1', 'Student 1', 'Student 1', 'student1@example.com', '0220652158', 'Auckland', 'I would like to work on a project that is related to machine learning.');
INSERT INTO Students (student_id, user_id, formal_name, alternative_name, preferred_name, email, phone, city, project_preference) VALUES (2, 2, 'Student 2', 'Student 2', 'Student 2', 'student2@example.com', '0220352158', 'Auckland', 'I would like to work on a project that is related to machine learning.');
INSERT INTO Students (student_id, user_id, formal_name, alternative_name, preferred_name, email, phone, city, project_preference) VALUES (3, 3, 'Student 3', 'Student 3', 'Student 3', 'student3@example.com', '0220252158', 'Auckland', 'I would like to work on a project that is related to machine learning.');
INSERT INTO Students (student_id, user_id, formal_name, alternative_name, preferred_name, email, phone, city, project_preference) VALUES (4, 4, 'Student 4', 'Student 4', 'Student 4', 'student4@example.com', '0220152158', 'Auckland', 'I would like to work on a project that is related to machine learning.');
INSERT INTO Students (student_id, user_id, formal_name, alternative_name, preferred_name, email, phone, city, project_preference) VALUES (5, 19, 'Student 5', 'Student 5', 'Student 5', 'student5@example.com', '0220256985', 'Auckland', 'I would like to work on a project that is related to machine learning.');
INSERT INTO Students (student_id, user_id, formal_name, alternative_name, preferred_name, email, phone, city, project_preference) VALUES (6, 20, 'Student 6', 'Student 6', 'Student 6', 'student6@example.com', '0220256985', 'Auckland', 'I would like to work on a project that is related to machine learning.');

-- Initisalise survey questions
INSERT INTO Survey (survey_name, survey_description, survey_question_json) VALUES ('Student Survey', 'Student Survey', '{
	"title": "Industry Project: Student Information Survey",
	"pages": [{
			"questions": [{
					"type": "text",
					"name": "full_name",
					"title": "Formal full name, i.e., the name on your passport or official documents, including your family name.",
					"placeHolder": "Jon Snow",
					"isRequired": "true"
				},
				{
					"type": "text",
					"name": "preferred_name",
					"title": "Preferred name, i.e., the name you would like to be called by.",
					"placeHolder": "Jon",
					"isRequired": "true"
				},
				{
					"type": "text",
					"name": "email",
					"title": "Please enter your student email:",
					"placeHolder": "",
					"isRequired": "true",
					"validators": [{
						"type": "email"
					}]
				},
				{
					"name": "phone",
					"type": "text",
					"title": "Please enter your phone number:",
					"placeHolder": "0224567890",
					"isRequired": "true",
					"validators": [{
						"type": "numeric",
						"minValue": "100000000",
						"maxValue": "999999999"
					}]
				},
				{
					"name": "location",
					"type": "dropdown",
					"title": "Please select your location:",
					"isRequired": "true",
					"colCount": "0",
					"choices": [
						"Auckland",
						"Wellington",
						"Christchurch",
						"Hamilton",
						"Tauranga",
						"Napier-Hastings",
						"Dunedin",
						"Palmerston North",
						"Nelson",
						"Rotorua",
						"New Plymouth",
						"Whangarei",
						"Invercargill",
						"Whanganui",
						"Gisborne"
					],
					"otherText": "Other (please specify)"
				}
			]
		},
		{
			"questions": [{
				"name": "skills",
				"type": "checkbox",
				"title": "Please select your skills:",
				"isRequired": "true",
				"colCount": "0",
				"choices": [
					"Java",
					"Python",
					"C#",
					"C++",
					"C",
					"JavaScript",
					"PHP",
					"SQL",
					"HTML",
					"CSS",
					"Swift",
					"Objective-C",
					"Ruby",
					"R",
					"Matlab",
					"Kotlin",
					"Scala",
					"Go",
					"Perl",
					"Rust",
					"Dart",
					"Haskell",
					"Lua",
					"Julia",
					"TypeScript",
					"Assembly",
					"VBA",
					"Visual Basic",
					"Groovy",
					"Delphi",
					"PL/SQL",
					"Visual Basic .NET",
					"D",
					"Elixir",
					"Clojure",
					"F#",
					"COBOL",
					"Ada",
					"Lisp",
					"Fortran",
					"Prolog",
					"Scheme",
					"Logo",
					"Scratch",
					"ABAP",
					"Apex",
					"Bash",
					"Erlang",
					"LabVIEW",
					"Ladder Logic",
					"Objective-J",
					"OpenEdge ABL",
					"OpenSCAD",
					"PL/I",
					"PostScript",
					"PowerShell",
					"PureScript",
					"Q#",
					"RPG",
					"Smalltalk",
					"Tcl",
					"Verilog",
					"VHDL",
					"XQuery",
					"Z shell"
				],
				"otherText": "Other (please specify)",
				"hasOther": "true"
			}]
		},
		{
			"questions": [
				{
					"name": "project_preference",
					"type": "comment",
					"title": "Please describe your ideal project for your industry project.",
					"isRequired": "true",
					"placeHolder": "I would like to work on a project that is related to machine learning."
				},
				{
					"name": "project_type",
					"type": "radiogroup",
					"title": "Which of the following types of project would you like to work on?",
					"isRequired": "true",
					"colCount": "0",
					"choices": [
						"Software development",
						"Web development",
						"Mobile development",
						"Data science",
						"Machine learning",
						"Artificial intelligence",
						"Computer vision",
						"Robotics",
						"Embedded systems",
						"Networking",
						"Security",
						"Cloud computing",
						"Database",
						"Game development",
						"Other"
					],
					"otherText": "Other (please specify)"
				}
			
			]
		}
	],
	"completedHtml": "<p><h4>Thank you for completing the survey!</h4></p>"
}');

-- Initialise the survey response table
INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (1, 1, '{
	"full_name": "Student 1",
	"preferred_name": "Student 1",
	"email": "student1@example.com",
	"phone": "0220652158",
	"location": "Auckland",
	"skills": [
		"Java",
		"Python",
		"C#",
		"C++",
		"C",
		"JavaScript",
		"PHP",
		"SQL"
	]
}');
INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (1, 2, '{
	"full_name": "Student 2",
	"preferred_name": "Student 2",
	"email": "student2@example.com",
	"phone": "0224652158",
	"location": "Auckland",
	"skills": [
		"Java",
		"Python",
		"JavaScript",
		"PHP",
		"SQL"
	]
}');
INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (1, 3, '{
	"full_name": "Student 3",
	"preferred_name": "Student 3",
	"email": "student3@example.com",
	"phone": "0224652158",
	"location": "Auckland",
	"skills": [
		"Java",
		"Python",
		"PHP",
		"SQL"
	]
}');
INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (1, 4, '{
	"full_name": "Student 4",
	"preferred_name": "Student 4",
	"email": "student2@example.com",
	"phone": "0224662158",
	"location": "Auckland",
	"skills": [
		"Java",
		"SQL"
	]
}');
INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (1, 5, '{
	"full_name": "Student 5",
	"preferred_name": "Student 5",
	"email": "student5@example.com",
	"phone": "0228882158",
	"location": "Auckland",
	"skills": [
		"SQL",
		"JavaScript"
	]
}');
INSERT INTO Survey_Response (survey_id, student_id, survey_response_json) VALUES (1, 6, '{
	"full_name": "Student 6",
	"preferred_name": "Student 6",
	"email": "student6@example.com",
	"phone": "0225555158",
	"location": "Auckland",
	"skills": [
		"SQL"
	]
}');


-- Initialise skills table
INSERT INTO Skills (skill_name) VALUES ('Java');
INSERT INTO Skills (skill_name) VALUES ('Python');
INSERT INTO Skills (skill_name) VALUES ('C#');
INSERT INTO Skills (skill_name) VALUES ('C++');
INSERT INTO Skills (skill_name) VALUES ('C');
INSERT INTO Skills (skill_name) VALUES ('JavaScript');
INSERT INTO Skills (skill_name) VALUES ('PHP');
INSERT INTO Skills (skill_name) VALUES ('SQL');
INSERT INTO Skills (skill_name) VALUES ('HTML');
INSERT INTO Skills (skill_name) VALUES ('CSS');
INSERT INTO Skills (skill_name) VALUES ('Swift');
INSERT INTO Skills (skill_name) VALUES ('Objective-C');
INSERT INTO Skills (skill_name) VALUES ('Ruby');
INSERT INTO Skills (skill_name) VALUES ('R');
INSERT INTO Skills (skill_name) VALUES ('Matlab');
INSERT INTO Skills (skill_name) VALUES ('Kotlin');
INSERT INTO Skills (skill_name) VALUES ('Scala');
INSERT INTO Skills (skill_name) VALUES ('Go');
INSERT INTO Skills (skill_name) VALUES ('Perl');
INSERT INTO Skills (skill_name) VALUES ('Rust');
INSERT INTO Skills (skill_name) VALUES ('Dart');
INSERT INTO Skills (skill_name) VALUES ('Haskell');
INSERT INTO Skills (skill_name) VALUES ('Lua');
INSERT INTO Skills (skill_name) VALUES ('Julia');
INSERT INTO Skills (skill_name) VALUES ('TypeScript');
INSERT INTO Skills (skill_name) VALUES ('Assembly');
INSERT INTO Skills (skill_name) VALUES ('VBA');
INSERT INTO Skills (skill_name) VALUES ('Visual Basic');
INSERT INTO Skills (skill_name) VALUES ('Groovy');

-- Initialise sutdent skills table
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 1);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 2);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 3);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 4);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 5);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 6);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 7);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (1, 8);

INSERT INTO Student_Skills (student_id, skill_id) VALUES (3, 1);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (3, 2);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (3, 3);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (3, 4);
INSERT INTO Student_Skills (student_id, skill_id) VALUES (3, 5);

-- Initialise company table
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (1, 'Company 1', 'Company 1 description', 'www.company1.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (2, 'Company 2', 'Company 2 description', 'www.company2.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (3, 'Company 3', 'Company 3 description', 'www.company3.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (4, 'Company 4', 'Company 4 description', 'www.company4.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (5, 'Company 5', 'Company 5 description', 'www.company5.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (6, 'Company 6', 'Company 6 description', 'www.company6.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (7, 'Company 7', 'Company 7 description', 'www.company7.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (8, 'Company 8', 'Company 8 description', 'www.company8.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (9, 'Company 9', 'Company 9 description', 'www.company9.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (10, 'Company 10', 'Company 10 description', 'www.company10.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (11, 'Company 11', 'Company 11 description', 'www.company11.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (12, 'Company 12', 'Company 12 description', 'www.company12.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (13, 'Company 13', 'Company 13 description', 'www.company13.com');
INSERT INTO Companies (company_id, company_name, company_detail, website) VALUES (14, 'Company 14', 'Company 14 description', 'www.company14.com');

-- Initialise mentor table
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (5, 1, 'Mentor 1', 'mentor1@email.com', '0220652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (6, 2, 'Mentor 2', 'mentor2@email.com', '0222652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (7, 3, 'Mentor 3', 'mentor3@email.com', '0225652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (8, 4, 'Mentor 4', 'mentor4@email.com', '0226652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (13, 5, 'Mentor 5', 'mentor5@email.com', '0228652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (14, 6, 'Mentor 6', 'mentor6@email.com', '0229652568');
Insert INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (15, 7, 'Mentor 7', 'mentor7@email.com', '0220652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (16, 8, 'Mentor 8', 'mentor8@email.com', '0220652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (17, 9, 'Mentor 9', 'mentor9@email.com', '0220652568');
INSERT INTO Mentors (user_id, company_id, mentor_name, mentor_email, mentor_phone) VALUES (18, 10, 'Mentor 10', 'mentor10@email.com', '0220652568');

-- Initialise staff table
INSERT INTO Staff (user_id, email, staff_name) VALUES (9, 'staff1@gmail.com', 'Staff 1');
INSERT INTO Staff (user_id, email, staff_name) VALUES (10, 'staff2@gmail.com', 'Staff 2');
INSERT INTO Staff (user_id, email, staff_name) VALUES (11, 'staff3@gmail.com', 'Staff 3');
INSERT INTO Staff (user_id, email, staff_name) VALUES (12, 'staff4@gamil.com', 'Staff 4');

-- Initialise project table
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 1', 'Software development', 'Project 1 description', 'Auckland', 1, 1, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 2', 'Web development', 'Project 2 description', 'Auckland', 2, 2, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 3', 'Mobile development', 'Project 3 description', 'Auckland', 3, 3, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 4', 'Data science', 'Project 4 description', 'Auckland', 4, 4, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 5', 'Machine learning', 'Project 5 description', 'Auckland', 5, 2, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 6', 'Artificial intelligence', 'Project 6 description', 'Auckland', 6, 3, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 7', 'Software development', 'Project 7 description', 'Auckland', 7, 4, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 8', 'Web development', 'Project 8 description', 'Auckland', 8, 1, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 9', 'Mobile development', 'Project 9 description', 'Auckland', 9, 2, 2, 'Actively Looking');
INSERT INTO Projects (project_name, project_type, project_description, project_location, company_id, mentor_id, num_students_required, placement_status) VALUES ('Project 10', 'Data science', 'Project 10 description', 'Auckland', 10, 3, 2, 'Actively Looking');

-- Initialise project skills table
INSERT INTO Project_Skills (project_id, skill_id) VALUES (1, 1);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (1, 2);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (1, 3);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (2, 4);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (2, 5);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (2, 6);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (2, 7);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (3, 8);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (3, 9);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (3, 10);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (3, 11);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (4, 12);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (4, 13);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (4, 14);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (4, 15);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (5, 16);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (5, 17);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (5, 18);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (5, 19);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (6, 20);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (6, 21);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (6, 22);
INSERT INTO Project_Skills (project_id, skill_id) VALUES (6, 23);

-- Create candidates preferece table
CREATE TABLE `Candidate_Preference` (
	`candidate_preference_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
	`student_id` INTEGER NOT NULL,
	`project_id` INTEGER NOT NULL,
	`score` INTEGER DEFAULT 0 NOT NULL,
	CONSTRAINT `fk_candidate_preference_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`) ON DELETE CASCADE,
	CONSTRAINT `fk_candidate_preference_project_id` FOREIGN KEY (`project_id`) REFERENCES `Projects`(`project_id`) ON DELETE CASCADE,
	CONSTRAINT `unique_candidate_preference` UNIQUE (`student_id`, `project_id`)
);

-- Initialise candidates preference table
INSERT INTO Candidate_Preference (student_id, project_id, score)
VALUES
    -- Student 1
    (1, 2, 4),(1, 4, 3),(1, 6, 2),(1, 8, 1),(1, 10, 5),(1, 1, 3),(1, 3, 2),
    (1, 5, 1),(1, 7, 4),(1, 9, 0),
    
    -- Student 2
    (2, 1, 3),(2, 3, 4),(2, 5, 2),(2, 7, 1),(2, 9, 5),(2, 2, 2),(2, 4, 1),
    (2, 6, 4),(2, 8, 3),(2, 10, 0),
    
    -- Student 3
    (3, 2, 5),(3, 4, 4),(3, 6, 3),(3, 8, 2),(3, 10, 1),(3, 1, 4),(3, 3, 3),
    (3, 5, 2),(3, 7, 1),(3, 9, 0),
    
    -- Student 4
    (4, 1, 2),(4, 3, 3),(4, 5, 4),(4, 7, 5),(4, 9, 1),(4, 2, 3),(4, 4, 2),
    (4, 6, 1),(4, 8, 4),(4, 10, 0),
    
    -- Student 5
    (5, 2, 5),(5, 4, 2),(5, 6, 4),(5, 8, 3),(5, 10, 1),(5, 1, 1),(5, 3, 4),
    (5, 5, 2),(5, 7, 3),(5, 9, 0);


-- Create host preference table
CREATE TABLE `Host_Preference` (
	`host_preference_id` INTEGER PRIMARY KEY AUTO_INCREMENT,
	`project_id` INTEGER NOT NULL,
	`student_id` INTEGER NOT NULL,
	`score` INTEGER DEFAULT 0 NOT NULL,
	CONSTRAINT `fk_host_preference_project_id` FOREIGN KEY (`project_id`) REFERENCES `Projects`(`project_id`) ON DELETE CASCADE,
	CONSTRAINT `fk_host_preference_student_id` FOREIGN KEY (`student_id`) REFERENCES `Students`(`student_id`) ON DELETE CASCADE,
	CONSTRAINT `unique_host_preference` UNIQUE (`project_id`, `student_id`)
);

-- Initialise host preference table
INSERT INTO Host_Preference (project_id, student_id, score)
VALUES
    (1, 1, 0),(1, 2, 4),(1, 3, 0),(1, 4, 2),(1, 5, 0),(2, 1, 5),(2, 2, 0),(2, 3, 4),
    (2, 4, 0),(2, 5, 3),(3, 1, 0),(3, 2, 3),(3, 3, 0),(3, 4, 4),(3, 5, 0),(4, 1, 2),
    (4, 2, 0),(4, 3, 3),(4, 4, 0),(4, 5, 4),(5, 1, 3),(5, 2, 4),(5, 3, 1),(5, 4, 2),
    (5, 5, 0),(6, 1, 3),(6, 2, 0),(6, 3, 5),(6, 4, 0),(6, 5, 2),(7, 1, 2),(7, 2, 1),
    (7, 3, 0),(7, 4, 4),(7, 5, 0),(8, 1, 5),(8, 2, 3),(8, 3, 2),(8, 4, 0),(8, 5, 4),
    (9, 1, 1),(9, 2, 3),(9, 3, 2),(9, 4, 5),(9, 5, 0),(10, 1, 1),(10, 2, 3),(10, 3, 0),
	(10, 4, 4),(10, 5, 2);






