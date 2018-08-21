from flask_socketio import emit

from utils.app import get_state, get_control, get_latest_data
from utils.redis import (
    increment_connection_count, decrement_connection_count, increment_requests_per_second,
    set_gyro_data)

from wsgi import socketio


@socketio.on('connect', namespace='/app')
def sockect_connect():
    increment_connection_count()
    increment_requests_per_second()

    state = get_state()
    emit('state', state, namespace='/presentation', broadcast=True)

    control = get_control()
    emit('control', control, namespace='/app', broadcast=True)


@socketio.on('disconnect', namespace='/app')
def socket_disconnect():
    decrement_connection_count()
    state = get_state()
    emit('state', state, namespace='/presentation', broadcast=True)


@socketio.on('gyroData', namespace='/app')
def socket_receive_gyro_data(json):
    increment_requests_per_second()
    set_gyro_data(json['clientId'], json['gamma'], json['beta'])

    latest_data = get_latest_data()
    emit('gyroData', latest_data, namespace='/presentation', broadcast=True)
