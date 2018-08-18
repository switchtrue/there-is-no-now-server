from flask import jsonify


def success(data):
    return jsonify({
        'data': data,
        'status': 'success'
    })


def error(data, status_code=500):
    return jsonify({
        'data': data,
        'status': 'error'
    }), status_code
