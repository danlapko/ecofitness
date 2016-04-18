import datetime

from dateutil import parser
from flask import g
from sqlalchemy import Column, Integer, ForeignKey, Date, Enum, String
from sqlalchemy.orm import relationship
import logging as log

from models.employee import Employee
from models.base import Base
from util.config import app_config


# таблица Абаонементов
class SeasonTicket(Base):
    __tablename__ = 'seasonTickets'

    # обязательные атрибуты
    id_season_ticket = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    id_client = Column(Integer, ForeignKey('clients.id_client'), nullable=False)
    client = relationship('Client', back_populates='season_ticket')
    id_registered_by = Column(Integer, ForeignKey('employees.id_employee'))
    registered_by = relationship('Employee', back_populates='registered_season_ticket')

    # допоплнительные атрибуты
    type = Column(Enum(*('fullday', 'morning')), default='fullday', nullable=True)  # тип абонемента
    status = Column(Enum(*('not_activated', 'active_before_freezing', 'freezing', 'active_after_freezing', 'expired')),
                    default='not_activated', nullable=True)  # статутс абонемента
    registration_date = Column(Date, default=datetime.date.today(), nullable=True)
    activation_date = Column(Date, nullable=True)  # дата активация
    expiration_date = Column(Date, nullable=True)  # дата истечения срока действия абонемента
    date_of_freezing = Column(Date, nullable=True)  # дата начала заморозки
    period_of_validity = Column(Integer, default=365)  # срок действия абонементов (365 дней, 90 дней и т.д.)
    period_of_freezing = Column(Integer, default=90)  # максимальный период заморозки
    contract_file = Column(String(255), nullable=True)

    def check_status(self):
        if (self.status == 'active_before_freezing') and (
                    (self.activation_date + datetime.timedelta(days=self.period_of_validity)) < datetime.date.today()):
            self.status = 'expired'

        elif (self.status == 'freezing') and (
                    (self.date_of_freezing + datetime.timedelta(days=self.period_of_freezing)) < datetime.date.today()):
            if (self.activation_date + datetime.timedelta(
                    days=self.period_of_freezing) + datetime.timedelta(
                    days=self.period_of_validity)) > datetime.date.today():
                self.status = 'active_after_freezing'
            else:
                self.status = 'expired'

        elif (self.status == 'active_after_freezing') and (self.activation_date + datetime.timedelta(
                days=self.period_of_freezing) + datetime.timedelta(
                days=self.period_of_validity)) < datetime.date.today():
            self.status = 'expired'

        return self.status

    def calculate_expiration_date(self):
        self.check_status()

        if self.status == 'not_activated':
            self.expiration_date = datetime.date.today() + datetime.timedelta(days=self.period_of_validity)
        else:
            self.expiration_date = self.activation_date + datetime.timedelta(days=self.period_of_validity)
            if self.status == 'freezing':
                self.expiration_date += datetime.date.today() - self.date_of_freezing
            elif self.status in ['active_after_freezing', 'expired']:
                self.expiration_date += datetime.timedelta(days=self.period_of_freezing)

        return self.expiration_date

    def read(self):
        from models import Client
        result = {
            'id_season_ticket': self.id_season_ticket,
            'client': {
                'id_client': self.id_client,
                'name': g.db_session.query(Client.name).filter(
                        Client.id_client == self.id_client).one_or_none()[0],
                'surname': g.db_session.query(Client.surname).filter(
                        Client.id_client == self.id_client).one_or_none()[0],
            },
            'registered_by': {
                'id_employee': self.id_registered_by,
                'role': g.db_session.query(Employee.role).filter(
                        Employee.id_employee == self.id_registered_by).one_or_none()[0],
                'name': g.db_session.query(Employee.name).filter(
                        Employee.id_employee == self.id_registered_by).one_or_none()[0],
                'surname': g.db_session.query(Employee.surname).filter(
                        Employee.id_employee == self.id_registered_by).one_or_none()[0],
            },
            'type': self.type,
            'status': self.check_status(),
            'activation_date': str(self.activation_date),
            'date_of_freezing': str(self.date_of_freezing),
            'period_of_validity': str(self.period_of_validity),
            'period_of_freezing': str(self.period_of_freezing),
            'expiration_date': str(self.calculate_expiration_date())
        }
        return result

    def read_for_preview(self):
        result = {
            'id_season_ticket': self.id_season_ticket,
            'type': self.type,
            'status': self.check_status(),
            'activation_date': str(self.activation_date),
            'expiration_date': str(self.calculate_expiration_date())
        }
        return result

    def create(self, fields):
        try:
            for column in fields.keys():
                if column in ['id_season_ticket', 'id_registered_by', 'status', 'registration_date', 'activation_date',
                              'expiration_date', 'date_of_freezing', 'contract_file']:
                    continue
                else:
                    setattr(self, column, fields[column])

                    # self.generate_contract()

        except Exception as ex:
            log.warning('плохие поля в models.SeasonTickets.create():  {0}'.format(ex))
            return False

        return True

    def activate(self):
        self.check_status()
        if self.status == 'not_activated':
            self.status = 'active_before_freezing'
            self.activation_date = datetime.date.today()
            return True
        elif self.status == 'freezing':
            self.status = 'active_after_freezing'
            self.activation_date = datetime.date.today()
            return True

        return False

    def freeze(self):
        self.check_status()
        if self.status == 'active_before_freezing':
            self.status = 'freezing'
            self.date_of_freezing = datetime.date.today()
            return True
        else:
            return False

    def generate_contract(self):
        # TODO generate real contract file
        self.contract_file = '{path}/{login}_{type}_{check_status}_{activation_date}.pdf'.format(
                path=app_config.season_tickets_contracts_path,
                login=self.client.login, type=self.type, status=self.status,
                acticvation_date=self.activation_date)
        pass
