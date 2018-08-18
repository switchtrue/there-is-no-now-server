from flask_socketio import emit, send

from utils.app import get_state
from utils.redis import (
    increment_connection_count, decrement_connection_count, increment_requests_per_second,
    set_gyro_data, get_data_frequency)

from wsgi import socketio


@socketio.on('connect', namespace='/app')
def sockect_connect():
    print('connection')
    increment_connection_count()
    increment_requests_per_second()
    state = get_state()
    emit('state', state, namespace='/presentation', broadcast=True)
    data = {
        'dataFrequency': get_data_frequency(),
    }
    emit('control', data, namespace='/app', broadcast=True)


@socketio.on('disconnect', namespace='/app')
def socket_disconnect():
    print('disconnection')
    decrement_connection_count()
    state = get_state()
    emit('state', state, namespace='/presentation', broadcast=True)


@socketio.on('gyroData', namespace='/app')
def socket_receive_gyro_data(json):
    increment_requests_per_second()
    set_gyro_data(json['clientId'], json['gamma'], json['beta'])
    print(json)
