import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# ==========================
# Carregamento dos Códigos
# ==========================

@st.cache_data
def carregar_codigo(caminho):
    try:
        df = pd.read_csv(caminho)
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        st.warning(f"Erro ao ler {caminho}: {e}")
        return None

cp_df = carregar_codigo("cp.csv")   # Código Penal
cpp_df = carregar_codigo("cpp.csv") # Código de Processo Penal


def buscar_artigo(df, artigo_str):
    """
    Busca o artigo no DataFrame do código.
    Supõe que exista uma coluna com 'art' no nome (ex: 'artigo')
    e outra com 'texto' ou 'descricao' no nome.
    """
    if df is None or not artigo_str:
        return None

    # Tentativa de identificar coluna de artigo
    col_artigos = [c for c in df.columns if "art" in c.lower()]
    if not col_artigos:
        return None
    col_art = col_artigos[0]

    # Buscar texto
    resultado = df[df[col_art].astype(str).str.strip() == str(artigo_str).strip()]
    if resultado.empty:
        return None

    # Coluna de texto
    col_texto_candidatas = [c for c in df.columns if "texto" in c.lower() or "descr" in c.lower()]
    if col_texto_candidatas:
        col_texto = col_texto_candidatas[0]
    else:
        # Se não achar, mostra tudo
        col_texto = None

    if col_texto:
        return "\n\n".join(resultado[col_texto].astype(str).tolist())
    else:
        return resultado.to_string(index=False)


# ==========================
# Funções de Prazos
# ==========================

def ler_feriados_csv(arquivo):
    """Recebe um uploaded_file (CSV) e devolve um set de datas (date)."""
    if arquivo is None:
        return set()
    try:
        df = pd.read_csv(arquivo)
        # Tenta achar coluna chamada 'data' ou semelhante
        col_datas = [c for c in df.columns if "data" in c.lower()]
        if not col_datas:
            st.warning("Não encontrei coluna de datas no CSV de feriados. Esperado algo como 'data'.")
            return set()
        col = col_datas[0]
        datas = set()
        for valor in df[col].dropna():
            valor = str(valor).strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    d = datetime.strptime(valor, fmt).date()
                    datas.add(d)
                    break
                except ValueError:
                    continue
        return datas
    except Exception as e:
        st.warning(f"Erro ao ler CSV de feriados: {e}")
        return set()


def calcular_prazo(data_inicial, dias, tipo_contagem, feriados):
    """
    Calcula data final de prazo:
    - tipo_contagem: 'Corridos' ou 'Úteis'
    - Regra simplificada: exclui o dia do começo e conta a partir do dia seguinte
    """
    linhas = []
    if tipo_contagem == "Corridos":
        data_final = data_inicial + timedelta(days=dias)
        for i in range(0, dias + 1):
            d = data_inicial + timedelta(days=i)
            linhas.append({
                "Data": d,
                "Dia da semana": d.strftime("%A"),
                "Contado?": "Sim" if i > 0 else "Dia do início (não contado)"
            })
        return data_final, pd.DataFrame(linhas)

    # Dias úteis
    data_atual = data_inicial + timedelta(days=1)
    dias_contados = 0
    while dias_contados < dias:
        eh_fim_de_semana = data_atual.weekday() >= 5  # 5 = sábado, 6 = domingo
        eh_feriado = data_atual in feriados

        if not eh_fim_de_semana and not eh_feriado:
            dias_contados += 1
            contagem = "Dia útil contado"
        else:
            contagem = "Não contado (fim de semana/feriado)"

        linhas.append({
            "Data": data_atual,
            "Dia da semana": data_atual.strftime("%A"),
            "Contado?": contagem
        })

        data_atual += timedelta(days=1)

    data_final = data_atual - timedelta(days=1)
    df = pd.DataFrame(linhas)
    return data_final, df


# ==========================
# Funções ANPP
# ==========================

