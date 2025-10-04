#!/usr/bin/env python3
"""
Script de migração para adicionar novos campos ao banco de dados
"""

import sqlite3
import os
from datetime import datetime
from src.models.rastreio import db
from src.main import app

def migrate_database():
    """Executa a migração do banco de dados"""
    
    # Caminho para o banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado. Criando novo banco...")
        return
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Iniciando migração do banco de dados...")
        
        # Verificar colunas existentes na tabela rastreios_esperados
        cursor.execute("PRAGMA table_info(rastreios_esperados)")
        rastreios_columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar campo timestamp se não existir na tabela rastreios_esperados
        if 'timestamp' not in rastreios_columns:
            print("Adicionando campo 'timestamp' na tabela rastreios_esperados...")
            cursor.execute("ALTER TABLE rastreios_esperados ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
            
            # Preencher timestamp com a data atual para registros existentes
            agora = datetime.now().isoformat()
            cursor.execute("UPDATE rastreios_esperados SET timestamp = ? WHERE timestamp IS NULL", (agora,))
            print(f"Preenchendo timestamp para registros existentes com: {agora}")
        
        # Verificar colunas existentes na tabela mercadorias_conferidas
        cursor.execute("PRAGMA table_info(mercadorias_conferidas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar campo transportadora se não existir
        if 'transportadora' not in columns:
            print("Adicionando campo 'transportadora'...")
            cursor.execute("ALTER TABLE mercadorias_conferidas ADD COLUMN transportadora TEXT")
        
        # Adicionar campo data_bipagem se não existir
        if 'data_bipagem' not in columns:
            print("Adicionando campo 'data_bipagem'...")
            cursor.execute("ALTER TABLE mercadorias_conferidas ADD COLUMN data_bipagem DATE")
            
            # Preencher data_bipagem com a data atual para registros existentes
            hoje = datetime.now().date().isoformat()
            cursor.execute("UPDATE mercadorias_conferidas SET data_bipagem = ? WHERE data_bipagem IS NULL", (hoje,))
            print(f"Preenchendo data_bipagem para registros existentes com: {hoje}")
        
        # Verificar se a tabela dashboard_cache existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_cache'")
        if not cursor.fetchone():
            print("Criando tabela 'dashboard_cache'...")
            cursor.execute("""
                CREATE TABLE dashboard_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data DATE NOT NULL UNIQUE,
                    transportadoras TEXT NOT NULL,
                    total_hoje INTEGER DEFAULT 0,
                    coleta_hoje INTEGER DEFAULT 0,
                    insucesso_hoje INTEGER DEFAULT 0,
                    sem_status_hoje INTEGER DEFAULT 0,
                    ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Tabela dashboard_cache criada com sucesso!")
        
        # Commit das alterações
        conn.commit()
        print("Migração concluída com sucesso!")
        
        # Verificar estrutura final das tabelas
        print("\nEstrutura final da tabela rastreios_esperados:")
        cursor.execute("PRAGMA table_info(rastreios_esperados)")
        rastreios_final = cursor.fetchall()
        for column in rastreios_final:
            print(f"  - {column[1]} ({column[2]})")
        
        print("\nEstrutura final da tabela mercadorias_conferidas:")
        cursor.execute("PRAGMA table_info(mercadorias_conferidas)")
        final_columns = cursor.fetchall()
        for column in final_columns:
            print(f"  - {column[1]} ({column[2]})")
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        conn.rollback()
    finally:
        conn.close()

def migrate_dashboard_cache():
    """Adiciona o campo rastreios_contados à tabela dashboard_cache"""
    with app.app_context():
        try:
            # Adicionar coluna rastreios_contados se não existir
            with db.engine.connect() as conn:
                conn.execute(db.text("""
                    ALTER TABLE dashboard_cache 
                    ADD COLUMN rastreios_contados TEXT DEFAULT '[]'
                """))
                conn.commit()
            print("Campo rastreios_contados adicionado com sucesso!")
        except Exception as e:
            print(f"Erro na migração: {e}")
            # Se a coluna já existe, ignorar o erro
            pass

if __name__ == "__main__":
    migrate_database()
    migrate_dashboard_cache()
