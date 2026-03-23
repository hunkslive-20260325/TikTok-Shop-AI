import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime
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
# 显示图片 + 下载按钮
# ------------------------------------------
def display_image(data, log_area=None, filename="image.png"):
    try:
        if log_area:
            log_area.info(f"🔹 原始模型返回数据类型: {type(data)}")

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

        if not img_data:
            raise ValueError("未找到可用图片字段")

        # Base64 格式
        if isinstance(img_data, str) and img_data.startswith("data:image"):
            img_base64 = img_data.split(",")[1]
            img = Image.open(BytesIO(base64.b64decode(img_base64)))
        elif isinstance(img_data, str) and img_data.startswith("http"):
            img = img_data
        else:
            try:
                img = Image.open(BytesIO(base64.b64decode(img_data)))
            except:
                raise ValueError(f"图片格式未知: {type(img_data)}")

        # 修复宽度问题
        st.image(img, use_container_width=True)

        # 下载按钮
        if isinstance(img, Image.Image):
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.download_button(
                label="⬇️ 下载图片",
                data=buf.getvalue(),
                file_name=filename,
                mime="image/png"
            )

        if log_area:
            log_area.success(f"✅ 图片显示成功")
    except Exception as e:
        if log_area:
            log_area.error(f"❌ 图片显示失败: {e}")
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

    # 核心需求优化部分：根据模特特征生成针对性 Prompt
    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file, log_area=None):
        try:
            mid = ALL_DRAWING_MODELS.get(mid_key)
            if not file:
                if log_area: log_area.error("❌ 未上传原图")
                return None
            
            b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

            # --- 高级摄影美术指导 Prompt 开始 ---
            if p_type == "模特图" and gender == "男性":
                prompt = (
                    f"Luxury jewelry campaign photography for {market} market. Model: deep tan skin, stubble, mature masculine facial contour. "
                    f"Outfit: high-quality black crew neck knitwear as a dark background. Focus on {category}: {title}. "
                    f"Background: blurred taupe and sand earth tones, minimalist studio, depth of field. "
                    f"Lighting: side-backlighting (rim light), 45-degree key light, strong highlights and shadows on metallic texture. "
                    f"Composition: Macro-Close-up (mouth to chest), interaction gesture: model hand pulling/tugging the chain. "
                    f"Vibe: high contrast, sharp details on beard and jewelry, sophisticated masculine tension, 8k resolution."
                )
            elif p_type == "模特图" and gender == "女性":
                prompt = (
                    f"Ethereal jewelry editorial photography for {market} market. Model: white luminous dewy skin, soft aesthetic. "
                    f"Makeup: soft pink tones, nude/translucent pink nails. Hair: natural wavy black hair with slight wisps. "
                    f"Outfit: pure white or off-white silk clothing. Focus on {category}: {title}. "
                    f"Lighting: soft diffused window light, no harsh shadows, bright and airy. "
                    f"Composition: large negative space, macro close-up of neck and collarbone, side profile, eyes/upper face cropped out. "
                    f"Interaction: finger gently touching the necklace or neckline. "
                    f"Vibe: serene, elegant, dreamy bokeh, 85mm f/1.8 lens effect, high-end fashion magazine quality."
                )
            else:
                # 商品图或其他情况
                prompt = (
                    f"High-end product photography of {title} {category}, retain the original product from uploaded image, "
                    f"1:1 ratio, high-end jewelry style, background: warm Morandi tones, geometric props, soft lighting, sharp focus."
                )
            # --- 高级摄影美术指导 Prompt 结束 ---

            payload = {
                "model": mid,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}
                    ]}
                ],
                "modalities": ["image"]
            }

            if log_area:
                log_area.info("⏳ 图片生成请求发送中...")
            res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload, timeout=120)
            
            choices = res_json.get('choices', [{}])
            msg = choices[0].get('message', {})
            img_list = msg.get('images', [])
            
            if img_list:
                if log_area: log_area.success("✅ 图片生成成功")
                return img_list[0]
            else:
                if log_area: log_area.error("❌ 图片生成失败，无返回图像")
                return res_json
        except Exception as e:
            if log_area: log_area.error(f"❌ 生成图片异常: {e}")
            return {"error": str(e)}

    # 标题生成
    def run_seo(self, model_id, title, market, gender, category, log_area=None):
        try:
            seo_prompt = (
                f"请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，"
                "生成三条优化标题，按点击率和浏览量综合排序，输出格式包含中文翻译和推荐理由。"
            )
            if log_area: log_area.info("⏳ 标题生成请求发送中...")
            res_json = safe_post(
                "https://openrouter.ai/api/v1/chat/completions",
                self.headers,
                {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]},
                timeout=60
            )
            content = res_json.get('choices',[{}])[0].get('message',{}).get('content', "")
            return content.strip()
        except Exception as e:
            return str(e)

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

for key in ["seo_result","p_img","m_img"]:
    if key not in st.session_state:
        st.session_state[key] = None

with st.sidebar:
    st.subheader("💎 AM JEWELRY")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美","中东","非洲"], index=0)
    u_category = st.selectbox("饰品类型", ["头饰","耳环","耳钉","项链","手链","手镯","戒指","脚链"], index=3)
    u_gender = st.radio("目标人群", ["女性","男性"], index=0)
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])

    model_text = st.selectbox("优化标题模型", ALL_TEXT_MODELS, index=0)
    model_img = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=1)

    if st.button("重置"):
        st.session_state.seo_result = None
        st.session_state.p_img = None
        st.session_state.m_img = None
        st.rerun()

st.title("💎 TikTok Shop 饰品生成 V48")
c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 生成标题")
btn_prod = c2.button("🖼️ 生成商品图")
btn_mod = c3.button("👤 生成模特图")

log_area = st.empty()

if btn_seo:
    st.session_state.seo_result = engine.run_seo(model_text, u_title, u_market, u_gender, u_category, log_area)

if st.session_state.seo_result:
    st.subheader("优化标题")
    pattern = r"推荐标题[一二三]：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)\n"
    matches = re.findall(pattern, st.session_state.seo_result+"\n", re.DOTALL)
    colors = ["#f0a500","#f4c542","#fde8a9"]
    if matches:
        for idx,(title,cn,reason) in enumerate(matches[:3]):
            color = colors[idx] if idx < len(colors) else "#fde8a9"
            st.markdown(
                f"""
                <div style="background-color:{color};padding:15px;border-radius:12px;margin-bottom:10px;box-shadow: 1px 1px 6px rgba(0,0,0,0.2);">
                    <div style="color:#333;font-size:18px;font-weight:bold;">{title}</div>
                    <div style="margin-top:5px;color:#444;font-size:14px;">
                        中文翻译: {cn}<br>
                        推荐理由: {reason}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
    else:
        st.info(st.session_state.seo_result)

if (btn_prod or btn_mod) and u_file:
    if btn_prod:
        st.session_state.p_img = engine.run_smart_gen(model_img, "商品图", u_title, u_gender, u_category, u_market, u_file, log_area)
    if btn_mod:
        st.session_state.m_img = engine.run_smart_gen(model_img, "模特图", u_title, u_gender, u_category, u_market, u_file, log_area)

if st.session_state.p_img or st.session_state.m_img:
    tab_prod, tab_model = st.tabs(["🖼️ 商品图","👤 模特图"])
    with tab_prod:
        if st.session_state.p_img:
            display_image(st.session_state.p_img, log_area, filename="product.png")
    with tab_model:
        if st.session_state.m_img:
            display_image(st.session_state.m_img, log_area, filename="model.png")
