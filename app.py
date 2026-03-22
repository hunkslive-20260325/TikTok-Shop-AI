import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime
import time

# ==========================================
# 🛡️ 全局静态模型库（硬编码，严禁精简）
# ==========================================
# 包含所有绘图模型 (17个) 和 文案/标题模型 (14个)
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "google/gemini-2.5-flash-image-preview": "google/gemini-2.5-flash-image-preview",
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "google/gemini-3-pro-image-preview": "google/gemini-3-pro-image-preview",
    "bytedance-seed/seedream-4.5": "bytedance-seed/seedream-4.5",
    "openai/gpt-5-image-mini": "openai/gpt-5-image-mini",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "sourceful/riverflow-v2-fast": "sourceful/riverflow-v2-fast",
    "sourceful/riverflow-v2-fast-preview": "sourceful/riverflow-v2-fast-preview",
    "sourceful/riverflow-v2-standard-preview": "sourceful/riverflow-v2-standard-preview",
    "sourceful/riverflow-v2-pro": "sourceful/riverflow-v2-pro",
    "sourceful/riverflow-v2-max-preview": "sourceful/riverflow-v2-max-preview",
    "black-forest-labs/flux.2-klein-4b": "black-forest-labs/flux.2-klein-4b",
    "black-forest-labs/flux.2-max": "black-forest-labs/flux.2-max",
    "black-forest-labs/flux.2-flex": "black-forest-labs/flux.2-flex",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
}

ALL_TEXT_MODELS = [
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-chat",
    "openai/gpt-5.4",
    "openai/gpt-5-mini",
    "openai/gpt-5-image-mini",
    "openai/gpt-5-image",
    "openai/gpt-4.1-mini",
    "openai/gpt-4.1",
    "google/gemini-3.1-flash-image-preview",
    "google/gemini-3-pro-image-preview",
    "google/gemini-2.5-flash-image",
    "google/gemini-2.5-flash-image-preview",
    "google/gemini-2.0-flash-001",
    "openrouter/auto"
]

# --- 1. 后端类：逻辑加固 ---
class JewelryAIEngineV47:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_Expert_V47"
        }

    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file, status_box):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        prog = status_box.progress(0, "🔍 正在进行多模态识图分析...")
        
        # 1. 识图锁定
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "请提取此饰品的几何形状、材质细节。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_in}"}}
            ]}]
        }
        try:
            v_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=v_payload, timeout=60)
            v_desc = v_res.json()['choices'][0]['message']['content']
        except: v_desc = f"Commercial {cat} jewelry"

        # 2. 注入摄影规范 (莫兰迪/水光肌/小麦色)
        prog.progress(40, "🎯 正在生成商业级 Prompt...")
        prompt = self.get_expert_prompt(p_type, cat, market, gen, v_desc)
        
        # 3. 渲染
        prog.progress(70, f"🎨 正在调用 {mid_key}...")
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": mid, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}], "modalities": ["image"]}, timeout=120)
            img_data = res.json()['choices'][0]['message'].get('images', [None])[0]
            prog.progress(100, "✅ 渲染完成！")
            return img_data
        except: return None

    def get_expert_prompt(self, p_type, cat, market, gen, v_desc):
        if p_type == "product":
            return f"Commercial jewelry photography. {v_desc}. Morandi warm tones, cream silk fabric, geometric podiums, soft light, 8k."
        style = "Male, tanned skin, black knitwear" if gen == "男性" else "Female, dewy skin, white outfit, soft pink background"
        return f"Fashion photography. {style} wearing {v_desc}. 45-degree side lighting, 8k."

    def run_seo(self, model_id, prompt, file):
        content = [{"type": "text", "text": prompt}]
        if file:
            b64 = base64.b64encode(file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json={"model": model_id, "messages": [{"role": "user", "content": content}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 分析失败"

# --- 2. 前端 UI 与 缓存保护 ---
st.set_page_config(page_title="饰品专家 V47.3", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV47(api_key)

# 强制初始化，防止 TypeError
for key in ["p_img", "m_img", "seo_txt"]:
    if key not in st.session_state: st.session_state[key] = None

st.title("💎 TikTok Shop 饰品 (V47.3)")

with st.sidebar:
    st.header("🛡️ 控制台")
    m_txt = st.selectbox("文案模型", ALL_TEXT_MODELS) # 引用硬编码列表
    m_img = st.selectbox("绘图模型", list(ALL_DRAWING_MODELS.keys())) # 引用硬编码列表
    st.divider()
    u_title = st.text_input("1. 标题", "心形项链")
    u_cat = st.selectbox("2. 类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 性别", ["女性", "男性"], horizontal=True)
    st.divider()
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(u_file, caption="原图预览", use_container_width=True)

status_box = st.empty()
tab_seo, tab_prod, tab_mod = st.tabs(["📊 SEO 优化结果", "🖼️ 商品图片结果", "👤 模特图片结果"])

# 渲染逻辑增加 None 检查（解决 TypeError）
with tab_seo:
    if st.session_state.seo_txt: st.markdown(st.session_state.seo_txt)
    else: st.caption("（尚未生成）")

with tab_prod:
    if st.session_state.p_img and isinstance(st.session_state.p_img, str):
        st.image(Image.open(BytesIO(base64.b64decode(st.session_state.p_img.split(",")[-1]))), use_container_width=True)
    else: st.caption("（待生成）")

with tab_mod:
    if st.session_state.m_img and isinstance(st.session_state.m_img, str):
        st.image(Image.open(BytesIO(base64.b64decode(st.session_state.m_img.split(",")[-1]))), use_container_width=True)
    else: st.caption("（待生成）")

st.divider()
st.subheader("🚀 专家指令")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
        if not u_file: st.warning("请上传图片"); st.stop()
        st.session_state.seo_txt = engine.run_seo(m_txt, f"为{u_market}优化标题：{u_title}", u_file)
        st.rerun()

with c2:
    if st.button("🖼️ 执行：商品图优化", use_container_width=True):
        if not u_file: st.warning("请上传图片"); st.stop()
        res = engine.run_smart_gen(m_img, "product", u_cat, u_market, u_gender, u_file, status_box)
        if res: st.session_state.p_img = res; st.rerun()

with c3:
    if st.button("👤 执行：模特图优化", use_container_width=True):
        if not u_file: st.warning("请上传图片"); st.stop()
        res = engine.run_smart_gen(m_img, "model", u_cat, u_market, u_gender, u_file, status_box)
        if res: st.session_state.m_img = res; st.rerun()
