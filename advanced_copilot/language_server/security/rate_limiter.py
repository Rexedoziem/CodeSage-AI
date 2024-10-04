import asyncio
from pylsp import uris
#from pylsp_jsonrpc.examples.langserver import LanguageServer
from functools import wraps
import time
import config

class RateLimiter:
    def __init__(self, max_requests, period):
        self.max_requests = max_requests
        self.period = period
        self.requests = {}

    def is_allowed(self, user_id):
        current_time = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        self.requests[user_id] = [t for t in self.requests[user_id] if current_time - t < self.period]
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(current_time)
            return True
        return False

rate_limiter = RateLimiter(config.MAX_REQUESTS_PER_MINUTE, 60)

def rate_limit(max_requests):
    #rate_limiter = RateLimiter()
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            user_id = kwargs.get('user_id')
            if not rate_limiter.is_allowed(user_id):
                return {'error': 'Rate limit exceeded'}, 429
            return await f(*args, **kwargs)
        return decorated_function
    return decorator