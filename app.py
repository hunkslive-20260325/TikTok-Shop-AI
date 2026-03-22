import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：保持 17 个绘图模型，文案模型由 UI 层动态控制 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V45"
        }
        # 绘图模型列表保持 V44.0 的完整阵容
        self.MODELS = {
            "OpenRouter Auto (自动选择)": "openrouter/auto",
            "Google Gemini 2.5 Flash Image": "google/gemini-2.5-flash-image",
            "Google Gemini 2.5 Flash Image Preview": "google/gemini-2.5-flash-image-preview",
            "Google Gemini 3.1 Flash Image Preview": "google/gemini-3.1-flash-image-preview",
            "Google Gemini 3 Pro Image Preview": "google/gemini-3-pro-image-preview",
            "ByteDance Seedream 4.5": "bytedance-seed/seedream-4.5",
            "OpenAI GPT-5 Image Mini": "openai/gpt-5-image-mini",
            "OpenAI GPT-5 Image": "openai/gpt-5-image",
            "Sourceful Riverflow v2 Fast": "sourceful/riverflow-v2-fast",
            "Sourceful Riverflow v2 Fast Preview": "sourceful/riverflow-v2-fast-preview",
            "Sourceful Riverflow v2 Standard Preview": "sourceful/riverflow-v2-standard-preview",
            "Sourceful Riverflow v2 Pro": "sourceful/riverflow-v2-pro",
            "Sourceful Riverflow v2 Max Preview": "sourceful/riverflow-v2-max-preview",
            "FLUX.2 Klein 4B": "black-forest-labs/flux.2-klein-4b",
            "FLUX.2 Max": "black-forest-labs/flux.2-max",
            "FLUX.2 Flex": "black-forest-labs/flux.2-flex",
            "FLUX.2 Pro": "black-forest-labs/flux.2-pro"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def get_balance(self):
        try:
            res = requests.get("https://openrouter.ai/api/v1/key", headers=self.headers, timeout=5)
            if res.status_code == 200:
                d = res.json().get('data', {})
                return f"{round(d.get('limit', 0) - d.get('usage', 0), 4)} USD"
            return "Error"
        except: return "Net Error"

    def run_gen(self, mid_key, prompt):
        mid = self.MODELS.get(mid_key)
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        try:
            self.log("INFO", f"正在生成图片: {mid}")
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=payload, timeout=60)
            if res.status_code == 200:
                img = res.json()['choices'][0]['message'].get('images', [None])[0]
                return img, mid
            return None, f"API 错误 ({res.status_code})"
        except Exception as e:
            return None, str(e)

    def run_seo(self, model_id, prompt, file):
        content = [{"type": "text", "text": prompt}]
        if file:
            b64 = base64.b64encode(file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            self.log("INFO", f"正在优化文案: {model_id}")
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": content}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ SEO 任务执行失败"

# --- 2. UI 层：注入 7 个文案优化模型 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngine(api_key)

if "seo_box" not in st.session_state: st.session_state.seo_box = ""
if "gallery" not in st.session_state: st.session_state.gallery = []

with st.sidebar:
    st.title("🛡️ 控制台")
    col_bal, col_ref = st.columns([2, 1])
    with col_bal: st.metric("API 余额 (USD)", st.session_state.get("bal_val", "待刷新"))
    with col_ref: 
        if st.button("刷新"): st.session_state.bal_val = engine.get_balance()

    st.divider()
    st.subheader("⚙️ 模型配置")
    # --- 核心修改：文案模型列表扩容 ---
    m_txt = st.selectbox("文案模型", [
        "openrouter/auto",
        "google/gemini-2.5-flash-image",
        "google/gemini-3.1-flash-image-preview",
        "google/gemini-3-pro-image-preview",
        "openai/gpt-5-image-mini",
        "openai/gpt-5-image",
        "google/gemini-2.5-flash-image-preview",
        "google/gemini-2.0-flash-001",
        "deepseek/deepseek-chat"
    ])
    m_img = st.selectbox("绘图模型", list(engine.MODELS.keys()), index=0)

    st.divider()
    st.subheader("📋 任务参数")
    u_title = st.text_input("1. 原始标题", "S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 目标市场", ["东南亚总区", "北美地区", "欧洲地区", "中东地区"])
    u_gender = st.radio("4. 目标性别趋势", ["女性", "男性"], horizontal=True)
    
    st.divider()
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])

# --- 主界面 ---
st.header("💎 TikTok Shop 饰品全能 AI 专家 (监控版)")
tab_exec, tab_log = st.tabs(["🚀 任务执行", "📜 服务日志"])

with tab_exec:
    c_btn, c_res = st.columns([1, 1.5])
    with c_btn:
        st.subheader("✨ 专家指令")
        if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
            prompt = f"针对{u_market}市场，优化{u_gender}款{u_cat}标题。原标题：{u_title}。请分析图片并给出建议。"
            st.session_state.seo_box = engine.run_seo(m_txt, prompt, u_file)
            
        if st.button("🖼️ 执行：商品图优化", use_container_width=True):
            prompt = f"Jewelry photography of {u_cat}, Morandi cream background, elegant, 8k"
            res, mid = engine.run_gen(m_img, prompt)
            if res: st.session_state.gallery.append({"u": res, "m": mid, "t": "商品优化图"})
            else: st.error(mid)

        if st.button("👤 执行：模特图优化", use_container_width=True):
            prompt = f"Professional model wearing {u_cat}, {u_market} style lifestyle photography, 8k"
            res, mid = engine.run_gen(m_img, prompt)
            if res: st.session_state.gallery.append({"u": res, "m": mid, "t": "模特佩戴图"})
            else: st.error(mid)

    with c_res:
        st.subheader("📊 成果展示")
        if st.session_state.seo_box:
            with st.container(border=True):
                st.info("SEO 建议结果")
                st.markdown(st.session_state.seo_box)
        
        if st.session_state.gallery:
            cols = st.columns(2)
            for idx, item in enumerate(st.session_state.gallery):
                with cols[idx % 2]:
                    b64 = str(item['u']).split(",")[-1]
                    st.image(Image.open(BytesIO(base64.b64decode(b64))), caption=f"{item['t']} ({item['m']})")

with tab_log:
    st.subheader("🛠️ 实时服务日志")
    log_text = "\n".join(st.session_state.get("logs", [])[::-1])
    st.text_area("Log Output", log_text, height=450)
