from typing import Union
from fastapi import Depends, FastAPI, HTTPException, UploadFile, Response, status, File, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from typing import Annotated, List
from . import schemas, models, hashing
import datetime
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
        **user.dict(exclude={"password"}),
        password=hashing.get_password_hash(user.password)        
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

@app.patch("/users/{user_id}/", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user: schemas.UserCreate,
    db: db_dependency,
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db_user.email = user.email
    db_user.password = hashing.get_password_hash(user.password)
    db_user.membership_expiration = user.membership_expiration
    db_user.type = user.type
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

@app.get("/dashboards/{user_id}/", response_model=schemas.Dashboard)
async def get_dashboard_data( user_id, db: db_dependency, dateFrom:  Annotated[datetime.datetime | None, Body()] = None, dateTo: Annotated[datetime.datetime | None, Body()] = None):
    
    selected_check_ins = db.query(models.CheckIn).filter(models.CheckIn.user_id == user_id).filter(models.CheckIn.created >= dateFrom).filter(models.CheckIn.created <= dateTo).all()
    
    # Calculate total check-ins
    total_check_ins = db.query(models.CheckIn).filter(models.CheckIn.user_id == user_id).count()

    # Calculate weight difference
    weight_difference = selected_check_ins[0].average_weight - selected_check_ins[-1].average_weight
    
    # Calculate average stress
    average_stress = sum(check_in.stress_level for check_in in selected_check_ins) / len(selected_check_ins)

    # Calculate average adherance
    average_adherance = sum(check_in.adherence_level for check_in in selected_check_ins) / len(selected_check_ins)

    # Get weight graph data
    weight_graph_x = [check_in.created for check_in in selected_check_ins]
    weight_graph_y = [check_in.average_weight for check_in in selected_check_ins]

    # Get adherance graph data
    adherance_graph_x = [check_in.created for check_in in selected_check_ins]
    adherance_graph_y = [check_in.adherence_level for check_in in selected_check_ins]

    # Get weekly soreness graph data
    weekly_soreness_x = [check_in.created for check_in in selected_check_ins]
    weekly_soreness_y = [check_in.recovery_level for check_in in selected_check_ins]

    # Get percieved energy/fatigue graph data
    percieved_energy_fatigue_graph_x = [check_in.created for check_in in selected_check_ins]
    percieved_energy_y = [check_in.energy_level for check_in in selected_check_ins]
    percieved_fatigue_y = [check_in.recovery_level for check_in in selected_check_ins]

    # Get sleep graph data
    sleep_graph_x = [check_in.created for check_in in selected_check_ins]
    sleep_graph_y = [check_in.sleep_level for check_in in selected_check_ins]

    # Get stress graph data
    stress_graph_x = [check_in.created for check_in in selected_check_ins]
    stress_graph_y = [check_in.stress_level for check_in in selected_check_ins]

    # Check if the user is a pedclient 
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user.type == "PEDCLIENT":
        # Get blood pressure graph data
        blood_pressure_graph_x = [check_in.created for check_in in selected_check_ins]
        blood_pressure_graph_y = [check_in.blood_pressure_systolic for check_in in selected_check_ins]
        blood_pressure_graph_y2 = [check_in.blood_pressure_diastolic for check_in in selected_check_ins]

        # Get blood sugar graph data
        blood_sugar_graph_x = [check_in.created for check_in in selected_check_ins]
        blood_sugar_graph_y = [check_in.blood_sugar for check_in in selected_check_ins]

        dashboard = schemas.Dashboard(
            total_checkins=total_check_ins,
            weight_difference=weight_difference,
            average_stress=average_stress,
            average_adherance=average_adherance,
            weight_graph_x=weight_graph_x,
            weight_graph_y=weight_graph_y,
            adherance_graph_x=adherance_graph_x,
            adherance_graph_y=adherance_graph_y,
            weekly_soreness_x=weekly_soreness_x,
            weekly_soreness_y=weekly_soreness_y,
            percieved_energy_fatigue_graph_x=percieved_energy_fatigue_graph_x,
            percieved_energy_y=percieved_energy_y,
            percieved_fatigue_y=percieved_fatigue_y,
            sleep_graph_x=sleep_graph_x,
            sleep_graph_y=sleep_graph_y,
            stress_graph_x=stress_graph_x,
            stress_graph_y=stress_graph_y,
            blood_pressure_graph_x=blood_pressure_graph_x,
            blood_pressure_systolic_y=blood_pressure_graph_y,
            blood_pressure_diastolic_y=blood_pressure_graph_y2,
            blood_sugar_graph_x=blood_sugar_graph_x,
            blood_sugar_graph_y=blood_sugar_graph_y
        )
    else:
        dashboard = schemas.Dashboard(
            total_checkins=total_check_ins,
            weight_difference=weight_difference,
            average_stress=average_stress,
            average_adherance=average_adherance,
            weight_graph_x=weight_graph_x,
            weight_graph_y=weight_graph_y,
            adherance_graph_x=adherance_graph_x,
            adherance_graph_y=adherance_graph_y,
            weekly_soreness_x=weekly_soreness_x,
            weekly_soreness_y=weekly_soreness_y,
            percieved_energy_fatigue_graph_x=percieved_energy_fatigue_graph_x,
            percieved_energy_y=percieved_energy_y,
            percieved_fatigue_y=percieved_fatigue_y,
            sleep_graph_x=sleep_graph_x,
            sleep_graph_y=sleep_graph_y,
            stress_graph_x=stress_graph_x,
            stress_graph_y=stress_graph_y,
        )

    return dashboard
