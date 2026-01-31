"""
Database schema for 777 Gift Bot
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
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
    emoji = Column(String(10), nullable=False)  # 💎⭐🎁🎀
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    rarity = Column(String(50), default='common')  # common, rare, epic, legendary
    quantity = Column(Integer, default=0)  # Количество доступных подарков
    gift_telegram_id = Column(String(255), nullable=True)  # ID реального подарка (потом)
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
    telegram_user_id = Column(Integer, nullable=False)  # Telegram ID для быстрого поиска
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


# Database engine and session
engine = None
SessionLocal = None


def get_engine():
    """Получить engine базы данных"""
    global engine
    if engine is None:
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Если это PostgreSQL URL, кодируем специальные символы в пароле
            if database_url.startswith('postgresql://'):
                try:
                    # Парсим URL
                    parts = database_url.replace('postgresql://', '').split('@')
                    if len(parts) == 2:
                        userpass, hostdb = parts
                        if ':' in userpass:
                            user, password = userpass.split(':', 1)
                            # Кодируем пароль
                            password_encoded = quote_plus(password)
                            database_url = f'postgresql://{user}:{password_encoded}@{hostdb}'
                            print(f"✅ Using PostgreSQL database")
                except Exception as e:
                    print(f"⚠️ Error parsing DATABASE_URL: {e}")
                    print("⚠️ Falling back to SQLite")
                    database_url = 'sqlite:///giftbot.db'
            else:
                print(f"✅ Using database: {database_url}")
        else:
            # SQLite по умолчанию
            database_url = 'sqlite:///giftbot.db'
            print("⚠️ DATABASE_URL not set, using SQLite (giftbot.db)")
        
        engine = create_engine(database_url, echo=False)
    return engine


def get_session():
    """Получить новую сессию базы данных"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(bind=get_engine())
    return SessionLocal()


def init_db():
    """Инициализация базы данных"""
    eng = get_engine()
    Base.metadata.create_all(eng)
    print("✅ Database initialized successfully!")


def add_initial_gifts():
    """Добавить начальные подарки"""
    session = get_session()
    
    # Проверяем, есть ли уже подарки
    existing = session.query(Gift).count()
    if existing > 0:
        print("⚠️ Gifts already exist in database")
        session.close()
        return
    
    # Добавляем начальные подарки
    gifts = [
        Gift(emoji='💎', name='Legendary Gift', rarity='legendary', quantity=1),
        Gift(emoji='⭐', name='Epic Gift', rarity='epic', quantity=3),
        Gift(emoji='🎁', name='Rare Gift', rarity='rare', quantity=5),
        Gift(emoji='🎀', name='Common Gift', rarity='common', quantity=10),
    ]
    
    session.add_all(gifts)
    session.commit()
    print("✅ Initial gifts added!")
    
    # Показываем что добавили
    for gift in gifts:
        print(f"  {gift.emoji} {gift.name} - {gift.quantity} шт ({gift.rarity})")
    
    session.close()


if __name__ == "__main__":
    print("🗄️ Initializing database...")
    init_db()
    add_initial_gifts()
    print("\n✅ Done! Database is ready to use.")