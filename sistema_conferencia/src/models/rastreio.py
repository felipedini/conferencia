from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class RastreioEsperado(db.Model):
    __tablename__ = 'rastreios_esperados'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_rastreio = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(db.String(50), default='pendente')
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_rastreio': self.codigo_rastreio,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }

class MercadoriaConferida(db.Model):
    __tablename__ = 'mercadorias_conferidas'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_rastreio = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    transportadora = db.Column(db.String(50), nullable=True)
    data_bipagem = db.Column(db.Date, default=datetime.now().date)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_rastreio': self.codigo_rastreio,
            'timestamp': self.timestamp.isoformat(),
            'transportadora': self.transportadora,
            'data_bipagem': self.data_bipagem.isoformat() if self.data_bipagem else None
        }

class DashboardCache(db.Model):
    __tablename__ = 'dashboard_cache'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.Date, nullable=False, unique=True)
    transportadoras = db.Column(db.JSON, nullable=False)  # Armazena contadores por transportadora
    total_hoje = db.Column(db.Integer, default=0)
    coleta_hoje = db.Column(db.Integer, default=0)
    insucesso_hoje = db.Column(db.Integer, default=0)
    sem_status_hoje = db.Column(db.Integer, default=0)
    rastreios_contados = db.Column(db.Text, default='[]')  # Lista de rastreios já contados no dashboard (JSON como texto)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat(),
            'transportadoras': self.transportadoras,
            'total_hoje': self.total_hoje,
            'coleta_hoje': self.coleta_hoje,
            'insucesso_hoje': self.insucesso_hoje,
            'sem_status_hoje': self.sem_status_hoje,
            'rastreios_contados': self.rastreios_contados or '[]',
            'ultima_atualizacao': self.ultima_atualizacao.isoformat()
        }

