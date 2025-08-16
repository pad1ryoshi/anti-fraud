# Documentação - Sistema IA Antifraude no Crédito Consignado

O projeto contará com o uso de um chatbot, uma API de backend e um módulo de Inteligência Artificial para realizar análises de risco e detectar possíveis fraudes em solicitações de crédito consignado. A arquitetura foi desenhada para ser modular, segura e eficiente.

### Chatbot

Tecnologia: n8n, integrado a aplicação web do ConsigFácil.
Ambiente: Opera dentro de um dashboard web após o login do usuário.

Objetivo:

Ser a principal interface de interação com o usuário, guiando-o de forma simples e conversacional através do processo de solicitação de empréstimo ou verificação do histórico de fraudes da sua conta, garantindo uma experiência fluida e sem atritos.

Responsabilidades atuais:
```
Iniciar o Fluxo de Análise: Após coletar os dados, o chatbot é responsável por acionar a API de backend, enviando todas as informações necessárias para a verificação de fraude.

Comunicar o Resultado: Receber a resposta da API e comunicar o status final ao usuário de forma clara e imediata, finalizando a interação.
```

Melhorias futuras:
```
Coletar Dados da Solicitação: Perguntar ao usuário informações essenciais para o empréstimo, como valor solicitado e número parcelas.
```

### API

Tecnologia: FastAPI (Python) ou TypeScript.
Banco de Dados: Supabase (PostgreSQL).

Objetivo:

Atuar como o serviço central (backend) que orquestra todo o processo de análise de fraude. Ela é o ponto de conexão entre a interface do usuário (chatbot) e a fornece as rotas para a IA analisar se existe fraude.

Responsabilidades:
```
Expor o Endpoint de Análise: Manter uma rota segura e bem definida (POST /api/check_fraud) para receber os dados da solicitação vindos do chatbot.

Comunicar-se com a IA: Formatar e enviar todos os dados relevantes para o módulo de Inteligência Artificial e aguardar o retorno da análise.

Executar Ações no Banco de Dados: Com base na resposta da IA, interagir com o Supabase. Especificamente, se a transação for fraudulenta, a API chama a função {{nome_funcao}} para atualizar o contador de fraudes do usuário de forma incremental.
```

Melhorias futuras:
```
Coletar Metadados de Segurança: Enriquecer a requisição com dados "invisíveis" ao usuário, como endereço de IP e user-agent, que são cruciais para a análise de risco.
```

### IA

Tecnologia: LLM - Google Gemini, via API.
Método: Engenharia de Prompt Estruturada.

Objetivo:

Realizar uma análise de risco eficiente e contextual de cada solicitação de empréstimo, agindo como um analista de fraude automatizado para identificar possíveis atividades suspeitas nos contextos de fraude no crédito consignado.

Responsabilidades:
```
Interpretar o "Scorecard": Processar o prompt detalhado que contém a "expertise humana" do negócio, com regras claras, pesos e um sistema de pontuação para múltiplos vetores de fraude.

Calcular o Score de Risco: Aplicar as regras do prompt aos dados da transação em tempo real para calcular um fraud_score numérico (0-100) que quantifica o nível de risco.

Gerar Resposta Estruturada: Retornar sua análise em um formato JSON previsível, contendo a decisão (is_fraudulent), o score, um código de tipo de fraude, uma justification detalhada em linguagem natural e uma ação recomendada, permitindo que a API tome decisões automatizadas.
```
