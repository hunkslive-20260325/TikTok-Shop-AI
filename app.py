import streamlit as st
import requests
import base64
from PIL import Image
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
        print(f"[ERROR] 请求失败: {e}")
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
class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_V48"
        }

    # 商品/模特图生成
    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file, log_area):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        if not file:
            log_area.error("未上传原图")
            return None

        log_area.info(f"⏳ {p_type} 生成中... {datetime.now().strftime('%H:%M:%S')}")
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

        # 自动生成 Prompt
        if p_type == "商品图":
            prompt = f"""
请生成一张高端饰品商品图，饰品类型为 {category}。
背景要求：
- 核心配色：暖色调莫兰迪色系或中性肤色系，米色/奶油色为主，辅以淡橙/香槟粉或丝绸香槟金
- 材质：哑光背景纸/卡纸，丝绸/缎面布料或皮革感纹理，质感高级
- 几何道具：几何立方体、多边形台子，金属线条支架，增加层次和立体感
- 灯光：大面积柔光，从斜上方45°打入，阴影柔和
- 拍摄角度：平铺俯拍或侧斜角45°，突出饰品主体
- 饰品摆放：{category}角度合理，避免违反重力，悬空自然
- 风格：8K超高清，高端奢华饰品风格
"""
        elif p_type == "模特图":
            if gender == "男性":
                prompt = f"""
请生成一张高端男士饰品模特图，模特肤色小麦色/古铜色，皮肤纹理清晰，胡须修剪整齐。
服装：黑色圆领针织衫或西装。饰品为 {category}。
背景与布景：
- 色调：深米色、大地色或灰褐色
- 虚化：模特距离背景一定距离，背景渐变虚化，无杂物干扰
- 灯光：侧逆光或45°侧光，突出颈部线条和首饰高光
- 构图：大特写（嘴部以下到胸部以上）
- 动作：手拉链条，链条弧线自然引导视线到吊坠
- 光影：反光板补光，避免阴影过黑，高光点缀吊坠
- 后期调色：锐度适中提升首饰与胡须质感，对比拉高，背景增加暖色感
- 风格：高端、沉稳、男性时尚感，8K超高清摄影风格
"""
            else:  # 女性
                prompt = f"""
请生成一张高端女模特饰品图，模特皮肤水光肌，白皙透亮，柔和妆容，嘴唇淡粉/豆沙色，指甲裸色/透粉色。
发型自然微卷或深色散落碎发。服装：纯白或米白色。饰品为 {category}。
背景与布景：
- 色彩：低饱和粉色、浅米色或纯白
- 光影：极度柔和弥散光，几乎无明显阴影
- 构图：大面积留白，展示颈部和肩部皮肤
- 动作：轻拨领口或靠近链条，侧头展示链条弧度
- 布景：模拟窗边柔光，反光板放置在下巴下方消除阴影
- 拍摄参数：85mm f/1.8或100mm Macro，大光圈虚化背景
- 风格：精致柔美、突出首饰细节，8K超高清摄影风格
"""

        res_payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "modalities": ["image"]
        }

        try:
            res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, res_payload, timeout=120)
            choices = res_json.get("choices", [{}])
            msg = choices[0].get("message", {})
            img_list = msg.get("images", [])
            if img_list:
                log_area.success(f"✅ {p_type} 生成成功")
                return img_list[0]
            content = msg.get("content", "")
            if content.startswith("data:image"):
                log_area.success(f"✅ {p_type} 生成成功")
                return content
            log_area.error(f"❌ {p_type} 生成失败：返回内容非图片")
            return None
        except Exception as e:
            log_area.error(f"❌ {p_type} 生成失败: {e}")
            return None

    # 标题生成
    def run_seo(self, model_id, title, market, gender, category, log_area):
        log_area.info(f"⏳ 标题生成中... {datetime.now().strftime('%H:%M:%S')}")
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
        res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers,
                             {"model": model_id, "messages":[{"role":"user","content":seo_prompt}]}, timeout=60)
        content = res_json.get('choices',[{}])[0].get('message',{}).get('content', "")
        if content:
            log_area.success("✅ 标题生成完成")
        else:
            log_area.error("❌ 标题生成失败")
        return content.strip()

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="饰品专家 V48", layout="wide")
engine = JewelryAIEngineV48(st.secrets.get("OPENROUTER_API_KEY", ""))

# session_state 初始化
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
    seo_model = st.selectbox("优化标题模型", ALL_TEXT_MODELS, index=0)
    img_model = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=0)

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

# 日志区
log_area = st.empty()

# 生成标题
if btn_seo:
    st.session_state.seo_result = engine.run_seo(seo_model, u_title, u_market, u_gender, u_category, log_area)

if st.session_state.seo_result:
    pattern = r"推荐标题[一二三]：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)\n"
    matches = re.findall(pattern, st.session_state.seo_result+"\n", re.DOTALL)
    colors = ["#f0a500","#f4c542","#fde8a9"]
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

# 生成商品图 / 模特图
if (btn_prod or btn_mod) and u_file:
    p_img = m_img_res = None
    if btn_prod:
        st.session_state.p_img = engine.run_smart_gen(img_model, "商品图", u_title, u_gender, u_category, u_market, u_file, log_area)
    if btn_mod:
        st.session_state.m_img = engine.run_smart_gen(img_model, "模特图", u_title, u_gender, u_category, u_market, u_file, log_area)

# Tabs 显示图片
if st.session_state.p_img or st.session_state.m_img:
    tab_prod, tab_model = st.tabs(["🖼️ 商品图","👤 模特图"])
    with tab_prod:
        if st.session_state.p_img:
            display_image(st.session_state.p_img)
    with tab_model:
        if st.session_state.m_img:
            display_image(st.session_state.m_img)
