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
# 显示图片
# ------------------------------------------
def display_image(data):
    try:
        if isinstance(data, dict) and "url" in data:
            st.image(data["url"], use_column_width=True)
        elif isinstance(data, str):
            if data.startswith("data:image"):
                data = data.split(",")[1]
            st.image(Image.open(BytesIO(base64.b64decode(data))), use_column_width=True)
        else:
            st.error("图片数据格式不支持")
    except Exception as e:
        st.error(f"图片解析失败: {e}")

# ==========================================
# AI 引擎
# ==========================================
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_V48"
        }

    # 商品/模特图生成
    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file, log_area=None):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        if not file:
            if log_area: log_area.error("未上传原图")
            return None
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
        if log_area: log_area.info(f"⏳ {p_type} 生成中... {datetime.now().strftime('%H:%M:%S')}")

        payload = {
            "model": mid,
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": f"生成 {p_type} 图，标题：{title}，饰品类型：{category}，目标人群：{gender}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_in}"}}
                ]}
            ]
        }

        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload, timeout=120)
        if log_area: log_area.info(f"{p_type} 返回原始 JSON:\n{res_json}")

        # 尝试提取图片数据
        result = None
        try:
            if isinstance(res_json, dict):
                if res_json.get("type") == "image_url":
                    result = res_json["image_url"]["url"]
                else:
                    choices = res_json.get("choices", [{}])
                    msg = choices[0].get("message", {})
                    img_list = msg.get("images", [])
                    if img_list:
                        result = img_list[0]
            elif isinstance(res_json, list) and len(res_json) > 1:
                choices = res_json[1].get("choices", [{}])
                msg = choices[0].get("message", {})
                content = msg.get("content")
                if content and content.startswith("data:image"):
                    result = content
        except Exception as e:
            if log_area: log_area.error(f"{p_type} 提取图片异常: {e}")

        if result:
            if log_area: log_area.success(f"{p_type} 生成成功，数据类型: {type(result)}")
        else:
            if log_area: log_area.error(f"{p_type} 生成失败，未获取到图片")
        return result

    # 标题生成
    def run_seo(self, model_id, title, market, gender, category, log_area=None):
        seo_prompt = f"""
请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，生成三条优化标题，按推荐级别排序。
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
        if log_area: log_area.info(f"⏳ 标题生成中... {datetime.now().strftime('%H:%M:%S')}")
        res_json = safe_post(
            "https://openrouter.ai/api/v1/chat/completions",
            self.headers,
            {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]},
            timeout=60
        )
        if log_area: log_area.info(f"标题生成返回 JSON:\n{res_json}")
        content = res_json.get('choices',[{}])[0].get('message',{}).get('content', "")
        if content:
            if log_area: log_area.success("✅ 标题生成完成")
        else:
            if log_area: log_area.error("❌ 标题生成失败")
        return content.strip()

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
engine = JewelryAIEngine(st.secrets.get("OPENROUTER_API_KEY", ""))

# session_state
for key in ["seo_result","p_img","m_img"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ------------------------------------------
# Sidebar 输入
# ------------------------------------------
with st.sidebar:
    st.subheader("💎 AM JEWELRY")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美","中东","非洲"], index=0)
    u_category = st.selectbox("饰品类型", ["头饰","耳环","耳钉","项链","手链","手镯","戒指","脚链"], index=3)
    u_gender = st.radio("目标人群", ["女性","男性"], index=0)
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])

    # 模型选择
    seo_model = st.selectbox("优化标题模型", ALL_TEXT_MODELS, index=0)
    img_model = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=1)

    if st.button("重置"):
        u_title = ""
        u_file = None
        st.session_state.seo_result = None
        st.session_state.p_img = None
        st.session_state.m_img = None
        st.experimental_rerun()

# ------------------------------------------
# 主区
# ------------------------------------------
st.title("💎 TikTok Shop 饰品生成 V48")
c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 生成标题")
btn_prod = c2.button("🖼️ 生成商品图")
btn_mod = c3.button("👤 生成模特图")

# --- 生成标题 ---
tab_seo_area = st.empty()
if btn_seo:
    log_area = tab_seo_area
    st.session_state.seo_result = engine.run_seo(
        model_id=seo_model,
        title=u_title,
        market=u_market,
        gender=u_gender,
        category=u_category,
        log_area=log_area
    )

if st.session_state.seo_result:
    pattern = r"推荐标题[一二三]：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)\n"
    matches = re.findall(pattern, st.session_state.seo_result+"\n", re.DOTALL)
    colors = ["#f0a500","#f4c542","#fde8a9"]  # 暖色调渐变
    st.subheader("优化标题")
    for idx,(title,cn,reason) in enumerate(matches[:3]):
        color = colors[idx] if idx < len(colors) else "#fde8a9"
        st.markdown(
            f"""
            <div style="
                background-color:{color};
                padding:15px;
                border-radius:12px;
                margin-bottom:10px;
                box-shadow: 1px 1px 6px rgba(0,0,0,0.2);
            ">
                <div style="color:#333; font-size:18px; font-weight:bold;">{title}</div>
                <div style="margin-top:5px; color:#444; font-size:14px;">
                    中文翻译: {cn}<br>
                    推荐理由: {reason}
                </div>
            </div>
            """, unsafe_allow_html=True
        )

# --- 生成商品图/模特图 ---
tab_img_area = st.empty()
if (btn_prod or btn_mod) and u_file:
    log_area = tab_img_area
    if btn_prod:
        st.session_state.p_img = engine.run_smart_gen(img_model, "商品图",
                                     u_title,u_gender,u_category,u_market,u_file, log_area)
    if btn_mod:
        st.session_state.m_img = engine.run_smart_gen(img_model, "模特图",
                                        u_title,u_gender,u_category,u_market,u_file, log_area)

# --- Tabs 显示图片 ---
if st.session_state.p_img or st.session_state.m_img:
    tab_prod, tab_model = st.tabs(["🖼️ 商品图","👤 模特图"])
    with tab_prod:
        if st.session_state.p_img:
            display_image(st.session_state.p_img)
    with tab_model:
        if st.session_state.m_img:
            display_image(st.session_state.m_img)
