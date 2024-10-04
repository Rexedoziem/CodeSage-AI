import asyncio
from functools import wraps

class RequestThrottler:
    def __init__(self, rate_limit: int = 5, time_window: int = 60):
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.request_times = []

    @staticmethod
    def throttle(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            current_time = asyncio.get_event_loop().time()
            self.request_times = [t for t in self.request_times if current_time - t < self.time_window]
            
            if len(self.request_times) >= self.rate_limit:
                wait_time = self.time_window - (current_time - self.request_times[0])
                await asyncio.sleep(wait_time)
            
            self.request_times.append(current_time)
            return await func(self, *args, **kwargs)
        return wrapper