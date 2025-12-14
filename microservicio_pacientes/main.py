# Archivo: microservicio_pacientes/main.py
from flask import Flask
from flask_cors import CORS 
from controllers.paciente_controller import controller

app = Flask(__name__)
CORS(app) 

app.register_blueprint(controller)

if __name__ == '__main__':
    # Puerto 5003 según docker-compose
    app.run(host='0.0.0.0', port=5003)