from flask import Flask, jsonify, g

from models.__init__ import Session
from models.employee import Employee
from resources.clients import clients_blueprint
from resources.employees import employees_blueprint
from resources.season_tickets import season_tickets_blueprint
from util.authentication import Authentication
from util.request import Req
from util.response import Resp

app = Flask(__name__)
app.register_blueprint(clients_blueprint)
app.register_blueprint(employees_blueprint)
app.register_blueprint(season_tickets_blueprint)

auth = Authentication()


@app.before_request
def before_request():
    g.db_session = Session()


@app.after_request
def after_request(response):
    """preflight request handler"""

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')

    g.db_session.close()
    return response


@app.route('/ecofitness/api/login', methods={'GET'})
@auth.by_role('admin', 'manager')
def login():
    """ main handler, returns user data"""
    req = Req().request
    reqargs = req.parse_args()

    employee = g.db_session.query(Employee).filter(Employee.login == reqargs['login']).first()

    resp = Resp().response
    resp['content']['employee'] = employee.read()
    return jsonify(resp), 200


if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.21')
