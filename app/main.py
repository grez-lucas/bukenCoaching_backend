from typing import Union
from fastapi import Depends, FastAPI, HTTPException, UploadFile, Response, status, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import Annotated, List
from . import schemas, models, hashing
import os
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
BUCKET_NAME = os.environ.get('BUCKET_NAME')
s3_client = boto3.client('s3',
                  aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

KB = 1024
MB = 1024 * KB

SUPPORTED_FILE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "application/zip": "zip",
}


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]



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

@app.get("/users/")
def read_users(db: db_dependency):
    users = db.query(models.User).all()
    return users


@app.post("/check-ins/", response_model=schemas.CheckIn)
async def create_check_in(
    check_in: schemas.CheckInCreate,
    db: db_dependency,
):
    # Create a new check-in
    db_check_in = models.CheckIn(
        **check_in.dict()
    )

    # Handle File Uploads
    for uploaded_file in check_in.files:
        # Process the file, save it, and associate it with the check-in
        # You can use libraries like Boto3 if you're using AWS S3
        # Otherwise, save it to your local storage or use a different cloud storage solution
        file_data = await handle_uploaded_file(db_check_in.id, uploaded_file, db)  # Pass db_check_in.id instead of check_in.id
        db_file = models.BucketFile(**file_data)
        db_check_in.files.append(db_file)

    # Add to DB
    db.add(db_check_in)
    db.commit()
    db.refresh(db_check_in)

    return db_check_in

async def handle_uploaded_file(checkin_id, file_upload: UploadFile, db : db_dependency):
    data = await file_upload.read()
    size = len(data)

    # Check file size
    max_size_mb = 4
    if not 0 < size <= max_size_mb * MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be between 0 and {max_size_mb} MB",
        )

    # This helps security detecting true filetype
    file_type = magic.from_buffer(buffer=data, mime=True)
    if file_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type {file_type}, supported types are {SUPPORTED_FILE_TYPES}",
        )
    detected_file_ext = SUPPORTED_FILE_TYPES[file_type]

    # Creation of bucketfile in Postgresql
    db_file = models.BucketFile(
        file_name=file_upload.filename,
        file_ext=detected_file_ext,
        ckeckin_id=checkin_id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Upload to S3
    s3_key = f"{db_file.id}.{db_file.file_ext}"
    s3_client.put_object(
        Body=data,
        Bucket=BUCKET_NAME,
        Key=s3_key,
    )

    # Return the file data
    return { "key": s3_key }