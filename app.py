import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import re

# ==========================================
# 模型库
# ==========================================
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
}

ALL_TEXT_MODELS = [
    "openrouter/auto",
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-chat",
    "openai/gpt-5.4",
]

# ------------------------------------------
# 安全请求函数
# ------------------------------------------
def safe_post(url, headers, json_data, timeout=60):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": f"请求失败: {e}"}

# ------------------------------------------
# 显示图片 + 下载按钮 (支持 800x800 缩放)
# ------------------------------------------
def display_image(data, log_area=None, filename="image.png"):
    try:
        img_data = None
        if isinstance(data, dict):
            if "images" in data and data["images"]:
                img_data = data["images"][0]
            elif "image_url" in data:
                img_data = data["image_url"].get("url")
            elif "content" in data:
                img_data = data["content"]
        elif isinstance(data, str):
            img_data = data

        if not img_data: return

        # 解码
        if isinstance(img_data, str) and img_data.startswith("data:image"):
            img_base64 = img_data.split(",")[1]
            img = Image.open(BytesIO(base64.b64decode(img_base64)))
        elif isinstance(img_data, str) and img_data.startswith("http"):
            img = img_data # 此时是 URL
        else:
            img = Image.open(BytesIO(base64.b64decode(img_data)))

        # 统一大小为 800x800
        if isinstance(img, Image.Image):
            img = img.resize((800, 800), Image.Resampling.LANCZOS)

        st.image(img, use_container_width=False, width=800)

        if isinstance(img, Image.Image):
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.download_button(label="⬇️ 下载", data=buf.getvalue(), file_name=filename, mime="image/png", key=f"dl_{hash(str(data))}")
    except Exception as e:
        st.error(f"图片显示失败: {e}")

# ==========================================
# AI 引擎
# ==========================================
class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_V48"
        }

    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file, log_area=None):
        try:
            mid = ALL_DRAWING_MODELS.get(mid_key)
            b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

            focus_parts = {"项链": "neck", "戒指": "fingers", "手链": "wrist", "手镯": "wrist", "耳环": "ear", "耳钉": "ear", "头饰": "hair", "脚链": "ankle"}
            target_part = focus_parts.get(category, "body")

            if p_type == "模特图" and gender == "男性":
                prompt = f"Professional male model wearing {title} {category}, focusing on {target_part}. Natural skin, black waffle-knit sweater, gray studio background, 8k."
            elif p_type == "模特图" and gender == "女性":
                prompt = f"Elegant East Asian female model wearing {title} {category}, focusing on {target_part}. Creamy skin, white linen shirt, beige background, 8k."
            else:
                prompt = f"Macro product photography of {title} {category} on concrete podium, palm leaf shadows, Morandi tones, 8k."

            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}]}],
                "modalities": ["image"]
            }
            res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload, timeout=120)
            return res_json.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
        except:
            return None

    def run_seo(self, model_id, title, market, gender, category):
        prompt = f"针对{title}生成三条{market}市场{gender}用{category}的SEO标题，含中文翻译和理由。"
        res = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, {"model": model_id, "messages":[{"role":"user","content":prompt}]})
        return res.get('choices',[{}])[0].get('message',{}).get('content', "")

# ==========================================
# Streamlit UI 优化
# ==========================================
st.set_page_config(page_title="AM JEWELRY V48", layout="wide")

# CSS 注入：调整 Radio 横向展示 + 缩小 FileUploader 高度
st.markdown("""
    <style>
    /* 让 Radio 横向排列 */
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
    /* 缩小上传组件高度 */
    .stFileUploader { padding-top: 0rem; }
    div[data-testid="stFileUploader"] section { padding: 0.5rem; min-height: 80px; }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []
if "seo_result" not in st.session_state: st.session_state.seo_result = None

with st.sidebar:
    st.subheader("💎 AM JEWELRY V48-20260324")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美","中东","非洲"])
    u_category = st.selectbox("饰品类型", ["头饰","耳环","耳钉","项链","手链","手镯","戒指","脚链"], index=3)
    u_gender = st.radio("目标人群", ["女性","男性"])
    
    # 缩小高度的上传组件
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
    
    st.divider()
    
    # 功能按钮移至此处
    c1, c2, c3 = st.columns(3)
    btn_seo = c1.button("标题")
    btn_prod = c2.button("商品")
    btn_mod = c3.button("模特")
    
    u_img_count = st.selectbox("生成图片数量", [1, 2, 4], index=0)
    model_text = st.selectbox("优化标题模型", ALL_TEXT_MODELS)
    model_img = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=4)

# --- 主界面逻辑 ---
log_area = st.empty()

if btn_seo:
    st.session_state.seo_result = engine.run_seo(model_text, u_title, u_market, u_gender, u_category)

if btn_prod and u_file:
    st.session_state.p_imgs = []
    for i in range(u_img_count):
        log_area.info(f"正在生成第 {i+1}/{u_img_count} 张商品图...")
        res = engine.run_smart_gen(model_img, "商品图", u_title, u_gender, u_category, u_market, u_file)
        if res: st.session_state.p_imgs.append(res)
    log_area.success("商品图生成完毕")

if btn_mod and u_file:
    st.session_state.m_imgs = []
    for i in range(u_img_count):
        log_area.info(f"正在生成第 {i+1}/{u_img_count} 张模特图...")
        res = engine.run_smart_gen(model_img, "模特图", u_title, u_gender, u_category, u_market, u_file)
        if res: st.session_state.m_imgs.append(res)
    log_area.success("模特图生成完毕")

# 展示区
if st.session_state.seo_result:
    with st.expander("📝 查看优化标题", expanded=True):
        st.write(st.session_state.seo_result)

if st.session_state.p_imgs or st.session_state.m_imgs:
    t1, t2 = st.tabs(["🖼️ 商品展示", "👤 模特展示"])
    with t1:
        for idx, img in enumerate(st.session_state.p_imgs):
            st.markdown(f"**版本 {idx+1}**")
            display_image(img, filename=f"prod_{idx}.png")
    with t2:
        for idx, img in enumerate(st.session_state.m_imgs):
            st.markdown(f"**版本 {idx+1}**")
            display_image(img, filename=f"model_{idx}.png")
