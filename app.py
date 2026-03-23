import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime
import re
import time

# =============================
# 模型配置
# =============================
ALL_DRAWING_MODELS = {
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview"
}
ALL_TEXT_MODELS = ["openrouter/auto"]

# -----------------------------
# 安全请求函数
# -----------------------------
def safe_post(url, headers, json_data, timeout=60):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except:
        return {"error": "请求失败"}

# -----------------------------
# 图片显示函数
# -----------------------------
def display_image(data):
    if not data:
        st.error("图片生成失败")
        return
    if isinstance(data, dict) and "url" in data:
        st.image(data["url"], use_column_width=True)
        return
    if isinstance(data, str):
        # Base64 解析
        b64_data = data.split(",")[-1] if "base64" in data else data
        try:
            img = Image.open(BytesIO(base64.b64decode(b64_data)))
            st.image(img, use_column_width=True)
        except Exception as e:
            st.error(f"图片解析失败: {e}")

# =============================
# AI 引擎
# =============================
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    # 图片生成
    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file):
        if not file:
            return None
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

        prompt = f"{p_type} photography. 标题：{title}, 性别：{gender}, 饰品类型：{category}, 市场：{market}. 高端饰品风格"

        res_payload = {
            "model": ALL_DRAWING_MODELS.get(mid_key),
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }

        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, res_payload, timeout=120)
        choices = res_json.get("choices", [{}])
        msg = choices[0].get("message", {})
        img_list = msg.get("images", [])
        return img_list[0] if img_list else None

    # 标题生成
    def run_seo(self, model_id, title, market, gender, category):
        seo_prompt = f"""
请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，生成三条优化标题。
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
        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers,
                             {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]}, timeout=60)
        content = res_json.get("choices",[{}])[0].get("message",{}).get("content","")
        return content.strip() if content else None

# =============================
# Streamlit 页面
# =============================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
engine = JewelryAIEngine(st.secrets.get("OPENROUTER_API_KEY",""))

# session_state
for key in ["seo_result","p_img","m_img"]:
    if key not in st.session_state:
        st.session_state[key] = None

# -----------------------------
# 左侧输入
# -----------------------------
with st.sidebar:
    st.subheader("💎 AM JEWELRY")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美","中东","非洲"], index=0)
    u_category = st.selectbox("饰品类型", ["头饰","耳环","耳钉","项链","手链","手镯","戒指","脚链"], index=3)
    u_gender = st.radio("目标人群", ["女性","男性"], index=0)
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])

    if st.button("重置"):
        # 清空 session_state
        for key in ["seo_result","p_img","m_img"]:
            st.session_state[key] = None
        st.success("已重置输入和生成内容")

# -----------------------------
# 主区按钮
# -----------------------------
st.title("💎 TikTok Shop 饰品生成 V48")
c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 生成标题")
btn_prod = c2.button("🖼️ 生成商品图", disabled=not u_file)
btn_mod = c3.button("👤 生成模特图", disabled=not u_file)

# -----------------------------
# Tabs 显示区
# -----------------------------
tab1, tab2, tab3 = st.tabs(["标题区","商品图区","模特图区"])

# --------- 标题区 ---------
with tab1:
    if btn_seo:
        st.session_state.seo_result = engine.run_seo(ALL_TEXT_MODELS[0], u_title, u_market, u_gender, u_category)
    if st.session_state.seo_result:
        colors = ["#e6f2ff","#cce0ff","#b3d1ff"]
        pattern = r"推荐标题[一二三]：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)\n"
        matches = re.findall(pattern, st.session_state.seo_result+"\n", re.DOTALL)
        for idx,(title,cn,reason) in enumerate(matches[:3]):
            color = colors[idx] if idx < len(colors) else "#b3d1ff"
            st.markdown(f"""
                <div style="
                    background-color:{color};
                    padding:15px;
                    border-radius:12px;
                    margin-bottom:10px;
                    box-shadow:1px 1px 6px rgba(0,0,0,0.2);
                ">
                    <div style="font-weight:bold;font-size:18px;color:#333">{title}</div>
                    <div style="margin-top:5px;font-size:14px;color:#444">
                        中文翻译: {cn}<br>推荐理由: {reason}
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --------- 商品图区 ---------
with tab2:
    if btn_prod and u_file:
        st.session_state.p_img = engine.run_smart_gen("google/gemini-3.1-flash-image-preview","商品图",
                                                      u_title,u_gender,u_category,u_market,u_file)
    if st.session_state.p_img:
        display_image(st.session_state.p_img)

# --------- 模特图区 ---------
with tab3:
    if btn_mod and u_file:
        st.session_state.m_img = engine.run_smart_gen("google/gemini-3.1-flash-image-preview","模特图",
                                                      u_title,u_gender,u_category,u_market,u_file)
    if st.session_state.m_img:
        display_image(st.session_state.m_img)
