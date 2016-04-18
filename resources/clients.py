import json

import sqlalchemy
import werkzeug
from flask import jsonify, Blueprint, g
import logging as log

from models.client import Client
from util.authentication import Authentication
from util.request import Req
from util.response import Resp

auth = Authentication()
clients_blueprint = Blueprint('clients_blueprint', __name__)


class Clients:
    @staticmethod
    @clients_blueprint.route('/ecofitness/api/clients', methods={'GET'})
    @auth.by_role('admin', 'manager', 'reception')
    def get_clients():

        clients = g.db_session.query(Client).all()

        resp = Resp().response
        if not clients:
            resp['content']['clients'] = []
            return jsonify(resp), 200

        if g.employee.role in ['admin', 'manager']:
            clients = [client.read() for client in clients]
        elif g.employee.role == 'reception':
            clients = [client.read_for_reception() for client in clients]

        resp['content']['clients'] = clients
        return jsonify(resp), 200

    @staticmethod
    @clients_blueprint.route('/ecofitness/api/clients/<int:id_client>', methods={'GET'})
    @auth.by_role('admin', 'manager', 'reception')
    def get_client(id_client):
        client = g.db_session.query(Client).get(id_client)

        resp = Resp().response
        if not client:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'item does not exist'
            return jsonify(resp), 404

        client = client.read()
        resp['content']['client'] = client
        return jsonify(resp), 200

    @staticmethod
    @clients_blueprint.route('/ecofitness/api/clients/<int:id_client>', methods={'PUT'})
    @auth.by_role('admin', 'manager')
    def put_client(id_client):
        req = Req().request
        req.add_argument('client')
        reqargs = req.parse_args()

        resp = Resp().response
        if not reqargs['client']:
            resp['meta']['code'] = 403
            resp['meta']['description'] = 'incorrect request'
            return jsonify(resp), 403

        client = g.db_session.query(Client).get(id_client)
        if client is None:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'client not found'
            return jsonify(resp), 404

        if not client.update(json.loads(reqargs['client'].replace("'", '"'))):
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'column not found/failed'
            return jsonify(resp), 404

        try:
            g.db_session.commit()
        except sqlalchemy.exc.IntegrityError as ex:
            log.warning('resources.Clients.put_client(): '+str(ex))
            if 'UNIQUE constraint failed: clients.login' in str(ex):
                resp['meta']['code'] = 403
                resp['meta']['description'] = 'login already exist'
                return jsonify(resp), 403
            elif 'NOT NULL constraint failed: clients.login' in str(ex):
                resp['meta']['code'] = 403
                resp['meta']['description'] = 'login is empty'
                return jsonify(resp), 403
            else:
                resp['meta']['code'] = 403
                resp['meta']['description'] = str(ex)
                return jsonify(resp), 403


        resp['meta']['description'] = 'success'

        return jsonify(resp), 200

    @staticmethod
    @clients_blueprint.route('/ecofitness/api/clients', methods={'POST'})
    @auth.by_role('admin', 'manager')
    def post_client():
        req = Req().request
        req.add_argument('client')
        reqargs = req.parse_args()

        resp = Resp().response
        if not reqargs['client']:
            resp['meta']['code'] = 403
            resp['meta']['description'] = 'incorrect request'
            return jsonify(resp), 403

        client = Client()
        if not client.create(json.loads(reqargs['client'].replace("'", '"'))):
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'column not found/failed/login already exists'
            return jsonify(resp), 404


        client.id_registered_by = g.employee.id_employee
        try:
            g.db_session.add(client)
            g.db_session.commit()
        except sqlalchemy.exc.IntegrityError as ex:
            log.warning('resources.Clients.post_client(): '+str(ex))
            if 'UNIQUE constraint failed: clients.login' in str(ex):
                resp['meta']['code'] = 403
                resp['meta']['description'] = 'login already exist'
                return jsonify(resp), 403
            elif 'NOT NULL constraint failed: clients.login' in str(ex):
                resp['meta']['code'] = 403
                resp['meta']['description'] = 'login is empty'
                return jsonify(resp), 403
            else:
                resp['meta']['code'] = 403
                resp['meta']['description'] = str(ex)
                return jsonify(resp), 403



        resp['meta']['description'] = 'success'
        resp['content']['id_client'] = client.id_client

        return jsonify(resp), 200

    @staticmethod
    @clients_blueprint.route('/ecofitness/api/clients/<int:id_client>', methods={'DELETE'})
    @auth.by_role('admin')
    def delete_client(id_client):
        client = g.db_session.query(Client).get(id_client)

        resp = Resp().response
        if not client:
            resp['meta']['code'] = 404
            resp['meta']['description'] = "client doesn't exist"
            return jsonify(resp), 404

        g.db_session.delete(client)
        g.db_session.commit()

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200

    @staticmethod
    @clients_blueprint.route('/ecofitness/api/clients/upload_photo/<int:id_client>', methods={'POST'})
    @auth.by_role('admin')
    def upload_photo(id_client):
        req = Req().request
        req.add_argument('photo_file', type=werkzeug.datastructures.FileStorage, location='files')
        photo_file = req.parse_args()['photo_file']

        client = g.db_session.query(Client).get(id_client)
        resp = Resp().response
        if client is None:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'client not found'
            return jsonify(resp), 404

        # app.logger.debug('File is saved as %s', filename)
        if not client.save_photo(photo_file):
            resp['meta']['code'] = 500
            resp['meta']['description'] = 'save photo error'
            return jsonify(resp), 500

        g.db_session.commit()
        g.db_session.close()

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200
