import time

from utils.redis import (
    get_connection_count, get_requests_per_second, get_max_requests_per_second, get_data_frequency)


def __avg_requests_per_second():
    now = int(time.time())
    rps = []
    rps.append(get_requests_per_second(now))
    rps.append(get_requests_per_second(now-1))
    rps.append(get_requests_per_second(now-3))
    rps.append(get_requests_per_second(now-3))
    rps.append(get_requests_per_second(now-4))

    return sum(rps) / len(rps)


def get_state():
    return {
        'connectionCount': get_connection_count(),
        'requestsPerSecond': __avg_requests_per_second(),
        'maxRequestsPerSecond': get_max_requests_per_second(),
    }
