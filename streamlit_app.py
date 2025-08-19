import streamlit as st
import pandas as pd
import time
import os

# ===============================
# INICIALIZA SESSION STATE
# ===============================
if "alunos" not in st.session_state:
    st.session_state.alunos = []
if "tempos" not in st.session_state:
    st.session_state.tempos = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "running" not in st.session_state:
    st.session_state.running = False

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def salvar_csv():
    df = pd.DataFrame(st.session_state.alunos)
    if st.session_state.tempos:
        tempos_df = pd.DataFrame([
            {"Número": num, "Tempo (s)": tempo}
            for num, tempo in st.session_state.tempos.items()
        ])
        df = df.merge(tempos_df, on="Número", how="left")
    df.to_csv("resultados_corrida.csv", index=False)

def iniciar_corrida():
    st.session_state.start_time = time.time()
    st.session_state.running = True

def resetar_tudo():
    st.session_state.alunos = []
    st.session_state.tempos = {}
    st.session_state.start_time = None
    st.session_state.running = False
    if os.path.exists("resultados_corrida.csv"):
        os.remove("resultados_corrida.csv")

# ===============================
# INTERFACE PRINCIPAL
# ===============================
st.title("🏃‍♂️ 1º CORRE NICÉA - Organização da Corrida Escolar")

menu = st.sidebar.radio("Menu", ["Cadastro", "Cronômetro", "Chegada Painel", "Ranking", "Exportar"])

# -------------------------------
# CADASTRO DE ATLETAS
# -------------------------------
if menu == "Cadastro":
    st.header("📋 Cadastro de Atletas")
    with st.form("cadastro_form"):
        nome = st.text_input("Nome do aluno")
        turma = st.text_input("Turma")
        submitted = st.form_submit_button("Cadastrar")

        if submitted and nome and turma:
            numero = f"{len(st.session_state.alunos)+1:03d}"
            st.session_state.alunos.append({"Número": numero, "Nome": nome, "Turma": turma})
            salvar_csv()
            st.success(f"✅ Atleta {nome} cadastrado com número {numero}")

    if st.session_state.alunos:
        st.subheader("Atletas Cadastrados")
        st.dataframe(pd.DataFrame(st.session_state.alunos))

# -------------------------------
# CRONÔMETRO
# -------------------------------
elif menu == "Cronômetro":
    st.header("⏱️ Controle da Corrida")
    if not st.session_state.running:
        if st.button("Iniciar Corrida"):
            iniciar_corrida()
    else:
        tempo_atual = time.time() - st.session_state.start_time
        st.metric("Tempo Decorrido", f"{tempo_atual:.2f} segundos")

    if st.button("Resetar Tudo"):
        resetar_tudo()
        st.warning("⚠️ Todos os dados foram apagados!")

# -------------------------------
# CHEGADA PELO PAINEL DE BOTÕES
# -------------------------------
elif menu == "Chegada Painel":
    st.header("🎛️ Registrar Chegada (Painel de Botões)")

    if not st.session_state.running:
        st.warning("⚠️ O cronômetro ainda não foi iniciado!")
    else:
        st.info("Clique no número do atleta quando ele cruzar a linha de chegada:")

        cols = st.columns(5)  # 5 botões por linha
        for i, atleta in enumerate(st.session_state.alunos):
            numero = atleta["Número"]
            col = cols[i % 5]
            if col.button(numero):
                if numero not in st.session_state.tempos:
                    tempo_corrida = time.time() - st.session_state.start_time
                    st.session_state.tempos[numero] = tempo_corrida
                    salvar_csv()
                    st.success(f"⏱️ Tempo registrado para atleta {numero}: {tempo_corrida:.2f}s")

    if st.session_state.tempos:
        df = pd.DataFrame([
            {"Número": num, "Tempo (s)": tempo}
            for num, tempo in st.session_state.tempos.items()
        ]).sort_values("Tempo (s)")
        df = df.merge(pd.DataFrame(st.session_state.alunos), on="Número", how="left")
        st.subheader("Tempos Registrados")
        st.dataframe(df[["Número", "Nome", "Turma", "Tempo (s)"]])

# -------------------------------
# RANKING
# -------------------------------
elif menu == "Ranking":
    st.header("🥇 Ranking Geral")
    if st.session_state.tempos:
        df = pd.DataFrame([
            {"Número": num, "Tempo (s)": tempo}
            for num, tempo in st.session_state.tempos.items()
        ]).sort_values("Tempo (s)")
        df = df.merge(pd.DataFrame(st.session_state.alunos), on="Número", how="left")
        df["Posição"] = range(1, len(df)+1)
        st.dataframe(df[["Posição", "Número", "Nome", "Turma", "Tempo (s)"]])
    else:
        st.info("Nenhum tempo registrado ainda.")

# -------------------------------
# EXPORTAÇÃO
# -------------------------------
elif menu == "Exportar":
    st.header("💾 Exportar Resultados")
    if os.path.exists("resultados_corrida.csv"):
        with open("resultados_corrida.csv", "rb") as f:
            st.download_button("⬇️ Baixar CSV", f, file_name="resultados_corrida.csv")
    else:
        st.info("Ainda não há resultados para exportar.")

