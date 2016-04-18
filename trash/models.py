import datetime
import os

from flask import g
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import Column, Integer, create_engine, String, Date, ForeignKey, Enum, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dateutil import parser
import logging as log

from util.config import app_config

engine = create_engine(app_config.db_path, echo=False)

Base = declarative_base()
Session = sessionmaker(bind=engine)


# таблица персонала
class Employee(Base):
    __tablename__ = 'employees'
    # обязательные атрибуты
    id_employee = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(128), unique=True, nullable=False)
    role = Column(Enum(*('admin', 'manager', 'reception', 'coach', 'barman')), nullable=False)
    status = Column(Enum(*('active', 'dismissed', 'vacation')), default='active', nullable=False)

    # дополнительные атрибуты
    id_registered_by = Column(Integer, ForeignKey('employees.id_employee'), nullable=True)
    registered_by = relationship('Employee', remote_side=id_employee)
    name = Column(String(255), nullable=True)
    surname = Column(String(255), nullable=True)  # фамилия
    patronymic = Column(String(255), nullable=True)  # отчество
    date_of_birth = Column(Date, nullable=True)
    employment_date = Column(Date, default=datetime.date.today(), nullable=True)
    dismissal_date = Column(Date, nullable=True)  # дата увольнения
    contract_file = Column(String(255), nullable=True)
    photo_file = Column(String(255), nullable=True)
    deposit = Column(Float, default=0)
    registered_client = relationship('Client', back_populates='registered_by')

    #  default=datetime.date(1990, 1, 1)
    # id_passport = Column(Integer, ForeignKey('passports.id_passport'), nullable=True)
    # passport = relationship('Passport', back_populates='employee')

    # атрибуты Кирилла

    # gender = Column(Enum(*{'male': 'male', 'female': 'female'}), default='female', nullable=False)

    def read(self):
        result = {
            'id_employee': self.id_employee,
            'login': self.login,
            'role': self.role,
            'check_status': self.status,
            'registered_by': {
                'id': self.id_registered_by,
                'role': g.db_session.query(Employee.role).filter(
                        Employee.id_employee == self.id_registered_by).one_or_none()[0],
                'name': g.db_session.query(Employee.name).filter(
                        Employee.id_employee == self.id_registered_by).one_or_none()[0],
                'surname': g.db_session.query(Employee.surname).filter(
                        Employee.id_employee == self.id_registered_by).one_or_none()[0],
            },
            'name': self.name,
            'surname': self.surname,
            'patronymic': self.patronymic,
            'date_of_birth': str(self.date_of_birth),
            'employment_date': str(self.employment_date),
            'dismissal_date': str(self.dismissal_date),
            'contract_file': self.contract_file,
            'photo_file': self.photo_file,
            'deposit': self.deposit,
        }
        return result

    def update(self, employee_fields):
        try:
            for column in employee_fields.keys():

                if column == 'login':
                    if g.db_session.query(Employee).filter(Employee.login == employee_fields[column]).first():
                        log.warning('login уже существует. models.Employee.update')
                        return False
                    setattr(self, column, employee_fields[column])

                elif column == 'password':
                    setattr(self, column, self.hash_password(employee_fields[column]))

                elif column == 'id_registered_by':
                    continue

                elif column == 'date_of_birth' or column == 'dismissal_date' or column == 'employment_date':
                    date = parser.parse(employee_fields[column]).date()
                    setattr(self, column, date)

                else:
                    setattr(self, column, employee_fields[column])

            self.rename_contract_file()

        except Exception:
            log.warning('плохие поля в models.Employee.update():  {0}'.format(employee_fields['name']))
            return False
        return True

    def create(self, employee_fields):
        try:

            for column in employee_fields.keys():

                if column == 'login':
                    if g.db_session.query(Employee).filter(Employee.login == employee_fields[column]).first():
                        log.warning('login уже существует. models.Employee.create')
                        return False
                    setattr(self, column, employee_fields[column])

                elif column == 'password':
                    self.hash_password(employee_fields[column])

                elif column == 'id_registered_by':
                    continue

                elif column == 'date_of_birth' or column == 'dismissal_date' or column == 'employment_date':
                    date = parser.parse(employee_fields[column]).date()
                    setattr(self, column, date)

                else:
                    setattr(self, column, employee_fields[column])

                self.generate_contract()

        except Exception:
            log.warning('плохие поля в models.Employee.create():  {0}'.format(employee_fields['name']))
            return False

        return True

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_contract(self):

        # TODO generate real contract file
        self.contract_file = '{path}/{role}_{login}_{surname}_{name}_{date_of_birth}.pdf'.format(
                path=app_config.employees_contracts_path,
                role=self.role, login=self.login,
                surname=self.surname, name=self.name,
                date_of_birth=self.date_of_birth)
        pass

    def rename_contract_file(self):

        # TODO rename real contract file
        self.contract_file = '{path}/{role}_{login}_{surname}_{name}_{date_of_birth}.pdf'.format(
                path=app_config.employees_contracts_path,
                role=self.role, login=self.login,
                surname=self.surname, name=self.name,
                date_of_birth=self.date_of_birth)
        pass

    def save_photo(self, photo_file):
        try:
            extension = os.path.splitext(photo_file.filename)[1]
            photo_file.filename = '{role}_{login}_{surname}_{name}_{date_of_birth}{extension}'.format(
                    role=self.role, login=self.login,
                    surname=self.surname, name=self.name,
                    date_of_birth=self.date_of_birth,
                    extension=extension)
            self.photo_file = app_config.employees_photos_path + photo_file.filename
            photo_file.save(app_config.employees_photos_path + '/' + photo_file.filename)
        except Exception as e:
            log.error(' save_photo:' + str(e))
            return False
        return True


