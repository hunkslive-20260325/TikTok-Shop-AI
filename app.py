import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO

# ==========================================
# 🛡️ 模型库（按性价比排序）
# ==========================================
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",  
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
}

ALL_TEXT_MODELS = [
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-chat",
    "openai/gpt-5.4",
    "google/gemini-3.1-flash-image-preview",
    "openrouter/auto"
]

# ==========================================
# ⚡ 安全请求函数
# ==========================================
def safe_post(url, headers, json_data, timeout=60):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except:
        return {"error": "请求失败"}

# ==========================================
# 🌐 在线 Google 翻译接口
# ==========================================
def translate_text(text, target_lang='zh-CN'):
    """
    使用 Google Translate 网页接口翻译
    """
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return ''.join([item[0] for item in res.json()[0]])
    except:
        return text  # 翻译失败返回原文

# ==========================================
# 💎 AI 核心引擎
# ==========================================
class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_V48"
        }

    # 生成图片
    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

        # 提取形状材质
        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": "提取形状、材质。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_in}"}}
                ]}
            ]
        }
        v_res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, v_payload, timeout=60)
        v_desc = v_res_json.get('choices', [{}])[0].get('message', {}).get('content', f"Commercial {cat} jewelry")

        prompt = f"Commercial jewelry photography. {v_desc}. Background: Morandi tones. 8k." \
            if p_type == "product" else f"Fashion photography. {gen} model wearing {v_desc}. 8k."

        res_payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, res_payload, timeout=120)
        choices = res_json.get('choices', [{}])
        msg = choices[0].get('message', {})
        img_list = msg.get('images', [])
        return img_list[0] if img_list else None

    # 生成多条标题
    def run_seo(self, model_id, u_title, u_cat, u_market, num_titles=3):
        titles = []
        for rank in range(num_titles):
            seo_prompt = f"针对 {u_market} 市场优化标题 '{u_title}'。参考 TikTok, Amazon 热搜词，生成第 {rank+1} 条标题。"
            res_json = safe_post(
                "https://openrouter.ai/api/v1/chat/completions",
                self.headers,
                {"model": model_id, "messages": [{"role": "user", "content": seo_prompt}]},
                timeout=60
            )
            content = res_json.get('choices', [{}])[0].get('message', {}).get('content', f"{u_title} {rank+1}")
            # 使用在线翻译
            translation = translate_text(content)
            titles.append((content, translation))
        return titles

# ==========================================
# 图片显示工具
# ==========================================
def display_image(data):
    if isinstance(data, dict) and "url" in data:
        st.image(data["url"], use_column_width=True)
    elif isinstance(data, str):
        if data.startswith("data:image"):
            data = data.split(",")[1]
        st.image(Image.open(BytesIO(base64.b64decode(data))), use_column_width=True)

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
engine = JewelryAIEngineV48(st.secrets.get("OPENROUTER_API_KEY", ""))

# session_state 初始化
for key, default in {"p_img": None, "m_img": None, "seo_titles": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Sidebar
with st.sidebar:
    st.subheader("💎 AM JEWELRY")
    m_txt = st.selectbox("文案/标题模型", ALL_TEXT_MODELS, index=0)
    m_img = st.selectbox("图像渲染模型", list(ALL_DRAWING_MODELS.keys()), index=0)
    u_title = st.text_input("1. 原始标题", "心形项链")
    u_cat = st.selectbox("2. 类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 性别", ["女性", "男性"], horizontal=True)
    u_file = st.file_uploader("📸 上传原图", type=["jpg", "png", "jpeg"])
    if u_file:
        st.image(u_file, use_column_width=True)

# Main UI
st.title("💎 TikTok Shop 饰品 (V48)")

c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 生成标题")
btn_prod = c2.button("🖼️ 生成商品图")
btn_mod = c3.button("👤 生成模特图")

# --- SEO ---
if btn_seo:
    st.session_state.seo_titles = engine.run_seo(m_txt, u_title, u_cat, u_market)
if st.session_state.seo_titles:
    for idx, (eng, cn) in enumerate(st.session_state.seo_titles, 1):
        st.markdown(f"**标题 {idx}:** {eng}")
        st.markdown(f"**中文翻译:** {cn}")
        st.markdown("---")

# --- 商品图 ---
if btn_prod and u_file:
    img = engine.run_smart_gen(m_img, "product", u_cat, u_market, u_gender, u_file)
    if img:
        display_image(img)

# --- 模特图 ---
if btn_mod and u_file:
    img = engine.run_smart_gen(m_img, "model", u_cat, u_market, u_gender, u_file)
    if img:
        display_image(img)
