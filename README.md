# READ ME

## Choice of Framework

The chosen framework for this project is FastAPI. FastAPI is a modern, fast, web framework for building APIs with Python. It is built on top of Starlette for handling asynchronous requests and Pydantic for data validation and serialization. Some reasons for choosing FastAPI are:

* Performance: FastAPI is built on Starlette, which is an asynchronous framework. This allows for high-performance handling of requests and responses.
* Type Annotations: FastAPI leverages Python type annotations and Pydantic models for automatic validation and serialization of data. This improves code readability and reduces the chance of bugs.
* Interactive Documentation: FastAPI automatically generates interactive API documentation using Swagger UI. This makes it easy to explore and understand the API endpoints.
* Ease of Use: FastAPI has a simple and intuitive API, making it easy for developers to create APIs quickly.

## DB SCHEMA

The database schema consists of two tables: users and data.

users Table:
* id: Primary key for the user.
* username: Unique username for the user.
* email: Unique email address of the user.
* password: Hashed password of the user.
* full_name: Full name of the user.
* age: Age of the user.
* gender: Gender of the user.


data Table:
* id: Primary key for the data.
* key: Unique key for the data.
* value: Value associated with the key.

## Instructions to Run the Code
To run the code, follow these steps:
1. Install the required dependencies:
```bash 
pip install fastapi uvicorn sqlalchemy mysql-connector-python passlib pyjwt python-multipart
```
2. Create the MySQL database with the name my_database and update the MySQL credentials in the code if necessary.
3. Run the FastAPI application using Uvicorn:
```bash
uvicorn app:app --reload
```
4. The application will be accessible at 'http://127.0.0.1:8000'.

## Instructions to Set Up the Code
To set up the code, follow these steps:
1. Clone the repository or download the code.
2. Install the required dependencies as mentioned in step 1 of "Instructions to Run the Code".
3. Create the MySQL database with the name my_database and update the MySQL credentials in the code if necessary.
4. Run the FastAPI application using Uvicorn as mentioned in step 3 of "Instructions to Run the Code".

## Docker-Compose File
```yaml
version: "3"
services:
  fastapi_app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MYSQL_USER=root
      - MYSQL_PASSWORD=mohit0205
      - MYSQL_HOST=db
      - MYSQL_PORT=3306
      - MYSQL_DB=my_database
      - SECRET_KEY=your_secret_key
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=60
    depends_on:
      - db

  db:
    image: mysql:latest
    environment:
      - MYSQL_ROOT_PASSWORD=mohit0205
      - MYSQL_DATABASE=my_database
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## Running with Docker-Compose
1. Save the docker-compose file to your project directory.
2. Open a terminal in the project directory and run the following command to start the application:
```bash
docker-compose up --build
```
3. The FastAPI application will be accessible at 'http://127.0.0.1:8000'.

Now, the entire system (FastAPI and MySQL) will be up and running using Docker Compose. You can access the API and interact with the database using the provided endpoints.

Please note that you may need to adjust the database configurations and other environment variables based on your requirements.




