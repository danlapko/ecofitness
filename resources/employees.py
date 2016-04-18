import json

import sqlalchemy
import werkzeug
from flask import jsonify, Blueprint, g
import logging as log

from models.employee import Employee
from util.authentication import Authentication
from util.request import Req
from util.response import Resp

auth = Authentication()

employees_blueprint = Blueprint('employees_blueprint', __name__)


class Employees:
    """ Access rights: Administrator """

    @staticmethod
    @employees_blueprint.route('/ecofitness/api/employees', methods={'GET'})
    @auth.by_role('admin')
    def get_employees():

        employees = g.db_session.query(Employee).all()

        resp = Resp().response
        if not employees:
            resp['content']['employees'] = []
            return jsonify(resp), 200

        employees = [employee.read() for employee in employees]
        resp['content']['employees'] = employees
        return jsonify(resp), 200

    @staticmethod
    @employees_blueprint.route('/ecofitness/api/employees/<int:id_employee>', methods={'GET'})
    @auth.by_role('admin')
    def get_employee(id_employee):
        employee = g.db_session.query(Employee).filter(Employee.id_employee == id_employee).first()

        resp = Resp().response
        if not employee:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'item does not exist'
            return jsonify(resp), 404

        employee = employee.read()
        resp['content']['employee'] = employee
        return jsonify(resp), 200

    @staticmethod
    @employees_blueprint.route('/ecofitness/api/employees/<int:id_employee>', methods={'PUT'})
    @auth.by_role('admin')
    def put_employee(id_employee):
        req = Req().request
        req.add_argument('employee')
        reqargs = req.parse_args()

        resp = Resp().response
        if not reqargs['employee']:
            resp['meta']['code'] = 403
            resp['meta']['description'] = 'incorrect request'
            return jsonify(resp), 403

        employee = g.db_session.query(Employee).filter(Employee.id_employee == id_employee).first()
        if employee is None:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'employee not found'
            return jsonify(resp), 404

        if not employee.update(json.loads(reqargs['employee'].replace("'", '"'))):
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'column not found/failed'
            return jsonify(resp), 404
        try:
            g.db_session.commit()
        except sqlalchemy.exc.IntegrityError as ex:
            log.warning('resources.Employees.put_employee(): '+str(ex))
            if 'UNIQUE constraint failed: employees.login' in str(ex):
                resp['meta']['code'] = 403
                resp['meta']['description'] = 'login already exist'
                return jsonify(resp), 403
            else:
                resp['meta']['code'] = 403
                resp['meta']['description'] = str(ex)
                return jsonify(resp), 403

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200

    @staticmethod
    @employees_blueprint.route('/ecofitness/api/employees', methods={'POST'})
    @auth.by_role('admin')
    def post_employee():
        req = Req().request
        req.add_argument('employee')
        reqargs = req.parse_args()

        resp = Resp().response
        if not reqargs['employee']:
            resp['meta']['code'] = 403
            resp['meta']['description'] = 'incorrect request'
            return jsonify(resp), 403

        employee = Employee()
        if not employee.create(json.loads(reqargs['employee'].replace("'", '"'))):
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'column not found/failed/login already exists'
            return jsonify(resp), 404

        employee.id_registered_by = g.employee.id_employee

        try:
            g.db_session.add(employee)
            g.db_session.commit()
        except sqlalchemy.exc.IntegrityError as ex:
            log.warning('resources.Employees.post_employee(): '+str(ex))
            if 'UNIQUE constraint failed: employees.login' in str(ex):
                resp['meta']['code'] = 403
                resp['meta']['description'] = 'login already exist'
                return jsonify(resp), 403
            else:
                resp['meta']['code'] = 403
                resp['meta']['description'] = str(ex)
                return jsonify(resp), 403

        resp['meta']['description'] = 'success'
        resp['content']['id_employee'] = employee.id_employee

        return jsonify(resp), 200

    @staticmethod
    @employees_blueprint.route('/ecofitness/api/employees/<int:id_employee>', methods={'DELETE'})
    @auth.by_role('admin')
    def delete_employee(id_employee):
        employee = g.db_session.query(Employee).get(id_employee)

        resp = Resp().response
        if not employee:
            resp['meta']['code'] = 404
            resp['meta']['description'] = "employee doesn't exist"
            return jsonify(resp), 404

        g.db_session.delete(employee)
        g.db_session.commit()

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200

    @staticmethod
    @employees_blueprint.route('/ecofitness/api/employees/upload_photo/<int:id_employee>', methods={'POST'})
    @auth.by_role('admin')
    def upload_photo(id_employee):
        req = Req().request
        req.add_argument('photo_file', type=werkzeug.datastructures.FileStorage, location='files')
        photo_file = req.parse_args()['photo_file']

        employee = g.db_session.query(Employee).get(id_employee)
        resp = Resp().response
        if employee is None:
            resp['meta']['code'] = 404
            resp['meta']['description'] = 'employee not found'
            return jsonify(resp), 404

        # app.logger.debug('File is saved as %s', filename)
        if not employee.save_photo(photo_file):
            resp['meta']['code'] = 500
            resp['meta']['description'] = 'save photo error'
            return jsonify(resp), 500

        g.db_session.commit()
        g.db_session.close()

        resp['meta']['description'] = 'success'

        return jsonify(resp), 200
