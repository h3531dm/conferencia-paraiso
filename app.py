import streamlit as st
import pdfplumber
import re
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.title("🔎 Conferência TCPOS x Opera")

debug = st.checkbox("Modo Debug")

# ==============================
# TCPOS
# ==============================

def extrair_tcpos(file):
    dados = {}

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas = texto.split("\n")

                if debug:
                    st.write("TCPOS linhas:")
                    st.write(linhas[:40])

                for linha in linhas:
                    valor_match = re.search(r'(\d+,\d{2})', linha)
                    partes = linha.split()

                    if len(partes) >= 3 and valor_match:
                        cupom = partes[2]
                        if cupom.isdigit():
                            valor = float(valor_match.group(1).replace(",", "."))
                            dados[cupom] = valor

    return dados


# ==============================
# OPERA
# ==============================

def extrair_opera(file):
    dados = defaultdict(float)
    duplicidade = defaultdict(int)

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas = texto.split("\n")

                if debug:
                    st.write("Opera linhas:")
                    st.write(linhas[:40])

                for linha in linhas:
                    nf_match = re.search(r'NF:(\d+)', linha)

                    if nf_match:
                        nf = nf_match.group(1)
                        numeros = re.findall(r'\d+\.\d{2}', linha)

                        if numeros:
                            valor = float(numeros[-1])
                            dados[nf] += valor
                            duplicidade[nf] += 1

    return dados, duplicidade


# ==============================
# UPLOADS
# ==============================

tcpos_file = st.file_uploader("Upload Relatório TCPOS", type="pdf")
opera_file = st.file_uploader("Upload Relatório Opera", type="pdf")

tcpos = {}
opera = {}
duplicidade = {}

if tcpos_file:
    tcpos = extrair_tcpos(tcpos_file)

if opera_file:
    opera, duplicidade = extrair_opera(opera_file)

# ==============================
# SE TIVER OS DOIS → CONCILIA
# ==============================

if tcpos and opera:

    resultados = []

    for cupom, valor_tcpos in tcpos.items():

        valor_opera = opera.get(cupom, 0)
        diferenca = round(valor_tcpos - valor_opera, 2)

        if cupom not in opera:
            status = "❌ Não encontrado no Opera"
        elif diferenca != 0:
            status = "⚠️ Valor divergente"
        elif duplicidade[cupom] > 1:
            status = "🔁 Split no Opera"
        else:
            status = "✅ OK"

        resultados.append({
            "NF": cupom,
            "Valor TCPOS": valor_tcpos,
            "Valor Opera": valor_opera,
            "Diferença": diferenca,
            "Status": status
        })

    df = pd.DataFrame(resultados)

    st.subheader("Resumo")
    st.write(df["Status"].value_counts())

    st.subheader("Detalhamento")
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False)

    st.download_button(
        label="📥 Baixar Excel",
        data=output.getvalue(),
        file_name="conferencia_paraiso.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
