"""
Script de gerenciamento de usuários — rode pelo terminal.

Uso:
    py gerenciar_usuarios.py

Use este script para:
- Criar o primeiro usuário (obrigatório antes de usar o sistema)
- Adicionar novos usuários (funcionários)
- Resetar a senha de alguém que esqueceu
- Desativar um usuário (ex: funcionário que saiu)
"""

import getpass
import sys

from database import init_db, get_db
import auth


def criar_usuario_interativo():
    print("\n--- Criar novo usuário ---")
    nome = input("Nome completo: ").strip()
    login = input("Login (sem espaços, ex: mathias): ").strip().lower()

    if not nome or not login:
        print("Nome e login são obrigatórios.")
        return

    if auth.buscar_usuario_por_login(login):
        print(f'Já existe um usuário com o login "{login}".')
        return

    senha = getpass.getpass("Senha: ")
    senha_confirma = getpass.getpass("Confirme a senha: ")

    if senha != senha_confirma:
        print("As senhas não coincidem. Operação cancelada.")
        return

    if len(senha) < 4:
        print("Use uma senha com pelo menos 4 caracteres.")
        return

    auth.criar_usuario(nome, login, senha)
    print(f'Usuário "{login}" criado com sucesso.')


def resetar_senha_interativo():
    print("\n--- Resetar senha de usuário ---")
    login = input("Login do usuário: ").strip().lower()
    usuario = auth.buscar_usuario_por_login(login)

    if not usuario:
        print(f'Nenhum usuário encontrado com o login "{login}".')
        return

    senha = getpass.getpass(f"Nova senha para {usuario.nome}: ")
    senha_confirma = getpass.getpass("Confirme a nova senha: ")

    if senha != senha_confirma:
        print("As senhas não coincidem. Operação cancelada.")
        return

    if len(senha) < 4:
        print("Use uma senha com pelo menos 4 caracteres.")
        return

    from werkzeug.security import generate_password_hash
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
            (generate_password_hash(senha), usuario.id),
        )
    print(f'Senha de "{login}" atualizada com sucesso.')


def listar_usuarios():
    print("\n--- Usuários cadastrados ---")
    with get_db() as conn:
        usuarios = conn.execute(
            "SELECT id, nome, login, ativo FROM usuarios ORDER BY nome"
        ).fetchall()

    if not usuarios:
        print("Nenhum usuário cadastrado ainda.")
        return

    for u in usuarios:
        status = "ativo" if u["ativo"] else "INATIVO"
        print(f'  [{u["id"]}] {u["nome"]} (login: {u["login"]}) - {status}')


def alternar_ativo_interativo():
    print("\n--- Ativar / desativar usuário ---")
    login = input("Login do usuário: ").strip().lower()
    usuario = auth.buscar_usuario_por_login(login)

    if not usuario:
        print(f'Nenhum usuário encontrado com o login "{login}".')
        return

    novo_status = 0 if usuario.ativo else 1
    with get_db() as conn:
        conn.execute(
            "UPDATE usuarios SET ativo = ? WHERE id = ?", (novo_status, usuario.id)
        )

    print(f'Usuário "{login}" agora está {"ativo" if novo_status else "INATIVO"}.')


def menu():
    init_db()
    while True:
        print("\n=== Gerenciamento de Usuários - Estoque de Bebidas ===")
        print("1. Criar novo usuário")
        print("2. Resetar senha de um usuário")
        print("3. Listar usuários")
        print("4. Ativar/desativar usuário")
        print("0. Sair")

        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "1":
            criar_usuario_interativo()
        elif escolha == "2":
            resetar_senha_interativo()
        elif escolha == "3":
            listar_usuarios()
        elif escolha == "4":
            alternar_ativo_interativo()
        elif escolha == "0":
            print("Até mais!")
            sys.exit(0)
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
