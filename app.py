from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from datetime import date, datetime
import os
import secrets

from database import get_db, init_db
import previsao
import auth

app = Flask(__name__)

# Chave de sessão: gerada uma vez e salva em arquivo, para não mudar a cada
# reinício (o que desconectaria todo mundo) e sem deixar fixa no código.
SECRET_KEY_PATH = "instance/secret_key.txt"
os.makedirs("instance", exist_ok=True)
if not os.path.exists(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, "w") as f:
        f.write(secrets.token_hex(32))
with open(SECRET_KEY_PATH) as f:
    app.secret_key = f.read().strip()

init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar o sistema."
login_manager.login_message_category = "erro"


@login_manager.user_loader
def load_user(user_id):
    return auth.buscar_usuario_por_id(user_id)


# ---------- AUTENTICAÇÃO ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if not auth.existe_algum_usuario():
        flash(
            "Nenhum usuário cadastrado ainda. Rode 'py gerenciar_usuarios.py' "
            "no terminal para criar o primeiro usuário.",
            "erro",
        )

    if request.method == "POST":
        login_str = request.form.get("login", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = auth.buscar_usuario_por_login(login_str)

        if usuario and usuario.ativo and auth.verificar_senha(usuario, senha):
            login_user(usuario)
            proxima = request.args.get("next")
            return redirect(proxima or url_for("dashboard"))

        flash("Login ou senha incorretos.", "erro")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("login"))


# ---------- helpers ----------

def listar_categorias():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT categoria FROM produtos ORDER BY categoria"
        ).fetchall()
    return [r["categoria"] for r in rows]


# ---------- DASHBOARD ----------

@app.route("/")
@login_required
def dashboard():
    with get_db() as conn:
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome"
        ).fetchall()

    alertas = []
    total_itens = len(produtos)
    valor_total_estoque = 0.0

    for p in produtos:
        valor_total_estoque += p["estoque_atual"] * p["preco_custo"]
        if p["estoque_atual"] <= p["estoque_minimo"]:
            alertas.append(p)

    # Próximos dias especiais cadastrados (a partir de hoje)
    hoje_iso = date.today().isoformat()
    with get_db() as conn:
        proximos_especiais = conn.execute(
            "SELECT * FROM dias_especiais WHERE data >= ? ORDER BY data LIMIT 5",
            (hoje_iso,),
        ).fetchall()

    return render_template(
        "dashboard.html",
        produtos=produtos,
        alertas=alertas,
        total_itens=total_itens,
        valor_total_estoque=round(valor_total_estoque, 2),
        proximos_especiais=proximos_especiais,
    )


# ---------- PRODUTOS ----------

@app.route("/produtos")
@login_required
def listar_produtos():
    with get_db() as conn:
        produtos = conn.execute(
            "SELECT * FROM produtos ORDER BY ativo DESC, nome"
        ).fetchall()
    return render_template("produtos.html", produtos=produtos)


