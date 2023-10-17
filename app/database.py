from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
pg_user = os.environ.get('POSTGRES_USER')
pg_password = os.environ.get('POSTGRES_PASSWORD')
pg_db = os.environ.get('POSTGRES_DB')
pg_server = os.environ.get('POSTGRES_SERVER')

SQLALCHEMY_DATABASE_URL = f"postgresql://{pg_user}:{pg_password}@{pg_server}/{pg_db}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()