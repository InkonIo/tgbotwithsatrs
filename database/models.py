"""
Database schema for 777 Gift Bot
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class User(Base):
    """Пользователи бота"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    wins = relationship("Win", back_populates="user")


class Gift(Base):
    """Подарки в пуле"""
    __tablename__ = 'gifts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    rarity = Column(String(50), default='common')  # common, rare, epic, legendary
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    wins = relationship("Win", back_populates="gift")


class Win(Base):
    """История выигрышей"""
    __tablename__ = 'wins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    gift_id = Column(Integer, ForeignKey('gifts.id'), nullable=False)
    status = Column(String(50), default='pending')  # pending, sent, claimed
    won_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="wins")
    gift = relationship("Gift", back_populates="wins")


class JackpotAttempt(Base):
    """История попыток выбить джекпот"""
    __tablename__ = 'jackpot_attempts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_jackpot = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Создание таблиц
def init_db():
    """Инициализация базы данных"""
    engine = create_engine(os.getenv('DATABASE_URL'))
    Base.metadata.create_all(engine)
    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    init_db()