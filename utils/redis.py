import os
import pickle
import time


from redis import StrictRedis
from redis.exceptions import TimeoutError

CONNECTION_COUNT = 0
CONNECTION_COUNT_KEY = 'connections.count'
REQUESTS_PER_SECOND_KEY = 'requests.per.second.{}'
MAX_REQUESTS_PER_SECOND_KEY = 'requests.per.second.max'
GYRO_DATA_ALL_KEY = 'gyro.data.{}.all'
GYRO_DATA_LATEST_KEY = 'gyro.data.{}.latest'
APP_DATA_FREQUENCY_KEY = 'app.data.frequency'

__REDIS = None

DEFAULT_APP_DATA_FREQUENCY = 1


def __get_redis_master_host():
    if os.environ.get('GET_HOSTS_FROM') == 'env':
        return os.environ['REDIS_MASTER_SERVICE_HOST']

    return 'redis-master'


def __get_redis_conn():
    global __REDIS
    if not __REDIS:
        host = __get_redis_master_host()
        __REDIS = StrictRedis(host, socket_timeout=5)

    return __REDIS


def __is_redis_available():
    try:
        redis_conn = __get_redis_conn()
        redis_conn.ping()
    except TimeoutError:
        return False
    else:
        return True


def get_connection_count():
    redis_conn = __get_redis_conn()
    connections = redis_conn.get(CONNECTION_COUNT_KEY)
    connections = int(connections) if connections else 0
    return connections


def __reset_connection_count():
    redis_conn = __get_redis_conn()
    redis_conn.set(CONNECTION_COUNT_KEY, 0)


def increment_connection_count():
    print('incrementing')
    redis_conn = __get_redis_conn()
    redis_conn.incr(CONNECTION_COUNT_KEY, 1)


def decrement_connection_count():
    print('decrementing')
    redis_conn = __get_redis_conn()
    redis_conn.decr(CONNECTION_COUNT_KEY, 1)


def __get_requests_per_second_key(ts=None):
    if ts is None:
        return REQUESTS_PER_SECOND_KEY.format(int(time.time()))
    else:
        return REQUESTS_PER_SECOND_KEY.format(ts)


def __reset_requests_per_second():
    redis_conn = __get_redis_conn()
    key_wildcard = REQUESTS_PER_SECOND_KEY.format('*')
    keys = redis_conn.keys(key_wildcard)
    if keys:
        redis_conn.delete(*keys)


def increment_requests_per_second():
    redis_conn = __get_redis_conn()
    key = __get_requests_per_second_key()
    current = redis_conn.incr(key, 1)

    max_requests = get_max_requests_per_second()
    if current > max_requests:
        redis_conn.set(MAX_REQUESTS_PER_SECOND_KEY, current)

    redis_conn.expire(key, 60)


def get_requests_per_second(ts=None):
    redis_conn = __get_redis_conn()
    key = __get_requests_per_second_key(ts)
    requests = redis_conn.get(key)
    requests = int(requests) if requests else 0
    return requests


def __reset_max_requests_per_second():
    redis_conn = __get_redis_conn()
    redis_conn.delete(MAX_REQUESTS_PER_SECOND_KEY)


def get_max_requests_per_second():
    redis_conn = __get_redis_conn()
    max_requests = redis_conn.get(MAX_REQUESTS_PER_SECOND_KEY)
    max_requests = int(max_requests) if max_requests else 0
    return max_requests


def __reset_gyro_data():
    redis_conn = __get_redis_conn()

    key_wildcard = GYRO_DATA_ALL_KEY.format('*')
    keys = redis_conn.keys(key_wildcard)
    if keys:
        redis_conn.delete(*keys)

    key_wildcard = GYRO_DATA_LATEST_KEY.format('*')
    keys = redis_conn.keys(key_wildcard)
    if keys:
        redis_conn.delete(*keys)


def set_gyro_data(client_id, gamma, beta):
    redis_conn = __get_redis_conn()

    all_key = GYRO_DATA_ALL_KEY.format(client_id)
    all_data = redis_conn.get(all_key)
    if all_data:
        all_data = pickle.loads(all_data)
        all_data.append((gamma, beta))
        print(all_data)
    else:
        all_data = [(gamma, beta)]
    redis_conn.set(all_key, pickle.dumps(all_data))
    redis_conn.expire(all_key, 60*5)

    latest_key = GYRO_DATA_LATEST_KEY.format(client_id)
    redis_conn.set(latest_key, pickle.dumps((gamma, beta)))
    redis_conn.expire(latest_key, 60*5)


def get_latest_gyro_data():
    latest_data = []

    redis_conn = __get_redis_conn()

    latest_key_wildcard = GYRO_DATA_LATEST_KEY.format('*')
    latest_keys = redis_conn.keys(latest_key_wildcard)

    if latest_keys:
        latest_data_raw = redis_conn.mget(latest_keys)

        if latest_data_raw:
            for raw_data in latest_data_raw:
                data = pickle.loads(raw_data)
                print(data)
                latest_data.append({
                    'gamma': data[0],
                    'beta': data[1],
                })

    print('xx', latest_data)
    return latest_data


def reset_all():
    __reset_connection_count()
    __reset_requests_per_second()
    __reset_max_requests_per_second()
    __reset_gyro_data()
    __reset_data_frequency()


def reset_gyro_data():
    __reset_gyro_data()


def __reset_data_frequency():
    redis_conn = __get_redis_conn()
    redis_conn.set(APP_DATA_FREQUENCY_KEY, DEFAULT_APP_DATA_FREQUENCY)


def set_data_frequency(frequency):
    redis_conn = __get_redis_conn()
    redis_conn.set(APP_DATA_FREQUENCY_KEY, frequency)


def get_data_frequency():
    redis_conn = __get_redis_conn()
    frequency = redis_conn.get(APP_DATA_FREQUENCY_KEY)

    if not frequency:
        frequency = DEFAULT_APP_DATA_FREQUENCY
    else:
        frequency = int(frequency)

    return frequency

