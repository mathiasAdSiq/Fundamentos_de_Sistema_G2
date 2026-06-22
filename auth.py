{% extends "base.html" %}
{% block title %}Feriados e Eventos{% endblock %}

{% block content %}
<h1>Feriados e eventos especiais</h1>
<p class="subtitle">
    Cadastre datas com movimento diferenciado (feriados, jogos, eventos locais).
    O fator multiplicador ajusta a previsão de consumo: por exemplo, <strong>1.5</strong> significa
    50% mais consumo do que a média normal daquele dia da semana.
</p>

<div class="panel">
    <h2>Adicionar / atualizar data especial</h2>
    <form method="POST" action="{{ url_for('novo_dia_especial') }}">
        <div class="form-row">
            <div class="form-group">
                <label for="data">Data</label>
                <input type="date" id="data" name="data" value="{{ hoje }}" required>
            </div>
            <div class="form-group">
                <label for="descricao">Descrição</label>
                <input type="text" id="descricao" name="descricao" placeholder="Ex: Réveillon, Jogo do Brasil, Festa Junina" required>
            </div>
            <div class="form-group">
                <label for="fator_multiplicador">Fator multiplicador</label>
                <input type="number" step="0.1" min="0.1" id="fator_multiplicador" name="fator_multiplicador" value="1.5" required>
            </div>
        </div>
        <div class="form-actions">
            <button type="submit" class="btn">Salvar data</button>
        </div>
    </form>
</div>

<div class="panel">
    <h2>Datas cadastradas</h2>
    {% if dias %}
    <table>
        <thead><tr><th>Data</th><th>Descrição</th><th>Fator</th><th></th></tr></thead>
        <tbody>
            {% for d in dias %}
            <tr>
                <td>{{ d.data }}</td>
                <td>{{ d.descricao }}</td>
                <td><span class="badge badge-yellow">x{{ d.fator_multiplicador }}</span></td>
                <td>
                    <form method="POST" action="{{ url_for('excluir_dia_especial', dia_id=d.id) }}" class="inline"
                          onsubmit="return confirm('Remover esta data especial?');">
                        <button type="submit" class="btn btn-sm btn-danger">Remover</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty-state">Nenhuma data especial cadastrada ainda.</div>
    {% endif %}
</div>
{% endblock %}
