import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime
import time

# --- 1. 后端类：深度优化视觉分析与进度监控 ---
class JewelryAIEngineV47:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_Expert_V47"
        }
        # 17个绘图模型全量回归
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

    def log(self, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    # 核心绘图逻辑：视觉锁定 + 进度条
    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file, status_box):
        mid = self.MODELS.get(mid_key)
        prog = status_box.progress(0, "🔍 第一步：深度识图分析中...")
        
        # 1. 识图：提取原图饰品特征
        b64 = base64.b64encode(file.getvalue()).decode('utf-8')
        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "请提取此图片的饰品形状、材质和核心特征，用于生成一致的优化图。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        }
        try:
            v_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=v_payload, timeout=60)
            v_desc = v_res.json()['choices'][0]['message']['content']
            prog.progress(35, "🎯 第二步：结合摄影规范构思 Prompt...")
        except:
            v_desc = f"Specific {cat} jewelry from the uploaded image"

        # 2. 构造 Prompt (注入你的商业摄影规范)
        expert_prompt = self.get_expert_prompt(p_type, cat, market, gen, v_desc)
        
        # 3. 渲染
        prog.progress(60, f"🎨 第三步：调用 {mid_key} 进行渲染...")
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": expert_prompt}]}],
            "modalities": ["image"]
        }
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=payload, timeout=90)
            if res.status_code == 200:
                img = res.json()['choices'][0]['message'].get('images', [None])[0]
                prog.progress(100, "✅ 生成成功！")
                time.sleep(1)
                status_box.empty()
                return img
            prog.progress(100, f"❌ 失败: {res.status_code}")
            return None
        except Exception as e:
            st.error(f"渲染异常: {str(e)}")
            return None

    def get_expert_prompt(self, p_type, cat, market, gen, v_desc):
        if p_type == "product":
            return (f"Commercial jewelry photography. Product: {v_desc}. Background: Morandi cream and beige tones, silk satin fabric texture with natural folds. "
                    f"Props: Minimalist geometric podiums. Lighting: 45-degree softbox light, soft shadows, premium 8k.")
        else:
            if gen == "男性":
                return (f"Fashion photography. Male model with tanned skin and neat stubbles wearing {v_desc}. "
                        f"Clothing: Black crew neck knitwear. Background: Blurred taupe earth tones. 45-degree side light.")
            else:
                return (f"Beauty photography. Female model with dewy glowing skin wearing {v_desc}. "
                        f"Clothing: Elegant white. Background: Diffused soft pink/champagne. Soft window lighting.")

    def run_seo(self, model_id, prompt, file):
        content = [{"type": "text", "text": prompt}]
        if file:
            b64 = base64.b64encode(file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": content}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 分析失败"

# --- 2. 前端 UI 布局 ---
st.set_page_config(page_title="饰品专家 V47", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV47(api_key)

if "p_img" not in st.session_state: st.session_state.p_img = None
if "m_img" not in st.session_state: st.session_state.m_img = None
if "seo_txt" not in st.session_state: st.session_state.seo_txt = ""

# 顶部名称精简
st.title("💎 TikTok Shop 饰品 (V47.0)")

with st.sidebar:
    st.header("🛡️ 控制台")
    st.button("刷新状态")
    st.divider()
    m_txt = st.selectbox("文案模型", ["google/gemini-3.1-flash-image-preview", "openai/gpt-5-image-mini", "openrouter/auto"])
    m_img = st.selectbox("绘图模型", list(engine.MODELS.keys()))
    st.divider()
    st.subheader("📋 经营信息")
    u_title = st.text_input("1. 原始标题", "心形项链")
    u_cat = st.selectbox("2. 类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 性别", ["女性", "男性"], horizontal=True)
    st.divider()
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), caption="已上传原图", use_container_width=True)

# 进度显示区
status_box = st.empty()

# 中间选项卡切换模式
tab_seo, tab_prod, tab_mod = st.tabs(["📊 标题 SEO 优化", "🖼️ 商品图片结果", "👤 模特图片结果"])

with tab_seo:
    if st.session_state.seo_txt:
        st.markdown(st.session_state.seo_txt)
    else:
        st.info("等待执行标题优化任务...")

with tab_prod:
    if st.session_state.p_img:
        st.image(Image.open(BytesIO(base64.b64decode(st.session_state.p_img))), caption="优化后的莫兰迪主图", use_container_width=True)
    else:
        st.caption("（预留位置：商品主图生成后在此显示）")

with tab_mod:
    if st.session_state.m_img:
        st.image(Image.open(BytesIO(base64.b64decode(st.session_state.m_img))), caption="优化后的模特实拍图", use_container_width=True)
    else:
        st.caption("（预留位置：模特佩戴图生成后在此显示）")

# 下方按钮区域
st.divider()
st.subheader("🚀 专家指令")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
        if not u_file: st.warning("请先上传图片"); st.stop()
        st.session_state.seo_txt = engine.run_seo(m_txt, f"优化标题'{u_title}'针对{u_market}市场", u_file)
        st.rerun()

with c2:
    if st.button("🖼️ 执行：商品图优化", use_container_width=True):
        if not u_file: st.warning("请先上传图片"); st.stop()
        res = engine.run_smart_gen(m_img, "product", u_cat, u_market, u_gender, u_file, status_box)
        if res: st.session_state.p_img = res; st.rerun()

with c3:
    if st.button("👤 执行：模特图优化", use_container_width=True):
        if not u_file: st.warning("请先上传图片"); st.stop()
        res = engine.run_smart_gen(m_img, "model", u_cat, u_market, u_gender, u_file, status_box)
        if res: st.session_state.m_img = res; st.rerun()
