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
pip install flask flask-login
```

(O banco de dados usa SQLite, que já vem com o Python — não precisa instalar nada além disso.)

### 2. Criar o primeiro usuário

Antes de usar o sistema pela primeira vez, você precisa criar um usuário de
acesso. Rode no terminal:

```bash
python3 gerenciar_usuarios.py
```

(No Windows, use `py gerenciar_usuarios.py`)

Escolha a opção **1 - Criar novo usuário** e preencha nome, login e senha.

Esse mesmo script serve para o dia a dia: adicionar funcionários, resetar
senha de quem esqueceu, listar usuários cadastrados, ou desativar o acesso
de alguém que saiu — tudo pelo terminal, sem precisar editar o banco de
dados manualmente.

### 3. Executar o site

```bash
python3 app.py
```

O terminal vai mostrar algo como:

```
Running on http://127.0.0.1:5000
```

Abra esse endereço no navegador e faça login com o usuário que você criou.

> O banco de dados (`instance/estoque.db`) é criado automaticamente na
> primeira execução, já vazio e pronto para você cadastrar seus produtos.

## Login e usuários

O sistema agora exige login para qualquer acesso — ninguém entra sem
usuário e senha cadastrados.

- **Múltiplos usuários**: você pode criar um login para cada funcionário
  que for usar o sistema (ex: caixa, gerente, etc), todos com acesso
  independente.
- **Esqueceu a senha?** Rode `python3 gerenciar_usuarios.py` (ou
  `py gerenciar_usuarios.py` no Windows), escolha a opção **2 - Resetar
  senha** e defina uma nova.
- **Funcionário saiu do restaurante?** Use a opção **4 - Ativar/desativar
  usuário** no mesmo script para bloquear o acesso dele sem precisar
  excluir o histórico de quem ele é.
- As senhas são armazenadas com hash seguro (nunca em texto puro) no banco
  de dados.

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
