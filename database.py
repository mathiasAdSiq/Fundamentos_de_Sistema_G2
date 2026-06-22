<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Estoque de Bebidas{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="navbar-brand">🍹 Estoque de Bebidas</div>
        <div class="navbar-links">
            <a href="{{ url_for('dashboard') }}">Dashboard</a>
            <a href="{{ url_for('listar_produtos') }}">Produtos</a>
            <a href="{{ url_for('listar_movimentacoes') }}">Movimentações</a>
            <a href="{{ url_for('previsao_geral') }}">Previsão</a>
            <a href="{{ url_for('listar_dias_especiais') }}">Feriados/Eventos</a>
        </div>
        {% if current_user.is_authenticated %}
        <div class="navbar-user">
            <span class="user-name">{{ current_user.nome }}</span>
            <a href="{{ url_for('logout') }}" class="btn btn-sm btn-secondary">Sair</a>
        </div>
        {% endif %}
    </nav>

    <main class="container">
        {% with mensagens = get_flashed_messages(with_categories=true) %}
            {% if mensagens %}
                {% for categoria, msg in mensagens %}
                    <div class="flash flash-{{ categoria }}">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>
</body>
</html>
