from flask import render_template, request
from flask_socketio import emit

from utils.app import get_state, get_control, get_latest_data
from utils.redis import (
    reset_all, reset_gyro_data, set_data_frequency, set_clock_skew,
    set_outage, reset_max_requests_per_second)
from utils.response import success

from wsgi import app


@app.route("/")
def hello():
    state = get_state()
    return render_template('index.html', state=state)


@app.route("/api/reset")
def api_reset_counter():
    reset_all()
    state = get_state()
    return success(state)


@app.route("/api/reset/max-requests")
def api_reset_max_requests():
    reset_max_requests_per_second()
    state = get_state()
    return success(state)


@app.route("/api/state")
def api_state():
    state = get_state()
    return success(state)


@app.route("/api/gyro/data/latest")
def api_gyro_data_latest():
    latest_data = get_latest_data()
    return success(latest_data)


@app.route("/api/gyro/data/reset")
def api_gyro_data_reset():
    reset_gyro_data()
    return success(None)


@app.route("/api/set-data-frequency")
def api_set_data_frequency():
    frequency = request.args.get('frequency', 1)

    set_data_frequency(frequency)

    control = get_control()
    emit('control', control, namespace='/app', broadcast=True)

    return success(get_state())


@app.route("/api/set-clock-skew")
def api_set_clock_skew():
    skew = request.args.get('skew', 1)
    print(skew)

    set_clock_skew(skew)

    control = get_control()
    emit('control', control, namespace='/app', broadcast=True)

    return success(get_state())


@app.route("/api/outage/create")
def api_outage_create():
    set_outage(True)

    control = get_control()
    emit('control', control, namespace='/app', broadcast=True)

    return success(get_state())


@app.route("/api/outage/fix")
def api_outage_fix():
    set_outage(False)

    control = get_control()
    emit('control', control, namespace='/app', broadcast=True)

    return success(get_state())
