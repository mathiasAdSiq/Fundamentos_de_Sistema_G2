# Controle de Estoque de Bebidas

Sistema web em Python (Flask + SQLite) para controle de estoque de bebidas de
restaurante, com previsão de demanda baseada em histórico de consumo e
eventos especiais (feriados, jogos, etc).

## Funcionalidades

- **Cadastro de produtos**: nome, categoria, unidade, estoque mínimo, preço de custo.
- **Entrada e saída de itens**: registro de movimentações com data e motivo,
  atualizando o estoque automaticamente. O sistema bloqueia saídas maiores
  que o estoque disponível.
- **Dashboard**: visão geral do estoque, valor total, alertas de produtos
  com estoque baixo.
- **Feriados/Eventos especiais**: cadastre datas com movimento diferenciado
  (ex: Réveillon, jogo de futebol, festa junina) e um "fator multiplicador"
  de consumo esperado para aquele dia.
- **Previsão de estoque**: calcula a média histórica de consumo de cada
  produto **por dia da semana** (ex: sábado costuma vender mais que terça) e
  combina com o fator dos dias especiais cadastrados para prever a demanda
  dos próximos 7 dias e recomendar se — e quanto — você precisa comprar.

## Como rodar

### 1. Instalar dependências

```bash
pip install flask
```

(Só o Flask é necessário; o banco de dados usa SQLite, que já vem com o Python.)

### 2. Executar

```bash
python3 app.py
```

O terminal vai mostrar algo como:

```
Running on http://127.0.0.1:5000
```

Abra esse endereço no navegador.

> O banco de dados (`instance/estoque.db`) é criado automaticamente na
> primeira execução, já vazio e pronto para você cadastrar seus produtos.

## Como usar no dia a dia

1. **Cadastre seus produtos** em "Produtos → Novo produto" (ex: Cerveja
   Heineken 600ml, Coca-Cola 2L, Caipirinha pronta, etc), definindo o
   estoque mínimo que dispara o alerta de reposição.
2. **Registre as movimentações** todo dia (ou ao final do expediente):
   - **Entrada**: quando chega mercadoria do fornecedor.
   - **Saída**: quando o produto é consumido/vendido. É esse histórico de
     saídas que alimenta a previsão.
3. **Cadastre feriados e eventos** com antecedência em "Feriados/Eventos"
   (ex: data de um jogo importante, véspera de feriado, festa local),
   definindo o fator de aumento esperado (1.5 = 50% mais, 2.0 = dobro, etc).
   Você pode ajustar esse fator com base na experiência de anos anteriores.
4. **Consulte "Previsão"** para ver, produto por produto, se o estoque atual
   é suficiente para os próximos 7 dias ou se é hora de fazer pedido ao
   fornecedor — já considerando os dias especiais cadastrados.

## Como funciona a previsão (resumo técnico)

Para cada produto, o sistema:

1. Olha o histórico de saídas dos últimos 90 dias.
2. Agrupa por dia da semana (segunda, terça, ..., domingo) e calcula a
   média de consumo de cada um.
3. Para cada um dos próximos 7 dias, verifica se existe um "dia especial"
   cadastrado naquela data. Se existir, multiplica a média do dia da semana
   pelo fator cadastrado (ex: sábado normal x2.0 por causa de um jogo).
4. Soma a previsão dos 7 dias e compara com o estoque atual menos o estoque
   mínimo de segurança, recomendando a quantidade de compra se necessário.

Quanto mais movimentações de saída você registrar (idealmente diárias), mais
precisa fica a previsão — o sistema usa dados reais do seu próprio
restaurante, não estimativas genéricas.

## Estrutura do projeto

```
estoque_bebidas/
├── app.py              # Aplicação Flask (rotas)
├── database.py         # Conexão e criação das tabelas (SQLite)
├── previsao.py          # Lógica de cálculo de médias e previsão de demanda
├── instance/
│   └── estoque.db       # Banco de dados (criado automaticamente)
├── templates/           # Páginas HTML (Jinja2)
└── static/
    └── style.css         # Estilo visual
```

## Próximos passos sugeridos (opcional)

- Adicionar autenticação (login) se mais pessoas forem usar o sistema.
- Exportar relatórios em PDF/Excel.
- Adicionar gráfico de consumo histórico (linha do tempo).
- Integrar com leitor de código de barras para agilizar o registro de saída.
