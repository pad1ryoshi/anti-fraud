# fraud_detector.py (versão atualizada)

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import openai

load_dotenv()

# --- Configuração do Provedor de IA ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# --- Prompt Principal (Reutilizável para ambos os modelos) ---
def get_prompt(context: dict):
    fraud_types = [
        "SEM_RISCO", "RISCO_GEOGRAFICO", "DISPOSITIVO_SUSPEITO", "HORARIO_ATIPICO", 
        "COMPORTAMENTO_AUTOMATIZADO", "ALTERACAO_CADASTRAL_SUSPEITA", 
        "RISCO_COMBINADO", "ERRO_ANALISE"
    ]
    
    return f"""
    **Você é um especialista em detecção de fraudes de crédito consignado.** Sua resposta DEVE SER apenas um objeto JSON, sem nenhum texto ou formatação adicional.

    **Missão:** Analise a transação atual (`current_transaction`) com base nos dados do usuário e seu histórico. Retorne um JSON com os seguintes campos: `is_fraudulent` (boolean), `fraud_score` (0-100), `fraud_type_code` (um dos tipos da lista), `justification` (explicação detalhada) e `recommended_action` ("APROVACAO_AUTOMATICA", "REQUER_AUTENTICACAO_ADICIONAL", "BLOQUEIO_AUTOMATICO_E_REVISAO_MANUAL").

    **Principais Indicadores de Fraude:**
    - **Geolocalização:** Inconsistência grave entre o IP atual e o endereço/histórico do usuário.
    - **Dispositivo:** Uso de um `dispositivo_fingerprint` completamente novo.
    - **Velocidade:** `tempo_preenchimento_formulario_segundos` muito baixo (< 20s) sugere automação.
    - **Alteração Cadastral:** `houve_alteracao_cadastral_recente` sendo `true` é um grande alerta.
    - **Hora:** Solicitações de madrugada são suspeitas.
    - **Combinação:** Múltiplos indicadores aumentam o score exponencialmente.

    **Tipos de Fraude Disponíveis:** {', '.join(fraud_types)}

    **DADOS PARA ANÁLISE:**
    {json.dumps(context, indent=2, ensure_ascii=False)}

    **Sua Resposta (APENAS O JSON):**
    """

# --- Funções Específicas de cada Provedor ---
def _analyze_with_gemini(prompt: str) -> dict:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned_response)

def _analyze_with_openai(prompt: str) -> dict:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- Função Principal (Interface Pública do Módulo) ---
def analyze_transaction(context: dict) -> dict:
    """
    Analisa uma transação usando o provedor de LLM configurado no .env
    """
    prompt = get_prompt(context)
    
    try:
        print(f"--- Usando provedor: {LLM_PROVIDER} ---")
        if LLM_PROVIDER == "openai":
            return _analyze_with_openai(prompt)
        # O padrão é Gemini
        return _analyze_with_gemini(prompt)
        
    except Exception as e:
        print(f"ERRO CRÍTICO na análise da IA: {e}")
        return {
            "is_fraudulent": True,
            "fraud_score": 100,
            "fraud_type_code": "ERRO_ANALISE",
            "justification": f"Ocorreu um erro interno no sistema de IA. A transação deve ser bloqueada e revisada manualmente. Detalhe técnico: {str(e)}",
            "recommended_action": "BLOQUEIO_AUTOMATICO_E_REVISAO_MANUAL"
        }