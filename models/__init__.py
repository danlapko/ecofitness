from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from util.config import app_config
from models.employee import Employee
from models.client import Client
from models.season_ticket import SeasonTicket

engine = create_engine(app_config.db_path, echo=False)
Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    session = Session()
    employee = Employee()
    employee.create(dict(login='admin', password='admin', role='admin', status='active', name='aaa', surname='bbb',
                         patronymic='ccc'))
    employee.id_registered_by = 1
    session.add(employee)
    session.commit()
    session.close()