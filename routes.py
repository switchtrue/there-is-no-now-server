from flask import render_template, request
from flask_socketio import emit

from utils.app import get_state
from utils.redis import reset_all, reset_gyro_data, get_latest_gyro_data, set_data_frequency
from utils.response import success

from wsgi import app, socketio


@app.route("/")
def hello():
    state = get_state()
    return render_template('index.html', connection_count=state['connectionCount'])


@app.route("/api/reset")
def api_reset_counter():
    reset_all()
    state = get_state()
    return success(state)


@app.route("/api/state")
def api_state():
    state = get_state()
    return success(state)


@app.route("/api/gyro/data/latest")
def api_gyro_data_latest():
    latest_data = get_latest_gyro_data()
    print('yy', latest_data)

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

    data = {
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
    }
    return success(data)


@app.route("/api/gyro/data/reset")
def api_gyro_data_reset():
    reset_gyro_data()
    return success(None)


@app.route("/api/set-data-frequency")
def api_gyro_set_frequency():
    frequency = request.args.get('frequency', 1)

    set_data_frequency(frequency)

    data = {
        'dataFrequency': frequency,
    }
    emit('control', data, namespace='/app', broadcast=True)

    return success(get_state())

