from flask_restful import reqparse


class Req:
    """request scheme for all resources"""

    def __init__(self):
        self.request = reqparse.RequestParser()
        self.request.add_argument('login', type=str)
        self.request.add_argument('password', type=str)
