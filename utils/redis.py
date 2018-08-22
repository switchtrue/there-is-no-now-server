import os
import pickle
import time

from collections import defaultdict

from redis import StrictRedis
from redis.exceptions import TimeoutError

CONNECTION_COUNT = 0
CONNECTION_COUNT_KEY = 'connections.count'
REQUESTS_PER_SECOND_KEY = 'requests.per.second.{}'
MAX_REQUESTS_PER_SECOND_KEY = 'requests.per.second.max'
GYRO_DATA_ALL_KEY = 'gyro.data.{}.all'
GYRO_DATA_LATEST_KEY = 'gyro.data.{}.latest'
GYRO_DATA_5SEC_KEY = 'gyro.data.{}.5sec.{}'
APP_DATA_FREQUENCY_KEY = 'app.data.frequency'
APP_CLOCK_SKEW_KEY = 'app.clock.skew'
SIMULATED_OUTAGE_KEY = 'server.outage'
OUTAGE_STRATEGY_KEY = 'server.outage.strategy'

__REDIS = None

DEFAULT_APP_DATA_FREQUENCY = 1
DEFAULT_APP_CLOCK_SKEW = 0


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
    redis_conn = __get_redis_conn()
    redis_conn.incr(CONNECTION_COUNT_KEY, 1)


def decrement_connection_count():
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


def reset_max_requests_per_second():
    __reset_max_requests_per_second()


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

    key_wildcard = GYRO_DATA_5SEC_KEY.format('*', '*')
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
    else:
        all_data = [(gamma, beta)]
    redis_conn.set(all_key, pickle.dumps(all_data))
    redis_conn.expire(all_key, 60*5)

    latest_key = GYRO_DATA_LATEST_KEY.format(client_id)
    redis_conn.set(latest_key, pickle.dumps((gamma, beta)))
    redis_conn.expire(latest_key, 60*5)

    now = int(time.time())
    offset = (now % 5)
    fivesec_block = now - offset
    fivesec_key = GYRO_DATA_5SEC_KEY.format(client_id, fivesec_block)
    redis_conn.set(fivesec_key, pickle.dumps({'ts': fivesec_block, 'data': (gamma, beta)}))
    redis_conn.expire(fivesec_key, 60 * 5)
    print({'client_id': client_id, 'ts': fivesec_block, 'data': (gamma, beta)})


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
                latest_data.append({
                    'gamma': data[0],
                    'beta': data[1],
                })

    return latest_data


def get_5sec_data():
    fivesec_data = {}

    redis_conn = __get_redis_conn()

    fivesec_key_wildcard = GYRO_DATA_5SEC_KEY.format('*', '*')
    fivesec_keys = redis_conn.keys(fivesec_key_wildcard)

    if fivesec_keys:
        fivesec_data_raw = redis_conn.mget(fivesec_keys)

        if fivesec_data_raw:
            for raw_data in fivesec_data_raw:
                data = pickle.loads(raw_data)
                ts = data['ts']
                if ts not in fivesec_data.keys():
                    fivesec_data[ts] = {'gamma': 0, 'beta': 0}
                fivesec_data[ts] = {
                    'gamma': fivesec_data[ts]['gamma'] + data['data'][0],
                    'beta': fivesec_data[ts]['beta'] + data['data'][1],
                }

                # print(ts, fivesec_data[ts])

    # print(fivesec_data[1534853165])
    return fivesec_data


def reset_all():
    __reset_connection_count()
    __reset_requests_per_second()
    __reset_max_requests_per_second()
    __reset_gyro_data()
    __reset_data_frequency()
    __reset_clock_skew()
    __reset_outage()
    __reset_outage_strategy()


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
        frequency = float(frequency)

    return frequency


def __reset_clock_skew():
    redis_conn = __get_redis_conn()
    redis_conn.set(APP_CLOCK_SKEW_KEY, DEFAULT_APP_CLOCK_SKEW)


def set_clock_skew(skew):
    redis_conn = __get_redis_conn()
    redis_conn.set(APP_CLOCK_SKEW_KEY, skew)


def get_clock_skew():
    redis_conn = __get_redis_conn()
    skew = redis_conn.get(APP_CLOCK_SKEW_KEY)

    if not skew:
        skew = DEFAULT_APP_CLOCK_SKEW
    else:
        skew = int(skew)

    return skew


def __reset_outage():
    redis_conn = __get_redis_conn()
    redis_conn.set(SIMULATED_OUTAGE_KEY, 0)


def set_outage(outage_state):
    redis_conn = __get_redis_conn()
    if outage_state:
        redis_conn.set(SIMULATED_OUTAGE_KEY, 1)
    else:
        redis_conn.set(SIMULATED_OUTAGE_KEY, 0)


def get_outage():
    redis_conn = __get_redis_conn()
    outage_state = redis_conn.get(SIMULATED_OUTAGE_KEY)

    if outage_state and int(outage_state) == 1:
        return True
    else:
        return False


def __reset_outage_strategy():
    redis_conn = __get_redis_conn()
    redis_conn.set(OUTAGE_STRATEGY_KEY, 0)


def set_outage_strategy(outage_strategy):
    redis_conn = __get_redis_conn()
    if outage_strategy == 'exponential-backoff':
        redis_conn.set(OUTAGE_STRATEGY_KEY, 1)
    else:
        redis_conn.set(OUTAGE_STRATEGY_KEY, 0)


def get_outage_strategy():
    redis_conn = __get_redis_conn()
    outage_strategy = redis_conn.get(OUTAGE_STRATEGY_KEY)

    if outage_strategy and int(outage_strategy) == 1:
        return 'exponential-backoff'
    else:
        return 'immediate'
