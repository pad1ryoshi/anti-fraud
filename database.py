# database.py (versão atualizada)

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
    endereco_registrado = Column(String) # Ex: "João Pessoa, PB"
    margem_consignavel = Column(Float)
    
    transacoes = relationship("HistoricoTransacao", back_populates="usuario")

class HistoricoTransacao(Base):
    __tablename__ = "historico_transacoes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    valor = Column(Float)
    data_hora = Column(DateTime)
    status = Column(String) # Ex: "Aprovado", "Recusado", "Análise"
    
    # --- CAMPOS DE METADADOS ATUALIZADOS ---
    ip = Column(String)
    geolocalizacao = Column(String) # Ex: "Campina Grande, PB"
    dispositivo_fingerprint = Column(String) # NOVO
    user_agent = Column(String) # NOVO (substituindo o antigo 'dispositivo')
    tempo_preenchimento_formulario_segundos = Column(Integer) # NOVO
    
    usuario = relationship("Usuario", back_populates="transacoes")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()