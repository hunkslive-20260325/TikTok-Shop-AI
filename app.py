import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import re
import random

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
    "google/gemini-3.1-pro-preview",
    "google/gemini-3.1-pro-preview-customtools"
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
# 显示图片 + 下载按钮 (回归原始比例)
# ------------------------------------------
def display_image(data, filename="image.png", preview_width=400):
    try:
        img_full = None 
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

        if isinstance(img_data, str) and img_data.startswith("data:image"):
            img_base64 = img_data.split(",")[1]
            raw_bytes = base64.b64decode(img_base64)
            img_full = Image.open(BytesIO(raw_bytes))
        elif isinstance(img_data, str) and img_data.startswith("http"):
            img_full = img_data  # URL 情况
        else:
            raw_bytes = base64.b64decode(img_data)
            img_full = Image.open(BytesIO(raw_bytes))

        # --- 关键修改：限制预览宽度 ---
        st.image(img_full, width=preview_width)

        if isinstance(img_full, Image.Image):
            buf = BytesIO()
            img_full.save(buf, format="PNG")
            st.download_button(label="⬇️ 下载全尺寸原图", data=buf.getvalue(), file_name=filename, mime="image/png", key=f"dl_{hash(str(data))}")
        elif isinstance(img_full, str) and img_full.startswith("http"):
            st.markdown(f"[🔗 打开原图链接]({img_full})")
            
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

    def run_smart_gen(self, mid_key, p_type, title, gender, category, market, file):
        try:
            mid = ALL_DRAWING_MODELS.get(mid_key)
            b64_in = base64.b64encode(file.getvalue()).decode('utf-8')

            focus_parts = {"项链": "neck", "戒指": "fingers", "手链": "wrist", "手镯": "wrist", "耳环": "ear", "耳钉": "ear", "头饰": "hair", "脚链": "ankle"}
            target_part = focus_parts.get(category, "body")
            # A类：支撑物（坚硬、几何）
            base_supports = [
                "a textured travertine stone pedestal",
                "a smooth concrete cylinder",
                "a stack of matte ceramic tiles",
                "a minimalist wooden block",
                "a raw-edged sandstone plinth"
            ]
            
            # B类：陪衬物（柔软、半透明、有机的）
            organic_elements = [
                "a softly folded linen cloth",
                "a few scattered dried botanical petals",
                "a delicate fluted glass perfume vial",
                "a single beautifully veined green leaf",
                "a strand of preserved moss"
            ]
            
            # C类：背景光影元素（保持您的标志性风格）
            shadow_elements = [
                "Monstera leaf",
                "palm frond",
                "venetian blinds",
                "abstract window pane",
                "arching fern"
            ]
            
            # ==========================================
            # 动态生成 Prompt 逻辑：实现“千人千面”
            # ==========================================
            
            # 在每次生成时，随机抽取 1 个 A类 和 1 个 B类 进行组合
            # 这样组合出的陈列方式有 5 * 5 = 25 种主要变化，且风格统一
            selected_support = random.choice(base_supports)
            selected_organic = random.choice(organic_elements)
            # 随机抽取一个阴影元素
            selected_shadow = random.choice(shadow_elements)
        
            # 移除强制 1:1 的 Prompt 约束，恢复自然构图描述
            if p_type == "模特图" and gender == "男性":
                prompt = f"Professional male model wearing {category}, focusing on {target_part}. Natural skin, black waffle-knit sweater, gray studio background, 2k."
            elif p_type == "模特图" and gender == "女性":
                prompt = f"Elegant East Asian female model wearing {category}, focusing on {target_part}. Creamy skin, white linen shirt, beige background, 2k."
            else:
                # ==========================================
                # 20260325 10:59 优化商品图prompt
                # ==========================================
                prompt = (
                    # ==========================================
                    # 20260324 调整prompt风格01
                    # ==========================================
                    # f"A high-end macro product photography of the {category} seen in the reference image. "
                    # f"The {category} is displayed elegantly on a configuration of minimalist smooth solid-colored geometric prisms (cylinders and blocks), "
                    # f"positioning it as the sole focal point. "
                    # f"The pedestal and the perfectly clean solid-colored matte background are made of the same matching warm grey or Morandi beige material. "
                    # f"with a smooth, matte finish that doesn't distract from the jewelry. "
                    # f"The palette is a soft, warm neutral range of beiges and pale greys. "
                    # f"Artistic, thin shadows of a monstera leaf or fern frond are delicately projected on the background, "
                    # f"leaving the {category} in clear, bright light. "
                    # f"High-end editorial aesthetic, 8k resolution, shallow depth of field, sharp focus strictly on the {category}'s textures and details."
                    # ==========================================
                    # 20260327 调整prompt风格02
                    # ==========================================
                    f"A high-end macro product photograph of the {category} from the reference image. "
                    f"The {category} is the absolute focal point, displayed elegantly on a minimalist arrangement of "
                    f"The arrangement features {selected_support} nestled with {selected_organic},{selected_organic} is positioned slightly behind or to the side of the {category}, "
                    "ensuring it does not obscure or overlap with the jewelry itself.  "
                    f"creating a unique play of varied textures and heights. "
                    "The scene is bathed in bright, soft diffused natural daylight. "
                    f"A delicate, clean artistic shadow of {selected_shadow} is cast across the neutral-colored matte background, adding artistic depth. "
                    f"The AI must strictly replicate the unique textures and original finish of the {category} "
                    f"exactly as seen in the reference image—whether it is matte, polished, organic, or faceted. "
                    f"The overall aesthetic is clean, sophisticated, and tailored for the {market} market. "
                    "Shot on a Hasselblad X1D II 50C with a 120mm macro lens. "
                    "Extremely sharp focus on the details, shallow depth of field, photorealistic, 8k, ray tracing. "
                )
                
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
        # prompt = f"针对{title}生成三条{market}市场{gender}用{category}的SEO标题，含中文翻译和理由。"
        # 20260324 16:37 优化标题prompt生成条件
        prompt = (
            f"请结合原始标题：{title}，目标市场：{market}，目标人群：{gender}，饰品类型：{category}，生成三条优化标题，按推荐级别排序。\n"
            f"要求：推荐理由不超过50字。\n\n"
            f"输出格式：\n"
            f"推荐标题一：****\n"
            f"中文翻译：****\n"
            f"推荐理由：****\n"
            f"推荐标题二：****\n"
            f"中文翻译：****\n"
            f"推荐理由：****\n"
            f"推荐标题三：****\n"
            f"中文翻译：****\n"
            f"推荐理由：****"
        )
        res = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, {"model": model_id, "messages":[{"role":"user","content":prompt}]})
        return res.get('choices',[{}])[0].get('message',{}).get('content', "")

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="AM JEWELRY V48", layout="wide")
# ==========================================
# 20260324 16:37 优化标题显示
# ==========================================
st.markdown("""
    <style>
    # ==========================================
    # 20260324 16:37 优化日志显示
    # ==========================================
    /* ======== 日志展示区 UI 样式 ======== */
    .log-container {
        background-color: #1e1e1e; /* 深灰色背景 */
        color: #00ff00;            /* 荧光绿字体，模拟控制台 */
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #0d47a1;
        margin-bottom: 20px;
        font-family: 'Courier New', Courier, monospace;
        min-height: 60px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .log-icon {
        margin-right: 12px;
        font-size: 1.2rem;
    }
    /* ======== 日志展示区 UI 样式 ======== */
    # ==========================================
    
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
    .stFileUploader { padding-top: 0rem; }
    div[data-testid="stFileUploader"] section { padding: 0.5rem; min-height: 80px; }
    
    /* ======== SEO 标题展示 UI 样式 ======== */
    .seo-card {
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
        font-family: sans-serif;
    }
    .seo-row {
        padding: 12px 16px;
        line-height: 1.6;
    }
    .seo-title {
        background-color: #e3f2fd; /* 浅蓝色背景 */
        color: #0d47a1;            /* 深蓝色字体 */
        border-bottom: 1px solid #bbdefb;
    }
    .seo-trans {
        background-color: #f1f8e9; /* 浅绿色背景 */
        color: #33691e;            /* 深绿色字体 */
        border-bottom: 1px solid #dcedc8;
    }
    .seo-reason {
        background-color: #fff3e0; /* 浅橙色背景 */
        color: #e65100;            /* 深橙色字体 */
    }
    .seo-label {
        font-weight: 600;
        margin-right: 8px;
    }
    </style>
""", unsafe_allow_html=True)
# ==========================================
st.markdown("""
    <style>
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
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
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
    
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    btn_seo = c1.button("标题")
    btn_prod = c2.button("商品")
    btn_mod = c3.button("模特")
    
    u_img_count = st.selectbox("生成图片数量", [1, 2, 4], index=0)
    model_text = st.selectbox("优化标题模型", ALL_TEXT_MODELS)
    model_img = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=4)

# --- 主界面逻辑 ---
log_area = st.empty()

# --- 注释: 生成标题重复 ---
# if btn_seo:
#     st.session_state.seo_result = engine.run_seo(model_text, u_title, u_market, u_gender, u_category)
    
# ==========================================
# 20260324 16:37 优化日志显示
# ==========================================  
# --- 主界面逻辑 ---
# 定义一个辅助函数来渲染日志
def update_log(msg, icon="⏳"):
    log_area.markdown(f"""
        <div class="log-container">
            <span class="log-icon">{icon}</span>
            <span>{msg}</span>
        </div>
    """, unsafe_allow_html=True)

log_area = st.empty()
# 初始状态提示（可选）
update_log("等待操作指令...", icon="🤖")

if btn_seo:
    update_log("正在分析市场趋势并生成 SEO 标题...", icon="🔍")
    st.session_state.seo_result = engine.run_seo(model_text, u_title, u_market, u_gender, u_category)
    update_log("标题生成任务已完成！", icon="✅")

if btn_prod and u_file:
    st.session_state.p_imgs = []
    for i in range(u_img_count):
        update_log(f"正在生成商品图：进度 {i+1}/{u_img_count}...", icon="🖼️")
        res = engine.run_smart_gen(model_img, "商品图", u_title, u_gender, u_category, u_market, u_file)
        if res: st.session_state.p_imgs.append(res)
    update_log("所有商品图已生成完毕！", icon="✅")

if btn_mod and u_file:
    st.session_state.m_imgs = []
    for i in range(u_img_count):
        update_log(f"正在生成模特图：进度 {i+1}/{u_img_count}...", icon="👤")
        res = engine.run_smart_gen(model_img, "模特图", u_title, u_gender, u_category, u_market, u_file)
        if res: st.session_state.m_imgs.append(res)
    update_log("所有模特图已生成完毕！", icon="✅")
# ==========================================

# ==========================================
# 20260324 16:37 注释优化日志显示
# ==========================================    
# if btn_prod and u_file:
#     st.session_state.p_imgs = []
#     for i in range(u_img_count):
#         log_area.info(f"正在生成第 {i+1}/{u_img_count} 张商品图...")
#         res = engine.run_smart_gen(model_img, "商品图", u_title, u_gender, u_category, u_market, u_file)
#         if res: st.session_state.p_imgs.append(res)
#     log_area.success("商品图生成完毕")

# if btn_mod and u_file:
#     st.session_state.m_imgs = []
#     for i in range(u_img_count):
#         log_area.info(f"正在生成第 {i+1}/{u_img_count} 张模特图...")
#         res = engine.run_smart_gen(model_img, "模特图", u_title, u_gender, u_category, u_market, u_file)
#         if res: st.session_state.m_imgs.append(res)
#     log_area.success("模特图生成完毕")
# ==========================================
    
# ==========================================
# 展示区
# ==========================================
# if st.session_state.seo_result:
#     with st.expander("📝 查看优化标题", expanded=True):
#         st.write(st.session_state.seo_result)
# ==========================================
# 20260324 16:37 展示区优化标题显示
# ==========================================
if st.session_state.seo_result:
    with st.expander("📝 查看优化标题", expanded=True):
        raw_text = st.session_state.seo_result
        
        # 使用正则提取三组内容
        pattern = r"推荐标题([一二三])：(.*?)\n中文翻译：(.*?)\n推荐理由：(.*?)(?=\n推荐标题|$)"
        matches = re.findall(pattern, raw_text, re.DOTALL)
        
        if matches:
            for match in matches:
                num, title, trans, reason = match
                # 拼接 HTML 卡片结构
                html_content = f"""
                <div class="seo-card">
                    <div class="seo-row seo-title">
                        <div class="seo-label">推荐标题{num}：</div> 
                        <div>{title.strip()}</div>
                    </div>
                    <div class="seo-row seo-trans">
                        <div class="seo-label">中文翻译：</div> 
                        <div>{trans.strip()}</div>
                    </div>
                    <div class="seo-row seo-reason">
                        <div class="seo-label">推荐理由：</div> 
                        <div>{reason.strip()}</div>
                    </div>
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
        else:
            # 降级处理：如果大模型偶尔没有严格按照格式输出，则回退到普通文本显示
            st.markdown(raw_text)
# ==========================================           

if st.session_state.p_imgs or st.session_state.m_imgs:
    t1, t2 = st.tabs(["🖼️ 商品展示", "👤 模特展示"])
    with t1:
        # 每行显示 2 个，这样 400px x 2 刚好适合大部分屏幕
        cols = st.columns(2) 
        for idx, img in enumerate(st.session_state.p_imgs):
            with cols[idx % 2]:
                st.markdown(f"**版本 {idx+1}**")
                display_image(img, filename=f"prod_{idx}.png", preview_width=400)
    with t2:
        cols = st.columns(2)
        for idx, img in enumerate(st.session_state.m_imgs):
            with cols[idx % 2]:
                st.markdown(f"**版本 {idx+1}**")
                display_image(img, filename=f"model_{idx}.png", preview_width=400)