# таблица Абаонементов
class SeasonTicket(Base):
    __tablename__ = 'seasonTickets'

    id_season_ticket = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    id_client = Column(Integer, ForeignKey('clients.id_client'), nullable=False, default=1)
    client = relationship('Client', back_populates='season_ticket')
    activation_date = Column(Date, nullable=True)  # дата активация
    date_of_freezing = Column(Date, nullable=True)  # дата начала заморозки
    period_of_validity = Column(Integer, default=365)  # срок действия абонементов (365 дней, 90 дней и т.д.)
    period_of_freezing = Column(Integer, default=90)  # максимальный период заморозки

    available_types = dict(fullday='fullday', morning='morning')  # возможные типы статуса абонементов (не  Column!!)
    available_statuses = dict(not_activated="not_activated", activated_before_freezing="activated_before_freezing",
                              frozen="frozen", activated_after_freezing="activated_after_freezing", expired="expired")

    type = Column(Enum(*available_types), default=available_types['fullday'], nullable=False)  # тип абонемента
    status = Column(Enum(*available_statuses), default=available_statuses['not_activated'],
                    nullable=False)  # статутс абонемента
    contract_file = Column(String(255), nullable=True)

    def generate_contract(self):
        # TODO generate real contract file
        self.contract_file = '{path}/{login}_{type}_{check_status}_{activation_date}.pdf'.format(
                path=app_config.season_tickets_contracts_path,
                login=self.client.login, type=self.type, status=self.status,
                acticvation_date=self.activation_date)
        pass

    def rename_contract_file(self):
        # TODO rename real contract file
        self.contract_file = '{path}/{login}_{type}_{check_status}_{activation_date}.pdf'.format(
                path=app_config.season_tickets_contracts_path,
                login=self.client.login, type=self.type, status=self.status,
                acticvation_date=self.activation_date)
        pass


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
    # print(pwd_context.encrypt('admin'))





    # таблица паспортов персонала
    # class Passport(Base):
    #     __tablename__ = 'passports'
    #
    #     id_passport = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=True)
    #     # employee = relationship('Employee', uselist=False, back_populates='passport')
    #     serial = Column(Integer, default=1000, nullable=False)
    #     number = Column(Integer, default=100000)
    #     date_of_issue = Column(Date, default=datetime.date(2000, 1, 1), nullable=False)
    #     issued_by = Column(Text, default='ТП №00', nullable=False)
    #     birth_place = Column(Text, default='Санкт-Петербург', nullable=False)
    #     registration_region = Column(Text, default='Санкт-Петербург', nullable=True)
    #     registration_locality = Column(Text, default='Санкт-Петербург', nullable=True)
    #     registration_street = Column(Text, default='Ленина ул.', nullable=True)
    #     registration_house = Column(Text, default='0', nullable=True)
    #     registration_flat = Column(Text, default='0', nullable=True)
    #     registration_issued = Column(Text, default='ТП №00', nullable=False)
    #
    #     @property
    #     def serial(self):
    #         return self.serial
    #
    #     @serial.setter
    #     def serial(self, serial):
    #         serial = re.sub('[\s,\n,\t,\r]', '', serial)
    #         serial = serial.replace('.', 'a')
    #         if (not len(serial) == 4) or (not serial.isdigit()):
    #             raise ValueError('serial in not 4 digit integer')
    #         self.serial = int(serial)
    #
    #     @property
    #     def number(self):
    #         return self.number
    #
    #     @number.setter
    #     def number(self, number):
    #         number = re.sub('[\s,\n,\t,\r]', ',', number)
    #         number = number.replace('.', 'a')
    #         if (not len(number) == 6) or (not number.isdigit()):
    #             raise ValueError('number is not 6 digit integer')
