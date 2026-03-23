import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO

# ==========================================
# 🛡️ 全局静态模型库
# ==========================================
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
}

ALL_TEXT_MODELS = [
    "deepseek/deepseek-v3.2", "deepseek/deepseek-chat", "openai/gpt-5.4",
    "google/gemini-3.1-flash-image-preview", "openrouter/auto"
]

# ==========================================
# ⚡ 安全请求函数
# ==========================================
def safe_post(url, headers, json_data, timeout=60):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except requests.Timeout:
        return {"error": "请求超时，请稍后重试"}
    except requests.RequestException as e:
        return {"error": f"请求失败: {str(e)}"}

# ==========================================
# 💎 AI 核心引擎
# ==========================================
class JewelryAIEngineV47:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_V47_Fix"
        }

    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file, log_area):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        log_area.info("⏳ 编码原图中...")
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

        # 提取形状、材质
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
        log_area.info(f"⏳ 正在通过 {mid_key} 渲染...")

        prompt = f"Commercial jewelry photography. {v_desc}. Background: Morandi tones. 8k." \
            if p_type == "product" else f"Fashion photography. {gen} model wearing {v_desc}. 8k."

        res_payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, res_payload, timeout=120)
        if "error" in res_json:
            log_area.error(res_json["error"])
            return None

        with st.expander("📄 查看 API 原始返参 (JSON)"):
            st.json(res_json)

        # 安全提取图片
        choices = res_json.get('choices', [{}])
        msg = choices[0].get('message', {})
        img_list = msg.get('images', [])
        return img_list[0] if img_list else None

    def run_seo(self, model_id, u_title, u_cat, u_market, log_area):
        log_area.info("⏳ 正在请求标题优化...")
        seo_prompt = f"针对 {u_market} 市场优化标题 '{u_title}'。参考 TikTok, Amazon 热搜词。"
        res_json = safe_post(
            "https://openrouter.ai/api/v1/chat/completions",
            self.headers,
            {"model": model_id, "messages": [{"role": "user", "content": seo_prompt}]},
            timeout=60
        )
        if "error" in res_json:
            log_area.error(res_json["error"])
            return f"Commercial {u_cat} jewelry"
        with st.expander("📄 查看 API 原始返参 (JSON)"):
            st.json(res_json)
        return res_json.get('choices', [{}])[0].get('message', {}).get('content', f"Commercial {u_cat} jewelry")

# ==========================================
# 🖼️ 显示图片工具函数
# ==========================================
def display_image(data):
    if isinstance(data, dict) and "url" in data:
        st.image(data["url"], use_column_width=True)
    elif isinstance(data, str):
        try:
            if data.startswith("data:image"):
                data = data.split(",")[1]
            st.image(Image.open(BytesIO(base64.b64decode(data))), use_column_width=True)
        except Exception as e:
            st.error(f"显示失败: {e}")

# ==========================================
# 🖥️ Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V47.7", layout="wide")
engine = JewelryAIEngineV47(st.secrets.get("OPENROUTER_API_KEY", ""))

# session_state 初始化
for key, default in {"p_img": None, "m_img": None, "seo_txt": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Sidebar
with st.sidebar:
    try:
        st.image(Image.open("logo.PNG"), use_column_width=True)
    except:
        st.subheader("💎 AM JEWELRY")
    st.markdown("---")
    m_txt = st.selectbox("文案/标题模型", ALL_TEXT_MODELS) 
    m_img = st.selectbox("图像渲染模型", list(ALL_DRAWING_MODELS.keys())) 
    u_title = st.text_input("1. 原始标题", "心形项链")
    u_cat = st.selectbox("2. 类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 性别", ["女性", "男性"], horizontal=True)
    u_file = st.file_uploader("📸 上传原图", type=["jpg", "png", "jpeg"])
    if u_file:
        st.image(u_file, use_column_width=True)

# Main
st.title("💎 TikTok Shop 饰品 (V47.7)")
c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 标题 SEO 优化")
btn_prod = c2.button("🖼️ 商品图优化")
btn_mod = c3.button("👤 模特图优化")

tab_seo, tab_prod, tab_mod = st.tabs(["📊 SEO 优化结果", "🖼️ 商品图结果", "👤 模特图结果"])

# --- SEO ---
with tab_seo:
    log_seo = st.empty()
    if btn_seo:
        with st.spinner("⏳ 正在生成标题..."):
            res = engine.run_seo(m_txt, u_title, u_cat, u_market, log_seo)
            st.session_state.seo_txt = res
            log_seo.success("✅ 成功！")
    if st.session_state.seo_txt:
        st.markdown(st.session_state.seo_txt)

# --- 商品图 ---
with tab_prod:
    log_prod = st.empty()
    if btn_prod:
        if not u_file: st.warning("请上传图片"); st.stop()
        with st.spinner("⏳ 正在生成商品图..."):
            res = engine.run_smart_gen(m_img, "product", u_cat, u_market, u_gender, u_file, log_prod)
            if res: st.session_state.p_img = res; log_prod.success("✅ 成功！")
            else: log_prod.error("❌ 失败")
    if st.session_state.p_img:
        display_image(st.session_state.p_img)

# --- 模特图 ---
with tab_mod:
    log_mod = st.empty()
    if btn_mod:
        if not u_file: st.warning("请上传图片"); st.stop()
        with st.spinner("⏳ 正在生成模特图..."):
            res = engine.run_smart_gen(m_img, "model", u_cat, u_market, u_gender, u_file, log_mod)
            if res: st.session_state.m_img = res; log_mod.success("✅ 成功！")
            else: log_mod.error("❌ 失败")
    if st.session_state.m_img:
        display_image(st.session_state.m_img)
