{% extends "base.html" %}
{% block title %}Nova Movimentação{% endblock %}

{% block content %}
<h1>Nova movimentação</h1>
<p class="subtitle">Registre uma entrada (compra/recebimento) ou saída (venda/consumo) de estoque.</p>

<div class="panel">
    {% if produtos %}
    <form method="POST">
        <div class="form-group">
            <label for="produto_id">Produto</label>
            <select id="produto_id" name="produto_id" required>
                {% for p in produtos %}
                <option value="{{ p.id }}">{{ p.nome }} (estoque: {{ p.estoque_atual }} {{ p.unidade }})</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="tipo">Tipo</label>
                <select id="tipo" name="tipo" required>
                    <option value="entrada">Entrada (compra/recebimento)</option>
                    <option value="saida">Saída (venda/consumo)</option>
                </select>
            </div>
            <div class="form-group">
                <label for="quantidade">Quantidade</label>
                <input type="number" step="0.01" min="0.01" id="quantidade" name="quantidade" required>
            </div>
            <div class="form-group">
                <label for="data">Data</label>
                <input type="date" id="data" name="data" value="{{ hoje }}" required>
            </div>
        </div>

        <div class="form-group">
            <label for="motivo">Motivo / observação (opcional)</label>
            <input type="text" id="motivo" name="motivo" placeholder="Ex: Compra fornecedor X, evento de sábado, perda/quebra...">
        </div>

        <div class="form-actions">
            <button type="submit" class="btn">Registrar movimentação</button>
            <a href="{{ url_for('listar_movimentacoes') }}" class="btn btn-secondary">Cancelar</a>
        </div>
    </form>
    {% else %}
    <div class="empty-state">
        Você precisa cadastrar produtos antes de registrar movimentações.
        <br><br>
        <a href="{{ url_for('novo_produto') }}" class="btn">Cadastrar produto</a>
    </div>
    {% endif %}
</div>
{% endblock %}
