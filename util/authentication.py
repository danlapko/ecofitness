from functools import wraps

from flask import jsonify, g

from models.employee import Employee
from util.request import Req
from util.response import Resp


class Authentication:
    def by_role(self, *roles):
        if len(roles) == 0:
            roles = ('admin', 'manager', 'reception', 'coach', 'barman', 'barman_admin')

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                req = Req().request
                reqargs = req.parse_args()

                resp = Resp().response

                if not (reqargs['login'] and reqargs['password']):
                    resp['meta']['code'] = 400
                    resp['meta']['description'] = 'both login and password required'
                    return jsonify(resp), 400

                if not g.db_session.query(Employee.login).filter(Employee.role.in_(roles)).filter(
                                Employee.login == reqargs['login']).one_or_none():
                    resp['meta']['code'] = 403
                    resp['meta']['description'] = 'login not found'
                    return jsonify(resp), 403

                employee = g.db_session.query(Employee).filter(Employee.role.in_(roles)).filter(
                        Employee.login == reqargs['login']).one_or_none()

                if not employee.verify_password(reqargs['password']):
                    resp['meta']['code'] = 403
                    resp['meta']['description'] = 'incorrect password'
                    return jsonify(resp), 403
                g.employee = employee
                return func(*args, **kwargs)

            return wrapper

        return decorator
