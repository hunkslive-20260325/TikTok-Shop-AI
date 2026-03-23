import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import json

# ==========================================
# 🛡️ 全局静态模型库（硬编码）
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

# --- 1. 后端引擎类 (增强日志输出) ---
class JewelryAIEngineV47:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "HTTP-Referer": "https://streamlit.io", "X-Title": "Jewelry_V47_Transparent"}

    def run_smart_gen(self, mid_key, p_type, cat, market, gen, file, log_area):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        log_area.info("⏳ 步骤 1: 正在将原图进行 Base64 编码...")
        
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
        v_payload = {
            "model": "google/gemini-3.1-flash-image-preview",
            "messages": [{"role": "user", "content": [{"type": "text", "text": "提取此饰品的形状、材质细节。"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_in}"}}]}]
        }
        
        log_area.info("⏳ 步骤 2: 正在请求 Gemini-3.1 进行多模态识图...")
        try:
            v_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, json=v_payload, timeout=60)
            v_json = v_res.json()
            # 打印识图返参
            with st.expander("📄 查看识图 API 原始返参 (JSON)"):
                st.json(v_json)
            v_desc = v_json['choices'][0]['message']['content']
        except: v_desc = f"Commercial {cat} jewelry"

        log_area.info(f"⏳ 步骤 3: 识图完成。正在调用渲染模型: {mid_key}...")
        prompt = f"Commercial jewelry photography. {v_desc}. Background: Morandi tones, silk fabric. 8k." if p_type == "product" else f"Fashion photography. {gen} model wearing {v_desc}. 8k."
        
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": mid, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}], "modalities": ["image"]}, timeout=120)
            res_json = res.json()
            # 打印渲染返参
            with st.expander(f"📄 查看 {mid_key} 渲染 API 原始返参 (JSON)"):
                st.json(res_json)
            
            img_list = res_json.get('choices', [{}])[0].get('message', {}).get('images', [])
            return img_list[0] if img_list else None
        except: return None

    def run_seo(self, model_id, u_title, u_cat, u_market, log_area):
        log_area.info(f"⏳ 步骤 1: 正在构建全平台热搜关键词 Prompt (参考 TikTok/Amazon/Etsy)...")
        seo_prompt = f"针对 {u_market} 市场和 {u_cat} 类目，优化标题 '{u_title}'。参考 TikTok, Amazon, Google Ads 热搜词。"
        
        log_area.info(f"⏳ 步骤 2: 正在请求 {model_id} 进行标题优化...")
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=self.headers, 
                                json={"model": model_id, "messages": [{"role": "user", "content": seo_prompt}]}, timeout=60)
            res_json = res.json()
            # 打印标题优化返参
            with st.expander("📄 查看标题优化 API 原始返参 (JSON)"):
                st.json(res_json)
            return res_json['choices'][0]['message']['content']
        except: return None

# --- 2. UI 界面 ---
st.set_page_config(page_title="饰品专家 V47.5", layout="wide")
engine = JewelryAIEngineV47(st.secrets.get("OPENROUTER_API_KEY", ""))

# 初始化
for key in ["p_img", "m_img", "seo_txt"]:
    if key not in st.session_state: st.session_state[key] = None

# --- 侧边栏 (Logo 替换控制台) ---
with st.sidebar:
    # 需求 1: 替换为 Logo
    try:
        logo_img = Image.open("logo.PNG")
        st.image(logo_img, width="stretch")
    except:
        st.subheader("💎 AM JEWELRY")
    
    st.divider()
    m_txt = st.selectbox("文案/标题模型", ALL_TEXT_MODELS) 
    m_img = st.selectbox("图像渲染模型", list(ALL_DRAWING_MODELS.keys())) 
    st.divider()
    u_title = st.text_input("1. 原始标题", "心形项链")
    u_cat = st.selectbox("2. 类型", ["项链", "耳饰", "戒指", "手链", "套装"])
    u_market = st.selectbox("3. 市场", ["东南亚", "北美", "欧洲"])
    u_gender = st.radio("4. 性别", ["女性", "男性"], horizontal=True)
    u_file = st.file_uploader("📸 上传原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(u_file, width="stretch")

st.title("💎 TikTok Shop 饰品 (V47.5)")

# 需求 4: 删除“专家指令”文案，仅保留按钮
c1, c2, c3 = st.columns(3)
btn_seo = c1.button("✨ 标题 SEO 优化", use_container_width=True)
btn_prod = c2.button("🖼️ 商品图优化", use_container_width=True)
btn_mod = c3.button("👤 模特图优化", use_container_width=True)

tab_seo, tab_prod, tab_mod = st.tabs(["📊 SEO 优化结果", "🖼️ 商品图结果", "👤 模特图结果"])

# 需求 2: 标题生成过程与日志
with tab_seo:
    log_seo = st.empty()
    if btn_seo:
        res = engine.run_seo(m_txt, u_title, u_cat, u_market, log_seo)
        if res: 
            st.session_state.seo_txt = res
            log_seo.success("✅ 标题优化生成成功！")
        else: log_seo.error("❌ 生成失败")
    
    if st.session_state.seo_txt:
        st.divider()
        st.markdown(st.session_state.seo_txt)
    else: st.caption("（待执行：标题优化基于全平台热搜词库）")

# 需求 3: 图片生成过程与日志
with tab_prod:
    log_prod = st.empty()
    if btn_prod:
        if not u_file: st.warning("请上传图片"); st.stop()
        res = engine.run_smart_gen(m_img, "product", u_cat, u_market, u_gender, u_file, log_prod)
        if res: 
            st.session_state.p_img = res
            log_prod.success("✅ 商品图生成成功！")
        else: log_prod.error("❌ 生成失败")
        
    if st.session_state.p_img:
        st.divider()
        clean_b64 = st.session_state.p_img.split(",")[-1].strip()
        st.image(Image.open(BytesIO(base64.b64decode(clean_b64))), width="stretch")
    else: st.caption("（待生成：点击上方按钮开始渲染）")

with tab_mod:
    log_mod = st.empty()
    if btn_mod:
        if not u_file: st.warning("请上传图片"); st.stop()
        res = engine.run_smart_gen(m_img, "model", u_cat, u_market, u_gender, u_file, log_mod)
        if res: 
            st.session_state.m_img = res
            log_mod.success("✅ 模特图生成成功！")
        else: log_mod.error("❌ 生成失败")

    if st.session_state.m_img:
        st.divider()
        clean_b64 = st.session_state.m_img.split(",")[-1].strip()
        st.image(Image.open(BytesIO(base64.b64decode(clean_b64))), width="stretch")
    else: st.caption("（待生成：点击上方按钮开始渲染）")
