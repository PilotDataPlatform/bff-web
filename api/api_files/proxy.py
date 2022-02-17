from flask import request
from flask_restx import Resource
from flask_jwt import jwt_required
import requests

from resources.decorator import check_role


class BaseProxyResource(Resource):
    methods = [] 
    url = ""
    content_type = ""

    def __init__(self, *args, **kwargs):
        self.method_decorators = []
        self.required_roles = []

    def dispatch_request(self, *args, **kwargs):
        if request.method not in self.methods:
            return super().dispatch_request(*args, **kwargs)

        # Add decorators to the methods
        if self.required_roles:
            self.method_decorators.append(check_role(self.required_roles[request.method]))
        self.method_decorators.append(jwt_required())
        return super().dispatch_request(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.call_api(**kwargs)

    def post(self, *args, **kwargs):
        return self.call_api(**kwargs)

    def put(self, *args, **kwargs):
        return self.call_api(**kwargs)

    def delete(self, *args, **kwargs):
        return self.call_api(**kwargs)

    def call_api(self, **kwargs): 
        try:
            method = request.method.lower()
            # kwargs from the urls params are formated into the url
            url = self.url.format(**kwargs)

            headers = {k: v for k, v in request.headers.items()}
            if self.content_type:
                headers.update({'Content-Type': self.content_type})

            requests_kwargs = {
                "params": request.args,
                "json": request.get_json(),
                "headers": headers,
                "data": request.form,
            }
            requests_method = getattr(requests, method)
            res = requests_method(
                url,
                **requests_kwargs
            )
            return res.json(), res.status_code
        except Exception as e:
            return {'result': str(e)}, 403
