from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
from passlib.context import CryptContext
import uuid
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_coach = Column(Boolean, default=False)
    membership_expiration = Column(DateTime, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    

class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    check_in_date = Column(DateTime, nullable=False)
    check_in_text = Column(String, nullable=False)
    energy_level = Column(Float, nullable=False)
    stress_level = Column(Float, nullable=False)
    sleep_level = Column(Float, nullable=False)
    achievements = Column(String, nullable=False)
    challenges = Column(String, nullable=False)
    next_wk_challenges = Column(String, nullable=False)
    next_wk_setup_for_success = Column(String, nullable=False)
    video_response_url = Column(String, nullable=True)
    photos = relationship("BucketPhoto", cascade="all, delete")
    created = Column(DateTime, default=datetime.datetime.now())


class BucketPhoto(Base):
    __tablename__ = "bucket_photos"

    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    photo_name = Column(String, index=True)
    photo_url = Column(String, index=True)

    checkin_id = Column(Integer, ForeignKey("check_ins.id"))