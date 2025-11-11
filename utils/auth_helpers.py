from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('rol') not in roles:
                return jsonify({'msg': 'Permiso denegado'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
