import streamlit as st
import pandas as pd
import time
from io import BytesIO

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

    with col1:
        if st.button("▶️ Iniciar Corrida"):
            st.session_state.cronometro_inicio = time.time()
            st.session_state.correndo = True
            st.success("Cronômetro iniciado!")

    with col2:
        if st.button("⏹️ Resetar Corrida"):
            st.session_state.cronometro_inicio = None
            st.session_state.tempos = {}
            st.session_state.correndo = False
            st.warning("Cronômetro resetado e tempos apagados!")

    if st.session_state.correndo and st.session_state.cronometro_inicio:
        tempo_atual = time.time() - st.session_state.cronometro_inicio
        st.metric("Tempo Correndo", f"{tempo_atual:.2f} s")
        st.button("🔄 Atualizar tempo")  # botão manual de refresh

    if st.session_state.cronometro_inicio:
        aluno_escolhido = st.selectbox("Selecione o aluno para registrar tempo:",
                                       [a["Nome"] for a in st.session_state.alunos])
        if st.button("Registrar Tempo"):
            tempo_final = time.time() - st.session_state.cronometro_inicio
            st.session_state.tempos[aluno_escolhido] = tempo_final
            st.success(f"Tempo de {tempo_final:.2f} segundos registrado para {aluno_escolhido}!")

    if st.session_state.tempos:
        st.write("📌 Tempos registrados:")
        df_temp = pd.DataFrame(list(st.session_state.tempos.items()), columns=["Aluno", "Tempo (s)"])
        st.table(df_temp)

# ---------- RANKING ----------
elif menu == "Ranking":
    st.subheader("🏆 Ranking")

    if st.session_state.tempos:
        df = pd.DataFrame([
            {"Número": a["Número"], "Nome": a["Nome"], "Turma": a["Turma"], "Tempo (s)": st.session_state.tempos.get(a["Nome"], None)}
            for a in st.session_state.alunos if a["Nome"] in st.session_state.tempos
        ])
        df = df.dropna().sort_values(by="Tempo (s)", ascending=True).reset_index(drop=True)

        # Destaque dos 3 primeiros
        def highlight_top3(row):
            if row.name == 0:
                return ['background-color: gold']*len(row)
            elif row.name == 1:
                return ['background-color: silver']*len(row)
            elif row.name == 2:
                return ['background-color: #cd7f32']*len(row)  # bronze
            return ['']*len(row)

        st.dataframe(df.style.apply(highlight_top3, axis=1))

    else:
        st.warning("Nenhum tempo registrado ainda.")

# ---------- EXPORTAR ----------
elif menu == "Exportar":
    st.subheader("📤 Exportar dados para Excel")

    if st.session_state.tempos:
        df = pd.DataFrame([
            {"Número": a["Número"], "Nome": a["Nome"], "Turma": a["Turma"], "Tempo (s)": st.session_state.tempos.get(a["Nome"], None)}
            for a in st.session_state.alunos
        ])
        df = df.dropna()

        st.dataframe(df)

        # Exportar para Excel usando BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Resultados")
        excel_bytes = output.getvalue()

        st.download_button(
            "⬇️ Baixar Excel",
            data=excel_bytes,
            file_name="resultados_corre_nicea.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("Nenhum dado disponível para exportar.")

