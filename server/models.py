from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class ShipmentPlan(Base):
    __tablename__ = 'shipment_plans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    Planweek = Column(String, nullable=False)
    Created_at = Column(String)
    Division = Column(String, nullable=False)
    From_Site = Column(String, name='From Site', nullable=False)
    Region = Column(String)
    To_Site = Column(String, name='To Site', nullable=False)
    Mapping_Model_Suffix = Column(String, name='Mapping Model.Suffix', nullable=False)
    Rep_PMS = Column(String, name='Rep PMS')
    Category = Column(String)
    Frozen = Column(String)
    Month = Column(String)
    Week_Name = Column(String, name='Week Name', nullable=False)
    SP = Column(Integer)

    __table_args__ = (
        UniqueConstraint(
            'Planweek', 'Created_at', 'Division', 'From Site', 'To Site', 'Mapping Model.Suffix', 'Category', 'Week Name',
            name='_shipment_plan_uc'
        ),
    )

    def __repr__(self):
        return f"<ShipmentPlan(id={self.id}, Planweek='{self.Planweek}', Division='{self.Division}')>"


class User(Base):
    """ORCA 사용자 모델"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    email = Column(String(100), nullable=False)
    team = Column(String(100), nullable=False)
    company = Column(String(100), nullable=False)
    status = Column(String(20), default='pending')  # pending, active, rejected
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    login_history = relationship('LoginHistory', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User(id={self.id}, userid='{self.userid}', status='{self.status}')>"


class LoginHistory(Base):
    """로그인 기록 모델"""
    __tablename__ = 'login_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    login_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))

    user = relationship('User', back_populates='login_history')

    def __repr__(self):
        return f"<LoginHistory(user_id={self.user_id}, login_at='{self.login_at}')>"
