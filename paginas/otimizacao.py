import io
import json
import re
from datetime import datetime

import matplotlib.pyplot as plt
import streamlit as st

from otimizacao.solver import resolver
from armazenamento.s3 import salvar_solucao, listar_solucoes, baixar_imagem, baixar_metadata

from utilidades.utils import _slug

# ─── Seção: Nova Solução ──────────────────────────────────────────────────────

def _secao_nova_solucao():
    nome_solucao = st.text_input(
        "Nome da Solução / Pedido",
        placeholder="Ex.: Pedido #2024-001 — Cliente XYZ",
        key="opt_nome",
    )

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Palete")
        comp_palete = st.number_input("Comprimento do palete (cm)", min_value=1.0, value=120.0, step=0.5, format="%.1f", key="opt_cp")
        larg_palete = st.number_input("Largura do palete (cm)",      min_value=1.0, value=100.0, step=0.5, format="%.1f", key="opt_lp")
    with col2:
        st.subheader("Caixa")
        comp_caixa = st.number_input("Comprimento da caixa (cm)", min_value=1.0, value=30.0, step=0.5, format="%.1f", key="opt_cc")
        larg_caixa = st.number_input("Largura da caixa (cm)",     min_value=1.0, value=20.0, step=0.5, format="%.1f", key="opt_lc")

    st.divider()

    if st.button("▶ Executar Otimização", type="primary", width="stretch", key="btn_exec"):
        if not nome_solucao.strip():
            st.warning("Informe o nome da solução / pedido.")
            st.session_state.pop("opt_resultado", None)
            return

        params = {
            "comprimento_palete_cm": comp_palete,
            "largura_palete_cm":     larg_palete,
            "comprimento_caixa_cm":  comp_caixa,
            "largura_caixa_cm":      larg_caixa,
        }

        with st.spinner("Executando otimização... ⏳"):
            solucoes, qtd_maxima, fig = resolver(comp_palete, larg_palete, comp_caixa, larg_caixa)

        if fig is None:
            st.error("O solver não encontrou solução viável para os parâmetros informados.")
            st.session_state.pop("opt_resultado", None)
            return

        usuario = st.session_state.usuario["nome_usuario"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefixo = f"{_slug(nome_solucao.strip())}_{timestamp}"

        meta = {
            "nome_solucao": nome_solucao.strip(),
            "timestamp": timestamp,
            "parametros": params,
            "qtd_caixas_sol1": len(solucoes[0]),
            "qtd_caixas_sol2": len(solucoes[1]) if len(solucoes) > 1 else 0,
        }

        # Renderiza a figura em memória e fecha para liberar recursos
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        img_bytes = buf.getvalue()

        chave_base = salvar_solucao(usuario, prefixo, img_bytes, meta)

        st.session_state["opt_resultado"] = {
            "img_bytes":    img_bytes,
            "chave_base":   chave_base,
            "qtd_sol1":     len(solucoes[0]),
            "qtd_sol2":     len(solucoes[1]) if len(solucoes) > 1 else 0,
            "qtd_maxima":   qtd_maxima,
            "nome_arquivo": f"{_slug(nome_solucao.strip())}_solucoes.png",
        }

    # Exibe resultado armazenado (persiste entre re-runs do Streamlit)
    if "opt_resultado" in st.session_state:
        res = st.session_state["opt_resultado"]
        st.success(
            f"Solução 1: **{res['qtd_sol1']} caixas**  |  "
            f"Solução 2: **{res['qtd_sol2']} caixas**  |  "
            f"Máximo teórico: **{res['qtd_maxima']}**"
        )
        st.image(res["img_bytes"], width="stretch")
        col_info, col_dl = st.columns([3, 1])
        col_info.caption(f"Salvo em S3: `{res['chave_base']}`")
        col_dl.download_button(
            label="⬇️ Baixar",
            data=res["img_bytes"],
            file_name=res["nome_arquivo"],
            mime="image/png",
            key="dl_nova",
        )


# ─── Seção: Histórico ─────────────────────────────────────────────────────────

def _secao_historico():
    usuario = st.session_state.usuario["nome_usuario"]
    solucoes = listar_solucoes(usuario)

    if not solucoes:
        st.info("Nenhuma solução salva para este usuário.")
        return

    selecionado = st.selectbox("Selecione uma solução salva", solucoes, key="hist_sel")

    meta = baixar_metadata(usuario, selecionado)
    if meta:
        st.subheader(meta.get("nome_solucao", selecionado))
        c1, c2, c3 = st.columns(3)
        c1.metric("Caixas — Sol. 1", meta.get("qtd_caixas_sol1", "—"))
        c2.metric("Caixas — Sol. 2", meta.get("qtd_caixas_sol2", "—"))
        ts = meta.get("timestamp", "")
        c3.metric("Data", f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else "—")
        with st.expander("Parâmetros"):
            st.json(meta.get("parametros", {}))

    img_bytes = baixar_imagem(usuario, selecionado)
    if img_bytes:
        st.image(img_bytes, width="stretch")
        st.download_button(
            label="⬇️ Baixar imagem",
            data=img_bytes,
            file_name=f"{selecionado}.png",
            mime="image/png",
            key="dl_hist",
        )
    else:
        st.warning("Imagem não encontrada no S3 para esta solução.")


# ─── Página principal ─────────────────────────────────────────────────────────

def pagina_otimizacao():
    st.header("📦 Otimização de Palete")

    aba_nova, aba_hist = st.tabs(["▶ Nova Solução", "📂 Histórico"])

    with aba_nova:
        _secao_nova_solucao()

    with aba_hist:
        _secao_historico()

