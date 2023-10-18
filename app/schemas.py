from pydantic import BaseModel, validator
from fastapi import UploadFile, File
from typing import List
import datetime
import os



class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    password: str
    membership_expiration: datetime.datetime
    is_coach: bool = False

    

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    membership_expiration: datetime.datetime
    is_coach: bool = False

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
    check_in_date: datetime.datetime
    energy_level: float
    stress_level: float
    sleep_level: float
    achievements: str
    challenges: str
    next_wk_challenges: str
    next_wk_setup_for_success: str
    video_response_url: str
    # files: list = []

class CheckInCreate(BaseModel):
    user_id: int
    check_in_date: datetime.datetime
    check_in_text: str
    energy_level: float
    stress_level: float
    sleep_level: float
    achievements: str
    challenges: str
    next_wk_challenges: str
    next_wk_setup_for_success: str
    video_response_url: str
    files: List[UploadFile] = []
