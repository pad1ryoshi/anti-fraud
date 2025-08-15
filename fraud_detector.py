import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import openai
import time

load_dotenv()

# --- Configuração do Provedor de IA ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini") 

# --- A FUNÇÃO QUE FALTAVA ---
def get_prompt(context: dict) -> str:
    """
    Formata o contexto da transação em um prompt detalhado para a IA.
    Esta função é o "cérebro" que instrui a IA sobre o que fazer.
    """
    fraud_types = [
        "SEM_RISCO", "RISCO_GEOGRAFICO", "DISPOSITIVO_SUSPEITO", "HORARIO_ATIPICO", 
        "COMPORTAMENTO_AUTOMATIZADO", "ALTERACAO_CADASTRAL_SUSPEITA", 
        "MANIPULACAO_DE_MARGEM", "AVERBACAO_SUSPEITA", "LIQUIDACAO_INDEVIDA",
        "CREDENCIAIS_COMPROMETIDAS", "RISCO_COMBINADO", "ERRO_ANALISE"
    ]
    
    return f"""
    **Você é um especialista em detecção de fraudes de crédito consignado.** Sua resposta DEVE SER apenas um objeto JSON, sem nenhum texto ou formatação adicional.

    **Missão:** Analise a transação atual (`current_transaction`) com base nos dados do usuário e seu histórico. Retorne um JSON com os seguintes campos: `is_fraudulent` (boolean), `fraud_score` (0-100), `fraud_type_code` (um dos tipos da lista), `justification` (explicação detalhada) e `recommended_action` ("APROVACAO_AUTOMATICA", "REQUER_AUTENTICACAO_ADICIONAL", "BLOQUEIO_AUTOMATICO_E_REVISAO_MANUAL").

    **SISTEMA DE SCORING PARA DETECÇÃO DE FRAUDE:**

    Calcule o score total baseado nos seguintes indicadores. Cada indicador contribui pontos para o score final (0-100):

    1. **Geolocalização (até 25 pontos):**
       - IP em país diferente do endereço cadastrado: +25 pontos
       - IP em estado diferente do endereço cadastrado: +15 pontos
       - IP em cidade diferente do endereço cadastrado: +5 pontos
       - IP consistente com endereço cadastrado: +0 pontos
       - Bônus se NUNCA acessou desse local antes (verificar histórico): +10 pontos adicionais

    2. **Dispositivo (até 20 pontos):**
       - Dispositivo nunca usado antes (não aparece no histórico): +20 pontos
       - Dispositivo usado menos de 3 vezes: +10 pontos
       - Dispositivo conhecido e frequente: +0 pontos
       - Múltiplos dispositivos diferentes em curto período: +15 pontos adicionais

    3. **Comportamento de Preenchimento (até 15 pontos):**
       - Tempo < 10 segundos: +15 pontos (alta probabilidade de automação)
       - Tempo entre 10-20 segundos: +10 pontos
       - Tempo entre 20-60 segundos: +5 pontos
       - Tempo > 60 segundos: +0 pontos

    4. **Alterações Cadastrais (até 25 pontos):**
       - Alteração recente de dados bancários: +25 pontos
       - Alteração recente de endereço: +15 pontos
       - Alteração recente de contato: +10 pontos
       - Sem alterações recentes: +0 pontos
       - Bônus para alteração seguida de empréstimo imediato: +10 pontos adicionais

    5. **Horário (até 10 pontos):**
       - Entre 23h e 5h: +10 pontos
       - Entre 19h e 23h ou 5h e 8h: +5 pontos
       - Entre 8h e 19h: +0 pontos
       - Bônus se horário inconsistente com histórico: +5 pontos adicionais

    6. **Margem Consignável (até 15 pontos):**
       - Tentativa de usar 90-100% da margem: +15 pontos
       - Tentativa de usar 70-90% da margem: +10 pontos
       - Tentativa de usar 50-70% da margem: +5 pontos
       - Tentativa de usar <50% da margem: +0 pontos
       - Bônus se valor muito diferente do histórico: +10 pontos adicionais

    7. **Histórico de Transações (até 15 pontos):**
       - Padrão muito diferente do histórico: +15 pontos
       - Algumas inconsistências com histórico: +7 pontos
       - Consistente com histórico: +0 pontos

    **Regras de Decisão Baseadas no Score:**
    - Score 0-30: Baixo risco → APROVACAO_AUTOMATICA
    - Score 31-65: Risco médio → REQUER_AUTENTICACAO_ADICIONAL
    - Score 66-100: Alto risco → BLOQUEIO_AUTOMATICO_E_REVISAO_MANUAL

    **Avaliação Combinada:**
    - Se dois ou mais indicadores de alto risco estiverem presentes simultaneamente, adicione +20 pontos extras ao score total.
    - Caso o score ultrapasse 100, mantenha em 100.

    **Tipos de Fraude Disponíveis:** {', '.join(fraud_types)}

    **DADOS PARA ANÁLISE:**
    {json.dumps(context, indent=2, ensure_ascii=False)}

    **Sua Resposta (APENAS O JSON):**
    """

# --- Funções dos Provedores Reais ---
def _analyze_with_gemini(prompt: str) -> dict:
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"ERRO ao chamar a API do Gemini: {e}")
        raise e

def _analyze_with_openai(prompt: str) -> dict:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- Função Principal de Análise ---
def analyze_transaction(context: dict) -> dict:
    if LLM_PROVIDER == "mock":
        return _analyze_with_mock(context)

    try:
        prompt = get_prompt(context)
        if not prompt or not prompt.strip():
            raise ValueError("O prompt gerado está vazio. Verifique os dados de entrada.")
    except Exception as e:
        print(f"ERRO CRÍTICO ao gerar o prompt: {e}")
        return {
            "is_fraudulent": True, "fraud_score": 100, "fraud_type_code": "ERRO_GERACAO_PROMPT",
            "justification": f"Ocorreu um erro interno ao preparar os dados para a IA. Detalhe técnico: {str(e)}",
            "recommended_action": "BLOQUEIO_AUTOMATICO_E_REVISAO_MANUAL"
        }
    
    try:
        print(f"--- Usando provedor: {LLM_PROVIDER} ---")
        if LLM_PROVIDER == "openai":
            return _analyze_with_openai(prompt)
        return _analyze_with_gemini(prompt)
    except Exception as e:
        print(f"ERRO CRÍTICO na análise da IA: {e}")
        return {
            "is_fraudulent": True, "fraud_score": 100, "fraud_type_code": "ERRO_API_EXTERNA",
            "justification": f"Ocorreu um erro na comunicação com a API externa. Detalhe técnico: {str(e)}",
            "recommended_action": "BLOQUEIO_AUTOMATICO_E_REVISAO_MANUAL"
        }
