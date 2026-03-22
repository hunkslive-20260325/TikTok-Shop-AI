import streamlit as st
import requests
import re
from PIL import Image

# --- 1. 状态锁定：确保你的输入参数和按钮名称不再变动 ---
if "v26_stable_init" not in st.session_state:
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.session_state.v26_stable_init = True
    st.session_state.seo_result = ""
    st.session_state.main_img_result = []
    st.session_state.model_img_result = []

# --- 2. 依照 OpenRouter 2026 官方文档规范的调用函数 ---
def call_openrouter_api(payload):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io", # 文档要求参数
        "X-Title": "TikTok Jewelry AI Expert"
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

# --- 3. 核心业务逻辑 ---
def handle_ai_task(task_type, cat, mkt, gen, title=""):
    # 文案生成：使用 Gemini 2.0 Flash (当前文档推荐的快速模型)
    if task_type == "SEO":
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [{"role": "user", "content": f"TikTok饰品专家：为{mkt}的{gen}优化{cat}标题。原始：{title}。请用表格输出建议。"}]
        }
        data = call_openrouter_api(payload)
        return data['choices'][0]['message'].get('content', "生成失败"), "Gemini 2.0"

    # 图片生成：依照 Quickstart 文档增加 modalities 参数
    # 优先使用 Flux，它是目前 OpenRouter 上最稳定的绘图 ID
    img_models = ["black-forest-labs/flux-schnell", "google/imagen-3", "openai/dall-e-3"]
    prompt = f"Jewelry photography of {cat}. Morandi background, 8k" if task_type == "MAIN" else f"Fashion photo of {gen} model wearing {cat}, 8k"
    
    for mid in img_models:
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image"] # 👈 文档规定的绘图必填项
        }
        data = call_openrouter_api(payload)
        if "choices" in data:
            msg = data['choices'][0]['message']
            # 2026 规范：优先从 images 数组取图
            img_out = msg.get("images", [None])[0] or msg.get("content", "")
            if img_out and len(str(img_out)) > 10:
                return img_out, mid
    return "❌ 所有图片模型调用均失败，请检查 API 额度或权限", "None"

# --- 4. 界面布局 (严格锁定你的原始需求) ---
st.set_page_config(page_title="饰品 AI 专家 V26", layout="wide")
st.title("💎 TikTok Shop 饰品全能 AI 专家")

with st.sidebar:
    st.header("📋 经营信息输入")
    u_title = st.text_input("1. 原始标题", value="S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("3. 目标市场", ["东南亚总区", "美国", "英国"])
    u_gen = st.radio("4. 目标性别趋势", ["女性", "男性"], horizontal=True)
    st.divider()
    f = st.file_uploader("🖼️ 上传原图", type=["jpg", "png", "jpeg"])
    if f: st.image(Image.open(f), caption="原图已锁定", use_container_width=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🚀 专家指令执行")
    # 保持你要求的按钮名称不变
    if st.button("✨ 1. 执行：标题 SEO 优化"):
        with st.status("优化中..."):
            st.session_state.seo_result, _ = handle_ai_task("SEO", u_cat, u_mkt, u_gen, u_title)
            
    if st.button("🖼️ 2. 执行：商品图优化"):
        with st.status("主图生成中..."):
            res, mod = handle_ai_task("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.main_img_result.append({"url": res, "mod": mod})

    if st.button("👤 3. 执行：模特图优化"):
        with st.status("模特匹配中..."):
            res, mod = handle_ai_task("MODEL", u_cat, u_mkt, u_gen)
            st.session_state.model_img_result.append({"url": res, "mod": mod})

with col2:
    st.subheader("📊 实时成果展示")
    if st.session_state.seo_result:
        st.info("SEO 标题建议")
        st.markdown(st.session_state.seo_result)
    
    # 合并展示生成的图片成果
    all_results = st.session_state.main_img_result + st.session_state.model_img_result
    if all_results:
        grid = st.columns(2)
        for i, item in enumerate(all_results):
            with grid[i % 2]:
                st.caption(f"驱动: {item['mod']}")
                img_val = str(item['url'])
                if img_val.startswith("http") or len(img_val) > 100:
                    st.image(img_val, use_container_width=True)
                else:
                    st.error(f"异常: {img_val}")