def analisar_anpp(inputs):
    motivos_nao = []

    if not inputs["sem_violencia"]:
        motivos_nao.append("O fato envolve violência ou grave ameaça à pessoa.")
    if not inputs["pena_minima_menor_quatro"]:
        motivos_nao.append("A pena mínima em abstrato não é inferior a 4 anos.")
    if not inputs["confissao"]:
        motivos_nao.append("Não há confissão formal e circunstanciada do investigado.")
    if inputs["reincidente_doloso"]:
        motivos_nao.append("O investigado é reincidente em crime doloso.")
    if inputs["crime_domestico"]:
        motivos_nao.append("O fato guarda relação com violência doméstica e familiar ou contra a mulher por razões da condição de sexo feminino.")
    if inputs["ja_teve_anpp"]:
        motivos_nao.append("O investigado já foi beneficiado por ANPP anterior em contexto semelhante (regra simplificada do app).")

    elegivel = len(motivos_nao) == 0

    if elegivel:
        parecer = (
            "À luz dos parâmetros simplificados adotados, o caso **é, em tese, elegível** ao Acordo de Não "
            "Persecução Penal (art. 28-A do CPP). Isso porque:\n\n"
            "- O fato é praticado sem violência ou grave ameaça;\n"
            "- A pena mínima em abstrato é inferior a 4 (quatro) anos;\n"
            "- Há confissão formal e circunstanciada do investigado;\n"
            "- Não há impeditivos relevantes (reincidência dolosa ou contexto de violência doméstica/familiar).\n\n"
            "⚠️ **Atenção:** trata-se de uma análise **didática e simplificada**. A aplicação concreta depende "
            "do exame integral dos autos, da interpretação jurisprudencial atualizada e da atuação do Ministério Público."
        )
    else:
        parecer = "Neste modelo simplificado, o caso **não é elegível** ao ANPP pelos seguintes motivos:\n\n"
        for m in motivos_nao:
            parecer += f"- {m}\n"
        parecer += (
            "\n⚠️ **Importante:** Esta é uma avaliação educacional, não substitui a análise jurídica concreta "
            "nem a decisão do Ministério Público ou do Judiciário."
        )

    return elegivel, parecer


# ==========================
# Funções Dosimetria
# ==========================

def calcular_pena_base(pena_min, pena_max, avaliacao_fatores):
    """
    pena_min, pena_max em anos (float).
    avaliacao_fatores: dict com valor em {'Desfavorável', 'Neutra', 'Favorável'}
    Regra simples: cada fator desfavorável adiciona 1/8 do intervalo,
                  cada favorável subtrai 1/8 do intervalo.
    """
    intervalo = pena_max - pena_min
    desfavoraveis = sum(1 for v in avaliacao_fatores.values() if v == "Desfavorável")
    favoraveis = sum(1 for v in avaliacao_fatores.values() if v == "Favorável")

    ajuste = (desfavoraveis - favoraveis) * (intervalo / 8.0)
    pena_base = pena_min + ajuste

    # Garante que fica entre mínimo e máximo
    pena_base = max(pena_min, min(pena_base, pena_max))
    return pena_base


def aplicar_causas(pena_base, causas):
    """
    causas: lista de dicts com campos:
       - tipo: 'Aumento' ou 'Diminuição'
       - fator: ex: 0.3333 para 1/3
    Aplica sequencialmente.
    """
    pena = pena_base
    for c in causas:
        if c["fator"] <= 0:
            continue
        if c["tipo"] == "Aumento":
            pena *= (1 + c["fator"])
        else:
            pena *= (1 - c["fator"])
    return pena


def formatar_anos(pena_anos):
    """
    Converte anos decimais em anos, meses aprox.
    (bem aproximado, só pra visualização didática)
    """
    anos = int(pena_anos)
    resto = pena_anos - anos
    meses = int(round(resto * 12))
    return anos, meses


