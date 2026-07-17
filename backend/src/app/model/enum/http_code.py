from enum import Enum


class HttpCode(int, Enum):

    # 2xx - Success
    OK = 200
    CREATED = 201

    # 4xx – Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    TOO_MANY_REQUESTS = 429
    UNPROCESSABLE_ENTITY = 422

    # 5xx – Server errors
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
