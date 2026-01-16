from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
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
    contact = Column(String(50))  # 연락처 추가
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

class MonitorStuffing(Base):
    """모니터 적재 수량(Stuffing) 기준 정보 모델"""
    __tablename__ = 'monitor_stuffing'

    id = Column(Integer, primary_key=True, autoincrement=True)
    series = Column(String(100), unique=True, nullable=False)
    qty_20ft = Column(Integer)
    qty_40ft = Column(Integer)
    qty_40hc = Column(Integer)

    def __repr__(self):
        return f"<MonitorStuffing(series='{self.series}', qty_20ft={self.qty_20ft})>"

class SiteMapping(Base):
    """사이트 매핑 정보 모델"""
    __tablename__ = 'site_mapping'

    ship_to = Column('Ship To', String(100), primary_key=True)
    to_site = Column('To Site', String(100))
    region = Column('Region', String(50))
    country = Column('Country', String(50))

    def __repr__(self):
        return f"<SiteMapping(ship_to='{self.ship_to}', to_site='{self.to_site}')>"

class OSModel(Base):
    """아웃소싱 모델 정보 모델"""
    __tablename__ = 'os_models'

    series = Column('Series', String(100), primary_key=True)

    def __repr__(self):
        return f"<OSModel(series='{self.series}')>"

class WorkDiary(Base):
    """업무 일지(Work Diary) 모델"""
    __tablename__ = 'work_diary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # HTML content
    author_id = Column(Integer, ForeignKey('users.id'))
    hashtags = Column(String(500))  # Comma-separated
    status = Column(String(20), default='진행중')  # 진행중, 완료
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship('User', backref='work_entries')
    comments = relationship('Comment', back_populates='work_entry', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkDiary(id={self.id}, title='{self.title}', status='{self.status}')>"

class Comment(Base):
    """댓글 모델"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_entry_id = Column(Integer, ForeignKey('work_diary.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    work_entry = relationship('WorkDiary', back_populates='comments')
    author = relationship('User', backref='diary_comments')

    def __repr__(self):
        return f"<Comment(id={self.id}, work_entry_id={self.work_entry_id})>"
