# populate_db.py (versão corrigida)

from database import engine, Base, SessionLocal, Usuario, HistoricoTransacao # <--- CORREÇÃO AQUI
from datetime import datetime

def populate():
    # Apaga e recria o banco de dados do zero
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # --- Usuário 1: João Silva (Comportamento normal) ---
    user1 = Usuario(
        nome="João Silva",
        cpf="111.111.111-11",
        email="joao.silva@email.com",
        telefone="83999991111",
        endereco_registrado="João Pessoa, PB",
        margem_consignavel=1200.50
    )
    db.add(user1)
    db.commit() # Commit para que user1.id seja gerado

    transacao1_user1 = HistoricoTransacao(
        usuario_id=user1.id,
        valor=5000.00,
        data_hora=datetime(2024, 8, 10, 14, 30),
        status="Aprovado",
        ip="177.15.23.10",
        geolocalizacao="João Pessoa, PB",
        dispositivo_fingerprint="e4d5f6a7b8c9d0e1f2a3b4c5d6e7f8a9", # Fingerprint consistente
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        tempo_preenchimento_formulario_segundos=150
    )
    db.add(transacao1_user1)

    # --- Usuário 2: Maria Oliveira (Histórico normal para contraste) ---
    user2 = Usuario(
        nome="Maria Oliveira",
        cpf="222.222.222-22",
        email="maria.oliveira@email.com",
        telefone="83988882222",
        endereco_registrado="Campina Grande, PB",
        margem_consignavel=2500.00
    )
    db.add(user2)
    db.commit() # Commit para que user2.id seja gerado

    transacao1_user2 = HistoricoTransacao(
        usuario_id=user2.id,
        valor=10000.00,
        data_hora=datetime(2025, 7, 1, 10, 0),
        status="Aprovado",
        ip="189.45.11.20",
        geolocalizacao="Campina Grande, PB",
        dispositivo_fingerprint="b8c9d0e1f2a3b4c5d6e7f8a9b8c9d0e1", # Fingerprint conhecido dela
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
        tempo_preenchimento_formulario_segundos=180
    )
    db.add(transacao1_user2)
    
    db.commit()
    db.close()
    print("Banco de dados (v2) populado com sucesso!")

if __name__ == "__main__":
    populate()