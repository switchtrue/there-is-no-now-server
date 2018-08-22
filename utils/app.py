import time

from utils.redis import (
    get_connection_count, get_requests_per_second, get_max_requests_per_second, get_data_frequency,
    get_clock_skew, get_outage, get_latest_gyro_data, get_5sec_data, get_outage_strategy)


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
        'simulatedOutage': get_outage(),
        'outageStrategy': get_outage_strategy(),
    }


def get_requests():
    return {
        'requestsPerSecond': __avg_requests_per_second(),
        'maxRequestsPerSecond': get_max_requests_per_second(),
    }


def get_control():
    return {
        'dataFrequency': get_data_frequency(),
        'clockSkew': get_clock_skew(),
        'simulatedOutage': get_outage(),
        'outageStrategy': get_outage_strategy(),
    }


def get_latest_data():
    latest_data = get_latest_gyro_data()

    max_gamma, max_beta = 0, 0
    min_gamma, min_beta = 0, 0
    sum_gamma, sum_beta = 0, 0
    for data in latest_data:
        gamma = data['gamma']
        beta = data['beta']

        sum_gamma += gamma
        sum_beta += beta

        min_gamma = gamma if gamma < min_gamma else min_gamma
        min_beta = beta if beta < min_beta else min_beta

        max_gamma = gamma if gamma > max_gamma else max_gamma
        max_beta = beta if beta > max_beta else max_beta

    fs = get_5sec_data()
    # print(fs)

    return {
        'latest': get_latest_gyro_data(),
        'max': {
            'gamma': max_gamma,
            'beta': max_beta,
        },
        'min': {
            'gamma': min_gamma,
            'beta': min_beta,
        },
        'avg': {
            'gamma': sum_gamma / len(latest_data) if len(latest_data) > 0 else 0,
            'beta': sum_beta / len(latest_data) if len(latest_data) > 0 else 0,
        },
        'sum': {
            'gamma': sum_gamma,
            'beta': sum_beta,
        },
        'fivesec': fs,
        'fivesecDelayed': __delay_5sec(fs),
    }


def __delay_5sec(fivesec_data):
    delayed_5sec = {}
    for k, v in fivesec_data.items():
        try:
            delay = fivesec_data[k - 5]
            delayed_5sec[k] = delay
        except:
            pass

    return delayed_5sec
