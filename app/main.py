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
        **user.dict(),
        
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

    # Add to DB
    db.add(db_check_in)
    db.commit()
    db.refresh(db_check_in)

    return db_check_in

@app.get("/check-ins/", response_model=List[schemas.CheckIn])
async def read_check_ins(db: db_dependency):
    check_ins = db.query(models.CheckIn).all()
    return check_ins

@app.get("/check-ins/{check_in_id}/", response_model=schemas.CheckIn)
async def get_check_in(check_in_id, db: db_dependency):
    db_check_in = db.query(models.CheckIn).filter(models.CheckIn.id == check_in_id).first()
    return db_check_in

@app.post("/check-ins/{check_in_id}/", response_model=schemas.CheckIn)
async def upload_url_response(check_in_id, url: str, db: db_dependency):
    db_check_in = db.query(models.CheckIn).filter(models.CheckIn.id == check_in_id).first()
    db_check_in.video_response_url = url
    db.commit()
    db.refresh(db_check_in)
    return db_check_in

@app.post("/check-ins/{check_in_id}/photos/", response_model=schemas.BucketPhoto)
async def upload_photo(checkin_id, file_upload: UploadFile, db : db_dependency):
    data = await file_upload.read()
    size = len(data)

    # Check file size
    max_size_mb = 100
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

    # Upload to S3
    s3_client.upload_fileobj(file_upload.file,BUCKET_NAME,  file_upload.filename,
                           )
    
    uploaded_file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_upload.filename}"


    # Creation of bucketfile in Postgresql
    db_file = models.BucketPhoto(
        photo_name=file_upload.filename,
        photo_url=uploaded_file_url,
        checkin_id=checkin_id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    


    # Return the file data
    return db_file

@app.get("/check-ins/{check_in_id}/photos/", response_model=List[schemas.BucketPhoto])
async def get_all_check_in_photos(check_in_id, db: db_dependency):
    db_photos = db.query(models.BucketPhoto).filter(models.BucketPhoto.checkin_id == check_in_id).all()
    return db_photos

