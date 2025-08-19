import streamlit as st
import pandas as pd
import time

# ---------- Inicialização de estados ----------
if "alunos" not in st.session_state:
    st.session_state.alunos = []
if "cronometro_inicio" not in st.session_state:
    st.session_state.cronometro_inicio = None
if "tempos" not in st.session_state:
    st.session_state.tempos = {}
if "correndo" not in st.session_state:
    st.session_state.correndo = False

st.set_page_config(page_title="1º CORRE NICÉA", layout="centered")
st.title("🏃‍♂️ 1º CORRE NICÉA")

menu = st.sidebar.radio("Navegação", ["Cadastro", "Cronômetro", "Ranking", "Exportar"])

# ---------- CADASTRO ----------
if menu == "Cadastro":
    st.subheader("📋 Cadastro dos alunos")

    with st.form("cadastro_form"):
        nome = st.text_input("Nome do aluno")
        turma = st.text_input("Turma")
        cadastrar = st.form_submit_button("Cadastrar")

    if cadastrar and nome and turma:
        numero = f"{len(st.session_state.alunos)+1:03}"
        st.session_state.alunos.append({"Número": numero, "Nome": nome, "Turma": turma})
        st.success(f"Aluno {nome} cadastrado com número {numero}!")

    if st.session_state.alunos:
        st.table(st.session_state.alunos)

# ---------- CRONÔMETRO ----------
elif menu == "Cronômetro":
    st.subheader("⏱️ Cronômetro")

    col1, col2 = st.columns(2)

    wit

