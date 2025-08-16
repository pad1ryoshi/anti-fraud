# main.py (versão corrigida)

from fastapi import FastAPI, Depends, HTTPException
import os
import time
import requests
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# --- CORREÇÃO NA IMPORTAÇÃO ---
# Removemos o "import models" e importamos diretamente de "database"
from database import get_db, Usuario, HistoricoTransacao
from fraud_detector import analyze_transaction

load_dotenv()

# --- Constantes do Supabase --- (Env bugou e não tá achando as variáveis)
SUPABASE_URL = "https://njwkdldbxyrevhyhdztv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qd2tkbGRieHlyZXZoeWhkenR2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUyOTc5NzIsImV4cCI6MjA3MDg3Mzk3Mn0.vtzEZsCyLyyW0d5KlzmAZP-u11eqjCI6bI-F6aynMh8"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qd2tkbGRieHlyZXZoeWhkenR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTI5Nzk3MiwiZXhwIjoyMDcwODczOTcyfQ.v3953ah77OiEiefZ_fVzeY9aCToY4pfU5CPBvD6c0Qc"

def incrementar_contador_fraude(id_cliente=None):
    """
    Incrementa o contador de fraudes na tabela 'test' do Supabase.
    Este contador é armazenado na coluna 'historicoFraude' para um cliente específico.
    
    Args:
        id_cliente: Identificador do cliente para filtrar qual linha atualizar.
                    Se None, incrementa o primeiro registro encontrado.
    
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        # Headers padrão para as chamadas à API
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # 1. Busca o registro específico do cliente (ou o primeiro se id_cliente=None)
        query_url = f"{SUPABASE_URL}/rest/v1/dados_cliente_hackaton"
        if id_cliente:
            # Se temos ID do cliente, filtra pelo idCliente específico
            query_url += f"?id_cliente=eq.{id_cliente}&select=historicoFraude,id_cliente"
            print(f"Buscando registro para o cliente: {id_cliente}")
        else:
            # Se não temos ID do cliente, pega o primeiro registro
            query_url += f"?select=historicoFraude,id_cliente"
            print("ID do cliente não fornecido, usando primeiro registro encontrado.")
            
        response = requests.get(query_url, headers=headers)
        
        if not response.ok:
            print(f"ERRO ao buscar registro: {response.text}")
            return False
        
        data = response.json()
        print(f"Dados recebidos: {data}")
        
        # 2. Se não encontrou registro para esse cliente, cria um novo
        if not data or len(data) == 0:
            if not id_cliente:
                print("Nenhum registro encontrado e ID do cliente não fornecido.")
                return False
            
            print(f"Nenhum registro encontrado para cliente {id_cliente}. Criando novo.")
            new_response = requests.post(
                f"{SUPABASE_URL}/rest/v1/dados_cliente_hackaton",
                headers=headers,
                json={
                    "historicoFraude": "1",
                    "id_cliente": id_cliente
                }
            )
            
            if not new_response.ok:
                print(f"ERRO ao criar registro: {new_response.text}")
                return False
                
            print(f"Novo registro criado para cliente {id_cliente} com historicoFraude=1")
            return True
        
        # 3. Obtemos o valor atual do registro do cliente
        # (como id_cliente é chave única, deve haver apenas um registro)
        
        # Inicializa com 0 e pega o ID do cliente
        valor_atual = 0
        id_cliente_encontrado = id_cliente
        registro_encontrado = False
        
        # Verificamos se encontrou algum registro
        if data and len(data) > 0:
            # Pega o valor atual do registro
            registro = data[0]
            valor_atual = registro.get("historicoFraude")
            id_registro = registro.get("id_cliente")
            
            if id_registro:
                id_cliente_encontrado = id_registro
                registro_encontrado = True
            
            # Converte para inteiro se for string ou 0 se for nulo
            if valor_atual is None:
                valor_atual = 0
            elif isinstance(valor_atual, str):
                valor_atual = int(valor_atual)
        
        # Incrementa o valor atual
        novo_valor = valor_atual + 1
        print(f"Incrementando historicoFraude para cliente {id_cliente_encontrado}: {valor_atual} → {novo_valor}")
        
        # Headers para as operações
        headers_api = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Dados para o registro
        novo_registro = {
            "historicoFraude": str(novo_valor),
            "id_cliente": id_cliente_encontrado
        }
        
        if registro_encontrado:
            # 4. Se o registro já existe, atualizamos com PATCH
            print(f"Atualizando registro existente: historicoFraude={novo_valor}")
            update_url = f"{SUPABASE_URL}/rest/v1/dados_cliente_hackaton?id_cliente=eq.{id_cliente_encontrado}"
            
            response = requests.patch(
                update_url,
                headers=headers_api,
                json={"historicoFraude": str(novo_valor)}
            )
        else:
            # 5. Se não existe registro, criamos um novo com POST
            print(f"Criando novo registro: historicoFraude={novo_valor}")
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/dados_cliente_hackaton",
                headers=headers_api,
                json=novo_registro
            )
        
        if not response.ok:
            print(f"ERRO na operação: Status {response.status_code}, {response.text}")
            return False
        
        print(f"Contador de fraudes incrementado com sucesso para {novo_valor} (Cliente: {id_cliente_encontrado})")
        return True
    
    except Exception as e:
        print(f"ERRO ao incrementar contador de fraudes: {str(e)}")
        return False

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

    # Analisa a transação em busca de fraude
    analysis_result = analyze_transaction(context_data)
    
    # Se for detectada fraude, incrementa o contador no Supabase
    if analysis_result["is_fraudulent"]:
        try:
            # Extrai o CPF para usar como identificador do cliente
            cpf = request.cpf
            # Usa o CPF como ID do cliente (mantendo formato texto com pontuação)
            id_cliente = cpf
            
            # Incrementa o contador de fraude no Supabase para este cliente específico
            incrementar_contador_fraude(id_cliente=id_cliente)
        except Exception as e:
            # Apenas loga o erro, não interrompe o fluxo da API
            print(f"ERRO ao atualizar contador no Supabase: {e}")
    
    return analysis_result

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Detecção de Fraude v2!"}

@app.post("/incrementar-contador")
def incrementar_contador(id_cliente: str = None):
    """
    Endpoint para incrementar manualmente o contador de fraudes.
    Útil para testar a integração com o Supabase.
    
    Args:
        id_cliente: ID opcional do cliente para incrementar o contador específico
    """
    resultado = incrementar_contador_fraude(id_cliente=id_cliente)
    if resultado:
        return {"mensagem": f"Contador incrementado com sucesso para cliente: {id_cliente if id_cliente else 'padrão'}"}
    else:
        raise HTTPException(status_code=500, detail=f"Falha ao incrementar contador para cliente: {id_cliente if id_cliente else 'padrão'}")
