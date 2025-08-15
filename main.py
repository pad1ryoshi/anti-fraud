# main.py (versão corrigida)

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

# --- CORREÇÃO NA IMPORTAÇÃO ---
# Removemos o "import models" e importamos diretamente de "database"
from database import get_db, Usuario, HistoricoTransacao
from fraud_detector import analyze_transaction

app = FastAPI(
    title="IA contra Fraude - Hackathon API v2",
    description="API com suporte a múltiplos LLMs para detectar fraudes em crédito consignado.",
    version="2.0.0"
)

# --- Pydantic Models (sem alterações) ---
class Endereco(BaseModel):
    cep: str
    logradouro: str
    numero: str
    cidade: str
    estado: str

class BancoDeposito(BaseModel):
    banco: str
    agencia: str
    conta: str

class LoanRequest(BaseModel):
    cpf: str = Field(..., example="222.222.222-22")
    houve_alteracao_cadastral_recente: bool = Field(..., example=True)
    valor_solicitado: float = Field(..., example=2500.00)
    numero_parcelas: int = Field(..., example=72)
    banco_para_deposito: BancoDeposito
    ip_origem: str = Field(..., example="200.220.10.5")
    geolocalizacao_ip: str = Field(..., example="Rio de Janeiro, RJ")
    dispositivo_fingerprint: str = Field(..., example="a7b1c9d8e2f3a4b5c6d7e8f901a2b3c4")
    user_agent: str = Field(..., example="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
    tempo_preenchimento_formulario_segundos: int = Field(..., example=15)

class FraudAnalysisResponse(BaseModel):
    is_fraudulent: bool
    fraud_score: int
    fraud_type_code: str
    justification: str
    recommended_action: str

# --- Endpoint da API (com correção nas queries) ---
@app.post("/check-fraud", response_model=FraudAnalysisResponse)
def check_fraud(request: LoanRequest, db: Session = Depends(get_db)):
    # --- CORREÇÃO NA QUERY: removemos o prefixo "models." ---
    user = db.query(Usuario).filter(Usuario.cpf == request.cpf).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # --- CORREÇÃO NA QUERY: removemos o prefixo "models." ---
    history = db.query(HistoricoTransacao).filter(HistoricoTransacao.usuario_id == user.id).all()
    
    context_data = {
        "user_data": {
            "nome": user.nome,
            "endereco_registrado": user.endereco_registrado,
            "margem_consignavel": user.margem_consignavel
        },
        "transaction_history": [
            {
                "valor": h.valor, 
                "data_hora": h.data_hora.isoformat(), 
                "ip": h.ip, 
                "geolocalizacao": h.geolocalizacao,
                "dispositivo_fingerprint": h.dispositivo_fingerprint,
                "user_agent": h.user_agent,
                "tempo_preenchimento_formulario_segundos": h.tempo_preenchimento_formulario_segundos
            } for h in history
        ],
        "current_transaction": {
            **request.model_dump(),
            "data_hora": datetime.now().isoformat()
        }
    }

    analysis_result = analyze_transaction(context_data)
    return analysis_result

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Detecção de Fraude v2!"}