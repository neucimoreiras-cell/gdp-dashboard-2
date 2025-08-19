import streamlit as st
import pandas as pd
import time
import os
import av
import cv2
from pyzbar import pyzbar
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# ===============================
# CONFIGURAÇÃO WEBRTC (câmera)
# ===============================
RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

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

menu = st.sidebar.radio("Menu", ["Cadastro", "Cronômetro", "Chegada Manual", "Chegada QR", "Ranking", "Exportar"])

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
# CHEGADA MANUAL
# -------------------------------
elif menu == "Chegada Manual":
    st.header("✍️ Registrar Chegada Manualmente")
    atleta_numero = st.text_input("Número do atleta")
    if st.button("Registrar Chegada"):
        if atleta_numero and st.session_state.running:
            tempo_corrida = time.time() - st.session_state.start_time
            st.session_state.tempos[atleta_numero] = tempo_corrida
            salvar_csv()
            st.success(f"⏱️ Tempo registrado para atleta {atleta_numero}: {tempo_corrida:.2f}s")

    if st.session_state.tempos:
        df = pd.DataFrame([
            {"Número": num, "Tempo (s)": tempo}
            for num, tempo in st.session_state.tempos.items()
        ]).sort_values("Tempo (s)")
        st.subheader("Tempos Registrados")
        st.dataframe(df)

# -------------------------------
# CHEGADA POR QR CODE
# -------------------------------
elif menu == "Chegada QR":
    st.header("📷 Registrar Chegada via QR Code")

    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        qrcodes = pyzbar.decode(img)

        for qr in qrcodes:
            atleta_numero = qr.data.decode("utf-8").strip()
            tempo_corrida = time.time() - st.session_state.start_time if st.session_state.start_time else 0

            if atleta_numero not in st.session_state.tempos:
                st.session_state.tempos[atleta_numero] = tempo_corrida
                salvar_csv()
                st.success(f"⏱️ Tempo registrado para atleta {atleta_numero}: {tempo_corrida:.2f}s")

            (x, y, w, h) = qr.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, atleta_numero, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    webrtc_streamer(
        key="qr-scanner",
        mode=WebRtcMode.RECVONLY,
        rtc_configuration=RTC_CONFIGURATION,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
    )

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

