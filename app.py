import streamlit as st
import requests
import time
from PIL import Image

# --- 1. 初始状态与页面配置 ---
st.set_page_config(page_title="TikTok 饰品优化专家 - DeepSeek", layout="wide")
st.title("💎 TikTok Shop 饰品全能优化助手 (DeepSeek 驱动)")

if "optimized_titles" not in st.session_state:
    st.session_state.optimized_titles = None
if "visual_advice" not in st.session_state:
    st.session_state.visual_advice = None

# --- 2. API 配置 (从 Secrets 读取) ---
DEEPSEEK_KEY = st.secrets.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

def call_deepseek(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_KEY}"
    }
    payload = {
        "model": "deepseek-chat", # 使用 DeepSeek-V3 模型
        "messages": [
            {"role": "system", "content": "你是一位精通 TikTok Shop 东南亚市场的饰品运营专家。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"❌ 调用失败 (错误代码: {response.status_code}): {response.text}"

# --- 3. 界面布局 ---
with st.sidebar:
    st.header("📥 商品输入")
    origin_title = st.text_input("1. 原始标题", "心形 925 银项链")
    category = st.selectbox("2. 商品类型", ["项链", "耳环", "戒指", "手链", "耳钉", "脚链"])
    market = st.selectbox("3. 目标市场", ["东南亚总区", "马来西亚", "泰国", "越南", "菲律宾"])
    gender = st.radio("4. 目标人群", ["女性", "男性"])
    uploaded_file = st.file_uploader("5. 上传预览图", type=["jpg", "png", "jpeg"])
    
    st.divider()
    if st.button("🔄 重置所有内容"):
        st.session_state.clear()
        st.rerun()

col_left, col_right = st.columns([1.5, 1])

with col_left:
    # --- 按钮 1：标题 SEO 优化 ---
    if st.button("✨ 执行全能 SEO 标题优化"):
        if not DEEPSEEK_KEY:
            st.error("请先在 Secrets 中配置 DEEPSEEK_API_KEY")
        else:
            with st.status("DeepSeek 正在搜索热词并生成标题...", expanded=True):
                prompt = f"""
                作为饰品运营专家，请优化此{category}标题: '{origin_title}'。
                市场: {market}，受众: {gender}。
                要求：
                1. 给出 3 个高转化标题（包含爆款关键词）。
                2. 解释每个标题的 SEO 逻辑。
                3. 提供对应中文翻译。
                """
                st.session_state.optimized_titles = call_deepseek(prompt)
                st.success("标题优化完成！")

    if st.session_state.optimized_titles:
        st.markdown("### 📝 标题优化建议")
        st.write(st.session_state.optimized_titles)

    st.divider()

    # --- 按钮 2：视觉拍摄建议 (Midjourney 指令) ---
    if st.button("📸 生成 AI 视觉优化建议"):
        with st.status("正在设计高质量拍摄方案...", expanded=True):
            prompt = f"""
            为这款{gender}款{category}设计一套高质感拍摄方案。
            请提供：
            1. 2条用于 AI 绘图的 Midjourney 提示词（英文）。
            2. 场景描述：要求莫兰迪色调背景、丝绸纹理、高级珠宝光影。
            3. 模特建议：要求展示佩戴细节，肤质要求水光肌。
            """
            st.session_state.visual_advice = call_deepseek(prompt)
            st.success("视觉建议已生成！")

    if st.session_state.visual_advice:
        st.markdown("### 🖼️ 拍摄与视觉建议")
        st.write(st.session_state.visual_advice)

with col_right:
    st.subheader("🖼️ 图片预览")
    if uploaded_file:
        st.image(uploaded_file, caption="待优化商品图", use_container_width=True)
    else:
        st.info("上传图片后将在此处显示预览")

# 样式美化
st.markdown("<style>.stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #f8f9fb; font-weight: bold; }</style>", unsafe_allow_html=True)
