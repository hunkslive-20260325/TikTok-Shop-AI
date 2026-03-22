import streamlit as st
import requests
import json
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide", page_icon="💎")

# 自定义样式
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; background: #2b2b2b; color: white; }
    .stButton>button:hover { background: #ff4b4b; border: none; }
    .res-box { padding: 20px; border-radius: 12px; background: #f9f9f9; border: 1px solid #eee; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心请求逻辑 (OpenRouter 专用) ---
def call_ai(prompt, model_id):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/hunkslive", # 建议填写你的项目地址
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
            # 捕获具体的错误信息提示给用户
            err_msg = data.get("error", {}).get("message", "未知错误")
            return f"❌ 模型调用失败: {err_msg}"
    except Exception as e:
        return f"❌ 网络请求异常: {str(e)}"

# --- 3. 侧边栏：输入面板 ---
with st.sidebar:
    st.header("📥 商品输入")
    u_title = st.text_input("原始标题", "Elegant Silver Necklace")
    u_cat = st.selectbox("商品类型", ["项链", "耳环", "戒指", "手链", "脚链"])
    u_market = st.selectbox("目标市场", ["东南亚总区", "马来西亚", "美国", "新加坡"])
    u_gender = st.radio("受众性别", ["女性", "男性"], horizontal=True)
    u_files = st.file_uploader("上传参考图", type=["jpg", "png", "jpeg"])
    
    st.divider()
    if st.button("🔄 重置会话"):
        st.session_state.clear()
        st.rerun()

# --- 4. 主界面布局 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.caption("当前引擎：OpenRouter (DeepSeek + Gemini/DALL-E 混合驱动)")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("🛠️ 专家指令执行")
    
    # --- 按钮 1：SEO 优化 ---
    if st.button("✨ 执行：标题 SEO 优化"):
        with st.status("🔍 正在分析 TikTok 热搜词...", expanded=True):
            prompt = f"作为TikTok电商专家，为{u_market}市场的{u_cat}优化标题。原始标题：{u_title}。请返回3个高权重SEO标题，包含组成公式、推荐理由和中文翻译。请用Markdown表格展示。"
            # 文本任务使用 DeepSeek 或 Gemini
            st.session_state.seo_res = call_ai(prompt, "google/gemini-2.0-flash-exp:free")

    # --- 按钮 2：视觉方案与出图 ---
    if st.button("🖼️ 执行：生成莫兰迪优化图"):
        with st.status("🎨 正在调配莫兰迪色调与光影...", expanded=True):
            # 这里是核心：直接要求生成具有莫兰迪美感的专业摄影描述及指令
            img_prompt = f"""
            Task: Provide a professional jewelry photography result for a {u_cat}.
            Style Requirements: 
            1. Background: Warm Morandi cream/beige tones, matte texture.
            2. Lighting: 45-degree soft lighting, subtle cinematic shadows.
            3. Model/Prop: {u_gender} model if applicable, skin should be 'glass skin' effect.
            Output: A high-resolution image URL or a highly detailed Midjourney v6 prompt.
            """
            # 优先尝试 DALL-E 3，如果余额不足可换成 google/gemini-pro-vision
            st.session_state.img_res = call_ai(img_prompt, "openai/dall-e-3")

with col_right:
    st.subheader("📋 实时生成结果")
    
    # 展示标题优化结果
    if "seo_res" in st.session_state:
        st.markdown('<div class="res-box">', unsafe_allow_html=True)
        st.markdown("### ✍️ 爆款标题建议")
        st.write(st.session_state.seo_res)
        st.markdown('</div>', unsafe_allow_html=True)

    # 展示图片/视觉方案结果
    if "img_res" in st.session_state:
        st.markdown('<div class="res-box">', unsafe_allow_html=True)
        st.markdown("### 📸 视觉优化方案")
        # 逻辑判断：如果返回的是图片链接则显示图片，否则显示文字
        if "http" in st.session_state.img_res and ".png" in st.session_state.img_res:
            st.image(st.session_state.img_res, caption="✅ AI 实时生成的莫兰迪大片")
        else:
            st.info("💡 视觉指令已生成：")
            st.write(st.session_state.img_res)
        st.markdown('</div>', unsafe_allow_html=True)

    # 原始图片预览
    if u_files:
        st.divider()
        st.caption("🖼️ 待优化原图预览")
        st.image(u_files, width=200)

# 页脚
st.markdown("---")
st.caption(f"TikTok Shop AI Expert | Power by OpenRouter | {datetime.now().strftime('%Y-%m-%d')}")
