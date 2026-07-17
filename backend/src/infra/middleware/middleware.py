from fastapi import FastAPI

from src.infra.middleware.cors import register_cors_middleware


class Middleware:

    @staticmethod
    def register_middlewares(app: FastAPI):
        register_cors_middleware(app)
