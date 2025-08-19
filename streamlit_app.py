import streamlit as st
import pandas as pd
import time

# ============================================
# Utilitários
# ============================================
def format_seconds(seconds: float) -> str:
    if seconds is None:
        return "--:--.---"
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{m:02d}:{s:02d}.{ms:03d}"


def pad3(n: int) -> str:
    return f"{n:03d}"


# ============================================
# Estados da Aplicação (com defaults persistentes)
# ============================================
st.set_page_config(page_title="1º CORRE NICÉA", layout="centered")

if "alunos" not in st.session_state:
    st.session_state.alunos = []
if "tempos" not in st.session_state:
    st.session_state.tempos = {}
if "running" not in st.session_state:
    st.session_state.running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

st.title("🏃‍♂️ 1º CORRE NICÉA")
menu = st.sidebar.radio("Navegação", ["Cadastro", "Cronômetro", "Ranking", "Exportar"], index=0)

# ============================================
# Página: CADASTRO
# ============================================
if menu == "Cadastro":
    st.subheader("📋 Cadastro dos alunos")

    with st.form("cadastro_form"):
        nome = st.text_input("Nome do aluno")
        turma = st.text_input("Turma")
        submitted = st.form_submit_button("Cadastrar")

    if submitted and nome and turma:
        numero = pad3(len(st.session_state.alunos) + 1)
        st.session_state.alunos.append({
            "Número": numero,
            "Nome": nome.strip(),
            "Turma": turma.strip()
        })
        st.success(f"Aluno {nome} cadastrado com número {numero}!")

    if st.session_state.alunos:
        st.dataframe(pd.DataFrame(st.session_state.alunos), use_container_width=True)

# ============================================
# Página: CRONÔMETRO
# ============================================
elif menu == "Cronômetro":
    st.subheader("⏱️ Cronômetro da Prova")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Iniciar Corrida"):
            st.session_state.start_time = time.time()
            st.session_state.running = True
    with col2:
        if st.button("⏹️ Parar"):
            st.session_state.running = False
    with col3:
        if st.button("🔁 Resetar Tudo"):
            st.session_state.start_time = None
            st.session_state.running = False
            st.session_state.tempos = {}

    if st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time if st.session_state.running else st.session_state.tempos.get("_ultimo_tempo", 0)
        st.metric("Tempo Correndo", format_seconds(elapsed))

    st.divider()

    if st.session_state.alunos:
        numeros_disponiveis = [a["Número"] for a in st.session_state.alunos if a["Número"] not in st.session_state.tempos]
        if numeros_disponiveis:
            numero = st.selectbox("Número do atleta:", numeros_disponiveis)
            if st.button("Registrar Tempo"):
                if st.session_state.start_time:
                    tempo_final = time.time() - st.session_state.start_time
                    st.session_state.tempos[numero] = tempo_final
                    atleta = next((a for a in st.session_state.alunos if a["Número"] == numero), None)
                    st.success(f"Tempo {format_seconds(tempo_final)} registrado para {numero} - {atleta['Nome'] if atleta else ''}")
    else:
        st.warning("Cadastre os alunos primeiro.")

    if st.session_state.tempos:
        st.dataframe(pd.DataFrame([
            {"Número": num, "Tempo": format_seconds(t)} for num, t in st.session_state.tempos.items()
        ]))

# ============================================
# Página: RANKING
# ============================================
elif menu == "Ranking":
    st.subheader("🏆 Ranking")

    if st.session_state.tempos:
        df = pd.DataFrame(st.session_state.alunos)
        df["Tempo (s)"] = df["Número"].map(st.session_state.tempos)
        df = df.dropna().sort_values(by="Tempo (s)")
        df["Tempo"] = df["Tempo (s)"].apply(format_seconds)
        st.dataframe(df)
    else:
        st.info("Nenhum tempo registrado ainda.")

# ============================================
# Página: EXPORTAR
# ============================================
elif menu == "Exportar":
    st.subheader("📤 Exportar dados (CSV)")

    if st.session_state.tempos:
        df = pd.DataFrame(st.session_state.alunos)
        df["Tempo (s)"] = df["Número"].map(st.session_state.tempos)
        df = df.dropna().sort_values(by="Tempo (s)")
        df["Tempo"] = df["Tempo (s)"].apply(format_seconds)

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar CSV", data=csv_bytes, file_name="resultados_corre_nicea.csv", mime="text/csv")
    else:
        st.info("Nenhum dado para exportar.")
