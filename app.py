import streamlit as st
import requests
import re

# --- 1. 界面与样式配置 ---
st.set_page_config(page_title="TikTok 饰品 AI 专家 (全模型自由版)", layout="wide")

st.markdown("""
    <style>
    .model-card {
        background-color: #f8f9fa;
        border-left: 5px solid #2e7d32;
        padding: 10px 15px;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    .stButton>button { border-radius: 10px; background: #2b2b2b; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心请求引擎 ---
def call_openrouter(prompt, model_id):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501", # OpenRouter 要求的来源标识
    }
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            error_msg = data.get("error", {}).get("message", "未知模型错误")
            return f"❌ 调用失败: {error_msg}"
    except Exception as e:
        return f"❌ 网络请求异常: {str(e)}"

# --- 3. 侧边栏：灵活的模型配置 ---
with st.sidebar:
    st.header("⚙️ 模型配置中心")
    
    # 文案模型选择
    st.subheader("📝 文案引擎")
    text_mode = st.toggle("手动输入文案模型 ID", False)
    if text_mode:
        text_model = st.text_input("输入 OpenRouter 模型 ID", "deepseek/deepseek-chat")
    else:
        text_model = st.selectbox("选择推荐模型", [
            "deepseek/deepseek-chat", # ⭐ 推荐
            "google/gemini-2.0-flash-exp:free",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3.1-405b"
        ], format_func=lambda x: f"⭐ {x}" if "deepseek" in x else x)

    st.divider()

    # 绘画模型选择
    st.subheader("🎨 绘画引擎")
    img_mode = st.toggle("手动输入绘画模型 ID", False)
    if img_mode:
        image_model = st.text_input("输入绘画模型 ID", "openai/dall-e-3")
    else:
        image_model = st.selectbox("选择推荐模型", [
            "openai/dall-e-3", # ⭐ 推荐
            "black-forest-labs/flux-schnell",
            "google/gemini-pro-vision",
            "midjourney/midjourney"
        ], format_func=lambda x: f"⭐ {x}" if "dall-e-3" in x else x)

    st.divider()
    u_title = st.text_input("原始产品标题", "Heart S925 Necklace")
    u_cat = st.selectbox("产品品类", ["项链", "耳环", "戒指", "手链"])

# --- 4. 主界面布局 ---
st.title("💎 TikTok Shop 饰品全能优化")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("🚀 指令台")
    
    # SEO 逻辑
    if st.button("✨ 生成爆款标题"):
        with st.spinner(f"正在调动 {text_model}..."):
            prompt = f"作为 TikTok 电商专家，请为这款{u_cat}生成 3 个高转化标题。原始标题：{u_title}。要求：符合东南亚审美，展示搜索词分析。请用 Markdown 表格。 "
            st.session_state.seo_res = call_openrouter(prompt, text_model)
            st.session_state.last_text_model = text_model

    # 绘图逻辑
    if st.button("🖼️ 生成莫兰迪展示图"):
        with st.spinner(f"正在调动 {image_model}..."):
            prompt = f"Jewelry advertising photography, {u_cat} on a premium Morandi cream background, elegant shadows, 8k resolution, cinematic lighting. Direct image URL only."
            st.session_state.img_res = call_openrouter(prompt, image_model)
            st.session_state.last_img_model = image_model

with col_right:
    st.subheader("📊 实时成果")

    # 显示文案结果
    if "seo_res" in st.session_state:
        st.markdown(f"""
            <div class="model-card">
                <small>📡 最终驱动模型：</small><br>
                <strong>{st.session_state.last_text_model}</strong>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.seo_res)

    # 显示绘画结果
    if "img_res" in st.session_state:
        st.divider()
        st.markdown(f"""
            <div class="model-card" style="border-left-color: #f57c00;">
                <small>🎨 最终驱动模型：</small><br>
                <strong>{st.session_state.last_img_model}</strong>
            </div>
        """, unsafe_allow_html=True)
        
        # 提取 URL
        raw_output = st.session_state.img_res
        urls = re.findall(r'(https?://[^\s)"]+)', raw_output)
        if urls:
            st.image(urls[0], caption=f"基于 {st.session_state.last_img_model} 的莫兰迪优化方案")
        else:
            st.info(raw_output)

st.sidebar.caption("TikTok Shop AI Expert | Powered by OpenRouter | 2026")
