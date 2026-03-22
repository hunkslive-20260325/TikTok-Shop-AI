import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：精准匹配 2026 官方模型 ID ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V41"
        }

    # 严格对应截图中的五个模型
    MODELS_2026 = {
        "Nano Banana (Gemini 2.5 Flash Image)": "google/gemini-2.5-flash-image",
        "Nano Banana 2 (Gemini 3.1 Flash Image)": "google/gemini-3.1-flash-image",
        "Nano Banana Pro (Gemini 3 Pro Image)": "google/gemini-3-pro-image",
        "ByteDance Seed: Seedream 4.5": "bytedance/seedream-4.5",
        "OpenAI: GPT-5 Image Mini": "openai/gpt-5-image-mini"
    }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def run_gen_image(self, model_display_name, prompt):
        """调用截图中的 2026 最新绘图模型"""
        mid = self.MODELS_2026.get(model_display_name)
        
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        try:
            self.log("INFO", f"正在启动 2026 引擎: {mid}")
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json=payload, timeout=60)
            
            if res.status_code == 200:
                data = res.json()
                img_data = data['choices'][0]['message'].get('images', [None])[0]
                if img_data: return img_data, mid
            
            self.log("ERROR", f"接口反馈 ({res.status_code}): {res.text[:100]}")
            return None, f"Error: {res.status_code}"
        except Exception as e:
            return None, str(e)

    def run_vision_seo(self, prompt, uploaded_file):
        """默认使用 Nano Banana 2 进行多模态识图"""
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
        except: return "❌ 识图分析失败，请检查网络或 Key 权限"

# --- 2. UI 界面 ---
st.set_page_config(page_title="饰品专家 V41", layout="wide")
key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngine(key)

if "imgs" not in st.session_state: st.session_state.imgs = []
if "seo" not in st.session_state: st.session_state.seo = ""

with st.sidebar:
    st.title("🛡️ 2026 官方模型库")
    # 动态渲染截图中的五个选项
    selected_m = st.selectbox("选择绘图引擎", list(engine.MODELS_2026.keys()), index=1)
    
    st.divider()
    u_title = st.text_input("产品原始标题", "S925 银心形项链")
    u_cat = st.selectbox("类目", ["项链", "耳饰", "戒指", "手链"])
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), caption="原图已锁定")

st.header("💎 TikTok Shop 饰品 AI (V41.0 官方同步版)")
c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 核心指令")
    if st.button("✨ 1. 识图并优化 SEO", use_container_width=True):
        with st.spinner("Nano Banana 2 正在深度分析..."):
            st.session_state.seo = engine.run_vision_seo(f"分析图片并为这款{u_cat}生成 3 个 TikTok 爆款标题。原始参考: {u_title}", u_file)
    
    if st.button("🖼️ 2. 生成莫兰迪风格主图", use_container_width=True):
        with st.spinner(f"正在调用 {selected_m}..."):
            res, mid = engine.run_gen_image(selected_m, f"Professional jewelry photography of {u_cat}, Morandi cream background, high-end, 8k")
            if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "主图"})
            else: st.error(f"生成失败，请看下方日志。")

    if st.button("👤 3. 生成模特实拍图", use_container_width=True):
        with st.spinner(f"正在调用 {selected_m}..."):
            res, mid = engine.run_gen_image(selected_m, f"Fashion model wearing {u_cat}, lifestyle photography, TikTok aesthetics, 8k")
            if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "模特图"})

with c2:
    st.subheader("📊 实时成果")
    if st.session_state.seo: 
        st.info("SEO 标题优化建议")
        st.markdown(st.session_state.seo)
    
    if st.session_state.imgs:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.imgs):
            with grid[i%2]:
                pure_b64 = str(item['u']).split(",")[-1]
                st.image(Image.open(BytesIO(base64.b64decode(pure_b64))), caption=f"{item['t']} ({item['m']})", use_container_width=True)

with st.expander("🛠️ 2026 官方接口调试日志"):
    st.text_area("Debug Output", "\n".join(st.session_state.get("logs", [])[::-1]), height=200)
