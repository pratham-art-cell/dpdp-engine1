from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # --- NEW BILLING FIELDS ---
    has_paid = Column(Boolean, default=False)
    access_valid_until = Column(DateTime, nullable=True)