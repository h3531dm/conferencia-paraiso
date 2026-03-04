import streamlit as st
import pdfplumber
import re
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.title("🔎 Conferência TCPOS x Opera")

def extrair_tcpos(file):
    dados = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas = texto.split("\n")
                for linha in linhas:
                    # procura padrão de valor R$ XX,XX
                    valor_match = re.search(r'R\$\s?(\d+,\d+)', linha)
                    partes = linha.split()

                    if len(partes) >= 5 and valor_match:
                        cupom = partes[2]

                        if cupom.isdigit():
                            valor = float(valor_match.group(1).replace(",", "."))
                            dados[cupom] = valor

    return dados


def extrair_opera(file):
    dados = defaultdict(float)
    duplicidade = defaultdict(int)

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas = texto.split("\n")
                for linha in linhas:
                    nf_match = re.search(r'NF:(\d+)', linha)

                    if nf_match:
                        nf = nf_match.group(1)

                        # captura número decimal da linha (coluna debit)
                        numeros = re.findall(r'\d+\.\d+|\d+,\d+', linha)

                        if numeros:
                            # assume que o último número decimal da linha é o debit
                            valor_bruto = numeros[-1].replace(",", ".")
                            try:
                                valor = float(valor_bruto)
                                dados[nf] += valor
                                duplicidade[nf] += 1
                            except:
                                pass

    return dados, duplicidade


tcpos_file = st.file_uploader("Upload Relatório TCPOS", type="pdf")
opera_file = st.file_uploader("Upload Relatório Opera", type="pdf")

if tcpos_file and opera_file:

    tcpos = extrair_tcpos(tcpos_file)
    opera, duplicidade = extrair_opera(opera_file)

    resultados = []

    for cupom, valor_tcpos in tcpos.items():

        valor_opera = opera.get(cupom, 0)
        diferenca = round(valor_tcpos - valor_opera, 2)

        if cupom not in opera:
            status = "Não encontrado no Opera"
        elif diferenca != 0:
            status = "Valor divergente"
        elif duplicidade[cupom] > 1:
            status = "Duplicidade no Opera"
        else:
            status = "OK"

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
