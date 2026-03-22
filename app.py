import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端引擎：模型全量回归 + 摄影级 Prompt 注入 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_Expert_V47"
        }
        # 【全部找回】17 个绘图模型 ID
        self.MODELS = {
            "openrouter/auto": "openrouter/auto",
            "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
            "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
            "google/gemini-3-pro-image-preview": "google/gemini-3-pro-image-preview",
            "bytedance-seed/seedream-4.5": "bytedance-seed/seedream-4.5",
            "openai/gpt-5-image-mini": "openai/gpt-5-image-mini",
            "openai/gpt-5-image": "openai/gpt-5-image",
            "sourceful/riverflow-v2-fast": "sourceful/riverflow-v2-fast",
            "sourceful/riverflow-v2-pro": "sourceful/riverflow-v2-pro",
            "sourceful/riverflow-v2-standard-preview": "sourceful/riverflow-v2-standard-preview",
            "sourceful/riverflow-v2-fast-preview": "sourceful/riverflow-v2-fast-preview",
            "sourceful/riverflow-v2-max-preview": "sourceful/riverflow-v2-max-preview",
            "black-forest-labs/flux.2-klein-4b": "black-forest-labs/flux.2-klein-4b",
            "black-forest-labs/flux.2-max": "black-forest-labs/flux.2-max",
            "black-forest-labs/flux.2-flex": "black-forest-labs/flux.2-flex",
            "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro",
            "google/gemini-2.5-flash-image-preview": "google/gemini-2.5-flash-image-preview"
        }

    # 【核心逻辑】严格对齐您的摄影需求手册
    def build_expert_prompt(self, task_type, category, market, gender):
        if task_type == "product":
            # 莫兰迪、丝缎、几何道具、45度柔光
            return (f"Commercial jewelry photography of {category}. Background: Warm Morandi cream and beige tones. "
                    f"Texture: Silk and satin fabric with natural elegant folds, matte paper base. "
                    f"Props: Minimalist geometric podiums (cubes and polyhedrons) for 3D depth. "
                    f"Lighting: Diffused softbox light from 45-degree above, no harsh shadows, 8k resolution.")
        elif task_type == "model":
            if gender == "男性":
                # 小麦色皮肤、黑色针织衫、大地色虚化背景
                return (f"Fashion photography. Male model with tanned skin, neat stubbles, defined facial contours. "
                        f"Wearing {category}. Clothing: Solid black crew neck knitwear. "
                        f"Background: Blurred taupe and sand earth tones. Lighting: 45-degree side lighting, highlighting metal luster.")
            else:
                # 水光肌、柔和妆容、窗边柔光、粉色/浅米色背景
                return (f"Beauty photography. Female model with dewy glowing skin and soft makeup. "
                        f"Wearing {category}. Clothing: Pure white elegant outfit. "
                        f"Background: Diffused soft pink or champagne beige. Lighting: Soft window lighting, no shadows.")
        return category

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def run_gen(self, mid_key, p_type, cat, market, gen):
        mid = self.MODELS.get(mid_key)
        final_prompt = self.build_expert_prompt(p_type, cat, market, gen)
        payload = {"model": mid, "messages": [{"role": "user", "content": [{"type": "text", "text": final_prompt}]}], "modalities": ["image"]}
        try:
            self.log("INFO", f"执行生成任务: {mid}")
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=payload, timeout=60)
            if res.status_code == 200:
                img = res.json()['choices'][0]['message'].get('images', [None])[0]
                return img, mid
            return None, f"Error {res.status_code}"
        except Exception as e: return None, str(e)

    def run_seo(self, model_id, prompt, file):
        content = [{"type": "text", "text": prompt}]
        if file:
            b64 = base64.b64encode(file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": content}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ SEO 任务失败"

# --- 2. UI 布局：找回所有经营输入项 & 按钮名称 ---
st.set_page_config(page_title="饰品全能 AI 专家", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngine(api_key)

if "gallery" not in st.session_state: st.session_state.gallery = []
if "seo_res" not in st.session_state: st.session_state.seo_res = ""

with st.sidebar:
    st.title("🛡️ 控制台")
    st.divider()
    st.subheader("⚙️ 模型配置")
    # 【全部找回】7 个文案优化模型
    m_txt = st.selectbox("文案模型", [
        "google/gemini-3.1-flash-image-preview", "openai/gpt-5-image-mini", 
        "google/gemini-2.5-flash-image", "google/gemini-3-pro-image-preview",
        "openai/gpt-5-image", "google/gemini-2.5-flash-image-preview", "openrouter/auto"
    ])
    m_img = st.selectbox("绘图模型", list(engine.MODELS.keys()))

    st.divider()
    st.subheader("📋 任务参数")
    u_title = st.text_input("1. 原始标题", "S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳饰", "戒指", "手链"])
    u_market = st.selectbox("3. 目标市场", ["东南亚总区", "北美地区", "欧洲地区", "中东地区"])
    u_gender = st.radio("4. 目标性别趋势", ["女性", "男性"], horizontal=True)
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])

# --- 主界面 ---
st.header("💎 TikTok Shop 饰品全能 AI 专家 (V47.0 商业级渲染版)")
c_btn, c_res = st.columns([1, 1.5])

with c_btn:
    st.subheader("✨ 专家指令")
    if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
        st.session_state.seo_res = engine.run_seo(m_txt, f"分析此饰品，针对{u_market}市场生成爆款 SEO 标题", u_file)
            
    if st.button("🖼️ 执行：商品图优化", use_container_width=True):
        res, mid = engine.run_gen(m_img, "product", u_cat, u_market, u_gender)
        if res: st.session_state.gallery.append({"u": res, "m": mid, "t": "莫兰迪商品图"})

    if st.button("👤 执行：模特图优化", use_container_width=True):
        res, mid = engine.run_gen(m_img, "model", u_cat, u_market, u_gender)
        if res: st.session_state.gallery.append({"u": res, "m": mid, "t": "模特实拍图"})

with c_res:
    if st.session_state.seo_res:
        with st.container(border=True): st.info("SEO 建议"), st.markdown(st.session_state.seo_res)
    if st.session_state.gallery:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.gallery):
            with grid[i%2]:
                st.image(Image.open(BytesIO(base64.b64decode(str(item['u']).split(",")[-1]))), caption=item['t'])
