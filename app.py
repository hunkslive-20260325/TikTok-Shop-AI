import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：根据官方日志 1:1 还原调用路径 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V42"
        }
        # 严格对齐你日志图中的模型名称与 ID
        self.MODEL_MAP = {
            "OpenAI GPT-5 Image Mini": "openai/gpt-5-image-mini",
            "Google Nano Banana 2": "google/gemini-3.1-flash-image",
            "ByteDance Seedream 4.5": "bytedance/seedream-4.5",
            "DeepSeek V3 (文案专用)": "deepseek/deepseek-chat"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def run_image_gen(self, display_name, prompt):
        mid = self.MODEL_MAP.get(display_name)
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        try:
            self.log("INFO", f"请求模型: {mid}")
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                img_data = data['choices'][0]['message'].get('images', [None])[0]
                return img_data, mid
            self.log("ERROR", f"{mid} 反馈: {res.status_code} - {res.text[:50]}")
            return None, f"接口报错: {res.status_code}"
        except Exception as e:
            return None, str(e)

    def run_vision_seo(self, prompt, uploaded_file):
        """识图 SEO 逻辑"""
        content = [{"type": "text", "text": prompt}]
        if uploaded_file:
            b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            # 识图统一用 Nano Banana 2
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, 
                                json={"model": "google/gemini-3.1-flash-image", "messages": [{"role": "user", "content": content}]}, 
                                timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 识图失败，请检查图片或 Key"

# --- 2. 增强型显示逻辑 ---
def display_img_item(img_raw, title, model_id):
    try:
        pure_b64 = str(img_raw).split(",")[-1]
        st.image(Image.open(BytesIO(base64.b64decode(pure_b64))), caption=f"{title} ({model_id})", use_container_width=True)
    except: st.warning(f"{title} 渲染失败")

# --- 3. UI 布局：从“异常满屏”进化到“生产力工具” ---
st.set_page_config(page_title="饰品专家 V42", layout="wide", initial_sidebar_state="expanded")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngine(api_key)

if "imgs" not in st.session_state: st.session_state.imgs = []
if "seo_res" not in st.session_state: st.session_state.seo_res = ""

with st.sidebar:
    st.title("💎 AI 饰品控制台")
    st.info("2026 满血运行中")
    sel_model = st.selectbox("核心绘图引擎", list(engine.MODEL_MAP.keys()), index=0)
    
    st.divider()
    u_title = st.text_input("产品标题", "S925 银心形项链")
    u_cat = st.selectbox("类目", ["项链", "手链", "戒指", "耳钉"])
    u_file = st.file_uploader("📸 核心原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), caption="原图锁定")

# 主界面
st.header("TikTok Shop 饰品全能 AI (V42.0 终极适配版)")
c_act, c_res = st.columns([1, 1.4])

with c_act:
    st.subheader("🚀 专家指令集")
    if st.button("✨ 1. 识图并优化 SEO", use_container_width=True):
        with st.status("正在进行多模态视觉分析...", expanded=True):
            st.session_state.seo_res = engine.run_vision_seo(f"结合图片细节，为'{u_title}'生成 3 个高转化率标题", u_file)
    
    if st.button("🖼️ 2. 生成莫兰迪商品主图", use_container_width=True):
        with st.status(f"调用 {sel_model} 生成中...", expanded=True):
            res, mid = engine.run_image_gen(sel_model, f"Jewelry photography of {u_cat}, Morandi style background, 8k")
            if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "主图"})
    
    if st.button("👤 3. 生成模特佩戴效果图", use_container_width=True):
        with st.status(f"调用 {sel_model} 渲染模特...", expanded=True):
            res, mid = engine.run_image_gen(sel_model, f"High-end model wearing {u_cat}, TikTok style lifestyle, 8k")
            if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "模特图"})

with c_res:
    st.subheader("📊 成果动态展示")
    if st.session_state.seo_res:
        with st.container(border=True):
            st.markdown(st.session_state.seo_res)
    
    if st.session_state.imgs:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.imgs):
            with grid[i%2]:
                display_img_item(item['u'], item['t'], item['m'])
    else:
        st.caption("等待任务执行中... 成功后成果将在此处即时展示")

with st.expander("🛠️ 开发者底层日志 (排障专用)"):
    st.text_area("Live Logs", "\n".join(st.session_state.get("logs", [])[::-1]), height=200)
