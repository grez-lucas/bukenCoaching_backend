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
    pedclient = "pedclient"
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
    adherence_level: float
    achievements: str
    challenges: str
    next_wk_challenges: str
    next_wk_setup_for_success: str
    video_response_url: str | None = None
    optional_questions: str | None = None
    average_weight: float
    blood_pressure_systolic: float
    blood_pressure_diastolic: float
    blood_sugar: float
    created: datetime.datetime
class CheckInCreate(BaseModel):
    user_id: int
    energy_level: float
    stress_level: float
    sleep_level: float
    recovery_level: float
    recovery_detail: str
    adherence_level: float
    achievements: str
    challenges: str
    next_wk_challenges: str
    next_wk_setup_for_success: str
    optional_questions: str | None = None
    average_weight: float
    blood_pressure_systolic: float | None = None
    blood_pressure_diastolic: float | None = None
    blood_sugar: float | None = None

class BucketPhoto(BaseModel):
    photo_name: str
    photo_url: str
    checkin_id: int

class Dashboard(BaseModel):
    # This is the dashboard for the client, where they can see their check-in data
    # In a neat format with graphs and stuff
    total_checkins: int
    weight_difference: float
    average_stress: float
    average_adherance: float
    weight_graph_x: List[datetime.datetime]
    weight_graph_y: List[float]
    adherance_graph_x: List[datetime.datetime]
    adherance_graph_y: List[float]
    weekly_soreness_x: List[datetime.datetime]
    weekly_soreness_y: List[float]
    percieved_energy_fatigue_graph_x: List[datetime.datetime]
    percieved_energy_y: List[float]
    percieved_fatigue_y: List[float]
    sleep_graph_x: List[datetime.datetime]
    sleep_graph_y: List[float]
    stress_graph_x: List[datetime.datetime]
    stress_graph_y: List[float]
    blood_pressure_graph_x: List[datetime.datetime] | None = None
    blood_pressure_systolic_y: List[float] | None = None
    blood_pressure_diastolic_y: List[float] | None = None
    blood_sugar_graph_x: List[datetime.datetime] | None = None
    blood_sugar_y: List[float] | None = None 