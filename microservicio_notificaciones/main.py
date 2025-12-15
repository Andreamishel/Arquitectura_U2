from flask import Flask
from flask_cors import CORS
from controllers.notificacion_controller import controller

app = Flask(__name__)
CORS(app)

app.register_blueprint(controller)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)