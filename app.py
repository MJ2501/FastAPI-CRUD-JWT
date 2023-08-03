from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field, EmailStr
import re
from datetime import timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

app = FastAPI()

# Security
# security = HTTPBasic() # For just access token
security = HTTPBearer()


# Database connection
MYSQL_USER = "root"
MYSQL_PASSWORD = "mohit0205"
MYSQL_HOST = "localhost"  # Change this to your MySQL host if it's not on localhost
MYSQL_PORT = "3306"  # Change this if your MySQL port is different
MYSQL_DB = "my_database"

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(50), unique=True, index=True)
    password = Column(String(50))
    full_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))

# Data Model
class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(String(100))

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate password hash
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Pydantic model for request data
class UserRegister(BaseModel):
    username: str = Field(..., min_length=5, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., max_length=100)
    age: int = Field(..., gt=0)
    gender: str = Field(..., max_length=10)

class TokenData(BaseModel):
    username: str

# Pydantic model for request data
class DataStore(BaseModel):
    key: str = Field(..., max_length=100)
    value: str = Field(...)

SECRET_KEY = "your_secret_key"  # Replace this with a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Error Response Model
class ErrorResponse(BaseModel):
    status: str = "error"
    code: str
    message: str

# Success Response Model
class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: dict

# For DataStore(key - value)
# class SuccessResponse(BaseModel):
#     status: str = "success"
#     message: str

# Token Response Model
class TokenResponse(BaseModel):
    status: str = "success"
    message: str = "Access token generated successfully."
    data: dict



# Endpoint to register a new user
@app.post("/api/register", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
def register_user(user_data: UserRegister):
    if not all(user_data.dict().values()):
        raise HTTPException(status_code=400, detail=ErrorResponse(code="INVALID_REQUEST", message="Invalid request. Please provide all required fields: username, email, password, full_name."))
    # Check if the username or email already exists
    session = SessionLocal()
    user = session.query(User).filter(User.username == user_data.username).first()
    if user:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="USERNAME_EXISTS", message="The provided username is already taken. Please choose a different username."))
    
    user = session.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="EMAIL_EXISTS", message="The provided email is already registered. Please use a different email address."))
    
    # Additional validations
    if not user_data.password:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="INVALID_PASSWORD", message="The provided password does not meet the requirements. Password must be at least 8 characters long and contain a mix of uppercase and lowercase letters, numbers, and special characters."))

    if user_data.age <= 0:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="INVALID_AGE", message="Invalid age value. Age must be a positive integer."))
    
    if not user_data.gender:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="GENDER_REQUIRED", message="Gender field is required. Please specify the gender (e.g., male, female, non-binary)."))

    # Create a new user record
    new_user = User(**user_data.dict())
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    user_data_dict = user_data.dict()
    user_data_dict["user_id"] = new_user.id
    session.close()
    return SuccessResponse(message="User successfully registered!", data=user_data_dict)

# Endpoint to generate access token
@app.post("/api/token", response_model=TokenResponse, responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def generate_token(credentials: HTTPBasicCredentials = Depends(security)):
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="MISSING_FIELDS", message="Missing fields. Please provide both username and password."))
    
    session = SessionLocal()
    user = session.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail=ErrorResponse(code="INVALID_CREDENTIALS", message="Invalid credentials. The provided username or password is incorrect."))

    token_data = TokenData(username=user.username)
    access_token = create_access_token(token_data)
    session.close()
    return TokenResponse(data={"access_token": access_token, "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60})

# Endpoint to store a key-value pair in the database
@app.post("/api/data", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def store_data(data: DataStore, authorization: HTTPAuthorizationCredentials = Depends(security)):
    access_token = authorization.credentials
    token_data = verify_access_token(access_token)
    if not token_data:
        raise HTTPException(status_code=401, detail=ErrorResponse(code="INVALID_TOKEN", message="Invalid access token provided"))

    # Check for missing or invalid key
    if not data.key or not data.key.strip():
        raise HTTPException(status_code=400, detail=ErrorResponse(code="INVALID_KEY", message="The provided key is not valid or missing."))

    # Check for missing or invalid value
    if not data.value or not data.value.strip():
        raise HTTPException(status_code=400, detail=ErrorResponse(code="INVALID_VALUE", message="The provided value is not valid or missing."))

    session = SessionLocal()
    # Check if the key already exists
    existing_data = session.query(Data).filter(Data.key == data.key).first()
    if existing_data:
        raise HTTPException(status_code=400, detail=ErrorResponse(code="KEY_EXISTS", message="The provided key already exists in the database. To update an existing key, use the update API."))

    # Store the key-value pair
    new_data = Data(**data.dict())
    session.add(new_data)
    session.commit()
    session.close()
    return SuccessResponse(message="Data stored successfully.")

# Endpoint to retrieve the value associated with a specific key
@app.get("/api/data/{key}", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def retrieve_data(key: str, authorization: HTTPAuthorizationCredentials = Depends(security)):
    access_token = authorization.credentials
    token_data = verify_access_token(access_token)
    if not token_data:
        raise HTTPException(status_code=401, detail=ErrorResponse(code="INVALID_TOKEN", message="Invalid access token provided"))

    session = SessionLocal()
    # Retrieve the value associated with the key
    data = session.query(Data).filter(Data.key == key).first()
    if not data:
        raise HTTPException(status_code=404, detail=ErrorResponse(code="KEY_NOT_FOUND", message="The provided key does not exist in the database."))

    session.close()
    return SuccessResponse(data={"key": data.key, "value": data.value})

# Endpoint to update the value associated with an existing key
@app.put("/api/data/{key}", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def update_data(key: str, updated_data: DataStore, authorization: HTTPAuthorizationCredentials = Depends(security)):
    access_token = authorization.credentials
    token_data = verify_access_token(access_token)
    if not token_data:
        raise HTTPException(status_code=401, detail=ErrorResponse(code="INVALID_TOKEN", message="Invalid access token provided"))

    session = SessionLocal()
    # Retrieve the data associated with the key
    data = session.query(Data).filter(Data.key == key).first()
    if not data:
        raise HTTPException(status_code=404, detail=ErrorResponse(code="KEY_NOT_FOUND", message="The provided key does not exist in the database."))

    # Update the value associated with the key
    data.value = updated_data.value
    session.commit()
    session.close()
    return SuccessResponse(message="Data updated successfully.")

# Endpoint to delete a key-value pair from the database
@app.delete("/api/data/{key}", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def delete_data(key: str, authorization: HTTPAuthorizationCredentials = Depends(security)):
    access_token = authorization.credentials
    token_data = verify_access_token(access_token)
    if not token_data:
        raise HTTPException(status_code=401, detail=ErrorResponse(code="INVALID_TOKEN", message="Invalid access token provided"))

    session = SessionLocal()
    # Retrieve the data associated with the key
    data = session.query(Data).filter(Data.key == key).first()
    if not data:
        raise HTTPException(status_code=404, detail=ErrorResponse(code="KEY_NOT_FOUND", message="The provided key does not exist in the database."))

    # Delete the key-value pair from the database
    session.delete(data)
    session.commit()
    session.close()
    return SuccessResponse(message="Data deleted successfully.")

# Create access token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify access token and get token data
def verify_access_token(access_token: str):
    try:
        token_data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return token_data
    except JWTError:
        return None

# Error handling for INTERNAL_SERVER_ERROR
@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(code="INTERNAL_SERVER_ERROR", message="An internal server error occurred. Please try again later.")
    )

