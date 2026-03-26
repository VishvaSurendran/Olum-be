from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from pgvector.sqlalchemy import Vector
from app.db.database import Base
import uuid

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    website_url = Column(String)
    owner_email = Column(String, nullable=True) 
    tier = Column(String, default="demo") # 'demo', 'pro', or 'enterprise'
    message_count = Column(Integer, default=0)
    stripe_customer_id = Column(String, nullable=True)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    content = Column(Text)  
    source_url = Column(String)
    embedding = Column(Vector(384))

class UnansweredQuestion(Base):
    __tablename__ = "unanswered_questions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    question = Column(String)
    is_answered = Column(Integer, default=0)  

class OTPVerification(Base):
    __tablename__ = "otp_verifications"
    email = Column(String, primary_key=True)
    otp_code = Column(String)
    expires_at = Column(DateTime)