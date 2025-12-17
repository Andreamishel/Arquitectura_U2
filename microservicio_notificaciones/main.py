import sys
import os
import time

sys.path.append(os.getcwd())

from consumers.evento_consumer import iniciar_consumidor

if __name__ == '__main__':
    print(" Iniciando Microservicio de Notificaciones (Modo Worker)...", flush=True)
    try:
        # Esto bloquea el programa y se queda escuchando a RabbitMQ para siempre
        iniciar_consumidor()
    except KeyboardInterrupt:
        print(" Deteniendo servicio...", flush=True)
    except Exception as e:
        print(f" Error fatal: {e}", flush=True)