def gerar_fundamentacao(pena_min, pena_max, avaliacao_fatores, pena_base, causas, pena_final):
    texto = []

    texto.append("**1ª Fase – Pena-base (art. 59 do CP)**\n")

    texto.append(
        f"Considerando os limites abstratos da pena, fixados entre **{pena_min:.2f}** e "
        f"**{pena_max:.2f}** anos, passa-se à análise das circunstâncias judiciais."
    )

    mapeamento_frases = {
        "culpabilidade": "a culpabilidade do agente",
        "antecedentes": "os antecedentes criminais",
        "conduta_social": "a conduta social",
        "personalidade": "a personalidade do agente",
        "motivos": "os motivos do crime",
        "circunstancias": "as circunstâncias do crime",
        "consequencias": "as consequências do crime",
        "comportamento_vitima": "o comportamento da vítima",
    }

    lista_descricoes = []
    for chave, valor in avaliacao_fatores.items():
        if valor == "Neutra":
            continue
        if valor == "Desfavorável":
            lista_descricoes.append(f"- {mapeamento_frases[chave]} mostra-se **desfavorável** ao réu;")
        else:
            lista_descricoes.append(f"- {mapeamento_frases[chave]} revela-se **favorável** ao réu;")

    if lista_descricoes:
        texto.append("\nNa forma do art. 59 do Código Penal, avaliam-se:\n")
        texto.extend(lista_descricoes)
    else:
        texto.append(
            "\nTodas as circunstâncias judiciais foram avaliadas como **neutras**, razão pela qual "
            "a pena-base é fixada próxima ao **mínimo legal**."
        )

    texto.append(
        f"\nDiante desse conjunto, a pena-base é fixada em **{pena_base:.2f} anos**."
    )

    # 2ª Fase / 3ª Fase simplificada
    if causas:
        texto.append("\n\n**2ª/3ª Fases – Causas de aumento e diminuição (modelo simplificado)**\n")
        for c in causas:
            sinal = "aumento" if c["tipo"] == "Aumento" else "diminuição"
            texto.append(
                f"- Aplica-se uma causa de **{sinal}** de aproximadamente **{c['fator']*100:.1f}%** "
                f"({c['descricao']})."
            )
        texto.append(
            f"\nApós a incidência sucessiva dessas causas, a pena definitiva resulta em **{pena_final:.2f} anos**."
        )
    else:
        texto.append(
            "\n\nNão foram consideradas, neste modelo didático, causas especiais de aumento ou diminuição, "
            "de modo que a pena provisória coincide com a pena-base."
        )

    texto.append(
        "\n\n⚠️ **Aviso importante:** Esta dosimetria é **meramente ilustrativa**, baseada em regras "
        "numéricas simplificadas para fins de estudo. Na prática forense, a fixação da pena "
        "depende de fundamentação qualitativa, da prova dos autos e da jurisprudência aplicável."
    )

    return "\n".join(texto)


# ==========================
# Interface Streamlit
# ==========================

st.set_page_config(page_title="JuriToolbox (Educacional)", layout="wide")

st.title("⚖️ JuriToolbox – Versão Educacional")
st.markdown(
    """
    **Aviso importante:** Este aplicativo tem finalidade **didática**.  
    Não substitui consulta a um advogado, ao Ministério Público ou à jurisprudência atualizada.  
    As regras aqui usadas são **simplificadas** e podem não refletir com precisão a prática forense.
    """
)

modulo = st.sidebar.radio(
    "Escolha o módulo:",
    [
        "1. Calculadora de Prazos Processuais (CPC/CPP)",
        "2. Elegibilidade ao ANPP (art. 28-A do CPP)",
        "3. Dosimetria Simplificada (art. 59 do CP)"
    ]
)

# ==========================
# Módulo 1 – Prazos
# ==========================

