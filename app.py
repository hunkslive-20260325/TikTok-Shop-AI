from io import BytesIO
from datetime import datetime
import re
import time

# ==========================================
# 模型库
# ==========================================
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview"
}

ALL_TEXT_MODELS = [
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-chat",
    "openai/gpt-5.4",
    "google/gemini-3.1-flash-image-preview",
    "openrouter/auto"
]
ALL_TEXT_MODELS = ["openrouter/auto"]

# ------------------------------------------
# 安全请求函数
@@ -40,17 +31,23 @@ def safe_post(url, headers, json_data, timeout=60):
# 显示图片
# ------------------------------------------
def display_image(data):
    if not data:
        st.error("图片生成失败")
        return
if isinstance(data, dict) and "url" in data:
st.image(data["url"], use_column_width=True)
elif isinstance(data, str):
if data.startswith("data:image"):
data = data.split(",")[1]
        st.image(Image.open(BytesIO(base64.b64decode(data))), use_column_width=True)
        try:
            st.image(Image.open(BytesIO(base64.b64decode(data))), use_column_width=True)
        except:
            st.error("图片解析失败")

# ==========================================
# AI 引擎
# ==========================================
class JewelryAIEngineV48:
class JewelryAIEngine:
def __init__(self, api_key):
self.api_key = api_key
self.headers = {
@@ -59,40 +56,39 @@ def __init__(self, api_key):
"X-Title": "Jewelry_V48"
}

    # 商品/模特图生成
    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file):
    # 图片生成
    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file, log_area):
mid = ALL_DRAWING_MODELS.get(mid_key)
        if not file:
            log_area.error("未上传原图")
            return None
        log_area.info(f"⏳ {p_type} 生成中... {datetime.now().strftime('%H:%M:%S')}")
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
        prompt = f"{p_type} photography. 标题：{title}, 性别：{gender}, 饰品类型：{category}, 市场：{market}. 8k 高端饰品风格"

res_payload = {
"model": mid,
"messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
"modalities": ["image"]
}
        time.sleep(1)  # 模拟进度
res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, res_payload, timeout=120)
choices = res_json.get('choices', [{}])
msg = choices[0].get('message', {})
img_list = msg.get('images', [])
        return img_list[0] if img_list else None
        if img_list:
            log_area.success("✅ 生成成功")
            return img_list[0]
        else:
            log_area.error("❌ 生成失败")
            return None

# 标题生成
    def run_seo(self, model_id, title, market, gender, category):
    def run_seo(self, model_id, title, market, gender, category, log_area):
        log_area.info(f"⏳ 标题生成中... {datetime.now().strftime('%H:%M:%S')}")
seo_prompt = f"""
请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，生成三条优化标题，按点击率和浏览量综合排序。
请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，生成三条优化标题，按推荐级别排序。
输出格式：
推荐标题一：****
中文翻译：****
@@ -104,20 +100,21 @@ def run_seo(self, model_id, title, market, gender, category):
中文翻译：****
推荐理由：****
"""
        res_json = safe_post(
            "https://openrouter.ai/api/v1/chat/completions",
            self.headers,
            {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]},
            timeout=60
        )
        time.sleep(1)  # 模拟进度
        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers,
                             {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]}, timeout=60)
content = res_json.get('choices',[{}])[0].get('message',{}).get('content', "")
        if content:
            log_area.success("✅ 标题生成完成")
        else:
            log_area.error("❌ 生成失败")
return content.strip()

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
engine = JewelryAIEngineV48(st.secrets.get("OPENROUTER_API_KEY", ""))
engine = JewelryAIEngine(st.secrets.get("OPENROUTER_API_KEY", ""))

# session_state
for key in ["seo_result","p_img","m_img"]:
@@ -135,15 +132,13 @@ def run_seo(self, model_id, title, market, gender, category):
u_gender = st.radio("目标人群", ["女性","男性"], index=0)
u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
if st.button("重置"):
        u_title = ""
        u_file = None
st.session_state.seo_result = None
st.session_state.p_img = None
st.session_state.m_img = None
st.experimental_rerun()

# ------------------------------------------
# 主区
# 主区按钮
# ------------------------------------------
st.title("💎 TikTok Shop 饰品生成 V48")
c1, c2, c3 = st.columns(3)
@@ -152,20 +147,16 @@ def run_seo(self, model_id, title, market, gender, category):
btn_mod = c3.button("👤 生成模特图")

# --- 生成标题 ---
tab_seo_area = st.empty()
if btn_seo:
    st.session_state.seo_result = engine.run_seo(
        model_id=ALL_TEXT_MODELS[0],
        title=u_title,
        market=u_market,
        gender=u_gender,
        category=u_category
    )
    log_area = tab_seo_area
    st.session_state.seo_result = engine.run_seo(ALL_TEXT_MODELS[0], u_title, u_market, u_gender, u_category, log_area)

if st.session_state.seo_result:
    tab_seo_area.markdown("### 优化标题")
pattern = r"推荐标题[一二三]：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)\n"
matches = re.findall(pattern, st.session_state.seo_result+"\n", re.DOTALL)
    colors = ["#f0a500","#f4c542","#fde8a9"]  # 暖色调渐变
    st.subheader("优化标题")
    colors = ["#f0a500","#f4c542","#fde8a9"]
for idx,(title,cn,reason) in enumerate(matches[:3]):
color = colors[idx] if idx < len(colors) else "#fde8a9"
st.markdown(
@@ -188,15 +179,13 @@ def run_seo(self, model_id, title, market, gender, category):

# --- 生成商品图/模特图 ---
if (btn_prod or btn_mod) and u_file:
    p_img = m_img_res = None
    log_area = st.empty()
if btn_prod:
        p_img = engine.run_smart_gen("google/gemini-3.1-flash-image-preview","商品图",
                                     u_title,u_gender,u_category,u_market,u_file)
        st.session_state.p_img = p_img
        st.session_state.p_img = engine.run_smart_gen("google/gemini-3.1-flash-image-preview","商品图",
                                                      u_title,u_gender,u_category,u_market,u_file, log_area)
if btn_mod:
        m_img_res = engine.run_smart_gen("google/gemini-3.1-flash-image-preview","模特图",
                                        u_title,u_gender,u_category,u_market,u_file)
        st.session_state.m_img = m_img_res
        st.session_state.m_img = engine.run_smart_gen("google/gemini-3.1-flash-image-preview","模特图",
                                                      u_title,u_gender,u_category,u_market,u_file, log_area)

# --- Tabs 显示图片 ---
if st.session_state.p_img or st.session_state.m_img:
