# Métricas Explicadas

Este guia explica cada métrica do sistema em linguagem simples.

---

## TME - Tempo Médio de Espera

### O que é?
O tempo que o cliente fica esperando uma resposta do atendente.

### Como é calculado?
```
TME = Soma dos tempos de espera ÷ Quantidade de respostas
```

### Por que importa?
- Clientes que esperam muito ficam **insatisfeitos**
- Pode causar **desistência** da compra
- Reflete a **produtividade** da equipe

### Meta Recomendada

| Nível | Tempo |
|-------|-------|
| 🟢 Excelente | < 1 minuto |
| 🟡 Bom | 1-3 minutos |
| 🟠 Regular | 3-5 minutos |
| 🔴 Crítico | > 5 minutos |

---

## TMA - Tempo Médio de Atendimento

### O que é?
Quanto tempo dura a conversa inteira, do início ao fim.

### Como é calculado?
```
TMA = Hora da última mensagem - Hora da primeira mensagem
```

### Por que importa?
- Conversas **muito longas** podem indicar dificuldade em resolver
- Conversas **muito curtas** podem indicar respostas superficiais
- Ajuda a dimensionar a **capacidade da equipe**

### O que é um bom TMA?
Depende do tipo de produto/serviço:

| Tipo de Atendimento | TMA Esperado |
|---------------------|--------------|
| Dúvida simples | 5-10 min |
| Orçamento | 15-30 min |
| Negociação | 30-60 min |
| Reclamação | 20-40 min |

---

## Taxa de Conversão

### O que é?
Porcentagem de conversas que resultaram em venda.

### Como é calculado?
```
Taxa = (Chats convertidos ÷ Total de chats) × 100
```

### Exemplo
Se de 100 chats, 15 viraram venda:
```
Taxa = (15 ÷ 100) × 100 = 15%
```

### Meta Recomendada
Varia muito por segmento, mas em média:

| Setor | Taxa Típica |
|-------|-------------|
| E-commerce | 2-5% |
| B2B | 10-20% |
| Serviços Premium | 20-40% |

---

## Score de Humanização

### O que é?
Uma nota de 1 a 5 que avalia quão "humana" e personalizada foi a conversa.

### Escala

| Score | Significado | Exemplo |
|-------|-------------|---------|
| 1 | Muito robótico | "Aguarde que vou transferir" |
| 2 | Respostas genéricas | Scripts prontos |
| 3 | Neutro | Funcional mas sem personalização |
| 4 | Personalizado | Usa nome, entende contexto |
| 5 | Muito humano | Empático, proativo, memorável |

### Por que importa?
- Clientes preferem atendimento **personalizado**
- Aumenta a **confiança** e **fidelização**
- Diferencial competitivo

---

## Funil de Vendas

### O que é?
Uma visualização de como as conversas "fluem" pelos estágios de venda.

### Estágios

| Estágio | Significado |
|---------|-------------|
| ⏳ Em Progresso | Conversa ainda aberta ou aguardando |
| ✅ Convertido | Resultou em venda |
| ❌ Perdido | Não resultou em venda |

### Por que importa?
- Mostra onde estamos **perdendo** clientes
- Ajuda a identificar **gargalos** no processo
- Base para **melhorias** no script de vendas

---

## Motivos de Perda

### O que é?
Classificação dos motivos pelos quais não fechamos vendas.

### Motivos Comuns

| Motivo | Descrição |
|--------|-----------|
| **Preço** | Cliente achou caro |
| **Estoque** | Produto não disponível |
| **Concorrente** | Escolheu outra empresa |
| **Sem resposta** | Cliente sumiu |
| **Timing** | Não era o momento certo |

### Por que importa?
- Orienta ações de **marketing** (se o problema é preço)
- Sinaliza problemas de **operação** (se é estoque)
- Ajuda a entender a **concorrência**
