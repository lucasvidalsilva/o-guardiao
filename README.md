# 🛡️ O Guardião

**O Guardião** é um projeto que criei com o objetivo de ajudar pessoas a se protegerem de golpes digitais. Ele funciona como uma central interativa com dados, explicações e até um chatbot educativo sobre fraudes online. Feito usando Python, Streamlit, e algumas integrações com Gemini IA através de sua API KEY.

---

## O que o Guardião faz

O Guardião é dividido em 3 partes principais:

- **Dashboard:** Exibe análises e gráficos interativos com dados golpes financeiros.
- **Informativo:** Explica de forma simples e direta os tipos de golpes mais comuns, como golpes do Pix, do boleto falso e mais.
- **Chatbot:** Um espaço para conversar com um agente virtual que ensina boas práticas para se proteger.

---

## Como rodar o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/o-guardiao.git
cd o-guardiao
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o projeto

```bash
streamlit run app.py
```

Pronto! O navegador vai abrir com o painel interativo. Se não abrir automaticamente, acesse `http://localhost:8501`.

---

## Estrutura do Projeto

```bash
o-guardiao/
├── app.py                  # arquivo principal com a interface do Streamlit
├── requirements.txt        # lista de bibliotecas necessárias
├── app.log                 # arquivo de log de execução dos codigos 
├── src/
│   ├── orchestrator.py     # o que orquestra a execução das pipelines dos agentes
│   ├── engineer.py         # codigo do agente engenherio de dados
│   ├── analyst.py          # codigo do analista de dados
│   ├── professor.py        # codigo do professor que sabe sobre golpes financeiros
│   └── utils.py            # funções dos logs
├── data/
│   └── analyst_data.parquet     # dados gerados pelo agente Analista a partir do arquivo do Engenheiro
│   └── engineer_data.parquet    # dados extraido pelo agente Engenheiro com prompt utilizando a Gemini API
```

---

## Observações

- Os dados vem de pouco em pouco quando vai executanto o orquestrador.py, mas pode alterar para fazer carga mais pesadas.

---

## Futuras melhorias

- Fazer uma tratação mais avançada de dados.
- Armazenar os dados em um banco como o Postgresql.
- Construção de um dashboard mais elaborado.
- Melhorar o agente Analise para criar metricas poderosas, como descobrir um perfil de alguem que cai mas em golpe.

---

## End

Desenvolvido com ajuda do Gemini e utilizando o conhecimento fornecido pela Imersão Alura + Google IA 2025.
Espero que gostem, e se quiserem darem alguma sugestão, fiquem a vontade!
