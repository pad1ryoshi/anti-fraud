# database.py (VERSÃO FINAL E CORRETA)

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./hackathon.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    telefone = Column(String)
    endereco_registrado = Column(String)
    margem_consignavel = Column(Float)
    
    transacoes = relationship("HistoricoTransacao", back_populates="usuario")

class HistoricoTransacao(Base):
    __tablename__ = "historico_transacoes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    valor = Column(Float)
    data_hora = Column(DateTime)
    status = Column(String)
    ip = Column(String)
    geolocalizacao = Column(String)
    
    # --- COLUNAS QUE ESTAVAM FALTANDO NA SUA DEFINIÇÃO ---
    dispositivo_fingerprint = Column(String)
    user_agent = Column(String)
    tempo_preenchimento_formulario_segundos = Column(Integer)
    foi_fraude = Column(Boolean, default=False)
    justificativa_fraude = Column(String, nullable=True)
    
    usuario = relationship("Usuario", back_populates="transacoes")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
