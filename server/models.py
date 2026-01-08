from sqlalchemy import Column, Integer, String, UniqueConstraint
from database import Base

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
