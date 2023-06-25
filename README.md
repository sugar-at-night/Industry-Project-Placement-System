# ReadMe
This is a school project for industry placement.

## Table of Contents
- [Background](#background)
- [Install](#install)
- [Usage](#usage)
    - [Public Interface](#Public-Interface)
    - [Staff Interface](#Staff-Interface)


## Background
COMP693 Industry Project is one of the core courses for Master of Applied Computing in which 
students work on an applied computing project with an external client. To manage the industry 
placements for students, we require a web application that can be used to manage students and 
industries. The students are allocated a project in a particular company based on the nature of the 
project and whether the students have the skill set required to complete the project. 
There are three types of users for this system:
• Student 
• Industry Mentors 
• Staff in-charge of the industry project

## Install
This application is based on the MySQL, Python, Flask.

1. Clone the repository. 
2. Run the requirements.txt to build a virtual envirnonment.
3. Build your database on your own server
You can use the scripts inside folder "MySQL Database" to build your database on your own server(AWS or SQL Sever, anywherer you prefer), and then fill in the connect.py under db
4. Then run the app.py. 
5. Now, you can enter the system through http://127.0.0.1:5000/
