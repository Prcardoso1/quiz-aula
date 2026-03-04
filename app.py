import streamlit as st
import pandas as pd
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
import unicodedata

st.set_page_config(page_title="Quiz da Aula", layout="centered")

st.title("📱 Quiz da Aula (ao vivo)")

# --- "Banco" simples em memória (MVP) ---
# Para rodar de verdade com turma, depois a gente troca por SQLite/Firestore.
if "answers_mc" not in st.session_state:
    st.session_state.answers_mc = []
if "answers_open" not in st.session_state:
    st.session_state.answers_open = []

# --- Sidebar: modo professor/aluno ---
mode = st.sidebar.radio("Modo", ["Aluno", "Professor"])
room = st.sidebar.text_input("Código da sala", value="ADS01")

# --- Perguntas (você edita aqui rápido) ---
QUESTION_MC = {
    "id": "q1",
    "text": "Qual camada do modelo OSI lida com endereçamento IP?",
    "options": ["Enlace", "Rede", "Transporte", "Aplicação"],
}
QUESTION_OPEN = {
    "id": "q2",
    "text": "Em UMA palavra, o que mais te confunde em redes?",
}

def normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # remove acentos
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

STOPWORDS_PT = {
    "a","o","os","as","de","do","da","dos","das","e","em","no","na","nos","nas",
    "um","uma","para","por","com","que","como","mais","menos","muito","pouco"
}

# ----------------- ALUNO -----------------
if mode == "Aluno":
    st.subheader("👤 Entrar e responder")
    name = st.text_input("Seu nome (ou apelido)", value="")

    with st.form("form_quiz", clear_on_submit=True):
        st.write(f"**{QUESTION_MC['text']}**")
        choice = st.radio("Escolha uma opção:", QUESTION_MC["options"], index=0)

        st.write(f"**{QUESTION_OPEN['text']}**")
        open_ans = st.text_input("Resposta curta:")

        submitted = st.form_submit_button("Enviar")

    if submitted:
        if not name.strip():
            st.error("Digite um nome/apelido.")
        else:
            st.session_state.answers_mc.append({"room": room, "name": name, "choice": choice})
            if open_ans.strip():
                st.session_state.answers_open.append({"room": room, "name": name, "text": open_ans})
            st.success("✅ Enviado! Você pode esperar o professor mostrar os resultados.")

# ----------------- PROFESSOR -----------------
else:
    st.subheader("📊 Painel do Professor")

    # Filtra só a sala atual
    df_mc = pd.DataFrame(st.session_state.answers_mc)
    df_open = pd.DataFrame(st.session_state.answers_open)

    if not df_mc.empty:
        df_mc = df_mc[df_mc["room"] == room]
    if not df_open.empty:
        df_open = df_open[df_open["room"] == room]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Respostas (múltipla escolha)", 0 if df_mc.empty else len(df_mc))
    with col2:
        st.metric("Respostas (abertas)", 0 if df_open.empty else len(df_open))

    st.divider()
    st.write(f"**Pergunta:** {QUESTION_MC['text']}")

    if df_mc.empty:
        st.info("Ainda não há respostas nesta sala.")
    else:
        counts = df_mc["choice"].value_counts().reindex(QUESTION_MC["options"]).fillna(0).astype(int)
        st.bar_chart(counts)

        st.write("**Detalhes:**")
        st.dataframe(df_mc[["name", "choice"]], use_container_width=True)

    st.divider()
    st.write(f"**Pergunta aberta:** {QUESTION_OPEN['text']}")

    if df_open.empty:
        st.info("Ainda não há respostas abertas nesta sala.")
    else:
        # monta word cloud
        all_text = " ".join(df_open["text"].astype(str).tolist())
        tokens = [normalize_text(t) for t in all_text.split()]
        tokens = [t for t in tokens if t and t not in STOPWORDS_PT and len(t) > 2]

        freq = Counter(tokens)

        if not freq:
            st.warning("Respostas abertas existem, mas sem palavras úteis após limpeza.")
        else:
            wc = WordCloud(width=900, height=450, background_color="white").generate_from_frequencies(freq)

            fig, ax = plt.subplots()
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

            st.write("**Top palavras:**")
            st.table(pd.DataFrame(freq.most_common(10), columns=["palavra", "freq"]))

    st.divider()
    if st.button("🧹 Limpar respostas desta sala"):
        st.session_state.answers_mc = [a for a in st.session_state.answers_mc if a["room"] != room]
        st.session_state.answers_open = [a for a in st.session_state.answers_open if a["room"] != room]
        st.success("Respostas apagadas (apenas desta sala).")