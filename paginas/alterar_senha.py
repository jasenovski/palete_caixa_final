import streamlit as st
from banco_dados.db import alterar_senha

def pagina_alterar_senha():
    st.header(":key: Alterar senha")
    usuario = st.session_state.usuario
    st.caption(f"Alterando senha de: **{usuario['razao_social']}** " \
               f"(`{usuario['nome_usuario']}`)")

    with st.form("form_mudar_senha"):
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar = st.text_input("Confirmar", type="password")
        salvar = st.form_submit_button("Salvar")

    if salvar:
        if len(nova_senha) < 6:
            st.warning(":warning: Senha deve ter 6 ou mais caracs")
        elif nova_senha != confirmar:
            st.error("Senhas não conferem")
        else:
            alterar_senha(usuario_id=usuario["id"],
                          nova_senha=nova_senha)
            st.success(":white_check_mark: Senha alterada com sucesso")

            st.session_state.usuario = None
            st.rerun()