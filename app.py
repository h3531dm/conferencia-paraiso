import streamlit as st
import pdfplumber
import re
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.title("🔎 Conferência TCPOS x Opera")
st.write("Upload dos relatórios do dia para conciliação automática.")

def extrair_tcpos(file):
    cupons = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas = texto.split("\n")
                for linha in linhas:
                    partes = linha.split()
                    if len(partes) >= 5:
                        cupom = partes[2]
                        valor = partes[-1].replace(",", ".")
                        if cupom.isdigit():
                            try:
                                cupons[cupom] = float(valor)
                            except:
                                pass
    return cupons

def extrair_opera(file):
    nfs = defaultdict(float)
    duplicidade = defaultdict(int)
    padrao_nf = r'NF:(\d+)'
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas = texto.split("\n")
                for linha in linhas:
                    nf_match = re.search(padrao_nf, linha)
                    if nf_match:
                        nf = nf_match.group(1)
                        partes = linha.split()
                        try:
                            valor = float(partes[-3])
                            nfs[nf] += valor
                            duplicidade[nf] += 1
                        except:
                            pass
    return nfs, duplicidade

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
            status = "Possível duplicidade"
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

    st.subheader("📊 Resultado")
    st.write(df["Status"].value_counts())

    st.subheader("📄 Detalhamento")
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="📥 Baixar Excel de Divergências",
        data=output.getvalue(),
        file_name="conferencia_paraiso.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