if modulo.startswith("1."):
    st.header("1. Calculadora de Prazos Processuais (CPC/CPP)")
    st.write("Conta dias corridos ou úteis, com opção de incluir feriados via CSV.")

    col1, col2 = st.columns(2)

    with col1:
        data_inicial = st.date_input("Data do início do prazo", value=date.today())
        dias = st.number_input("Quantidade de dias de prazo", min_value=0, step=1, value=15)

    with col2:
        tipo_contagem = st.radio("Tipo de contagem", ["Corridos", "Úteis"])
        feriados_csv = st.file_uploader(
            "CSV com feriados (coluna 'data' em formato YYYY-MM-DD ou DD/MM/YYYY)", 
            type=["csv"]
        )

    if st.button("Calcular prazo"):
        feriados = ler_feriados_csv(feriados_csv)
        data_final, df_linha_tempo = calcular_prazo(data_inicial, dias, tipo_contagem, feriados)

        st.success(f"Data final do prazo (modelo simplificado): **{data_final.strftime('%d/%m/%Y')}**")
        st.write("Linha do tempo do prazo:")
        st.dataframe(df_linha_tempo)

        st.info(
            "⚠️ Contagem de prazo baseada em regra **simplificada** (exclui o dia do começo, "
            "dias úteis = exclui fins de semana e datas do CSV de feriados). "
            "Confira sempre com o CPC/CPP atualizados e com a prática do tribunal."
        )

# ==========================
# Módulo 2 – ANPP
# ==========================

elif modulo.startswith("2."):
    st.header("2. Elegibilidade ao ANPP (art. 28-A do CPP)")

    st.markdown(
        """
        Este módulo faz um **checklist guiado**, inspirado no art. 28-A do CPP, para avaliar, de forma
        **simplificada e educacional**, se um caso **poderia** ser elegível a Acordo de Não Persecução Penal.
        """
    )

    col_esq, col_dir = st.columns(2)

    with col_esq:
        artigo_cp = st.text_input("Artigo do CP (opcional, para consulta de texto)", help="Ex.: 155, 171, 129...")

        if artigo_cp:
            texto_art = buscar_artigo(cp_df, artigo_cp)
            if texto_art:
                st.markdown("**Texto (resumo) do artigo no CP (conforme CSV):**")
                st.code(texto_art)
            else:
                st.warning("Não encontrei esse artigo no CSV do CP (ou colunas não batem).")

    with col_dir:
        st.subheader("Checklist simplificado")

        sem_violencia = st.checkbox("O fato é praticado **sem violência ou grave ameaça** à pessoa?")
        pena_minima_menor_quatro = st.checkbox("A pena mínima em abstrato é **inferior a 4 anos**?")
        confissao = st.checkbox("Há **confissão formal e circunstanciada** do investigado?")
        reincidente_doloso = st.checkbox("O investigado é **reincidente em crime doloso**?", value=False)
        crime_domestico = st.checkbox(
            "O fato está ligado a **violência doméstica ou familiar** / contra a mulher por razões do sexo feminino?",
            value=False
        )
        ja_teve_anpp = st.checkbox(
            "O investigado já foi beneficiado por ANPP em situação semelhante?",
            value=False
        )

    if st.button("Analisar elegibilidade (modelo didático)"):
        inputs = {
            "sem_violencia": sem_violencia,
            "pena_minima_menor_quatro": pena_minima_menor_quatro,
            "confissao": confissao,
            "reincidente_doloso": reincidente_doloso,
            "crime_domestico": crime_domestico,
            "ja_teve_anpp": ja_teve_anpp,
        }

        elegivel, parecer = analisar_anpp(inputs)

        if elegivel:
            st.success("Resultado do modelo: Caso **potencialmente elegível** ao ANPP (em tese).")
        else:
            st.error("Resultado do modelo: Caso **não elegível** ao ANPP, segundo este checklist simplificado.")

        st.markdown("---")
        st.markdown("### Parecer em linguagem natural (rascunho didático):")
        st.markdown(parecer)

# ==========================
# Módulo 3 – Dosimetria
# ==========================

