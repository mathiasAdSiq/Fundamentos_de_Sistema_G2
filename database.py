import sqlite3
from contextlib import contextmanager

DB_PATH = "instance/estoque.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT NOT NULL DEFAULT 'Outros',
                unidade TEXT NOT NULL DEFAULT 'un',
                estoque_atual REAL NOT NULL DEFAULT 0,
                estoque_minimo REAL NOT NULL DEFAULT 0,
                preco_custo REAL NOT NULL DEFAULT 0,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
                quantidade REAL NOT NULL,
                motivo TEXT,
                data TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS dias_especiais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL UNIQUE,
                descricao TEXT NOT NULL,
                fator_multiplicador REAL NOT NULL DEFAULT 1.5
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_mov_produto ON movimentacoes(produto_id);
            CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentacoes(data);
            """
        )