@app.route("/produtos/novo", methods=["GET", "POST"])
@login_required
def novo_produto():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        categoria = request.form["categoria"].strip() or "Outros"
        unidade = request.form["unidade"].strip() or "un"
        estoque_atual = float(request.form.get("estoque_atual", 0) or 0)
        estoque_minimo = float(request.form.get("estoque_minimo", 0) or 0)
        preco_custo = float(request.form.get("preco_custo", 0) or 0)

        if not nome:
            flash("O nome do produto é obrigatório.", "erro")
            return redirect(url_for("novo_produto"))

        with get_db() as conn:
            conn.execute(
                """INSERT INTO produtos
                   (nome, categoria, unidade, estoque_atual, estoque_minimo, preco_custo)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (nome, categoria, unidade, estoque_atual, estoque_minimo, preco_custo),
            )
        flash(f'Produto "{nome}" cadastrado com sucesso.', "sucesso")
        return redirect(url_for("listar_produtos"))

    return render_template("produto_form.html", produto=None, categorias=listar_categorias())


@app.route("/produtos/<int:produto_id>/editar", methods=["GET", "POST"])
@login_required
def editar_produto(produto_id):
    with get_db() as conn:
        produto = conn.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()

    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("listar_produtos"))

    if request.method == "POST":
        nome = request.form["nome"].strip()
        categoria = request.form["categoria"].strip() or "Outros"
        unidade = request.form["unidade"].strip() or "un"
        estoque_minimo = float(request.form.get("estoque_minimo", 0) or 0)
        preco_custo = float(request.form.get("preco_custo", 0) or 0)
        ativo = 1 if request.form.get("ativo") == "on" else 0

        with get_db() as conn:
            conn.execute(
                """UPDATE produtos SET nome=?, categoria=?, unidade=?,
                   estoque_minimo=?, preco_custo=?, ativo=? WHERE id=?""",
                (nome, categoria, unidade, estoque_minimo, preco_custo, ativo, produto_id),
            )
        flash("Produto atualizado.", "sucesso")
        return redirect(url_for("listar_produtos"))

    return render_template("produto_form.html", produto=produto, categorias=listar_categorias())


@app.route("/produtos/<int:produto_id>/excluir", methods=["POST"])
@login_required
def excluir_produto(produto_id):
    with get_db() as conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    flash("Produto excluído.", "sucesso")
    return redirect(url_for("listar_produtos"))


# ---------- MOVIMENTAÇÕES ----------

@app.route("/movimentacoes")
@login_required
def listar_movimentacoes():
    with get_db() as conn:
        movs = conn.execute(
            """SELECT m.*, p.nome AS produto_nome, p.unidade AS produto_unidade
               FROM movimentacoes m
               JOIN produtos p ON p.id = m.produto_id
               ORDER BY m.data DESC, m.id DESC
               LIMIT 200"""
        ).fetchall()
    return render_template("movimentacoes.html", movimentacoes=movs)


@app.route("/movimentacoes/nova", methods=["GET", "POST"])
@login_required
def nova_movimentacao():
    with get_db() as conn:
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome"
        ).fetchall()

    if request.method == "POST":
        produto_id = int(request.form["produto_id"])
        tipo = request.form["tipo"]
        quantidade = float(request.form["quantidade"])
        motivo = request.form.get("motivo", "").strip()
        data_mov = request.form.get("data") or date.today().isoformat()

        if quantidade <= 0:
            flash("A quantidade deve ser maior que zero.", "erro")
            return redirect(url_for("nova_movimentacao"))

        with get_db() as conn:
            produto = conn.execute(
                "SELECT * FROM produtos WHERE id = ?", (produto_id,)
            ).fetchone()

            if tipo == "saida" and quantidade > produto["estoque_atual"]:
                flash(
                    f'Estoque insuficiente. Estoque atual de "{produto["nome"]}": '
                    f'{produto["estoque_atual"]} {produto["unidade"]}.',
                    "erro",
                )
                return redirect(url_for("nova_movimentacao"))

            conn.execute(
                """INSERT INTO movimentacoes (produto_id, tipo, quantidade, motivo, data)
                   VALUES (?, ?, ?, ?, ?)""",
                (produto_id, tipo, quantidade, motivo, data_mov),
            )

            delta = quantidade if tipo == "entrada" else -quantidade
            conn.execute(
                "UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?",
                (delta, produto_id),
            )

        flash("Movimentação registrada com sucesso.", "sucesso")
        return redirect(url_for("listar_movimentacoes"))

    return render_template(
        "movimentacao_form.html", produtos=produtos, hoje=date.today().isoformat()
    )


# ---------- DIAS ESPECIAIS (feriados / eventos) ----------

@app.route("/dias-especiais")
@login_required
def listar_dias_especiais():
    with get_db() as conn:
        dias = conn.execute(
            "SELECT * FROM dias_especiais ORDER BY data"
        ).fetchall()
    return render_template("dias_especiais.html", dias=dias, hoje=date.today().isoformat())


@app.route("/dias-especiais/novo", methods=["POST"])
@login_required
def novo_dia_especial():
    data_str = request.form["data"]
    descricao = request.form["descricao"].strip()
    fator = float(request.form.get("fator_multiplicador", 1.5) or 1.5)

    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO dias_especiais (data, descricao, fator_multiplicador)
                   VALUES (?, ?, ?)
                   ON CONFLICT(data) DO UPDATE SET
                     descricao = excluded.descricao,
                     fator_multiplicador = excluded.fator_multiplicador""",
                (data_str, descricao, fator),
            )
        flash("Dia especial salvo.", "sucesso")
    except Exception as e:
        flash(f"Erro ao salvar: {e}", "erro")

    return redirect(url_for("listar_dias_especiais"))


@app.route("/dias-especiais/<int:dia_id>/excluir", methods=["POST"])
@login_required
def excluir_dia_especial(dia_id):
    with get_db() as conn:
        conn.execute("DELETE FROM dias_especiais WHERE id = ?", (dia_id,))
    flash("Dia especial removido.", "sucesso")
    return redirect(url_for("listar_dias_especiais"))


# ---------- PREVISÃO ----------

@app.route("/previsao")
@login_required
def previsao_geral():
    with get_db() as conn:
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome"
        ).fetchall()

    resultados = []
    for p in produtos:
        rec = previsao.recomendacao_compra(
            p["id"], p["estoque_atual"], p["estoque_minimo"], n_dias=7
        )
        resultados.append({"produto": p, "recomendacao": rec})

    return render_template("previsao.html", resultados=resultados)


@app.route("/previsao/<int:produto_id>")
@login_required
def previsao_produto(produto_id):
    with get_db() as conn:
        produto = conn.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()

    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("previsao_geral"))

    medias = previsao.media_consumo_por_dia_semana(produto_id)
    rec = previsao.recomendacao_compra(
        produto_id, produto["estoque_atual"], produto["estoque_minimo"], n_dias=7
    )

    medias_lista = [
        {"dia": previsao.DIAS_SEMANA_PT[i], "media": round(medias[i], 2)} for i in range(7)
    ]

    return render_template(
        "previsao_produto.html", produto=produto, medias=medias_lista, rec=rec
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
