from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to users
    users = relationship("User", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to tenant
    tenant = relationship("Tenant", back_populates="users")


class DiagnosticsLog(Base):
    __tablename__ = "diagnostics_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_ip = Column(String, nullable=False)
    destination_ip = Column(String, nullable=False)
    status = Column(String, nullable=False)  # e.g. "success", "failure"
    output = Column(Text)  # store ping output or error message
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
