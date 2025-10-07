# Video Streaming System
## Overview

The Video Streaming System is a microservices-based web application that enables users to upload, stream, and manage videos through a centralized dashboard.

# Architecture
The application is composed of several interconnected services, each responsible for specific functionality:

	### Authentication Service (auth-service)
	Manages user registration, authentication, and admin authorization.

	### File Service (file-service)
	Handles uploading, storing, and deleting video files on the server’s file system.

	### Video Service (video-service)
	Manages video metadata (e.g., names, file paths, owners) and proxies streaming requests to the file service.

	### Gateway Service (gateway)
	A Flask-based web interface that allows users to log in, upload videos, stream content, manage their library, and for admins — manage users.

	### MySQL (db)
	Stores user credentials (through the auth service) and video metadata (through the video service).

	Each service connects to the database as needed to perform authentication, user management, and video indexing.

# Setup Instructions
1. Clone the Repository

    `git clone https://link.com`

    `cd video-streaming-system`

2. Build and Start Services

    Use Docker Compose to build and run all services:

    `docker-compose up --build`

    This will build the images for all services and start the containers in the correct order.

3. Access the Application

    Once all containers are running, open your browser and navigate to:

    `http://localhost:5000`

    Here you can log in, upload videos, stream content, and manage users.
    
## Admin Credentials
user: `admin`

pass: `password123`

# Directory Structure
```
├── auth-service
│   ├── app.py
│   └── Dockerfile
├── docker-compose.yml
├── file-data
│   ├── admin
├── file-service
│   ├── app.py
│   └── Dockerfile
├── gateway
│   ├── app.py
│   ├── Dockerfile
│   └── templates
│       ├── dashboard.html
│       └── login.html
├── init.sql
├── README.md
└── video-service
    ├── app.py
    └── Dockerfile
```
# Technologies Used:

Backend: **Python (Flask)**

Frontend: **HTML / Jinja templates**

Database: **MySQL**

Containerization: **Docker & Docker Compose**
