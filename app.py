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
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-chat",
    "openai/gpt-5.4",
    "google/gemini-3.1-flash-image-preview",
    "openrouter/auto"
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
        return {"error": str(e)}

# ------------------------------------------
# 显示图片（支持 base64 和嵌套 image_url）
# ------------------------------------------
def display_image(data):
    """
    显示图片：
    支持：
    - dict 包含 "url" 或 "image_url": {"url": ...}
    - base64 字符串
    """
    try:
        if isinstance(data, dict):
            if "url" in data:
                st.image(data["url"], use_column_width=True)
            elif "image_url" in data and "url" in data["image_url"]:
                st.image(data["image_url"]["url"], use_column_width=True)
            else:
                st.error("⚠️ 图片数据格式不支持")
                st.json(data)
        elif isinstance(data, str):
            if data.startswith("data:image"):
                header, data = data.split(",", 1)
            img_bytes = base64.b64decode(data)
            image = Image.open(BytesIO(img_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            st.image(image, use_column_width=True)
        else:
            st.error("⚠️ 图片数据格式不支持")
            st.json(data)
    except Exception as e:
        st.error(f"图片解析失败: {e}")
        if isinstance(data, str):
            st.text(f"Base64 前100字符: {data[:100]}")
        else:
            st.json(data)

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

    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": f"生成 {p_type} 图，标题：{title}，饰品类型：{category}，目标人群：{gender}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_in}"}}
                ]}
            ]
        }
        v_res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, v_payload, timeout=60)
        v_desc = v_res_json.get('choices', [{}])[0].get('message', {}).get('content', f"{p_type} {category} image")

        prompt = f"{p_type} photography. {v_desc}. 8k, 高端饰品风格，背景色和道具符合要求。"

        res_payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }
        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, res_payload, timeout=120)

        choices = res_json.get('choices', [{}])
        msg = choices[0].get('message', {})
        img_list = msg.get('images', [])
        if img_list and isinstance(img_list, list):
            return img_list[0]  # 返回第一个图片
        else:
            return None, res_json  # 返回失败信息方便调试

    def run_seo(self, model_id, title, market, gender, category):
        seo_prompt = f"""
请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，生成三条优化标题，按点击率和浏览量综合排序。
输出格式：
推荐标题一：****
中文翻译：****
推荐理由：****
推荐标题二：****
中文翻译：****
推荐理由：****
推荐标题三：****
中文翻译：****
推荐理由：****
"""
        res_json = safe_post(
            "https://openrouter.ai/api/v1/chat/completions",
            self.headers,
            {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]},
            timeout=60
        )
        content = res_json.get('choices',[{}])[0].get('message',{}).get('content', "")
        return content.strip() if content else res_json

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
engine = JewelryAIEngineV48(st.secrets.get("OPENROUTER_API_KEY", ""))

for key in ["seo_result","p_img","m_img"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Sidebar 输入
with st.sidebar:
    st.subheader("💎 AM JEWELRY")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美","中东","非洲"], index=0)
    u_category = st.selectbox("饰品类型", ["头饰","耳环","耳钉","项链","手链","手镯","戒指","脚链"], index=3)
    u_gender = st.radio("目标人群", ["女性","男性"], index=0)
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
    u_text_model = st.selectbox("优化标题模型", ALL_TEXT_MODELS, index=0)
    u_image_model = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=0)

    if st.button("重置"):
        u_title = ""
        u_file = None
        st.session_state.seo_result = None
        st.session_state.p_img = None
        st.session_state.m_img = None
        st.experimental_rerun()

# 主区
st.title("💎 TikTok Shop 饰品生成 V48")
c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 生成标题")
btn_prod = c2.button("🖼️ 生成商品图")
btn_mod = c3.button("👤 生成模特图")

# 生成标题
if btn_seo:
    log_area = st.empty()
    log_area.info("⏳ 标题生成中...")
    try:
        seo_result = engine.run_seo(
            model_id=u_text_model,
            title=u_title,
            market=u_market,
            gender=u_gender,
            category=u_category
        )
        st.session_state.seo_result = seo_result
        if isinstance(seo_result, str):
            log_area.success("✅ 标题生成完成")
        else:
            log_area.error("❌ 标题生成失败")
            st.json(seo_result)
    except Exception as e:
        log_area.error(f"生成标题时发生错误: {e}")

# 生成商品图 / 模特图
if (btn_prod or btn_mod) and u_file:
    log_area = st.empty()
    try:
        if btn_prod:
            log_area.info("⏳ 商品图生成中...")
            p_img = engine.run_smart_gen(
                u_image_model, "商品图", u_title, u_gender, u_category, u_market, u_file
            )
            st.session_state.p_img = p_img
            if p_img:
                log_area.success("✅ 商品图生成成功")
            else:
                log_area.error("❌ 商品图生成失败")

        if btn_mod:
            log_area.info("⏳ 模特图生成中...")
            m_img = engine.run_smart_gen(
                u_image_model, "模特图", u_title, u_gender, u_category, u_market, u_file
            )
            st.session_state.m_img = m_img
            if m_img:
                log_area.success("✅ 模特图生成成功")
            else:
                log_area.error("❌ 模特图生成失败")

    except Exception as e:
        log_area.error(f"生成图片时发生错误: {e}")
        st.exception(e)

# Tabs 显示图片
tab_prod, tab_model = st.tabs(["🖼️ 商品图","👤 模特图"])
with tab_prod:
    if st.session_state.p_img:
        display_image(st.session_state.p_img)
with tab_model:
    if st.session_state.m_img:
        display_image(st.session_state.m_img)

# 显示优化标题
if st.session_state.seo_result and isinstance(st.session_state.seo_result, str):
    pattern = r"推荐标题[一二三]：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)\n"
    matches = re.findall(pattern, st.session_state.seo_result + "\n", re.DOTALL)
    colors = [
        "linear-gradient(90deg, #f0a500, #f4c542)", 
        "linear-gradient(90deg, #f4c542, #fde8a9)", 
        "linear-gradient(90deg, #fde8a9, #fff4cc)"
    ]
    st.subheader("✨ 优化标题")
    for idx, (title, cn, reason) in enumerate(matches[:3]):
        color = colors[idx] if idx < len(colors) else "linear-gradient(90deg, #fde8a9, #fff4cc)"
        st.markdown(
            f"""
            <div style="
                background: {color};
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            ">
                <div style="color:#222; font-size:20px; font-weight:bold; margin-bottom:8px;">{title}</div>
                <div style="color:#444; font-size:15px; margin-bottom:5px;">中文翻译: {cn}</div>
                <div style="color:#555; font-size:14px;">推荐理由: {reason}</div>
            </div>
            """, unsafe_allow_html=True
        )
