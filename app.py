from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, datetime
import os

from database import get_db, init_db
import previsao

app = Flask(__name__)
app.secret_key = "troque-essa-chave-em-producao"

os.makedirs("instance", exist_ok=True)
init_db()


# ---------- helpers ----------

def listar_categorias():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT categoria FROM produtos ORDER BY categoria"
        ).fetchall()
    return [r["categoria"] for r in rows]


# ---------- DASHBOARD ----------

@app.route("/")
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
def listar_produtos():
    with get_db() as conn:
        produtos = conn.execute(
            "SELECT * FROM produtos ORDER BY ativo DESC, nome"
        ).fetchall()
    return render_template("produtos.html", produtos=produtos)


@app.route("/produtos/novo", methods=["GET", "POST"])
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
def excluir_produto(produto_id):
    with get_db() as conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    flash("Produto excluído.", "sucesso")
    return redirect(url_for("listar_produtos"))


# ---------- MOVIMENTAÇÕES ----------

@app.route("/movimentacoes")
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
def listar_dias_especiais():
    with get_db() as conn:
        dias = conn.execute(
            "SELECT * FROM dias_especiais ORDER BY data"
        ).fetchall()
    return render_template("dias_especiais.html", dias=dias, hoje=date.today().isoformat())


@app.route("/dias-especiais/novo", methods=["POST"])
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
def excluir_dia_especial(dia_id):
    with get_db() as conn:
        conn.execute("DELETE FROM dias_especiais WHERE id = ?", (dia_id,))
    flash("Dia especial removido.", "sucesso")
    return redirect(url_for("listar_dias_especiais"))


# ---------- PREVISÃO ----------

@app.route("/previsao")
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