elif modulo.startswith("3."):
    st.header("3. Dosimetria Simplificada (art. 59 do CP)")

    st.markdown(
        """
        Este módulo faz uma **simulação numérica** da dosimetria da pena, com base no art. 59 do CP,
        apenas para fins de estudo.  
        O usuário define os limites abstratos da pena e avalia as circunstâncias judiciais como
        **favoráveis, neutras ou desfavoráveis**.
        """
    )

    col_art, col_limites = st.columns(2)

    with col_art:
        artigo_cp = st.text_input("Artigo do CP (opcional, para consulta)", help="Ex.: 155, 157, 171...")

        if artigo_cp:
            texto_art = buscar_artigo(cp_df, artigo_cp)
            if texto_art:
                st.markdown("**Texto (resumo) do artigo no CP (conforme CSV):**")
                st.code(texto_art)
            else:
                st.warning("Não encontrei esse artigo no CSV do CP (ou colunas não batem).")

    with col_limites:
        pena_min = st.number_input("Pena mínima em abstrato (anos)", min_value=0.0, value=1.0, step=0.5)
        pena_max = st.number_input("Pena máxima em abstrato (anos)", min_value=0.0, value=5.0, step=0.5)

        if pena_max < pena_min:
            st.error("A pena máxima não pode ser menor que a pena mínima.")

    st.subheader("Avaliação das circunstâncias judiciais (art. 59 do CP)")
    opcoes = ["Desfavorável", "Neutra", "Favorável"]

    col1, col2, col3 = st.columns(3)

    with col1:
        culpabilidade = st.selectbox("Culpabilidade", opcoes, index=1)
        antecedentes = st.selectbox("Antecedentes", opcoes, index=1)
        conduta_social = st.selectbox("Conduta social", opcoes, index=1)

    with col2:
        personalidade = st.selectbox("Personalidade", opcoes, index=1)
        motivos = st.selectbox("Motivos", opcoes, index=1)
        circunstancias = st.selectbox("Circunstâncias", opcoes, index=1)

    with col3:
        consequencias = st.selectbox("Consequências", opcoes, index=1)
        comportamento_vitima = st.selectbox("Comportamento da vítima", opcoes, index=1)

    avaliacao_fatores = {
        "culpabilidade": culpabilidade,
        "antecedentes": antecedentes,
        "conduta_social": conduta_social,
        "personalidade": personalidade,
        "motivos": motivos,
        "circunstancias": circunstancias,
        "consequencias": consequencias,
        "comportamento_vitima": comportamento_vitima,
    }

    st.subheader("Causas de aumento/diminuição (modelo ilustrativo)")
    num_causas = st.number_input("Número de causas especiais a considerar", min_value=0, max_value=5, value=0, step=1)

    causas = []
    for i in range(num_causas):
        st.markdown(f"**Causa {i + 1}:**")
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            tipo = st.selectbox(f"Tipo {i+1}", ["Aumento", "Diminuição"], key=f"tipo_{i}")
        with c2:
            fator = st.number_input(
                f"Fator (ex: 0.333 para 1/3)", 
                min_value=0.0, max_value=5.0, value=0.3333, step=0.05,
                key=f"fator_{i}"
            )
        with c3:
            desc = st.text_input(
                f"Descrição (ex: concurso de pessoas, tentativa, etc.)", 
                key=f"desc_{i}"
            )
        causas.append({"tipo": tipo, "fator": fator, "descricao": desc})

    if st.button("Calcular dosimetria (modelo didático)"):
        if pena_max < pena_min:
            st.error("A pena máxima precisa ser maior ou igual à pena mínima.")
        else:
            pena_base = calcular_pena_base(pena_min, pena_max, avaliacao_fatores)
            pena_final = aplicar_causas(pena_base, causas)

            anos_base, meses_base = formatar_anos(pena_base)
            anos_final, meses_final = formatar_anos(pena_final)

            st.markdown("### Resultado numérico (simplificado)")
            st.write(f"**Pena-base:** {pena_base:.2f} anos ≈ {anos_base} ano(s) e {meses_base} mês(es).")
            st.write(f"**Pena após causas de aumento/diminuição:** {pena_final:.2f} anos ≈ {anos_final} ano(s) e {meses_final} mês(es).")

            fundamentacao = gerar_fundamentacao(pena_min, pena_max, avaliacao_fatores, pena_base, causas, pena_final)

            st.markdown("---")
            st.markdown("### Rascunho de fundamentação (texto didático)")
            st.markdown(fundamentacao)
