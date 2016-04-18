import datetime
import os

from passlib.apps import custom_app_context as pwd_context
from dateutil import parser
from flask import g
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, Enum
from sqlalchemy.orm import relationship
import logging as log

from models.season_ticket import SeasonTicket
from models.base import Base
from models.employee import Employee
from util.config import app_config


# таблица клиентов
class Client(Base):
    __tablename__ = 'clients'

    # обязательные атрибуты
    id_client = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)

    # дополнительные атрибуты
    id_registered_by = Column(Integer, ForeignKey('employees.id_employee'), nullable=True)
    registered_by = relationship('Employee', back_populates='registered_client')
    name = Column(String(255), nullable=True)
    surname = Column(String(255), nullable=True)  # фамилия
    patronymic = Column(String(255), nullable=True)  # отчество
    date_of_birth = Column(Date, nullable=True)
    registration_date = Column(Date, default=datetime.date.today())  # дата регистрации
    photo_file = Column(String(255), nullable=True)
    deposit = Column(Float, default=0)
    gender = Column(Enum(*('male', 'female')), nullable=True)

    season_ticket = relationship('SeasonTicket', back_populates='client')  # foregin key Абонемент

    def read(self):
        result = {'id_client': self.id_client,
                  'login': self.login,
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
                  'registration_date': str(self.registration_date),
                  'photo_file': self.photo_file,
                  'deposit': self.deposit,
                  'gender': self.gender,
                  'season_tickets': [season_ticket.read_for_preview() for season_ticket in
                                     g.db_session.query(SeasonTicket).filter(
                                             SeasonTicket.id_client == self.id_client).all()]
                  }
        return result

    def read_for_reception(self):
        result = {'id_client': self.id_client,
                  'name': self.name,
                  'surname': self.surname,
                  'patronymic': self.patronymic,
                  'date_of_birth': str(self.date_of_birth),
                  }
        return result

    def update(self, fields):
        try:
            for column in fields.keys():
                if column in ['id_client', 'id_registered_by', 'registration_date']:
                    continue
                elif column == 'password':
                    setattr(self, column, self.hash_password(fields[column]))

                elif column == 'date_of_birth':
                    date = parser.parse(fields[column]).date()
                    setattr(self, column, date)

                else:
                    setattr(self, column, fields[column])

        except Exception as ex:
            log.warning('плохие поля в models.Employee.update():  {0}'.format(ex))
            return False
        return True

    def create(self, fields):
        try:

            for column in fields.keys():
                if column in ['id_client', 'id_registered_by', 'registration_date']:
                    continue
                elif column == 'password':
                    self.hash_password(fields[column])
                elif column == 'date_of_birth':
                    date = parser.parse(fields[column]).date()
                    setattr(self, column, date)
                else:
                    setattr(self, column, fields[column])

        except Exception as ex:
            log.warning('плохие поля в models.Client.create():  {0}'.format(ex))
            return False

        return True

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def save_photo(self, photo_file):
        try:
            photo_file.filename = '{login}_{surname}_{name}_{date_of_birth}'.format(
                    login=self.login, surname=self.surname, name=self.name,
                    date_of_birth=self.date_of_birth)
            self.photo_file = 'http://192.168.43.48/clients_photos/' + photo_file.filename
            photo_file.save(app_config.clients_photos_path + '/' + photo_file.filename)
        except Exception as e:
            log.error(' save clients photo: ' + str(e))
            return False
        return True
