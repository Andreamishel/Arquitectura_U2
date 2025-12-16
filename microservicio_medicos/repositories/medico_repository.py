import sqlite3
import uuid
from datetime import datetime
from domain.models import Medico, HorarioConfiguracion, SlotAgenda, DiaSemana, EstadoSlot

class SQLiteMedicoRepository:
    def __init__(self, db_path="medicos.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Tablas
            cursor.execute('''CREATE TABLE IF NOT EXISTS medicos (
                id TEXT PRIMARY KEY, especialidadId TEXT, nombre TEXT, apellido TEXT, especialidad TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS horarios (
                id TEXT PRIMARY KEY, medicoId TEXT, dia TEXT, horaInicio TEXT, horaFin TEXT, duracion INTEGER)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS slots (
                id TEXT PRIMARY KEY, horarioId TEXT, horaInicio TEXT, horaFin TEXT, estado TEXT)''')
            conn.commit()

    def save(self, medico: Medico):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO medicos VALUES (?,?,?,?,?)', 
                (str(medico.id), str(medico.especialidadId), medico.nombre, medico.apellido, medico.especialidad))
            conn.commit()
        return medico

    def save_horario_completo(self, horario: HorarioConfiguracion):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. Guardar Config
            cursor.execute('INSERT INTO horarios VALUES (?,?,?,?,?,?)',
                (str(horario.id), str(horario.medicoId), horario.dia.value, 
                 horario.horaInicio.strftime("%H:%M"), horario.horaFin.strftime("%H:%M"), horario.duracionCita))
            # 2. Guardar Slots
            for slot in horario.slots:
                cursor.execute('INSERT INTO slots VALUES (?,?,?,?,?)',
                    (str(slot.id), str(horario.id), 
                     slot.horaInicio.strftime("%H:%M"), slot.horaFin.strftime("%H:%M"), slot.estado.value))
            conn.commit()

    def find_by_id(self, medico_id: str) -> Medico:
        """RECUPERACIÓN COMPLETA: Médico -> Horarios -> Slots"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # A. Médico
            cursor.execute('SELECT * FROM medicos WHERE id = ?', (medico_id,))
            row = cursor.fetchone()
            if not row: return None
            
            medico = Medico(row[2], row[3], row[4])
            medico.id = uuid.UUID(row[0])
            medico.especialidadId = uuid.UUID(row[1])
            
            # B. Horarios
            cursor.execute('SELECT * FROM horarios WHERE medicoId = ?', (medico_id,))
            rows_horarios = cursor.fetchall()
            
            for rh in rows_horarios:
                dia_enum = DiaSemana(rh[2])
                h_inicio = datetime.strptime(rh[3], "%H:%M").time()
                h_fin = datetime.strptime(rh[4], "%H:%M").time()
                duracion = rh[5]
                
                horario = HorarioConfiguracion(medico.id, dia_enum, h_inicio, h_fin, duracion)
                horario.id = uuid.UUID(rh[0])
                
                # C. Slots
                cursor.execute('SELECT * FROM slots WHERE horarioId = ?', (str(horario.id),))
                rows_slots = cursor.fetchall()
                for rs in rows_slots:
                    s_inicio = datetime.strptime(rs[2], "%H:%M").time()
                    s_fin = datetime.strptime(rs[3], "%H:%M").time()
                    estado_enum = EstadoSlot(rs[4])
                    
                    slot = SlotAgenda(horario.id, s_inicio, s_fin)
                    slot.id = uuid.UUID(rs[0])
                    slot.estado = estado_enum
                    horario.slots.append(slot)
                
                medico.horarios.append(horario)
                
            return medico
    
    def reservar_slot(self, slot_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. Validar que el slot exista y esté DISPONIBLE
            cursor.execute('SELECT estado FROM slots WHERE id = ?', (slot_id,))
            row = cursor.fetchone()
            
            if not row or row[0] != 'DISPONIBLE':
                return False
            
            # 2. Actualizar estado a RESERVADO
            cursor.execute('UPDATE slots SET estado = ? WHERE id = ?', ('RESERVADO', slot_id))
            conn.commit()
            return cursor.rowcount > 0
        
    # --- LISTAR TODOS ---
    def find_all(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM medicos')
            rows = cursor.fetchall()
            return self._map_rows_to_medicos(cursor, rows) # Usamos helper para no repetir código

    # --- BUSCAR POR NOMBRE O APELLIDO ---
    def search(self, query):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            param = f"%{query}%"
            cursor.execute('''
                SELECT * FROM medicos 
                WHERE nombre LIKE ? OR apellido LIKE ? OR especialidad LIKE ?
            ''', (param, param, param))
            rows = cursor.fetchall()
            return self._map_rows_to_medicos(cursor, rows)

    # Helper interno para no repetir la lógica de reconstrucción de objetos
    def _map_rows_to_medicos(self, cursor, rows):
        medicos = []
        for row in rows:
            # row: 0:id, 1:espId, 2:nombre, 3:apellido, 4:especialidad
            m = Medico(row[2], row[3], row[4])
            m.id = uuid.UUID(row[0])
            m.especialidadId = uuid.UUID(row[1])
            medicos.append(m)
        return medicos