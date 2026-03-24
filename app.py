import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import json
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
    /* 1. 日志区样式：稍微增加高度以容纳更多状态 */
    .log-container {
        min-height: 65px;
        background-color: #f1f3f5;
        border-radius: 8px;
        padding: 10px 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: #495057;
        font-size: 14px;
        margin-bottom: 20px;
        border: 1px solid #dee2e6;
    }
    .log-status { font-weight: bold; color: #0d6efd; }
    
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

    /* 3. 侧边栏样式微调 */
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
    div[data-testid="stFileUploader"] section { padding: 0.5rem; min-height: 80px; }
    
    /* 4. JSON 渲染区样式 */
    .json-box {
        font-family: monospace;
        background-color: #212529;
        color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        font-size: 12px;
        overflow-x: auto;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 核心功能逻辑
# ==========================================
def safe_post(url, headers, json_data):
    """安全请求函数，返回元组 (数据, 原始响应)"""
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=120)
        res_json = res.json()
        return res_json, res_json
    except Exception as e:
        error_msg = {"error": str(e), "status": "failed"}
        return error_msg, error_msg

def process_and_display(img_data, caption, idx):
    """处理并展示图片，解决 URL/Base64 混用问题"""
    try:
        if isinstance(img_data, str) and (img_data.startswith("http://") or img_data.startswith("https://")):
            st.image(img_data, width=800, caption=caption)
        else:
            if isinstance(img_data, str) and "base64," in img_data:
                img_data = img_data.split("base64,")[1]
            img_bytes = base64.b64decode(img_data)
            img = Image.open(BytesIO(img_bytes))
            img = img.resize((800, 800), Image.Resampling.LANCZOS)
            st.image(img, width=800, caption=caption)
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.download_button(label=f"⬇️ 下载 {caption}", data=buf.getvalue(), file_name=f"{caption}.png", mime="image/png", key=f"dl_{idx}")
    except Exception as e:
        st.error(f"图片显示异常: {e}")

class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "HTTP-Referer": "https://streamlit.io"}

    def run_smart_gen(self, mid_key, p_type, title, gender, category, file):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
        
        if p_type == "模特图":
            p_style = "Elegant East Asian female, creamy skin" if gender == "女性" else "Rugged male model, sharp jawline"
            prompt = f"High-end jewelry photography, focus on {category}, {p_style}, wearing {title}, 8k resolution."
        else:
            prompt = f"Macro shot of {title} {category} on concrete podium, palm shadows, Morandi tones, 8k."

        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}]}],
            "modalities": ["image"]
        }
        data, raw = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload)
        
        img_res = None
        try:
            img_res = data['choices'][0]['message']['images'][0]
        except:
            img_res = None
        return img_res, raw

    def run_seo(self, model_id, title, market, gender, category):
        prompt = f"为{title}生成三条针对{market}市场{gender}用户的{category}SEO标题，包含翻译和理由。"
        data, raw = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, {"model": model_id, "messages":[{"role":"user","content":prompt}]})
        
        content = ""
        try:
            content = data['choices'][0]['message']['content']
        except:
            content = "解析失败，请查看日志。"
        return content, raw

# ==========================================
# 主界面处理
# ==========================================
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 初始化 Session State
if "logs" not in st.session_state: st.session_state.logs = "等待操作..."
if "raw_response" not in st.session_state: st.session_state.raw_response = {}
if "seo_res" not in st.session_state: st.session_state.seo_res = ""
if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

with st.sidebar:
    st.subheader("💎 AM JEWELRY V48-20260324")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美"])
    u_category = st.selectbox("饰品类型", ["项链","戒指","手链","耳钉","头饰"], index=0)
    u_gender = st.radio("目标人群", ["女性","男性"])
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    btn_seo = c1.button("✨ 标题")
    btn_prod = c2.button("🖼️ 商品")
    btn_mod = c3.button("👤 模特")
    
    u_img_count = st.selectbox("生成图片数量", [1, 2, 4], index=1)
    model_text = st.selectbox("优化标题模型", ALL_TEXT_MODELS)
    model_img = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=4)

# --- 右侧主界面 ---

# 1. 增强版日志输出区
with st.container():
    st.markdown(f"""
        <div class="log-container">
            <div><span class="log-status">当前状态：</span>{st.session_state.logs}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 原始返参打印（如果存在数据则显示）
    if st.session_state.raw_response:
        with st.expander("🔍 查看模型原始返回参数 (API Response JSON)", expanded=False):
            st.json(st.session_state.raw_response)

# 2. 选项卡展示
tab_seo, tab_prod, tab_mod = st.tabs(["📝 优化标题", "🖼️ 优化商品图", "👤 优化模特图"])

with tab_seo:
    if st.session_state.seo_res:
        st.info(st.session_state.seo_res)
    else:
        st.markdown('<div class="empty-placeholder">暂无标题内容</div>', unsafe_allow_html=True)

with tab_prod:
    if st.session_state.p_imgs:
        for idx, img in enumerate(st.session_state.p_imgs):
            process_and_display(img, f"商品图版本 {idx+1}", f"p_{idx}")
    else:
        st.markdown('<div class="empty-placeholder">暂无商品图内容</div>', unsafe_allow_html=True)

with tab_mod:
    if st.session_state.m_imgs:
        for idx, img in enumerate(st.session_state.m_imgs):
            process_and_display(img, f"模特图版本 {idx+1}", f"m_{idx}")
    else:
        st.markdown('<div class="empty-placeholder">暂无模特图内容</div>', unsafe_allow_html=True)

# ==========================================
# 逻辑执行
# ==========================================
if btn_seo:
    st.session_state.logs = "⏳ 正在请求标题模型..."
    res_text, raw = engine.run_seo(model_text, u_title, u_market, u_gender, u_category)
    st.session_state.seo_res = res_text
    st.session_state.raw_response = raw
    st.session_state.logs = "✅ 标题生成尝试完成"
    st.rerun()

if btn_prod and u_file:
    st.session_state.p_imgs = []
    all_raws = []
    for i in range(u_img_count):
        st.session_state.logs = f"⏳ 正在生成商品图 ({i+1}/{u_img_count})..."
        res_img, raw = engine.run_smart_gen(model_img, "商品图", u_title, u_gender, u_category, u_file)
        if res_img: st.session_state.p_imgs.append(res_img)
        all_raws.append(raw)
    st.session_state.raw_response = {"batch_results": all_raws}
    st.session_state.logs = "✅ 商品图批量生成尝试完成"
    st.rerun()

if btn_mod and u_file:
    st.session_state.m_imgs = []
    all_raws = []
    for i in range(u_img_count):
        st.session_state.logs = f"⏳ 正在生成模特图 ({i+1}/{u_img_count})..."
        res_img, raw = engine.run_smart_gen(model_img, "模特图", u_title, u_gender, u_category, u_file)
        if res_img: st.session_state.m_imgs.append(res_img)
        all_raws.append(raw)
    st.session_state.raw_response = {"batch_results": all_raws}
    st.session_state.logs = "✅ 模特图批量生成尝试完成"
    st.rerun()
