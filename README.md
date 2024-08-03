# Blog API

This is a simple Flask API I created to manage my blog which is used on my portfolio website. The API provides functionality for user registration, login, and CRUD operations for blog posts. JWT authentication is used to secure certain endpoints.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Environment Variables](#environment-variables)
- [Major Modules](#major-modules)
- [License](#license)

## Features

- User registration with password hashing and code verification
- User login with JWT token generation
- Generate a registration code
- CRUD operations for blog posts (Create, Read, Update, Delete)
- Token-based authentication for protected routes

## Prerequisites

- Python 3.7 or higher
- MongoDB
- Pip (Python package installer)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/asdhamidi/blog-api.git
    ```

2. Navigate to the project directory:
    ```bash
    cd blog-api
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Start the Flask server:
    ```bash
    cd api/
    flask run
    ```

2. The server will run on `http://127.0.0.1:5000/`. You can use tools like Postman or curl to interact with the API endpoints.

## Endpoints

### Public Endpoints

- `GET /` 
  - **Description**: Home route. Returns a welcome message.

### Authentication Endpoints

- `POST /register`
  - **Body**: `{ "username": "string", "password": "string", "register_code": "string" }`
  - **Description**: Registers a new user. Requires a valid registration code.
  - **Responses**:
    - `201 Created`: User registered successfully.
    - `400 Bad Request`: Missing or invalid data.

- `POST /login`
  - **Body**: `{ "username": "string", "password": "string" }`
  - **Description**: Logs in a user and returns a JWT token.
  - **Responses**:
    - `200 OK`: Login successful, returns JWT token.
    - `401 Unauthorized`: Invalid username or password.

### Post Endpoints (Requires Token)

- `POST /generate_code`
  - **Headers**: `Authorization: Bearer <token>`
  - **Description**: Generates a new registration code.
  - **Responses**:
    - `201 Created`: Registration code generated.
    - `401 Unauthorized`: Token is missing or invalid.

- `GET /posts`
  - **Headers**: `Authorization: Bearer <token>`
  - **Description**: Retrieves a list of all posts.
  - **Responses**:
    - `200 OK`: Returns a list of posts.
    - `401 Unauthorized`: Token is missing or invalid.

- `GET /posts/<id>`
  - **Headers**: `Authorization: Bearer <token>`
  - **Description**: Retrieves a specific post by ID.
  - **Responses**:
    - `200 OK`: Returns the requested post.
    - `404 Not Found`: Post not found.
    - `401 Unauthorized`: Token is missing or invalid.

- `POST /posts`
  - **Headers**: `Authorization: Bearer <token>`
  - **Body**: `{ "title": "string", "content": "string", "author": "string" }`
  - **Description**: Creates a new post.
  - **Responses**:
    - `201 Created`: Post created successfully.
    - `401 Unauthorized`: Token is missing or invalid.

- `PUT /posts/<id>`
  - **Headers**: `Authorization: Bearer <token>`
  - **Body**: `{ "title": "string", "content": "string" }`
  - **Description**: Updates a post by ID.
  - **Responses**:
    - `200 OK`: Post updated successfully.
    - `404 Not Found`: Post not found.
    - `401 Unauthorized`: Token is missing or invalid.

- `DELETE /posts/<id>`
  - **Headers**: `Authorization: Bearer <token>`
  - **Description**: Deletes a post by ID.
  - **Responses**:
    - `200 OK`: Post deleted successfully.
    - `404 Not Found`: Post not found.
    - `401 Unauthorized`: Token is missing or invalid.

## Environment Variables

Create a `.env` file in the project root and include the following variables:

```env
MONGODB_URI=mongodb://<username>:<password>@<host>:<port>/<database>
BLOG_DB=<your_database_name>
JWT_SECRET=<your_jwt_secret>
```

## Major Modules

This project uses several key Python modules. Here’s a list of the major ones and their purposes:

- **Flask**: A lightweight WSGI web application framework. Used to create the web server and handle HTTP requests.
  - Installation: `pip install Flask`

- **Flask-CORS**: A Flask extension for handling Cross-Origin Resource Sharing (CORS). Allows the API to handle requests from different origins.
  - Installation: `pip install Flask-CORS`

- **PyMongo**: A Python driver for MongoDB. Provides tools for connecting to and interacting with the MongoDB database.
  - Installation: `pip install pymongo`

- **python-dotenv**: A module to read key-value pairs from a `.env` file and set them as environment variables. Used to manage environment configuration.
  - Installation: `pip install python-dotenv`

- **bcrypt**: A library for hashing passwords. Ensures passwords are securely hashed before being stored.
  - Installation: `pip install bcrypt`

- **PyJWT**: A Python library for working with JSON Web Tokens (JWT). Used for encoding and decoding JWTs for authentication.
  - Installation: `pip install PyJWT`

## License

This project is licensed under... I don't know which license. Use it, don't use it, I couldn't care less.