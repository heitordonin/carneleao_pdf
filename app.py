import streamlit as st
import pdfplumber
import re
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
import os
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# === IDENTIDADE VISUAL ===
COR_PRIMARIA = "#0b485a"
COR_SECUNDARIA = "#01b7e9"
COR_DESTAQUE = "#e59500"

st.set_page_config(page_title="Carnê-Leão | Declara Psi", layout="centered")

# === ESTILO PARA IMPRESSÃO ===
st.markdown("""
    <style>
        @media print {
            body {
                -webkit-print-color-adjust: exact;
            }
            .element-container { 
                page-break-inside: avoid; 
            }
        }
        .spacer-below-filter {
            margin-bottom: 60px;
        }
        .resumo-margin-top {
            margin-top: 30px;
        }
    </style>
""", unsafe_allow_html=True)

# === TOPO COM LOGO E TÍTULO ===
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    try:
        caminho_logo = os.path.join(os.path.dirname(__file__), "logo.png")
        logo = Image.open(caminho_logo)
        st.image(logo, width=90)
    except:
        st.warning("Logo não encontrada.")

with col_titulo:
    st.markdown(f"""
        <div style='padding-top:10px'>
        <h1 style='color:{COR_PRIMARIA}; margin-bottom:0;'>Dashboard Carnê-Leão</h1>
        <p style='color:{COR_SECUNDARIA}; font-size:18px; margin-top:0;'>Análise tributária com alíquota efetiva</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border:1px solid #ccc'>", unsafe_allow_html=True)

# === UPLOAD PDF ===
meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
arquivo = st.file_uploader("📄 Envie o demonstrativo em PDF", type=["pdf"])

if arquivo:
    try:
        with pdfplumber.open(arquivo) as pdf:
            texto = pdf.pages[0].extract_text()

        dados_extraidos = {"nome": None, "cpf": None, "rendimentos_total": [], "deducao_considerada": [], "imposto_devido_I": []}

        nome_match = re.search(r"NOME:\s+(.*?)\s+DEMONSTRATIVO", texto)
        cpf_match = re.search(r"CPF:\s+([\d\.]+-\d+)", texto)
        rendimentos_match = re.search(r"Total\s+([\d\.,\s]+)\s+Deduções", texto)
        deducao_match = re.search(r"Dedução Considerada\s+([\d\.,\s]+)\s+Cálculo", texto)
        imposto_match = re.search(r"Imposto Devido I\s+([\d\.,\s]+)\s+Imposto Pago", texto)

        if nome_match: dados_extraidos["nome"] = nome_match.group(1)
        if cpf_match: dados_extraidos["cpf"] = cpf_match.group(1)
        if rendimentos_match:
            dados_extraidos["rendimentos_total"] = [val.replace(".", "").replace(",", ".") for val in rendimentos_match.group(1).split()]
        if deducao_match:
            dados_extraidos["deducao_considerada"] = [val.replace(".", "").replace(",", ".") for val in deducao_match.group(1).split()]
        if imposto_match:
            dados_extraidos["imposto_devido_I"] = [val.replace(".", "").replace(",", ".") for val in imposto_match.group(1).split()]

        dados_mensais = {}
        for i in range(12):
            rendimento = float(dados_extraidos["rendimentos_total"][i])
            deducao = float(dados_extraidos["deducao_considerada"][i])
            imposto = float(dados_extraidos["imposto_devido_I"][i])
            aliquota = round((imposto / rendimento) * 100, 2) if rendimento > 0 else 0.0

            dados_mensais[meses[i]] = {
                "rendimento": rendimento,
                "deducao": deducao,
                "imposto": imposto,
                "aliquota": aliquota
            }

        st.markdown(f"<h3 style='color:{COR_PRIMARIA}; margin-bottom:0.5em;'>🗓️ Selecione os meses</h3>", unsafe_allow_html=True)
        meses_selecionados = st.multiselect("Meses:", meses, default=meses)

        st.markdown("<div class='spacer-below-filter'></div>", unsafe_allow_html=True)

        rendimentos = [dados_mensais[mes]["rendimento"] for mes in meses_selecionados]
        deducoes = [dados_mensais[mes]["deducao"] for mes in meses_selecionados]
        impostos = [dados_mensais[mes]["imposto"] for mes in meses_selecionados]
        aliquotas = [dados_mensais[mes]["aliquota"] for mes in meses_selecionados]

        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown(f"<h4 class='resumo-margin-top' style='color:{COR_PRIMARIA}'>📋 Resumo</h4>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Recebido", f"R$ {sum(rendimentos):,.2f}")
        col_b.metric("Total de Impostos", f"R$ {sum(impostos):,.2f}")
        col_c.metric("Alíquota Média", f"{np.mean(aliquotas):.2f}%")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<h4 style='color:{COR_PRIMARIA}'>📊 Comparativo de Valores</h4>", unsafe_allow_html=True)
            fig_valores, ax = plt.subplots(figsize=(6, 3))
            x = np.arange(len(meses_selecionados))
            width = 0.25
            ax.bar(x - width, rendimentos, width, label='Rendimento', color=COR_PRIMARIA)
            ax.bar(x, deducoes, width, label='Deducao', color=COR_SECUNDARIA)
            ax.bar(x + width, impostos, width, label='Imposto', color=COR_DESTAQUE)
            ax.set_xticks(x)
            ax.set_xticklabels(meses_selecionados)
            ax.set_ylabel("R$")
            ax.legend()
            st.pyplot(fig_valores)

        with col2:
            st.markdown(f"<h4 style='color:{COR_PRIMARIA}'>📈 Evolução da Alíquota</h4>", unsafe_allow_html=True)
            fig_aliquota, ax2 = plt.subplots(figsize=(6, 3))
            ax2.plot(meses_selecionados, aliquotas, marker='o', color=COR_DESTAQUE)
            ax2.set_ylim(0, max(aliquotas + [20]) + 2)
            ax2.set_ylabel("%")
            ax2.grid(True)
            st.pyplot(fig_aliquota)

        st.markdown(f"<h4 style='color:{COR_PRIMARIA}'>🚦 Alíquota Efetiva Média</h4>", unsafe_allow_html=True)
        media_aliquota = round(np.mean(aliquotas), 2)

        fig_gauge = go.Figure(go.Indicator(
            number={'font': {'color': 'black'}},
            delta={'reference': 0, 'increasing': {'color': 'black'}, 'decreasing': {'color': 'black'}},
            mode="gauge+number+delta",
            value=media_aliquota,
            title={'text': "Alíquota Efetiva Média (%)", 'font': {'color': 'black'}},
            gauge={
                'axis': {'range': [0, 20]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [0, 10], 'color': "green"},
                    {'range': [10, 15], 'color': "yellow"},
                    {'range': [15, 20], 'color': "red"},
                ],
                'threshold': {
                    'line': {'color': COR_SECUNDARIA, 'width': 4},
                    'thickness': 0.5,
                    'value': media_aliquota
                }
            }
        ))
        fig_gauge.update_layout(height=300, paper_bgcolor='white')
        st.plotly_chart(fig_gauge)

    except Exception as e:
        st.error(f"Erro ao processar o PDF: {e}")
