from pydantic import BaseModel, validator
from fastapi import UploadFile, File
from typing import List
import datetime
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
import os

# User Types
class UserType(str, Enum):
    dietclient = "dietclient"
    workoutclient = "workoutclient"
    fullclient = "fullclient"
    coach = "coach"


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    password: str
    membership_expiration: datetime.datetime
    type : UserType

    

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    membership_expiration: datetime.datetime
    type: UserType = UserType.dietclient

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    membership_expiration: datetime.datetime
    is_coach: bool = False


class CheckIn(BaseModel):
    id: int
    user_id: int
    energy_level: float
    stress_level: float
    sleep_level: float
    recovery_level: float
    recovery_detail: str
    achievements: str
    challenges: str
    next_wk_challenges: str
    next_wk_setup_for_success: str
    video_response_url: str | None = None
    # files: list = []

class CheckInCreate(BaseModel):
    user_id: int
    energy_level: float
    stress_level: float
    sleep_level: float
    recovery_level: float
    recovery_detail: str
    achievements: str
    challenges: str
    next_wk_challenges: str
    next_wk_setup_for_success: str
    video_response_url: str | None = None

class BucketPhoto(BaseModel):
    photo_name: str
    photo_url: str
    checkin_id: int