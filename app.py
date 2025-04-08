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
        valor_total_recebido = f"R$ {sum(rendimentos):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col_a.metric("Total Recebido", valor_total_recebido)

        valor_total_impostos = f"R$ {sum(impostos):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col_b.metric("Total de Impostos", valor_total_impostos)

        valor_aliquota_media = f"{np.mean(aliquotas):.2f}".replace(".", ",") + "%"
        col_c.metric("Alíquota Média", valor_aliquota_media)


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

        # === Planejamento Tributário ===
        st.markdown("<hr>", unsafe_allow_html=True)
        with st.expander("📊 Simular economia tributária como PJ"):
            st.markdown("Informe abaixo suas despesas pessoais para análise comparativa entre PF e PJ:")
            col1, col2, col3 = st.columns(3)
            with col1:
                gasto_terapia = st.number_input("Terapia (R$/mês)", min_value=0.0, format="%.2f")
            with col2:
                plano_saude = st.number_input("Plano de saúde (R$/mês)", min_value=0.0, format="%.2f")
            with col3:
                outros_saude = st.number_input("Outros gastos com saúde (R$/mês)", min_value=0.0, format="%.2f")

            if st.button("Calcular Comparativo PF vs PJ"):
                receita_mensal = sum(rendimentos) / len([v for v in rendimentos if v > 0])
                despesas_consultorio = sum(deducoes) / len([v for v in deducoes if v > 0])
                despesas_pessoais = gasto_terapia + plano_saude + outros_saude

                # Custo PF
                contabilidade_pf = 289.00
                inss_pf = 166.98  # fixo
                base_completa = receita_mensal - despesas_consultorio - despesas_pessoais - contabilidade_pf - inss_pf
                base_completa = max(base_completa, 0)
                ir_completa = 0
                if base_completa <= 2259.20:
                    ir_completa = 0
                elif base_completa <= 2826.65:
                    ir_completa = base_completa * 0.075 - 169.44
                elif base_completa <= 3751.05:
                    ir_completa = base_completa * 0.15 - 381.44
                elif base_completa <= 4664.68:
                    ir_completa = base_completa * 0.225 - 662.77
                else:
                    ir_completa = base_completa * 0.275 - 896.00
                ir_completa = max(ir_completa, 0)
                custo_total_pf_completa = contabilidade_pf + inss_pf + ir_completa

                deducao_simplificada = min(receita_mensal * 0.2, 16754.34 / 12)
                base_simplificada = receita_mensal - deducao_simplificada
                base_simplificada = max(base_simplificada, 0)
                ir_simplificada = 0
                if base_simplificada <= 2259.20:
                    ir_simplificada = 0
                elif base_simplificada <= 2826.65:
                    ir_simplificada = base_simplificada * 0.075 - 169.44
                elif base_simplificada <= 3751.05:
                    ir_simplificada = base_simplificada * 0.15 - 381.44
                elif base_simplificada <= 4664.68:
                    ir_simplificada = base_simplificada * 0.225 - 662.77
                else:
                    ir_simplificada = base_simplificada * 0.275 - 896.00
                ir_simplificada = max(ir_simplificada, 0)
                custo_total_pf_simplificada = contabilidade_pf + inss_pf + ir_simplificada

                if custo_total_pf_completa < custo_total_pf_simplificada:
                    custo_total_pf = custo_total_pf_completa
                    tipo_pf = "Completa"
                else:
                    custo_total_pf = custo_total_pf_simplificada
                    tipo_pf = "Simplificada"

                if receita_mensal <= 15000:
                    simples_pj = receita_mensal * 0.06
                elif receita_mensal <= 20000:
                    simples_pj = receita_mensal * 0.07
                else:
                    simples_pj = receita_mensal * 0.08

                prolabore = max(1518.00, receita_mensal * 0.28)
                inss_prolabore = prolabore * 0.11
                base_ir_prolabore = prolabore - inss_prolabore

                if base_ir_prolabore <= 2259.20:
                    irrf_prolabore = 0
                elif base_ir_prolabore <= 2826.65:
                    irrf_prolabore = base_ir_prolabore * 0.075 - 169.44
                elif base_ir_prolabore <= 3751.05:
                    irrf_prolabore = base_ir_prolabore * 0.15 - 381.44
                elif base_ir_prolabore <= 4664.68:
                    irrf_prolabore = base_ir_prolabore * 0.225 - 662.77
                else:
                    irrf_prolabore = base_ir_prolabore * 0.275 - 896.00
                irrf_prolabore = max(irrf_prolabore, 0)

                # Restituição do IR do Pro Labore
                if tipo_pf == "Completa":
                    base_restituicao = base_ir_prolabore - despesas_pessoais
                else:
                    base_restituicao = prolabore * 0.8

                if base_restituicao <= 2259.20:
                    ir_restituir = 0
                elif base_restituicao <= 2826.65:
                    ir_restituir = base_restituicao * 0.075 - 169.44
                elif base_restituicao <= 3751.05:
                    ir_restituir = base_restituicao * 0.15 - 381.44
                elif base_restituicao <= 4664.68:
                    ir_restituir = base_restituicao * 0.225 - 662.77
                else:
                    ir_restituir = base_restituicao * 0.275 - 896.00
                ir_restituir = max(ir_restituir, 0)

                contabilidade_pj = 489.00
                taxas_pj = 50.00
                # custo_total_pj = simples_pj + inss_prolabore + irrf_prolabore + contabilidade_pj + taxas_pj - ir_restituir
                custo_total_pj = simples_pj + inss_prolabore + irrf_prolabore + contabilidade_pj + taxas_pj

                st.markdown("## 💰 Resultado da Simulação")
                col_pf, col_pj = st.columns(2)
                with col_pf:
                    st.metric("Custo Anual PF", f"R$ {custo_total_pf * 12:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    st.caption(f"Custo mensal: R$ {custo_total_pf:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                with col_pj:
                    st.metric("Custo Anual PJ", f"R$ {custo_total_pj * 12:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    st.caption(f"Custo mensal: R$ {custo_total_pj:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                economia = (custo_total_pf - custo_total_pj) * 12
                if economia > 0:
                    st.success(f"💡 Migrar para PJ gera economia estimada de R$ {economia:,.2f} por ano")
                else:
                    st.info(f"🤔 No cenário atual, PF ainda é mais vantajoso em cerca de R$ {abs(economia):,.2f} ao ano")

                st.markdown("### 📊 Comparativo Visual")
                fig_comp = plt.figure(figsize=(6,3))
                plt.bar(["PF"], [custo_total_pf * 12], color=COR_PRIMARIA)
                plt.bar(["PJ"], [custo_total_pj * 12], color=COR_SECUNDARIA)
                plt.ylabel("Custo Anual (R$)")
                st.pyplot(fig_comp)

                # Debug: Exibir variáveis e fórmulas
                # st.markdown("### 🧾 Variáveis e Fórmulas utilizadas")
                st.markdown(f"**Receita média mensal:** R$ {receita_mensal:.2f}")
                st.markdown(f"**Despesas consultório médias:** R$ {despesas_consultorio:.2f}")
                st.markdown(f"**Despesas pessoais:** R$ {despesas_pessoais:.2f}")

                deducao_completa = despesas_consultorio + despesas_pessoais + contabilidade_pf + inss_pf
                st.markdown(f"**Dedução completa:** R$ {deducao_completa:.2f}")
                st.markdown(f"**Dedução simplificada:** R$ {deducao_simplificada:.2f}")
                st.markdown(f"**Base IR completa:** receita - dedução completa = R$ {base_completa:.2f}")
                st.markdown(f"**IR completa:** R$ {ir_completa:.2f}")
                st.markdown(f"**Base IR simplificada:** receita - dedução simplificada = R$ {base_simplificada:.2f}")
                st.markdown(f"**IR simplificada:** R$ {ir_simplificada:.2f}")
                st.markdown("---")
                st.markdown(f"**Simples Nacional:** R$ {simples_pj:.2f}")
                st.markdown(f"**Pró-labore:** R$ {prolabore:.2f}")
                st.markdown(f"**INSS sobre pró-labore:** R$ {inss_prolabore:.2f}")
                st.markdown(f"**Base IRRF pró-labore:** R$ {base_ir_prolabore:.2f}")
                st.markdown(f"**IRRF sobre pró-labore:** R$ {irrf_prolabore:.2f}")
                st.markdown(f"**Restituição IR pró-labore:** R$ {ir_restituir:.2f}")
                st.markdown(f"**Total PJ:** R$ {custo_total_pj:.2f}")

                # # st.markdown("### 🧾 Detalhamento da Restituição IR sobre Pró-labore")
# st.markdown(f"**Tipo de declaração:** {tipo_pf}")
# st.markdown(f"**Pró-labore:** R$ {prolabore:,.2f}")
# st.markdown(f"**INSS pró-labore (11%):** R$ {inss_prolabore:,.2f}")
# st.markdown(f"**Base de cálculo IRRF:** R$ {base_ir_prolabore:,.2f}")
# st.markdown(f"**IRRF retido sobre pró-labore:** R$ {irrf_prolabore:,.2f}")
# if tipo_pf == "Completa":
#     st.markdown(f"**Base de restituição (base - despesas pessoais):** R$ {base_restituicao:,.2f}")
# else:
#     st.markdown(f"**Base de restituição (pró-labore × 80%):** R$ {base_restituicao:,.2f}")
# st.markdown(f"**IR ajustado na declaração:** R$ {ir_restituir:,.2f}")
# st.markdown(f"**Valor restituído (IRRF - IR ajustado):** R$ {(irrf_prolabore - ir_restituir):,.2f}")

    except Exception as e:
        st.error(f"Erro ao processar o PDF: {e}")
