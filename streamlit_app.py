import streamlit as st
import pandas as pd
import time
import os

# ============================================
# Funções auxiliares
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


def salvar_csv():
    if st.session_state.tempos:
        df = pd.DataFrame(st.session_state.alunos)
        df["Tempo (s)"] = df["Número"].map(st.session_state.tempos)
        df = df.dropna().sort_values(by="Tempo (s)")
        df["Tempo"] = df["Tempo (s)"].apply(format_seconds)
        df.to_csv("resultados_corre_nicea.csv", index=False, encoding="utf-8")

# ============================================
# Configuração inicial e persistência
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
        salvar_csv()
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
            st.session_state.alunos = []
            if os.path.exists("resultados_corre_nicea.csv"):
                os.remove("resultados_corre_nicea.csv")

    if st.session_state.start_time:
        if st.session_state.running:
            elapsed = time.time() - st.session_state.start_time
            st.metric("Tempo Correndo", format_seconds(elapsed))
        else:
            ultimo = max(st.session_state.tempos.values(), default=0)
            st.metric("Tempo Correndo", format_seconds(ultimo))

    st.divider()

    if st.session_state.alunos:
        numeros_disponiveis = [a["Número"] for a in st.session_state.alunos if a["Número"] not in st.session_state.tempos]
        if numeros_disponiveis:
            numero = st.selectbox("Número do atleta:", numeros_disponiveis)
            if st.button("Registrar Tempo"):
                if st.session_state.start_time:
                    tempo_final = time.time() - st.session_state.start_time
                    st.session_state.tempos[numero] = tempo_final
                    salvar_csv()
                    atleta = next((a for a in st.session_state.alunos if a["Número"] == numero), None)
                    st.success(f"Tempo {format_seconds(tempo_final)} registrado para {numero} - {atleta['Nome'] if atleta else ''}")
    else:
        st.warning("Cadastre os alunos primeiro.")

    if st.session_state.tempos:
        tabela_tempos = [
            {"Número": num, "Tempo": format_seconds(t)} for num, t in st.session_state.tempos.items()
        ]
        st.dataframe(pd.DataFrame(tabela_tempos))

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
        if os.path.exists("resultados_corre_nicea.csv"):
            with open("resultados_corre_nicea.csv", "rb") as f:
                st.download_button("⬇️ Baixar CSV", data=f, file_name="resultados_corre_nicea.csv", mime="text/csv")
    else:
        st.info("Nenhum dado para exportar.")
import av
import cv2
import pandas as pd
import streamlit as st
from pyzbar import pyzbar
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import time

# Configuração WebRTC
RTC_CONFIGURATION = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# Inicializa session_state
if "tempos" not in st.session_state:
    st.session_state.tempos = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None

st.title("🏁 Chegada por QR Code")

# Função para processar frames da câmera
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    qrcodes = pyzbar.decode(img)

    for qr in qrcodes:
        atleta_numero = qr.data.decode("utf-8").strip()
        tempo_corrida = time.time() - st.session_state.start_time if st.session_state.start_time else 0

        # Salva tempo apenas se ainda não registrado
        if atleta_numero not in st.session_state.tempos:
            st.session_state.tempos[atleta_numero] = tempo_corrida
            st.success(f"⏱️ Tempo registrado para atleta {atleta_numero}: {tempo_corrida:.2f}s")

        # Desenha retângulo no vídeo
        (x, y, w, h) = qr.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, atleta_numero, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")

# Iniciar câmera
webrtc_streamer(
    key="qr-scanner",
    mode=WebRtcMode.RECVONLY,
    rtc_configuration=RTC_CONFIGURATION,
    video_frame_callback=video_frame_callback,
    media_stream_constraints={"video": True, "audio": False},
)

# Mostrar ranking parcial
if st.session_state.tempos:
    df = pd.DataFrame([
        {"Número": num, "Tempo (s)": tempo}
        for num, tempo in st.session_state.tempos.items()
    ]).sort_values("Tempo (s)")
    st.dataframe(df)
