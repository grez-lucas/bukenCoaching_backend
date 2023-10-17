from pydantic import BaseModel, validator
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
