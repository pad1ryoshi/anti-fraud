# populate_db.py (Versão Final de Verificação)

from database import engine, Base, SessionLocal, Usuario, HistoricoTransacao
from datetime import datetime

def populate():
    # Apaga e recria a estrutura do banco de dados do zero
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # --- Usuário 1: João Silva ---
    user1 = Usuario(
        nome="João Silva",
        cpf="111.111.111-11",
        email="joao.silva@email.com",
        telefone="83999991111",
        endereco_registrado="João Pessoa, PB",
        margem_consignavel=1200.50
    )
    db.add(user1)
    db.commit()

    transacao1_user1 = HistoricoTransacao(
        usuario_id=user1.id,
        valor=5000.00,
        data_hora=datetime(2024, 8, 10, 14, 30),
        status="Aprovado",
        ip="177.15.23.10",
        geolocalizacao="João Pessoa, PB",
        dispositivo_fingerprint="e4d5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
        tempo_preenchimento_formulario_segundos=150,
        foi_fraude=False, # Campo obrigatório agora
        justificativa_fraude=None
    )
    db.add(transacao1_user1)

    # --- Usuário 2: Maria Oliveira ---
    user2 = Usuario(
        nome="Maria Oliveira",
        cpf="222.222.222-22",
        email="maria.oliveira@email.com",
        telefone="83988882222",
        endereco_registrado="Campina Grande, PB",
        margem_consignavel=2500.00
    )
    db.add(user2)
    db.commit()

    transacao1_user2 = HistoricoTransacao(
        usuario_id=user2.id,
        valor=10000.00,
        data_hora=datetime(2025, 7, 1, 10, 0),
        status="Aprovado",
        ip="189.45.11.20",
        geolocalizacao="Campina Grande, PB",
        dispositivo_fingerprint="b8c9d0e1f2a3b4c5d6e7f8a9b8c9d0e1",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) ...",
        tempo_preenchimento_formulario_segundos=180,
        foi_fraude=False, # Campo obrigatório agora
        justificativa_fraude=None
    )
    db.add(transacao1_user2)
    
    db.commit()
    db.close()
    print("Banco de dados final recriado e populado com sucesso!")

if __name__ == "__main__":
    populate()
