import datetime
import os

from passlib.apps import custom_app_context as pwd_context
from dateutil import parser
from flask import g
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, Float
from sqlalchemy.orm import relationship
import logging as log

from models.base import Base
from util.config import app_config


# таблица персонала
class Employee(Base):
    __tablename__ = 'employees'
    # обязательные атрибуты
    id_employee = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(128), unique=True, nullable=False)
    role = Column(Enum(*('admin', 'manager', 'reception', 'coach', 'barman')), default='reception', nullable=False)
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
    registered_season_ticket = relationship('SeasonTicket', back_populates='registered_by')
    gender = Column(Enum(*('male','female')), nullable=True)

    # id_passport = Column(Integer, ForeignKey('passports.id_passport'), nullable=True)
    # passport = relationship('Passport', back_populates='employee')

    # атрибуты Кирилла

    # gender = Column(Enum(*{'male': 'male', 'female': 'female'}), default='female', nullable=False)

    def read(self):
        result = {
            'id_employee': self.id_employee,
            'login': self.login,
            'role': self.role,
            'status': self.status,
            'registered_by': {
                'id_employee': self.id_registered_by,
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
            'gender': self.gender
        }
        return result

    def update(self, employee_fields):
        try:
            for column in employee_fields.keys():
                if column in ['id_employee', 'id_registered_by']:
                    continue
                elif column == 'password':
                    setattr(self, column, self.hash_password(employee_fields[column]))
                elif column == 'date_of_birth' or column == 'dismissal_date' or column == 'employment_date':
                    date = parser.parse(employee_fields[column]).date()
                    setattr(self, column, date)
                else:
                    setattr(self, column, employee_fields[column])

            self.rename_contract_file()

        except Exception as ex:
            log.warning('плохие поля в models.Employee.update():  {0}'.format(ex))
            return False
        return True

    def create(self, employee_fields):
        try:

            for column in employee_fields.keys():
                if column in ['id_employee', 'id_registered_by']:
                    continue
                elif column == 'password':
                    self.hash_password(employee_fields[column])
                elif column == 'date_of_birth' or column == 'dismissal_date' or column == 'employment_date':
                    date = parser.parse(employee_fields[column]).date()
                    setattr(self, column, date)
                else:
                    setattr(self, column, employee_fields[column])

                self.generate_contract()

        except Exception as e:
            log.warning('плохие поля в models.Employee.create():  {0}'.format(e))
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
            photo_file.filename = '{role}_{login}_{surname}_{name}_{date_of_birth}'.format(
                    role=self.role, login=self.login,
                    surname=self.surname, name=self.name,
                    date_of_birth=self.date_of_birth)
            self.photo_file = 'http://192.168.43.48/employees_photos/'+photo_file.filename
            photo_file.save(app_config.employees_photos_path + '/' + photo_file.filename)
        except Exception as e:
            log.error(' save_photo:' + str(e))
            return False
        return True
