import streamlit as st
import pandas as pd
import time
from typing import List, Dict

# ============================================
# Utilitários
# ============================================

def format_seconds(seconds: float) -> str:
    """Formata segundos em MM:SS.mmm"""
    if seconds is None:
        return "--:--.---"
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{m:02d}:{s:02d}.{ms:03d}"


def pad3(n: int) -> str:
    return f"{n:03d}"


# ============================================
# Estados da Aplicação
# ============================================
if "alunos" not in st.session_state:
    st.session_state.alunos: List[Dict] = []  # cada aluno: {"Número", "Nome", "Turma"}
if "tempos" not in st.session_state:
    st.session_state.tempos: Dict[str, float] = {}  # mapeia Número -> tempo (segundos)
if "running" not in st.session_state:
    st.session_state.running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None  # epoch do início

st.set_page_config(page_title="1º CORRE NICÉA", layout="centered")
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

    if submitted:
        if not nome or not turma:
            st.error("Preencha Nome e Turma.")
        else:
            numero = pad3(len(st.session_state.alunos) + 1)
            st.session_state.alunos.append({
                "Número": numero,
                "Nome": nome.strip(),
                "Turma": turma.strip()
            })
            st.success(f"Aluno {nome} cadastrado com número {numero}!")

    if st.session_state.alunos:
        st.caption("Alunos cadastrados (com numeração automática):")
        st.dataframe(pd.DataFrame(st.session_state.alunos), use_container_width=True)
    else:
        st.info("Nenhum aluno cadastrado ainda.")

