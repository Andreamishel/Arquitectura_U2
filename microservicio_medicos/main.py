from flask import Flask
from flask_cors import CORS 
from controllers.medico_controller import controller

app = Flask(__name__)
CORS(app)  

app.register_blueprint(controller)

if __name__ == '__main__':
    # Puerto 5002 según tu configuración de Docker
    app.run(host='0.0.0.0', port=5002)