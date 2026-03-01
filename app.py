import streamlit as st
from groq import Groq
from pypdf import PdfReader
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AI Trainer Pro", page_icon="🚀", layout="wide")

# --- API ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SESSION STATE ---
if "sop_teks" not in st.session_state:
    st.session_state.sop_teks = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "skor" not in st.session_state:
    st.session_state.skor = 0

if "mode" not in st.session_state:
    st.session_state.mode = "quiz"  # quiz / roleplay

if "roleplay_active" not in st.session_state:
    st.session_state.roleplay_active = False

if "scenario" not in st.session_state:
    st.session_state.scenario = "Angry Customer"

if "level" not in st.session_state:
    st.session_state.level = "easy"

if "company_type" not in st.session_state:
    st.session_state.company_type = "Retail"

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"

if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 1

if "theme" not in st.session_state:
    st.session_state.theme = "auto"  # auto / light / dark

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

if "edit_text" not in st.session_state:
    st.session_state.edit_text = ""

# --- APPLY THEME ---
def apply_theme():
    if st.session_state.theme == "light":
        st.markdown("""
        <style>
        .stApp {
            background-color: white;
            color: black;
        }
        </style>
        """, unsafe_allow_html=True)

    elif st.session_state.theme == "dark":
        st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

st.markdown("""
<style>

.chat-wrapper {
    position: relative;
    margin-bottom: 10px;
}

.edit-btn {
    position: absolute;
    bottom: -5px;
    right: -5px;
    background: rgba(0,0,0,0.05);
    border-radius: 50%;
    width: 32px;
    height: 32px;
    border: none;
    font-size: 16px;
    cursor: pointer;
}

.edit-btn:hover {
    background: rgba(0,0,0,0.15);
}

</style>
""", unsafe_allow_html=True)

# inisialisasi chat pertama
if st.session_state.current_chat_id not in st.session_state.all_chats:
    st.session_state.all_chats[st.session_state.current_chat_id] = []

# --- AI FUNCTION ---
def panggil_ai(teks_input, konteks_sop):

    chat_id = st.session_state.current_chat_id
    chat_list = st.session_state.all_chats[chat_id]

    # Prevent duplicate user message when regenerating
    if not chat_list or chat_list[-1]["content"] != teks_input:
        chat_list.append({
            "role": "user",
            "content": teks_input
        })

    # ROLEPLAY MODE
    if st.session_state.mode == "roleplay":

        st.session_state.conversation_history.append({
            "role": "user",
            "content": teks_input
        })

        if "END ROLEPLAY" in teks_input.upper():

            prompt = f"""
            You are an AI Trainer.

            Analyze this conversation:
            {st.session_state.conversation_history}

            Give score (0-100):
            - Communication
            - Empathy
            - Problem Solving
            - Persuasion

            Then calculate final score.

            Give:
            1. Strength
            2. Mistakes
            3. Better answer example
            4. Tips
            """

        else:
            prompt = f"""
            You are a CUSTOMER.

            SCENARIO:
            Company: {st.session_state.company_type}
            Scenario: {st.session_state.scenario}
            Level: {st.session_state.level}

            RULES:
            - Act like human
            - Show emotion
            - No explanation
            - Stay in role

            Conversation:
            {st.session_state.conversation_history}
            """

    # QUIZ MODE
    else:
        prompt = f"""
        Kamu adalah Mentor Training Profesional.
        Gunakan SOP ini: {konteks_sop}

        - Buat soal jika diminta
        - Jika benar: 'Tepat sekali!'
        - Jika salah: 'Kurang tepat'
        """

    # CALL AI
    riwayat = [{"role": "system", "content": prompt}]

    for m in st.session_state.all_chats[st.session_state.current_chat_id]:
        riwayat.append(m)

    response = client.chat.completions.create(
        messages=riwayat,
        model="llama-3.3-70b-versatile"
    )

    hasil = response.choices[0].message.content

    # simpan ke chat aktif
    st.session_state.all_chats[st.session_state.current_chat_id].append({
    "role": "assistant",
    "content": hasil
    })

    # simpan history roleplay
    if st.session_state.mode == "roleplay":
        st.session_state.conversation_history.append({
            "role": "assistant",
            "content": hasil
        })

    # scoring quiz
    if "Tepat sekali" in hasil:
        st.session_state.skor += 1

# --- REGENERATE RESPONSE AFTER EDIT ---
def regenerate_from_index(edit_index):

    chat_id = st.session_state.current_chat_id
    chat_history = st.session_state.all_chats[chat_id]

    # keep messages until edited index
    new_history = chat_history[:edit_index + 1]

    # reset chat
    st.session_state.all_chats[chat_id] = new_history

    # reset roleplay history if needed
    if st.session_state.mode == "roleplay":
        st.session_state.conversation_history = []

        for msg in new_history:
            st.session_state.conversation_history.append(msg)

    # ambil pesan terakhir user
    last_user_message = new_history[-1]["content"]

    # panggil ulang AI
    panggil_ai(last_user_message, st.session_state.sop_teks)

