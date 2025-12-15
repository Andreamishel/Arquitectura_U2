import sqlite3
from domain.models import Cita, PacienteRef, MedicoRef, EstadoCita

class SQLiteCitaRepository:
    def __init__(self, db_path="citas.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS citas (
                    id TEXT PRIMARY KEY,
                    fecha_hora TEXT,
                    motivo TEXT,
                    estado TEXT,
                    paciente_id TEXT,
                    paciente_nombre TEXT,
                    paciente_email TEXT,
                    paciente_tel TEXT,
                    medico_id TEXT,
                    medico_nombre TEXT,
                    medico_especialidad TEXT
                )
            ''')
            conn.commit()

    def save(self, cita: Cita):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO citas VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                str(cita.id), cita.fechaHora, cita.motivo, cita.estado.value,
                str(cita.paciente.id), cita.paciente.nombre, cita.paciente.email, cita.paciente.telefono,
                str(cita.medico.id), cita.medico.nombre, cita.medico.especialidad
            ))
            conn.commit()
        return cita

    def find_by_id(self, cita_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM citas WHERE id = ?', (cita_id,))
            row = cursor.fetchone()
            if not row: return None

            # Reconstrucción (Mapping)
            # Row index: 0:id, 1:fecha, 2:motivo, 3:estado, 
            # 4:p_id, 5:p_nom, 6:p_mail, 7:p_tel
            # 8:m_id, 9:m_nom, 10:m_esp
            
            p_ref = PacienteRef(row[4], row[5], row[6], row[7])
            m_ref = MedicoRef(row[8], row[9], row[10])
            
            cita = Cita(row[1], row[2], p_ref, m_ref)
            cita.id = row[0] # UUID original
            cita.estado = EstadoCita(row[3])
            
            return cita

    def update(self, cita: Cita):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE citas SET fecha_hora = ?, estado = ?, motivo = ? WHERE id = ?
            ''', (cita.fechaHora, cita.estado.value, cita.motivo, str(cita.id)))
            conn.commit()