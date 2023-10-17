from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
from passlib.context import CryptContext
import uuid

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
    files = Relationship("BucketFile", cascade="all, delete")

class BucketFile(Base):
    __tablename__ = "bucket_files"

    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    file_name = Column(String, index=True)
    file_ext = Column(String, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))