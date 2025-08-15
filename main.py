# main.py (Versão Final Corrigida)

from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

# Importações dos outros arquivos
from database import get_db, Usuario, HistoricoTransacao
from fraud_detector import analyze_transaction

app = FastAPI(
    title="IFTech - API Antifraude",
    description="API para detecção de fraudes em crédito consignado usando IA.",
    version="3.0.1"
)

# --- Modelos de Dados (Pydantic) ---
class BancoDeposito(BaseModel):
    banco: str
    agencia: str
    conta: str

class LoanRequestFinal(BaseModel):
    cpf: str
    dispositivo_fingerprint: str
    valor_solicitado: float
    numero_parcelas: int
    banco_para_deposito: BancoDeposito
    alteracoes_recentes: List[str] = Field(..., example=["contato", "banco"])

# --- ROTA ÚNICA ---
@app.post("/api/check_fraud")
def check_fraud(request_data: LoanRequestFinal, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Desconhecido")
    
    user = db.query(Usuario).filter(Usuario.cpf == request_data.cpf).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    history = db.query(HistoricoTransacao).filter(HistoricoTransacao.usuario_id == user.id).order_by(HistoricoTransacao.data_hora.desc()).all()

    # --- CORREÇÃO DO ERRO "JSON Serializable" ---
    # Criamos o dicionário do histórico manualmente, evitando dados internos do SQLAlchemy.
    history_for_ia = [
        {
            "valor": h.valor,
            "data_hora": h.data_hora.isoformat(),
            "ip": h.ip,
            "geolocalizacao": h.geolocalizacao,
            "dispositivo_fingerprint": h.dispositivo_fingerprint,
            "foi_fraude": h.foi_fraude
        } for h in history
    ]

    current_transaction_data = {
        **request_data.model_dump(),
        "ip_origem": client_ip,
        "geolocalizacao_ip": "A ser inferida",
        "user_agent": user_agent,
        "tempo_preenchimento_formulario_segundos": 60,
        "data_hora": datetime.now().isoformat()
    }
    
    context = {
        "user_data": { "nome": user.nome, "endereco_registrado": user.endereco_registrado, "margem_consignavel": user.margem_consignavel },
        "transaction_history": history_for_ia, # Usando a lista limpa
        "current_transaction": current_transaction_data
    }

    analysis_result = analyze_transaction(context)
    is_fraudulent = analysis_result.get("is_fraudulent", False)

    nova_transacao = HistoricoTransacao(
        usuario_id=user.id,
        valor=request_data.valor_solicitado,
        data_hora=datetime.now(),
        status="BLOQUEADO_POR_FRAUDE" if is_fraudulent else "APROVADO_AUTOMATICAMENTE",
        ip=client_ip,
        geolocalizacao="A ser inferida",
        dispositivo_fingerprint=request_data.dispositivo_fingerprint,
        user_agent=user_agent,
        tempo_preenchimento_formulario_segundos=60,
        foi_fraude=is_fraudulent,
        justificativa_fraude=analysis_result.get("justification")
    )
    db.add(nova_transacao)
    db.commit()

    return analysis_result

@app.get("/")
def read_root():
    return {"message": "API Antifraude IFTech - Operacional"}
