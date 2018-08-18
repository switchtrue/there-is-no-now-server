import eventlet
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sslify import SSLify

eventlet.monkey_patch()

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
SSLify(app)
socketio = SocketIO(app)

from routes import *
from routes_sockets import *

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
