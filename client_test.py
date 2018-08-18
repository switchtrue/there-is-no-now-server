import random
import time
import uuid

from socketIO_client import SocketIO, BaseNamespace


class AppNamespace(BaseNamespace):
    pass


socketIO = SocketIO('localhost', 5000)
app_namespace = socketIO.define(AppNamespace, '/app')

client_id = str(uuid.uuid4())

while True:
    data = {
        'clientId': client_id,
        'gamma': random.randint(-90, 90),
        'beta': random.randint(-90, 90),
    }
    app_namespace.emit('gyroData', data)
    time.sleep(1)
