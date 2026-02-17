from flask import jsonify

def build_response(success: bool,
                   payload: dict = None,
                   *,
                   error: str = None,
                   message: str = None,
                   cache_hit: bool = False,
                   data_source: str = None,
                   authenticated: bool = False,
                   status_code: int = 200,
                   page: int = None,
                   pages: int = None,
                   total: int = None,
                   extra: dict = None):
    """Construct a unified JSON response with optional automatic data_points counting.

    Standard keys:
      success (bool)
      cache_hit (bool)
      data_source (str)
      authenticated (bool)
      error (optional str)
      message (optional str)
      page/pages/total (optional pagination metadata)

    Enhancements:
      - extra (dict): arbitrary extra meta keys merged without overwriting existing keys
      - automatic data_points: if not already present, infer from common list payload keys
    """
    body = {}
    if payload:
        body.update(payload)
    body.setdefault('success', success)
    body.setdefault('cache_hit', cache_hit)
    if data_source is not None:
        body.setdefault('data_source', data_source)
    body.setdefault('authenticated', authenticated)
    if not success and error:
        body.setdefault('error', error)
    if message:
        body.setdefault('message', message)
    # Pagination metadata (only include if provided)
    if page is not None:
        body.setdefault('page', page)
    if pages is not None:
        body.setdefault('pages', pages)
    if total is not None:
        body.setdefault('total', total)

    # Merge extra meta keys without overwriting existing values
    if extra:
        for k, v in extra.items():
            body.setdefault(k, v)

    # Automatic data_points calculation if not provided
    if 'data_points' not in body:
        candidate_keys = ('data', 'items', 'results', 'records', 'rows')
        for ck in candidate_keys:
            if ck in body and isinstance(body[ck], list):
                body['data_points'] = len(body[ck])
                break
        else:
            # If payload is a single-key dict whose value is a list, count it
            if payload and len(payload) == 1:
                only_key = next(iter(payload))
                if isinstance(payload[only_key], list):
                    body['data_points'] = len(payload[only_key])

    return jsonify(body), status_code

def ok(payload: dict, *, extra: dict = None, **meta):
    return build_response(True, payload, extra=extra, **meta)

def fail(error: str, *, message: str = None, data: dict = None, extra: dict = None, **meta):
    # Allow passing a data dict that will be merged
    payload = data or {}
    return build_response(False, payload, error=error, message=message, extra=extra, **meta)
