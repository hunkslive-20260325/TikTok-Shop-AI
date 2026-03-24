import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import re

# ==========================================
# 模型库与配置
# ==========================================
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
}

ALL_TEXT_MODELS = ["openrouter/auto", "deepseek/deepseek-v3.2", "deepseek/deepseek-chat", "openai/gpt-5.4"]

# ==========================================
# UI 样式定制 (CSS)
# ==========================================
st.set_page_config(page_title="AM JEWELRY V48", layout="wide")

st.markdown("""
    <style>
    /* 1. 日志区样式 */
    .log-container {
        height: 65px;
        background-color: #f1f3f5; /* 经典的工业浅灰色 */
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #6c757d;
        font-size: 14px;
        margin-bottom: 20px;
        border: 1px solid #dee2e6;
    }
    
    /* 2. 选项卡占位符样式 */
    .empty-placeholder {
        height: 400px;
        background-color: #f8f9fa;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #adb5bd;
        border: 1px dashed #ced4da;
        margin-top: 10px;
    }

    /* 3. 让 Radio 横向排列 */
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
    
    /* 4. 缩小上传组件高度 */
    div[data-testid="stFileUploader"] section { padding: 0.5rem; min-height: 80px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 核心功能逻辑
# ==========================================
def safe_post(url, headers, json_data):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=120)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "HTTP-Referer": "https://streamlit.io"}

    def run_smart_gen(self, mid_key, p_type, title, gender, category, file):
        try:
            mid = ALL_DRAWING_MODELS.get(mid_key)
            b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
            focus_parts = {"项链": "neck", "戒指": "fingers", "手链": "wrist", "耳环": "ear", "头饰": "hair"}
            target = focus_parts.get(category, "body")

            if p_type == "模特图":
                if gender == "男性":
                    prompt = f"Professional male model wearing {title} {category}, focus on {target}, 8k, urban style."
                else:
                    prompt = f"East Asian female model wearing {title} {category}, focus on {target}, 8k, creamy skin."
            else:
                prompt = f"Macro product shot of {title} {category}, concrete podium, palm shadows, 8k."

            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}]}],
                "modalities": ["image"]
            }
            res = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload)
            return res.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
        except: return None

# ==========================================
# Sidebar 布局
# ==========================================
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 初始化 Session State
for k in ["logs", "seo_res", "p_imgs", "m_imgs"]:
    if k not in st.session_state: st.session_state[k] = "" if k in ["logs", "seo_res"] else []

with st.sidebar:
    st.subheader("💎 AM JEWELRY V48-20260324")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美"])
    u_category = st.selectbox("饰品类型", ["项链","戒指","手链","耳环","头饰"], index=0)
    u_gender = st.radio("目标人群", ["女性","男性"])
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
    
    st.divider()
    # 按钮上移
    c1, c2, c3 = st.columns(3)
    btn_seo = c1.button("标题")
    btn_prod = c2.button("商品")
    btn_mod = c3.button("模特")
    
    u_img_count = st.selectbox("生成图片数量", [1, 2, 4], index=0)
    model_text = st.selectbox("优化标题模型", ALL_TEXT_MODELS)
    model_img = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=4)

# ==========================================
# 右侧主界面 (日志区 + 选项卡)
# ==========================================

# 1. 固定高度日志输出位置
log_msg = st.session_state.logs if st.session_state.logs else "暂无日志信息"
st.markdown(f'<div class="log-container">{log_msg}</div>', unsafe_allow_html=True)

# 2. 选项卡切换
tab_seo, tab_prod, tab_mod = st.tabs(["📝 优化标题", "🖼️ 优化商品图", "👤 优化模特图"])

with tab_seo:
    if st.session_state.seo_res:
        st.info(st.session_state.seo_res)
    else:
        st.markdown('<div class="empty-placeholder">暂无内容</div>', unsafe_allow_html=True)

with tab_prod:
    if st.session_state.p_imgs:
        for i, img in enumerate(st.session_state.p_imgs):
            st.image(img, width=800, caption=f"商品图版本 {i+1}")
    else:
        st.markdown('<div class="empty-placeholder">暂无内容</div>', unsafe_allow_html=True)

with tab_mod:
    if st.session_state.m_imgs:
        for i, img in enumerate(st.session_state.m_imgs):
            st.image(img, width=800, caption=f"模特图版本 {i+1}")
    else:
        st.markdown('<div class="empty-placeholder">暂无内容</div>', unsafe_allow_html=True)

# ==========================================
# 按钮动作逻辑
# ==========================================
if btn_seo:
    st.session_state.logs = "正在优化标题..."
    st.rerun() # 立即刷新日志状态（实际项目中可使用 st.empty 动态更新）

if btn_prod and u_file:
    st.session_state.p_imgs = []
    for i in range(u_img_count):
        st.session_state.logs = f"正在生成商品图 {i+1}/{u_img_count}..."
        # 这里为了演示简化了逻辑，实际调用应在循环中更新 session
        res = engine.run_smart_gen(model_img, "商品图", u_title, u_gender, u_category, u_file)
        if res: st.session_state.p_imgs.append(res)
    st.session_state.logs = "商品图生成完毕"
    st.rerun()

if btn_mod and u_file:
    st.session_state.m_imgs = []
    for i in range(u_img_count):
        st.session_state.logs = f"正在生成模特图 {i+1}/{u_img_count}..."
        res = engine.run_smart_gen(model_img, "模特图", u_title, u_gender, u_category, u_file)
        if res: st.session_state.m_imgs.append(res)
    st.session_state.logs = "模特图生成完毕"
    st.rerun()
