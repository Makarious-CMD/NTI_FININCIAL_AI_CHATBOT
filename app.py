import streamlit as st
from gradio_client import Client
import os
import tempfile # <-- تمت الإضافة هنا

# 1. Page Config
st.set_page_config(page_title="AI Financial Educator ChatBot", page_icon="💬", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 AI Financial Assistant")
st.markdown("Chat with the AI. Ask a question and use the **➕ Attach** button to add your context (Optional).")

# 2. Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_input" not in st.session_state:
    st.session_state.query_input = ""
if "context_text_input" not in st.session_state:
    st.session_state.context_text_input = ""
if "context_url_input" not in st.session_state:
    st.session_state.context_url_input = ""
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = str(0)
if "pending_submission" not in st.session_state:
    st.session_state.pending_submission = False

# --- الجديد: دالة الـ Callback اللي بتحفظ القيم وتفضي الخانات بأمان ---
def handle_submit():
    # 1. حفظ السؤال
    st.session_state.final_query = st.session_state.query_input
    
    # 2. حفظ نوع الـ Context
    c_type = st.session_state.context_type_radio
    st.session_state.final_c_type = c_type
    
    # 3. حفظ الداتا أو الملف المرفوع
    c_data = ""
    if c_type == "Text":
        c_data = st.session_state.context_text_input
    elif c_type == "URL":
        c_data = st.session_state.context_url_input
        
    # ------------- التعديل هنا للصور وملفات الوورد -------------
    elif c_type == "Image":
        file = st.session_state.get(f"img_{st.session_state.file_uploader_key}")
        if file:
            # استخراج امتداد الصورة الأصلي (مثال: jpg, png)
            file_extension = file.name.split(".")[-1]
            # إنشاء ملف مؤقت وحفظ الصورة فيه
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                tmp_file.write(file.getvalue())
                c_data = tmp_file.name # استخراج المسار الآمن
                
    elif c_type == "Document":
        file = st.session_state.get(f"doc_{st.session_state.file_uploader_key}")
        if file:
            # إنشاء ملف مؤقت وحفظ ملف الوورد فيه
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                tmp_file.write(file.getvalue())
                c_data = tmp_file.name # استخراج المسار الآمن
    # -------------------------------------------------------------
    
    st.session_state.final_c_data = c_data
    
    # تفعيل المعالجة لو المستخدم كتب سؤال فعلاً
    if st.session_state.final_query.strip():
        st.session_state.pending_submission = True

    # 4. تفريغ الخانات برمجياً (هنا Streamlit مش هيعترض)
    st.session_state.query_input = ""
    st.session_state.context_text_input = ""
    st.session_state.context_url_input = ""
    st.session_state.file_uploader_key = str(int(st.session_state.file_uploader_key) + 1)

# 3. Display previous chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 4. معالجة الإرسال الجديد (بيتعرض بعد الشات القديم وقبل الخانات عشان الترتيب يكون صح)
if st.session_state.pending_submission:
    user_query = st.session_state.final_query
    context_type = st.session_state.final_c_type
    context_data = st.session_state.final_c_data
    
    if context_data:
        user_display_msg = f"**Query:** {user_query}\n\n**Attached ({context_type}):**\n{context_data if context_type in ['Text', 'URL'] else 'File Uploaded'}"
    else:
        user_display_msg = f"**Query:** {user_query}"
        
    st.session_state.messages.append({"role": "user", "content": user_display_msg})
    
    with st.chat_message("user"):
        st.write(user_display_msg)
        
    with st.chat_message("assistant"):
        with st.spinner("🧠 AI is thinking..."):
            try:

                client = Client("https://a535215d7f410e3791.gradio.live")
                final_answer = client.predict(
                    input1=user_query,
                    input2=context_data if context_data else "", 
                )
                st.write(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            except Exception as e:
                error_msg = f"⚠️ Connection Error: Ensure Gradio server is running. Details: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
   
    st.session_state.pending_submission = False

st.divider()

# 5. Input Section 
st.markdown("### New Message")

col1, col2 = st.columns([8, 2])

with col1:

    st.text_input("Message:", key="query_input", placeholder="e.g., What is inflection?", label_visibility="collapsed")

with col2:
    with st.popover("➕ Attach", use_container_width=True):
       
        context_type = st.radio(
            "Choose Context Type:",
            ["Text", "URL", "Image", "Document"],
            key="context_type_radio",
            label_visibility="collapsed"
        )


if context_type == "Text":
    st.text_area("📄 Enter your text here:", key="context_text_input", placeholder="Paste your article or data here...")
elif context_type == "URL":
    st.text_input("🔗 Enter URL:", key="context_url_input", placeholder="https://www.example.com")
elif context_type == "Image":
    st.file_uploader("🖼️ Upload Image", type=["png", "jpg", "jpeg", "webp"], key=f"img_{st.session_state.file_uploader_key}")
elif context_type == "Document":
    st.file_uploader("📝 Upload Document", type=["docx"], key=f"doc_{st.session_state.file_uploader_key}")


st.button("Send 🚀", use_container_width=True, type="primary", on_click=handle_submit)
