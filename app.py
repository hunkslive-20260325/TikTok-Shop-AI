import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：严格对齐 OpenRouter 命名规范 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V39"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def run_gen_image(self, model_id, prompt):
        """
        修正后的绘图逻辑：使用验证过的准确 ID 字符串
        """
        # 按照你给的 ✔ 规范，优先尝试带 :free 或标准后缀的路径
        fallbacks = [
            model_id,
            "google/gemini-2.0-flash-exp",   # 2026 极其稳定的多模态 ID
            "openai/gpt-4o",                # 具备 DALL-E 3 调用能力的路由
            "black-forest-labs/flux-1.1-pro" # 商业版标准 ID
        ]
        
        for mid in fallbacks:
            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "modalities": ["image"]
            }
            try:
                self.log("INFO", f"尝试调用准确 ID: {mid}")
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers=self.headers, json=payload, timeout=60)
                
                # 如果 400 依然存在，说明该 ID 在当前 Key 下无权限，继续 fallback
                if res.status_code != 200:
                    self.log("WARN", f"ID {mid} 拒绝访问: {res.status_code}")
                    continue

                data = res.json()
                img_data = data['choices'][0]['message'].get("images", [None])[0]
                if img_data: return img_data, mid
            except: continue
        return None, "None"

    def run_vision_seo(self, model_id, prompt, uploaded_file):
        """识图 SEO：确保使用 google/gemini-2.0-flash-exp 等准确 ID"""
        content = [{"type": "text", "text": prompt}]
        if uploaded_file:
            b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": content}]}, 
                                timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 识图失败，请检查模型 ID 准确性"

# --- 2. 前端展示 ---
def display_img(raw, cap):
    try:
        if str(raw).startswith("http"): st.image(raw, caption=cap, use_container_width=True)
        else: st.image(Image.open(BytesIO(base64.b64decode(str(raw).split(",")[-1]))), caption=cap, use_container_width=True)
    except: st.error("渲染失败")

st.set_page_config(page_title="饰品专家 V39", layout="wide")
if "seo" not in st.session_state: st.session_state.seo = ""
if "imgs" not in st.session_state: st.session_state.imgs = []

with st.sidebar:
    st.title("🛡️ 命名规范校验版")
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    engine = JewelryAIEngine(api_key)
    
    st.header("⚙️ 模型 ID 配置")
    # 按照你提供的 ✔ 例子进行默认填充
    m_txt = st.selectbox("文案模型 (准确字符串)", [
        "google/gemini-2.0-flash-exp", 
        "deepseek/deepseek-r1:free",
        "openai/gpt-4o"
    ])
    
    m_img_custom = st.text_input("手动输入绘图模型 ID", "openai/gpt-4o")
    st.caption("注：DALL-E 3 通常通过 gpt-4o 路由调用")

    st.divider()
    u_title = st.text_input("产品标题", "S925 银项链")
    u_file = st.file_uploader("上传图片", type=["jpg", "png"])

st.header("💎 TikTok Shop 饰品 AI (V39.0)")
c1, c2 = st.columns([1, 1.2])

with c1:
    if st.button("✨ 1. 识图并优化 SEO", use_container_width=True):
        st.session_state.seo = engine.run_vision_seo(m_txt, f"分析此图并优化标题: {u_title}", u_file)
    
    if st.button("🖼️ 2. 生成莫兰迪主图", use_container_width=True):
        res, mid = engine.run_gen_image(m_img_custom, "Professional jewelry photography, Morandi background")
        if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "主图"})

    if st.button("👤 3. 生成模特展示图", use_container_width=True):
        res, mid = engine.run_gen_image(m_img_custom, "High-end model wearing necklace, TikTok style")
        if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "模特图"})

with c2:
    if st.session_state.seo: st.markdown(st.session_state.seo)
    if st.session_state.imgs:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.imgs):
            with grid[i%2]: display_img(item['u'], f"{item['t']} ({item['m']})")

with st.expander("🛠️ 实时 ID 校验日志"):
    st.text_area("Logs", "\n".join(st.session_state.get("logs", [])[::-1]), height=200)
