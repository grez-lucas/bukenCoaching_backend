from typing import Union
from fastapi import Depends, FastAPI, HTTPException, UploadFile, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import Annotated
from . import schemas, models, hashing
import boto3
import magic





app = FastAPI(title="BUKENCOACHING API", openapi_url=f"/openapi.json")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://frontend:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)


# S3 Setup

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
def read_root():
    return {"Hello": "World2"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: db_dependency,
):
    db_user = models.User(
        email=user.email,
        password=hashing.get_password_hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        membership_expiration=user.membership_expiration,
        is_coach=user.is_coach
        
    )

    # Uploading to DB
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create a response using UserResponse schema
    user_response = schemas.UserResponse(
        id=db_user.id,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        email=db_user.email,
        membership_expiration=db_user.membership_expiration,
        is_coach=db_user.is_coach
    )

    return user_response

@app.get("/users/", response_model=list[schemas.User])
def read_users(db: db_dependency):
    users = db.query(models.User).all()
    return users