# --- SIDEBAR ---
# --- SIDEBAR ---
with st.sidebar:

    # =========================
    # 🔍 SEARCH
    # =========================
    st.markdown("### 🔍 Telusuri Pesan")
    search_query = st.text_input("Cari pesan...")

    results = []

    if search_query:
        for chat_id, messages in st.session_state.all_chats.items():
            for m in messages:
                if search_query.lower() in m["content"].lower():
                    results.append((chat_id, m["content"]))

        if results:
            for chat_id, text in results:
                st.write(f"📌 {chat_id}: {text[:50]}...")
        else:
            st.write("Tidak ditemukan")


    # =========================
    # ✏️ NEW CHAT
    # =========================
    if st.button("✏️ Percakapan baru"):
        st.session_state.chat_counter += 1
        new_chat_id = f"chat_{st.session_state.chat_counter}"

        st.session_state.current_chat_id = new_chat_id
        st.session_state.all_chats[new_chat_id] = []

        st.rerun()


    # =========================
    # 📜 HISTORY
    # =========================
    st.markdown("### 📜 Percakapan")

    for chat_id in st.session_state.all_chats.keys():
        if st.button(f"💬 {chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.rerun()


    # =========================
    # PROFIL
    # =========================
   
    st.markdown("### 🎨 Tampilan")
   
    theme_option = st.selectbox(
        "Pilih Tema",
        ["Auto", "Light", "Dark"]
    )
   
    if theme_option == "Light":
        st.session_state.theme = "light"
    elif theme_option == "Dark":
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "auto"

    st.header("👤 Profil")
    nama_user = st.text_input("Nama")

    st.header("🧠 Mode")

    mode = st.selectbox("Pilih Mode", ["Quiz SOP", "Roleplay Training"])

    if mode == "Roleplay Training":
        st.session_state.mode = "roleplay"
    else:
        st.session_state.mode = "quiz"


    # =========================
    # ROLEPLAY
    # =========================
    if st.session_state.mode == "roleplay":

        st.header("🎭 Roleplay Settings")

        st.session_state.company_type = st.selectbox(
            "Tipe Perusahaan",
            ["Retail", "Restaurant", "Bank", "E-commerce"]
        )

        st.session_state.scenario = st.selectbox(
            "Scenario",
            ["Angry Customer", "Upselling", "Complaint Handling", "Problem Solving"]
        )

        st.session_state.level = st.selectbox("Level", ["easy", "medium", "hard"])

        if st.button("🎬 Mulai Roleplay"):
            st.session_state.roleplay_active = True
            st.session_state.conversation_history = []

            panggil_ai("START ROLEPLAY", st.session_state.sop_teks)
            st.rerun()


    st.metric("🎯 Skor", st.session_state.skor)

    st.markdown('</div>', unsafe_allow_html=True)


    # =========================
    # SOP
    # =========================
    st.header("📂 SOP")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file:
        sop_teks = ""
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            sop_teks += page.extract_text()

        st.session_state.sop_teks = sop_teks
        st.success("SOP berhasil dibaca")

        if st.button("Buat Kuis"):
            panggil_ai("Buat 1 soal pilihan ganda", st.session_state.sop_teks)
            st.rerun()


    st.markdown("---")


    # =========================
    # KIRIM SKOR
    # =========================
    if st.button("🚀 Kirim Skor"):
        if nama_user:
            df_baru = pd.DataFrame({
                "Nama": [nama_user],
                "Skor": [st.session_state.skor],
                "Tanggal": [datetime.now()]
            })

            url = st.secrets["connections"]["gsheets"]["spreadsheet"]

            try:
                df_lama = conn.read(spreadsheet=url, worksheet="Sheet1")
            except:
                df_lama = pd.DataFrame()

            df = pd.concat([df_lama, df_baru])
            conn.update(spreadsheet=url, worksheet="Sheet1", data=df)

            st.success("Terkirim!")
            st.balloons()
        else:
            st.warning("Isi nama dulu!")

# --- MAIN UI ---
st.title("🚀 AI Trainer")
st.caption("Training karyawan berbasis AI")
st.divider()

st.subheader("💬 AI Training Chat")

if st.session_state.mode == "roleplay":
    st.info("💡 Ketik 'END ROLEPLAY' untuk melihat penilaian")

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

chat = st.session_state.all_chats.get(st.session_state.current_chat_id, [])

for i, msg in enumerate(chat):
    role = msg["role"]
    content = msg["content"]

    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

    with st.chat_message(role):

        if role == "user":

            if st.session_state.get("edit_index") == i:
                new_text = st.text_area(
                    "Edit pesan:",
                    value=content,
                    key=f"edit_{i}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("💾", key=f"save_{i}"):
                        chat[i]["content"] = new_text
                        st.session_state.edit_index = None
                        regenerate_from_index(i)
                        st.rerun()

                with col2:
                    if st.button("❌", key=f"cancel_{i}"):
                        st.session_state.edit_index = None
                        st.rerun()

            else:
                st.write(content)

        else:
            st.write(content)

    # floating edit button (only user message)
    if role == "user" and st.session_state.get("edit_index") != i:
        if st.button("🖊️", key=f"floating_edit_{i}"):
            st.session_state.edit_index = i
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- INPUT ---
prompt = st.chat_input("💬 Tulis pertanyaan atau jawab kuis...")

if prompt:
    if st.session_state.mode == "roleplay":
        panggil_ai(prompt, st.session_state.sop_teks)
        st.rerun()

    else:
        if st.session_state.sop_teks:
            panggil_ai(prompt, st.session_state.sop_teks)
            st.rerun()
        else:
            st.warning("Upload SOP dulu!")
