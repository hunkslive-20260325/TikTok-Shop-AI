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
    "deepseek/deepseek-v3.2", "deepseek/deepseek-chat", "openai/gpt-5.4", "openai/gpt-5-mini",
    "openai/gpt-5-image-mini", "openai/gpt-5-image", "openai/gpt-4.1-mini", "openai/gpt-4.1",
    "google/gemini-3.1-flash-image-preview", "google/gemini-3-pro-image-preview",
    "google/gemini-2.5-flash-image", "google/gemini-2.5-flash-image-preview",
    "google/gemini-2.0-flash-001", "openrouter/auto"
]

# --- 1. 后端引擎类 ---
class JewelryAIEngineV47:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "HTTP-Referer": "https://streamlit.io", "X-Title": "Jewelry_V47_Final"}

    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file, status_box):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        prog = status_box.progress(0, "🔍 第一步：深度识图分析中...")
        
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "提取此饰品的形状、材质与核心设计语言，用于生成一致的展示图。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_in}"}}
            ]}]
        }
        try:
            v_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=v_payload, timeout=60)
            v_desc = v_res.json()['choices'][0]['message']['content']
            prog.progress(40, "🎯 第二步：构思商业级渲染指令...")
        except:
            v_desc = f"Specific {cat} jewelry"

        prompt = self.get_expert_prompt(p_type, cat, market, gen, v_desc)
        prog.progress(70, f"🎨 第三步：正在通过 {mid_key} 渲染图片...")
        
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": mid, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}], "modalities": ["image"]}, timeout=120)
            img_list = res.json().get('choices', [{}])[0].get('message', {}).get('images', [])
            img_data = img_list[0] if img_list else None
            prog.progress(100, "✅ 任务处理完成")
            return img_data
        except: return None

    def get_expert_prompt(self, p_type, cat, market, gen, v_desc):
        if p_type == "product":
            return f"Commercial jewelry photography. {v_desc}. Background: Morandi warm tones, cream silk fabric, geometric podiums. 8k, softbox light."
        style = "Male model, tanned skin, black knitwear" if gen == "男性" else "Female model, dewy skin, white outfit, soft pink background"
        return f"Fashion jewelry photography. {style} wearing {v_desc}. 45-degree cinematic light, 8k."

    def run_seo(self, model_id, u_title, u_cat, u_market):
        # 纯文本 SEO 逻辑，参考 TikTok/Amazon/Google/Temu/Etsy 热搜词
        seo_prompt = (
            f"Role: E-commerce SEO Expert. Target Market: {u_market}. Category: {u_cat}. "
            f"Task: Optimize the title '{u_title}' for maximum CTR and search visibility. "
            f"Requirements: 1. Incorporate trending keywords from TikTok Shop, Amazon, Google Ads, Temu, and Etsy. "
            f"2. Focus on high-conversion hooks (e.g., 'Gift for her', 'Waterproof', 'Minimalist'). "
            f"3. Provide 3 versions: [TikTok Optimized], [Amazon SEO Standard], [High-Click Ad Version]."
        )
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": seo_prompt}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return None

# --- 2. 前端界面与状态加固 ---
st.set_page_config(page_title="饰品专家 V47.4", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV47(api_key)

for key in ["p_img", "m_img", "seo_txt"]:
    if key not in st.session_state: st.session_state[key] = None

st.title("💎 TikTok Shop 饰品 (V47.4)")

with st.sidebar:
    st.header("🛡️ 控制台")
    m_txt = st.selectbox("文案/标题模型", ALL_TEXT_MODELS) 
    m_img = st.selectbox("图像渲染模型", list(ALL_DRAWING_MODELS.keys())) 
    st.divider()
    u_title = st.text_input("1. 原始标题", "心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 目标市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 模特性别", ["女性", "男性"], horizontal=True)
    st.divider()
    u_file = st.file_uploader("📸 上传核心原图 (仅用于绘图参照)", type=["jpg", "png", "jpeg"])
    if u_file:
        # 新用法：width="stretch"
        st.image(u_file, caption="原图已载入", width="stretch")

status_box = st.empty()
tab_seo, tab_prod, tab_mod = st.tabs(["📊 SEO 标题优化", "🖼️ 商品主图 (莫兰迪)", "👤 模特佩戴 (实拍感)"])

with tab_seo:
    if st.session_state.seo_txt: st.markdown(st.session_state.seo_txt)
    else: st.caption("（待执行：标题优化基于全平台热搜词库）")

with tab_prod:
    if st.session_state.p_img and isinstance(st.session_state.p_img, str):
        try:
            clean_b64 = st.session_state.p_img.split(",")[-1].strip()
            # 新用法：width="stretch"
            st.image(Image.open(BytesIO(base64.b64decode(clean_b64))), width="stretch")
        except Exception as e: st.error(f"渲染失败: {e}")
    else: st.caption("（待生成）")

with tab_mod:
    if st.session_state.m_img and isinstance(st.session_state.m_img, str):
        try:
            clean_b64 = st.session_state.m_img.split(",")[-1].strip()
            # 新用法：width="stretch"
            st.image(Image.open(BytesIO(base64.b64decode(clean_b64))), width="stretch")
        except Exception as e: st.error(f"渲染失败: {e}")
    else: st.caption("（待生成）")

st.divider()
st.subheader("🚀 专家指令")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
        # 移除标题优化对图片的强制依赖
        res = engine.run_seo(m_txt, u_title, u_cat, u_market)
        if res:
            st.session_state.seo_txt = res
            st.rerun()
        else: st.error("❌ SEO 优化执行失败")

with c2:
    if st.button("🖼️ 执行：商品图优化", use_container_width=True):
        if not u_file: st.warning("⚠️ 绘图任务需上传原图"); st.stop()
        res = engine.run_smart_gen(m_img, "product", u_cat, u_market, u_gender, u_file, status_box)
        if res: 
            st.session_state.p_img = res
            st.rerun()
        else: st.warning("⚠️ 生成失败，请尝试更换渲染模型")

with c3:
    if st.button("👤 执行：模特图优化", use_container_width=True):
        if not u_file: st.warning("⚠️ 绘图任务需上传原图"); st.stop()
        res = engine.run_smart_gen(m_img, "model", u_cat, u_market, u_gender, u_file, status_box)
        if res: 
            st.session_state.m_img = res
            st.rerun()
        else: st.warning("⚠️ 渲染超时，请重试")
