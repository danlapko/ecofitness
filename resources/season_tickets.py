import json

import sqlalchemy
import werkzeug
from flask import jsonify, Blueprint, g
import logging as log

from models import SeasonTicket
from models.client import Client
from util.authentication import Authentication
from util.request import Req
from util.response import Resp

auth = Authentication()
season_tickets_blueprint = Blueprint('season_tickets_blueprint', __name__)


class Clients:
    @staticmethod
    @season_tickets_blueprint.route('/ecofitness/api/season_tickets', methods={'GET'})
    @auth.by_role('admin', 'manager', 'reception')
    def get_season_tickets():

        season_tickets = g.db_session.query(SeasonTicket).all()

        resp = Resp().response
        if not season_tickets:
            resp['content']['clients'] = []
            return jsonify(resp), 200

        if g.employee.role in ['admin', 'manager']:
            season_tickets = [season_ticket.read() for season_ticket in season_tickets]
        elif g.employee.role == 'reception':
            season_tickets = [season_ticket.read_for_preview() for season_ticket in season_tickets]

        resp['content']['season_tickets'] = season_tickets
        return jsonify(resp), 200

    @staticmethod
    @season_tickets_blueprint.route('/ecofitness/api/season_tickets/<int:id_season_ticket>', methods={'GET'})
    @auth.by_role('admin', 'manager', 'reception')
    def get_season_ticket(id_season_ticket):
        season_ticket = g.db_session.query(SeasonTicket).get(id_season_ticket)

        resp = Resp().response
        if not season_ticket:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'item does not exist'
            return jsonify(resp), 404

        season_ticket = season_ticket.read()
        resp['content']['season_ticket'] = season_ticket
        return jsonify(resp), 200

    @staticmethod
    @season_tickets_blueprint.route('/ecofitness/api/season_tickets', methods={'POST'})
    @auth.by_role('admin', 'manager')
    def post_season_ticket():
        req = Req().request
        req.add_argument('season_ticket')
        reqargs = req.parse_args()

        resp = Resp().response
        if not reqargs['season_ticket']:
            resp['meta']['code'] = 403
            resp['meta']['description'] = 'incorrect request'
            return jsonify(resp), 403

        season_ticket = SeasonTicket()
        if not season_ticket.create(json.loads(reqargs['season_ticket'].replace("'", '"'))):
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'column not found/failed/login already exists'
            return jsonify(resp), 404

        season_ticket.id_registered_by = g.employee.id_employee
        try:
            g.db_session.add(season_ticket)
            g.db_session.commit()
        except sqlalchemy.exc.IntegrityError as ex:
            log.warning('resources.SeasonTickets.post_seasonTicket(): ' + str(ex))
            resp['meta']['code'] = 403
            resp['meta']['description'] = str(ex)
            return jsonify(resp), 403

        resp['meta']['description'] = 'success'
        resp['content']['id_season_ticket'] = season_ticket.id_season_ticket

        return jsonify(resp), 200

    @staticmethod
    @season_tickets_blueprint.route('/ecofitness/api/season_tickets/activate/<int:id_season_ticket>', methods={'PUT'})
    @auth.by_role('admin', 'manager')
    def activate_season_ticket(id_season_ticket):
        season_ticket = g.db_session.query(SeasonTicket).get(id_season_ticket)

        resp = Resp().response
        if not season_ticket:
            resp['meta']['code'] = 404
            resp['meta']['description'] = "season_ticket doesn't exist"
            return jsonify(resp), 404
        if not season_ticket.activate():
            resp['meta']['code'] = 403
            resp['meta']['description'] = "check_status does not appropriate for activate()"
            return jsonify(resp), 403

        g.db_session.commit()

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200

    @staticmethod
    @season_tickets_blueprint.route('/ecofitness/api/season_tickets/freeze/<int:id_season_ticket>', methods={'PUT'})
    @auth.by_role('admin', 'manager')
    def freeze_season_ticket(id_season_ticket):
        season_ticket = g.db_session.query(SeasonTicket).get(id_season_ticket)

        resp = Resp().response
        if not season_ticket:
            resp['meta']['code'] = 404
            resp['meta']['description'] = "season_ticket doesn't exist"
            return jsonify(resp), 404
        if not season_ticket.freeze():
            resp['meta']['code'] = 403
            resp['meta']['description'] = "check_status does not appropriate for freeze()"
            return jsonify(resp), 403

        g.db_session.commit()

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200

    @staticmethod
    @season_tickets_blueprint.route('/ecofitness/api/season_tickets/<int:id_season_ticket>', methods={'DELETE'})
    @auth.by_role('admin')
    def delete_season_ticket(id_season_ticket):
        season_ticket = g.db_session.query(SeasonTicket).get(id_season_ticket)

        resp = Resp().response
        if not season_ticket:
            resp['meta']['code'] = 404
            resp['meta']['description'] = "season_ticket doesn't exist"
            return jsonify(resp), 404
        if not season_ticket.delete():
            resp['meta']['code'] = 403
            resp['meta']['description'] = "check_status does not appropriate for delete()"
            return jsonify(resp), 403

        g.db_session.delete(season_ticket)
        g.db_session.commit()

        resp['meta']['description'] = 'success'
