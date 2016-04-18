class Resp:
    """response scheme for all resources"""

    def __init__(self):
        self.response = dict()
        self.response['meta'] = dict()
        self.response['content'] = dict()
        self.response['meta']['code'] = 200
        self.response['meta']['description'] = 'Ok'