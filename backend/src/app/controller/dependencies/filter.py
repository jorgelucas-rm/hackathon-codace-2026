from fastapi import Request

EXCLUDED_QUERY_PARAMS = {"page", "size", "order_by", "order_direction"}


def get_filters(request: Request) -> dict:
    filters = {}

    for key in request.query_params.keys():
        if key in EXCLUDED_QUERY_PARAMS:
            continue

        values = request.query_params.getlist(key)

        if len(values) == 1:
            filters[key] = values[0]
        else:
            filters[key] = values

    return filters
