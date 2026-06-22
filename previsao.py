from datetime import date, timedelta
from collections import defaultdict
from database import get_db

DIAS_SEMANA_PT = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]


def _historico_saidas(produto_id, janela_dias=90):
    """Retorna lista de (data, quantidade) das saídas do produto nos últimos N dias."""
    limite = (date.today() - timedelta(days=janela_dias)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT data, quantidade FROM movimentacoes
            WHERE produto_id = ? AND tipo = 'saida' AND data >= ?
            """,
            (produto_id, limite),
        ).fetchall()
    return rows


def media_consumo_por_dia_semana(produto_id, janela_dias=90):
    """
    Calcula a média de saída (consumo) do produto para cada dia da semana,
    com base no histórico de movimentações.
    Retorna dict: {0: media_segunda, 1: media_terca, ..., 6: media_domingo}
    """
    rows = _historico_saidas(produto_id, janela_dias)

    soma_por_dia = defaultdict(float)
    contagem_dias_distintos = defaultdict(set)

    for row in rows:
        d = date.fromisoformat(row["data"])
        dia_semana = d.weekday()  # 0 = segunda, 6 = domingo
        soma_por_dia[dia_semana] += row["quantidade"]
        contagem_dias_distintos[dia_semana].add(row["data"])

    medias = {}
    for dia in range(7):
        qtd_dias = len(contagem_dias_distintos[dia])
        medias[dia] = soma_por_dia[dia] / qtd_dias if qtd_dias > 0 else 0.0

    return medias


def buscar_dia_especial(data_iso):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM dias_especiais WHERE data = ?", (data_iso,)
        ).fetchone()
    return row


def prever_demanda(produto_id, data_alvo, janela_dias=90):
    """
    Prevê a demanda esperada de um produto para uma data específica,
    combinando média histórica do dia da semana + fator de dia especial (se houver).
    """
    medias = media_consumo_por_dia_semana(produto_id, janela_dias)
    dia_semana = data_alvo.weekday()
    media_base = medias[dia_semana]

    dia_especial = buscar_dia_especial(data_alvo.isoformat())
    fator = dia_especial["fator_multiplicador"] if dia_especial else 1.0
    descricao_especial = dia_especial["descricao"] if dia_especial else None

    previsao = media_base * fator

    return {
        "media_base": round(media_base, 2),
        "fator_aplicado": fator,
        "descricao_especial": descricao_especial,
        "previsao": round(previsao, 2),
        "dia_semana": DIAS_SEMANA_PT[dia_semana],
    }


def prever_proximos_dias(produto_id, n_dias=7, janela_dias=90):
    """Gera previsão de consumo para os próximos N dias a partir de hoje."""
    resultado = []
    hoje = date.today()
    for i in range(n_dias):
        data_alvo = hoje + timedelta(days=i)
        previsao = prever_demanda(produto_id, data_alvo, janela_dias)
        previsao["data"] = data_alvo.isoformat()
        resultado.append(previsao)
    return resultado


def recomendacao_compra(produto_id, estoque_atual, estoque_minimo, n_dias=7, janela_dias=90):
    """
    Soma a previsão de consumo dos próximos N dias e compara com o estoque atual
    para recomendar se é necessário comprar, e quanto.
    """
    previsoes = prever_proximos_dias(produto_id, n_dias, janela_dias)
    consumo_previsto_total = sum(p["previsao"] for p in previsoes)

    estoque_projetado_final = estoque_atual - consumo_previsto_total
    precisa_comprar = estoque_projetado_final < estoque_minimo

    qtd_sugerida = 0.0
    if precisa_comprar:
        qtd_sugerida = round((estoque_minimo - estoque_projetado_final), 2)

    return {
        "consumo_previsto_total": round(consumo_previsto_total, 2),
        "estoque_projetado_final": round(estoque_projetado_final, 2),
        "precisa_comprar": precisa_comprar,
        "quantidade_sugerida": qtd_sugerida,
        "detalhe_dias": previsoes,
    }
