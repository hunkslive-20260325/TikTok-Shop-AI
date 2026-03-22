import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端引擎：严格按照你提供的成功日志路径 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V42"
        }
        # 对应你截图日志中显示成功的模型 ID
        self.MODELS = {
            "OpenAI GPT-5 Image Mini": "openai/gpt-5-image-mini",
            "Google Nano Banana 2": "google/gemini-3.1-flash-image",
            "ByteDance Seedream 4.5": "bytedance/seedream-4.5"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def run_image_gen(self, model_name, prompt):
        mid = self.MODELS.get(model_name)
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        try:
            self.log("INFO", f"正在调用: {mid}")
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                img_data = data['choices'][0]['message'].get('images', [None])[0]
                if img_data: return img_data, mid
            
            self.log("ERROR", f"{mid} 失败: {res.status_code} {res.text[:50]}")
            return None, f"状态码: {res.status_code}"
        except Exception as e:
            return None, str(e)

    def run_vision_seo(self, prompt, uploaded_file):
        """识图统一使用 Nano Banana 2 (Gemini 3.1)"""
        content = [{"type": "text", "text": prompt}]
        if uploaded_file:
            b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, 
                                json={"model": "google/gemini-3.1-flash-image", "messages": [{"role": "user", "content": content}]}, 
                                timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 识图分析失败"

# --- 2. 前端界面 ---
st.set_page_config(page_title="饰品专家 V42", layout="wide")
key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngine(key)

if "imgs" not in st.session_state: st.session_state.imgs = []
if "seo" not in st.session_state: st.session_state.seo = ""

with st.sidebar:
    st.title("💎 AI 控制台")
    sel_model = st.selectbox("选择绘图模型", list(engine.MODELS.keys()))
    
    st.divider()
    u_title = st.text_input("产品原始标题", "S925 银心形项链")
    u_cat = st.selectbox("类目", ["项链", "手链", "戒指", "耳钉"])
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), caption="原图已就绪")

st.header("TikTok Shop 饰品全能 AI (V42.0 满血回归版)")
c1, c2 = st.columns([1, 1.4])

with c1:
    st.subheader("🚀 指令区")
    if st.button("✨ 1. 识图并优化标题", use_container_width=True):
        with st.spinner("Nano Banana 2 正在读取图片..."):
            st.session_state.seo = engine.run_vision_seo(f"分析图片并为这款{u_cat}生成 3 个 TikTok 标题。原始参考: {u_title}", u_file)
    
    if st.button("🖼️ 2. 生成莫兰迪商品主图", use_container_width=True):
        with st.spinner(f"正在通过 {sel_model} 生成..."):
            res, mid = engine.run_image_gen(sel_model, f"Professional jewelry photography of {u_cat}, Morandi cream background, 8k")
            if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "主图"})
    
    if st.button("👤 3. 生成模特效果图", use_container_width=True):
        with st.spinner(f"正在通过 {sel_model} 渲染模特..."):
            res, mid = engine.run_image_gen(sel_model, f"High-end model wearing {u_cat}, TikTok style lifestyle, 8k")
            if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "模特图"})

with c2:
    st.subheader("📊 成果展示")
    if st.session_state.seo: 
        with st.container(border=True): st.markdown(st.session_state.seo)
    
    if st.session_state.imgs:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.imgs):
            with grid[i%2]:
                pure_b64 = str(item['u']).split(",")[-1]
                st.image(Image.open(BytesIO(base64.b64decode(pure_b64))), caption=f"{item['t']} ({item['m']})")

with st.expander("🛠️ 运行日志"):
    st.text_area("Logs", "\n".join(st.session_state.get("logs", [])[::-1]), height=150)