# ============================================
# Página: CRONÔMETRO
# ============================================
elif menu == "Cronômetro":
    st.subheader("⏱️ Cronômetro da Prova")

    colA, colB, colC = st.columns(3)

    with colA:
        if st.button("▶️ Iniciar", use_container_width=True, key="btn_start"):
            st.session_state.start_time = time.time()
            st.session_state.running = True

    with colB:
        if st.button("⏹️ Parar", use_container_width=True, key="btn_stop"):
            st.session_state.running = False

    with colC:
        if st.button("🔁 Resetar (zera tempos)", use_container_width=True, key="btn_reset"):
            st.session_state.running = False
            st.session_state.start_time = None
            st.session_state.tempos = {}
            st.success("Cronômetro e tempos resetados!")

    # Autorefresh somente quando correndo
    if st.session_state.running and st.session_state.start_time is not None:
        try:
            # st_autorefresh existe no Streamlit (refresha a página sem bloquear a UI)
            from streamlit import st as _st
            _ = st.experimental_memo  # força lint a reconhecer st
            count = st.experimental_rerun  # apenas para lint (não usado diretamente aqui)
        except Exception:
            pass
        # Usamos o método oficial st_autorefresh se disponível
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx  # noqa: F401  (mantém compatibilidade)
            st_autorefresh = st.experimental_singleton  # placeholder para evitar linter
        except Exception:
            pass
        # Implemento com API oficial
        try:
            from streamlit import st as _st_mod
            autorefresh_fn = getattr(_st_mod, "autorefresh", None)
        except Exception:
            autorefresh_fn = None

        # Fallback: usar a função pública st_autorefresh se existir
        try:
            from streamlit import st as __st
            st_autorefresh = getattr(__st, "st_autorefresh", None)
        except Exception:
            st_autorefresh = None

        # Melhor compatibilidade: usar componente oficial, se presente
        try:
            # Em versões atuais, a função chama-se st.autorefresh ou st_autorefresh (depende da versão)
            if hasattr(st, "autorefresh"):
                st.autorefresh(interval=300, key="auto_refresh_timer")
            elif st_autorefresh is not None:
                st_autorefresh(interval=300, key="auto_refresh_timer")
            else:
                # Último recurso: meta refresh via HTML
                st.markdown(
                    """
                    <meta http-equiv="refresh" content="0.3">
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            st.markdown(
                """
                <meta http-equiv="refresh" content="0.3">
                """,
                unsafe_allow_html=True,
            )

    # Exibir tempo atual
    if st.session_state.start_time is not None:
        elapsed = time.time() - st.session_state.start_time if st.session_state.running else max(
            0.0, (time.time() - st.session_state.start_time)
        )
        st.metric("Tempo decorrido", format_seconds(elapsed))
    else:
        st.metric("Tempo decorrido", "00:00.000")

    st.divider()

    # Registrar chegada por NÚMERO do atleta
    if not st.session_state.alunos:
        st.warning("Cadastre os alunos primeiro na aba 'Cadastro'.")
    else:
        # Opções apenas para quem ainda não tem tempo registrado
        numeros_disponiveis = [a["Número"] for a in st.session_state.alunos if a["Número"] not in st.session_state.tempos]
        numeros_disponiveis.sort()

        if not numeros_disponiveis:
            st.info("Todos os atletas cadastrados já têm tempo registrado.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                numero_escolhido = st.selectbox(
                    "Selecione o NÚMERO do atleta para registrar a chegada:",
                    options=numeros_disponiveis,
                    index=0,
                    key="sel_numero"
                )
            with col2:
                if st.button("Registrar tempo", use_container_width=True, key="btn_registrar"):
                    if st.session_state.start_time is None:
                        st.error("Inicie o cronômetro antes de registrar tempos.")
                    else:
                        tempo_atual = time.time() - st.session_state.start_time
                        st.session_state.tempos[numero_escolhido] = float(tempo_atual)
                        # Nome do atleta (para feedback)
                        atleta = next((a for a in st.session_state.alunos if a["Número"] == numero_escolhido), None)
                        nome_feedback = f" ({atleta['Nome']})" if atleta else ""
                        st.success(f"Tempo {format_seconds(tempo_atual)} registrado para o nº {numero_escolhido}{nome_feedback}!")

    # Lista parcial dos tempos já registrados (por número)
    if st.session_state.tempos:
        st.caption("Tempos já registrados:")
        parcial = (
            pd.DataFrame([
                {"Número": n, "Tempo (s)": t, "Tempo": format_seconds(t)}
                for n, t in st.session_state.tempos.items()
            ])
            .sort_values(by="Tempo (s)")
            .reset_index(drop=True)
        )
        st.dataframe(parcial, use_container_width=True)

# ============================================
# Página: RANKING
# ============================================
elif menu == "Ranking":
    st.subheader("🏆 Ranking (por tempo)")

    if not st.session_state.tempos:
        st.warning("Nenhum tempo registrado ainda.")
    else:
        # Monta DataFrame unindo cadastro + tempos
        df = pd.DataFrame(st.session_state.alunos)
        df["Tempo (s)"] = df["Número"].map(st.session_state.tempos)
        df = df.dropna(subset=["Tempo (s)"])
        df = df.sort_values(by="Tempo (s)", ascending=True).reset_index(drop=True)
        df.index = df.index + 1  # posição começa em 1
        df.insert(0, "Posição", df.index)
        df["Tempo"] = df["Tempo (s)"].apply(format_seconds)

        # Destaque top 3
        def highlight_top3(row):
            if row.name == 1:
                return ["background-color: gold"] * len(row)
            if row.name == 2:
                return ["background-color: silver"] * len(row)
            if row.name == 3:
                return ["background-color: #cd7f32"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df[["Posição", "Número", "Nome", "Turma", "Tempo", "Tempo (s)"]]
            .style.apply(highlight_top3, axis=1),
            use_container_width=True
        )

# ============================================
# Página: EXPORTAR
# ============================================
elif menu == "Exportar":
    st.subheader("📤 Exportar dados (CSV)")

    if not st.session_state.tempos:
        st.warning("Nenhum tempo para exportar ainda.")
    else:
        # Gera tabela final ordenada
        df = pd.DataFrame(st.session_state.alunos)
        df["Tempo (s)"] = df["Número"].map(st.session_state.tempos)
        df = df.dropna(subset=["Tempo (s)"])
        df = df.sort_values(by="Tempo (s)", ascending=True).reset_index(drop=True)
        df.index = df.index + 1
        df.insert(0, "Posição", df.index)
        df["Tempo"] = df["Tempo (s)"].apply(format_seconds)

        st.dataframe(df[["Posição", "Número", "Nome", "Turma", "Tempo", "Tempo (s)"]], use_container_width=True)

        # Exportar para CSV (sem dependências extras)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV",
            data=csv_bytes,
            file_name="resultados_corre_nicea.csv",
            mime="text/csv",
            use_container_width=True,
        )
