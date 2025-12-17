import pika
import json
import time
import sys
import os

# Ajuste técnico para importar módulos hermanos
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.models import ServicioNotificacion
from repositories.notificacion_repository import SQLiteNotificacionRepository

def iniciar_consumidor():
    print(" [*] Esperando al Broker...", flush=True)
    
    # Reintento de conexión
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('broker'))
            channel = connection.channel()
            channel.queue_declare(queue='cola_notificaciones', durable=True)
            break
        except Exception:
            print(" [!] Reintentando conexión al broker en 5s...", flush=True)
            time.sleep(5)

    print(" [*] Conectado. Escuchando eventos...", flush=True)

    # Inyección de dependencias (Capas inferiores)
    repo = SQLiteNotificacionRepository()
    servicio = ServicioNotificacion(repo)

    def callback(ch, method, properties, body):
        print(f" [x] Recibido: {body}", flush=True)
        try:
            data = json.loads(body)
            # Llamada al Dominio
            servicio.preparar_estrategia(data.get('tipo', 'EMAIL'))
            servicio.procesar_notificacion(data)
            print(" [x] Procesado correctamente", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f" [!] Error: {e}", flush=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='cola_notificaciones', on_message_callback=callback)
    channel.start_consuming()