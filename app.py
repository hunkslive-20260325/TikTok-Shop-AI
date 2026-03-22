import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime
import time

# --- 1. 后端类：模型库扩容与逻辑锁定 ---
class JewelryAIEngineV47:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_Expert_V47"
        }
        # 保持 17 个绘图模型阵容
        self.MODELS_IMG = {
            "openrouter/auto": "openrouter/auto",
            "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
            "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
            "google/gemini-3-pro-image-preview": "google/gemini-3-pro-image-preview",
            "bytedance-seed/seedream-4.5": "bytedance-seed/seedream-4.5",
            "openai/gpt-5-image-mini": "openai/gpt-5-image-mini",
            "openai/gpt-5-image": "openai/gpt-5-image",
            "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro",
            "sourceful/riverflow-v2-pro": "sourceful/riverflow-v2-pro"
        }
        # 【新增项】扩容后的标题生成/文案模型
        self.MODELS_TXT = [
            "deepseek/deepseek-v3.2",
            "deepseek/deepseek-chat",
            "openai/gpt-5.4",
            "openai/gpt-5-mini",
            "openai/gpt-4.1-mini",
            "openai/gpt-4.1",
            "google/gemini-3.1-flash-image-preview",
            "openrouter/auto"
        ]

    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file, status_box):
        mid = self.MODELS_IMG.get(mid_key)
        prog = status_box.progress(0, "🔍 第一步：深度识图分析中...")
        
        b64 = base64.b64encode(file.getvalue()).decode('utf-8')
        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "提取此饰品的形状与核心特征，确保生成图与原图一致。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        }
        try:
            v_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=v_payload, timeout=60)
            v_desc = v_res.json()['choices'][0]['message']['content']
            prog.progress(35, "🎯 第二步：注入商业摄影规范...")
        except:
            v_desc = f"Unique {cat} jewelry"

        # 注入摄影规范 Prompt
        expert_prompt = self.get_expert_prompt(p_type, cat, market, gen, v_desc)
        
        prog.progress(60, f"🎨 第三步：调用 {mid_key} 渲染...")
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
            return None
        except Exception: return None

    def get_expert_prompt(self, p_type, cat, market, gen, v_desc):
        if p_type == "product":
            return (f"Commercial jewelry photography. Product: {v_desc}. Background: Morandi cream tones, silk satin texture with natural folds. "
                    f"Props: Geometric podiums. 45-degree softbox light, premium 8k.")
        else:
            style = "Male model, tanned skin, black knitwear" if gen == "男性" else "Female model, dewy skin, white outfit, soft pink background"
            return f"Fashion photography. {style} wearing {v_desc}. 45-degree side lighting, 8k."

    def run_seo(self, model_id, prompt, file):
        content = [{"type": "text", "text": prompt}]
        if file:
            b64 = base64.b64encode(file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": content}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 标题优化失败，请检查模型权限。"

# --- 2. 前端 UI 布局 ---
st.set_page_config(page_title="饰品专家 V47.1", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV47(api_key)

if "p_img" not in st.session_state: st.session_state.p_img = None
if "m_img" not in st.session_state: st.session_state.m_img = None
if "seo_txt" not in st.session_state: st.session_state.seo_txt = ""

# 顶部精简名称
st.title("💎 TikTok Shop 饰品 (V47.1)")

with st.sidebar:
    st.header("🛡️ 控制台")
    st.divider()
    # 文案模型下拉列表更新
    m_txt = st.selectbox("文案模型", engine.MODELS_TXT)
    m_img = st.selectbox("绘图模型", list(engine.MODELS_IMG.keys()))
    st.divider()
    st.subheader("📋 经营信息")
    u_title = st.text_input("1. 原始标题", "心形项链")
    u_cat = st.selectbox("2. 类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 性别", ["女性", "男性"], horizontal=True)
    st.divider()
    u_file = st.file_uploader("📸 上传商品原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), caption="原图预览", use_container_width=True)

status_box = st.empty()

# 选项卡切换模式
tab_seo, tab_prod, tab_mod = st.tabs(["📊 标题 SEO 优化", "🖼️ 商品图片结果", "👤 模特图片结果"])

with tab_seo:
    if st.session_state.seo_txt: st.markdown(st.session_state.seo_txt)
    else: st.caption("（尚未生成）标题优化结果将在此显示。")

with tab_prod:
    if st.session_state.p_img:
        st.image(Image.open(BytesIO(base64.b64decode(st.session_state.p_img))), use_container_width=True)
    else: st.caption("（尚未生成）莫兰迪主图将在此显示。")

with tab_mod:
    if st.session_state.m_img:
        st.image(Image.open(BytesIO(base64.b64decode(st.session_state.m_img))), use_container_width=True)
    else: st.caption("（尚未生成）模特实拍图将在此显示。")

# 按钮下移至底部
st.divider()
st.subheader("🚀 专家指令")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
        if not u_file: st.warning("请上传图片"); st.stop()
        st.session_state.seo_txt = engine.run_seo(m_txt, f"分析此饰品，为{u_market}市场优化爆款标题。原标题：{u_title}", u_file)
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
