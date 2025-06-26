from flask import request

class CustomLoggerMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        method = environ.get('REQUEST_METHOD')
        path = environ.get('PATH_INFO')
        with open("access.log", "a") as f:
            f.write(f"{method} {path}\n")
        return self.app(environ, start_response)