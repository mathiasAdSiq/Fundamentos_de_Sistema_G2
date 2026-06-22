from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db


class Usuario(UserMixin):
    """Wrapper de usuário compatível com Flask-Login."""

    def __init__(self, row):
        self.id = row["id"]
        self.nome = row["nome"]
        self.login = row["login"]
        self.senha_hash = row["senha_hash"]
        self.ativo = bool(row["ativo"])

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.ativo


def buscar_usuario_por_id(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
    return Usuario(row) if row else None


def buscar_usuario_por_login(login):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE login = ?", (login,)
        ).fetchone()
    return Usuario(row) if row else None


def verificar_senha(usuario, senha):
    return check_password_hash(usuario.senha_hash, senha)


def criar_usuario(nome, login, senha):
    senha_hash = generate_password_hash(senha)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usuarios (nome, login, senha_hash) VALUES (?, ?, ?)",
            (nome, login, senha_hash),
        )


def existe_algum_usuario():
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM usuarios").fetchone()
    return row["c"] > 0
