import streamlit as st
import openai
from dotenv import load_dotenv
import os
from docx import Document
from fpdf import FPDF
from io import BytesIO
import pyrebase
import requests
import json

load_dotenv()

# ✅ Multiple AI Provider Support
AI_PROVIDERS = {
    "OpenAI": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "available": bool(os.getenv("OPENAI_API_KEY"))
    },
    "Hugging Face (FREE)": {
        "api_key": os.getenv("HUGGINGFACE_API_KEY"),
        "available": True  # Ücretsiz tier var
    },
    "Groq (FREE)": {
        "api_key": os.getenv("GROQ_API_KEY"), 
        "available": True  # Ücretsiz tier var
    }
}

# OpenAI client (eğer varsa)
if AI_PROVIDERS["OpenAI"]["available"]:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    client = None

# ✅ Firebase Config
firebaseConfig = {
  "apiKey": "AIzaSyB9tHRV1jgMKwtwewOhPT555Lh1Lh-31Pc",
  "authDomain": "blogcraftt.firebaseapp.com",
  "projectId": "blogcraftt",
  "storageBucket": "blogcraftt.appspot.com",
  "messagingSenderId": "708843280683",
  "appId": "1:708843280683:web:1ab9d956168b5ad5b89d6e",
  "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# ✅ Prompt Library Tanımlaması
prompt_library = {
    "📝 Blog Yazısı": "Sen profesyonel bir Türk blog yazarı ve içerik üreticisisin. Türkçe olarak başlangıç, gelişme ve sonuç yapısıyla en az 1000 kelimelik özgün ve SEO uyumlu bir blog yaz. Başlıklar kullan ve düzenli bir yapıda sun. Yanıtını tamamen Türkçe ver.",
    
    "🔗 LinkedIn Post": """Sen LinkedIn'de başarılı bir Türk profesyonel içerik üreticisisin. Türkçe olarak etkili LinkedIn postları yazarsın. Kuralların:
1. İlgi çekici bir Türkçe hook ile başla
2. Değerli bilgi ver
3. Paragraflar kısa olsun (2-3 cümle max)
4. Emojiler kullan ama abartma
5. Sonunda engaging bir Türkçe soru sor
6. İlgili Türkçe hashtagleri ekle
7. Profesyonel ama samimi bir Türkçe ton kullan
8. 150-200 kelime arasında tut
Yanıtını tamamen Türkçe ver.""",
    
    "🐦 Tweet": "Sen yaratıcı bir Türk içerik üreticisisin. 280 karakteri geçmeyen, kısa, vurucu ve etkileyici bir Türkçe tweet hazırla. Türkçe hashtag kullan ve viral olabilecek şekilde yaz. Yanıtını tamamen Türkçe ver.",
    
    "🛍 Ürün Tanıtımı": "Türk pazarlama uzmanı gibi Türkçe ürün tanıtımı yap. Sorun-çözüm odaklı Türkçe yaz. Ürünün faydalarını vurgula ve satış odaklı Türkçe içerik üret. Yanıtını tamamen Türkçe ver.",
    
    "📧 Email Marketing": "Profesyonel Türk email pazarlama uzmanısın. Türkçe konu başlığından başlayarak, açılış oranı yüksek, dönüşüm odaklı Türkçe email içeriği yaz. Yanıtını tamamen Türkçe ver.",
    
    "🎥 Video Script": "Türk video içerik üreticisisin. Hook, içerik ve call-to-action yapısıyla Türkçe video script'i hazırla. Dakika başına 150 kelime hesabıyla Türkçe yaz. Yanıtını tamamen Türkçe ver."
}

st.set_page_config(page_title="AI Content Factory - Login", layout="wide")
st.title("🔐 AI Content Factory")

# Kullanıcı oturumu
if 'user' not in st.session_state:
    st.session_state['user'] = None

# Email & Şifre Inputları
st.sidebar.header("User Authentication")
email = st.sidebar.text_input("📧 Email")
password = st.sidebar.text_input("🔑 Password", type="password")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.sidebar.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state['user'] = user
            st.sidebar.success(f"✅ Welcome {email}")
        except:
            st.sidebar.error("❌ Invalid email or password")

with col2:
    if st.sidebar.button("Sign Up"):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            st.sidebar.success("✅ Account created successfully! Please log in.")
        except:
            st.sidebar.error("❌ Failed to register. Email may already be in use or password is weak.")

# Oturum varsa logout göster
if st.session_state['user']:
    if st.sidebar.button("Logout"):
        st.session_state['user'] = None
        st.sidebar.success("✅ Logged out successfully")

# Content Generation Section
if st.session_state['user']:
    st.subheader("✨ Welcome to AI Content Generation")
    
    # ✅ Prompt Library Seçici
    st.sidebar.title("📚 Prompt Library")
    selected_prompt_category = st.sidebar.selectbox("Kategori Seç", list(prompt_library.keys()))
    default_prompt = prompt_library[selected_prompt_category]
    custom_prompt = st.sidebar.text_area("✏️ Promptu Düzenle veya Yaz", value=default_prompt, height=150)
    
    # ✅ Prompt Kaydetme (Demo)
    if st.sidebar.button("💾 Promptu Kaydet (Demo)"):
        st.sidebar.success("✅ Prompt kaydedildi (demo)")
    
    st.sidebar.markdown("---")
    
    # Blog Detail Inputs
    st.sidebar.title("Input your Blog Detail")
    st.sidebar.subheader("Enter details of the Blog You want to generate")
    
    # Blog title 
    blog_title = st.sidebar.text_input("Blog Title") 
    
    # Keywords input 
    keywords = st.sidebar.text_area("Keywords (comma-seperated)")
    
    num_words = st.sidebar.slider("Number of words", min_value=250, max_value=1000, step=250)
    
    submit_button = st.sidebar.button("Generate")

    # Ana içerik üretimi
    if submit_button and keywords:
        
        # Seçilen promptu al
        final_prompt = custom_prompt.strip()
        
        # Öncelik sırası: Groq > Hugging Face (backend'de saklı key'ler)
        current_groq_key = os.getenv("GROQ_API_KEY", "")
        current_hf_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
        selected_service = None
        if current_groq_key:
            selected_service = "Groq"
        elif current_hf_key:
            selected_service = "Hugging Face"
        else:
            st.error("⚠️ Sistem yapılandırması eksik. Lütfen yönetici ile iletişime geçin.")
            st.stop()
        
        st.info(f"🤖 {selected_service} servisi kullanılıyor...")
        
        # API Çağrısı yapacak fonksiyon
        def make_ai_request(prompt, user_message, max_tokens=2048):
            if selected_service == "Groq":
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {current_groq_key}",
                        "Content-Type": "application/json"
                    }
                    
                    data = {
                        "model": "llama3-8b-8192",
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "max_tokens": min(max_tokens, 2048),
                        "temperature": 0.7
                    }
                    
                    response = requests.post(url, headers=headers, json=data)
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        st.warning(f"Groq API hatası, Hugging Face'e geçiliyor...")
                        return fallback_to_hf(prompt, user_message)
                except Exception as e:
                    st.warning(f"Groq bağlantı hatası, Hugging Face'e geçiliyor...")
                    return fallback_to_hf(prompt, user_message)
            
            elif selected_service == "Hugging Face":
                return fallback_to_hf(prompt, user_message)
            
            return None
        
        def fallback_to_hf(prompt, user_message):
            try:
                API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
                headers = {"Authorization": f"Bearer {current_hf_key}"}
                
                full_prompt = f"{prompt}\n\nUser: {user_message}\nAssistant: Türkçe olarak yanıtlayacağım:"
                payload = {"inputs": full_prompt[:1000], "parameters": {"max_new_tokens": 500}}
                
                response = requests.post(API_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        if "Assistant:" in generated_text:
                            return generated_text.split("Assistant:")[-1].strip()
                        return generated_text
                    return f"HuggingFace ile basit Türkçe içerik: {user_message[:100]}..."
                else:
                    return f"📝 Template içerik: {keywords} konusunda {selected_prompt_category} formatında profesyonel Türkçe içerik."
            except Exception as e:
                return f"📝 Template içerik: {keywords} konusunda {selected_prompt_category} formatında profesyonel Türkçe içerik."

        # Kategoriye göre içerik üretimi
        content_for_download = ""
        
        if "Blog" in selected_prompt_category:
            with st.spinner(f"🤖 {selected_service} ile Türkçe blog yazısı oluşturuluyor..."):
                user_message = f"Konu: {keywords}. Yaklaşık {num_words} kelime uzunluğunda, '{blog_title}' başlıklı Türkçe blog yazısı yaz. Yanıtını tamamen Türkçe ver."
                blog_content = make_ai_request(final_prompt, user_message, 4096)
                
                if blog_content:
                    st.subheader("📝 Oluşturulan Blog Yazısı")
                    st.write(blog_content)
                    content_for_download = blog_content
                else:
                    content_for_download = f"Blog yazısı: {keywords} konusunda içerik oluşturulamadı."
        
        elif "LinkedIn" in selected_prompt_category:
            with st.spinner(f"🤖 {selected_service} ile Türkçe LinkedIn postu oluşturuluyor..."):
                user_message = f"Bu konular hakkında profesyonel bir Türkçe LinkedIn postu yaz: {keywords}. Yanıtını tamamen Türkçe ver."
                linkedin_content = make_ai_request(final_prompt, user_message, 600)
                
                if linkedin_content:
                    st.subheader("📝 Oluşturulan LinkedIn Postu")
                    st.write(linkedin_content)
                    content_for_download = linkedin_content
                else:
                    content_for_download = f"LinkedIn Post: {keywords} hakkında profesyonel bir paylaşım oluşturulamadı."
        
        elif "Tweet" in selected_prompt_category:
            with st.spinner(f"🤖 {selected_service} ile Türkçe tweet oluşturuluyor..."):
                user_message = f"Bu konular hakkında Türkçe tweet yaz: {keywords}. Yanıtını tamamen Türkçe ver."
                tweet_content = make_ai_request(final_prompt, user_message, 100)
                
                if tweet_content:
                    st.subheader("📝 Oluşturulan Tweet")
                    st.write(tweet_content)
                    content_for_download = tweet_content
                else:
                    content_for_download = f"Tweet: {keywords} hakkında kısa bir paylaşım oluşturulamadı."
        
        else:
            with st.spinner(f"🤖 {selected_service} ile Türkçe {selected_prompt_category} oluşturuluyor..."):
                user_message = f"Bu konular hakkında Türkçe içerik yaz: {keywords}. Yanıtını tamamen Türkçe ver."
                general_content = make_ai_request(final_prompt, user_message, 2048)
                
                if general_content:
                    st.subheader(f"📝 Oluşturulan {selected_prompt_category}")
                    st.write(general_content)
                    content_for_download = general_content
                else:
                    content_for_download = f"{selected_prompt_category}: {keywords} konusunda içerik oluşturulamadı."

        # DOCX İndirme
        full_content = f"""
{selected_prompt_category} İçeriği
Başlık: {blog_title}
Anahtar Kelimeler: {keywords}
Kullanılan AI Servisi: {selected_service}
Kullanılan Prompt: {final_prompt}

--- İÇERİK ---
{content_for_download}
        """
        
        def generate_docx(content):
            buffer = BytesIO()
            doc = Document()
            doc.add_paragraph(content)
            doc.save(buffer)
            buffer.seek(0)
            return buffer
                
        docx_file = generate_docx(full_content)

        st.download_button(
            label="📄 Download as DOCX",
            data=docx_file,
            file_name=f"{selected_prompt_category.replace('🔗', '').replace('📝', '').replace('🐦', '').replace('🛍', '').strip()}_output.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    elif submit_button and not keywords:
        st.warning("⚠️ Lütfen keywords girin!")

else:
    st.warning("⚠️ Lütfen giriş yapın veya kayıt olun.")