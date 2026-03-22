import streamlit as st
import requests
import time
import zipfile
import io
from datetime import datetime

# --- 1. 页面配置与美化 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家 (DeepSeek版)", layout="wide")
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.8em; font-weight: bold; background: #2b2b2b; color: white; }
    .stButton>button:hover { background: #ff4b4b; border: none; }
    .result-card { padding: 20px; border-radius: 15px; background: #f8f9fa; border: 1px solid #eee; margin-bottom: 20px; }
    .img-box { border: 2px dashed #ccc; border-radius: 10px; padding: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Session State 初始化 ---
if "data" not in st.session_state:
    st.session_state.data = {"seo": None, "visual": None, "model_shot": None, "logs": []}

def add_log(msg):
    st.session_state.data["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- 3. DeepSeek 核心调用 ---
def call_deepseek(prompt):
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    if not api_key:
        st.error("❌ 没检测到 DEEPSEEK_API_KEY，请在 Secrets 中配置")
        return None
    
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一位拥有10年经验的 TikTok Shop 饰品爆款专家，精通东南亚市场。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"API 异常: {str(e)}")
        return None

# --- 4. 侧边栏：输入区 ---
with st.sidebar:
    st.title("💎 商品配置")
    origin_title = st.text_input("1. 原始标题", placeholder="如：925银蝴蝶项链")
    category = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"])
    market = st.selectbox("3. 目标市场", ["东南亚总区", "马来西亚", "新加坡", "泰国", "越南", "菲律宾", "美国"])
    age_range = "18-35"
    gender = st.radio("4. 目标人群性别", ["女性", "男性"], horizontal=True)
    uploaded_files = st.file_uploader("5. 上传原始图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    st.divider()
    if st.button("🔄 开启新任务"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主界面布局 ---
st.title("🛍️ TikTok Shop 饰品全能优化助手")
st.caption("当前引擎：DeepSeek-V3 ｜ 状态：独占运行中")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("🛠️ 专家指令台")
    
    # --- 按钮 1：标题优化 ---
    if st.button("✨ 按钮：执行标题优化"):
        with st.status("🔍 检索 TikTok/Amazon/Etsy 热词...", expanded=True) as s:
            add_log(f"开始分析 {market} 市场的 {category} SEO...")
            prompt = f"""
            任务：优化{category}标题。参考平台：TikTok, Amazon, Etsy, Temu。
            原始信息：{origin_title}，目标：{market}，人群：{age_range}岁{gender}。
            要求：
            1. 提供3个爆款标题（优先级排序）。
            2. 每个标题包含：【英文标题】、【中文翻译】、【组成公式】、【推荐理由】。
            使用 Markdown 表格输出。
            """
            st.session_state.data["seo"] = call_deepseek(prompt)
            s.update(label="✅ 标题优化完成！", state="complete")

    # --- 按钮 2：商品图优化 (生成 MJ 指令) ---
    if st.button("🖼️ 按钮：生成商品图优化建议"):
        with st.status("🎨 正在设计莫兰迪布景方案...", expanded=True) as s:
            add_log("构建拍摄台：45度柔光、莫兰迪色调...")
            prompt = f"""
            为这款{gender}{category}设计两套拍摄方案（符合莫兰迪色调、中性肤色背景）。
            要求提供：
            1. 【主图拍摄建议】：包含光影布局、几何道具使用、微距参数。
            2. 【Midjourney 英文指令】：用于生成背景及氛围图。
            """
            st.session_state.data["visual"] = call_deepseek(prompt)
            s.update(label="✅ 视觉方案已生成！", state="complete")

    # --- 按钮 3：模特图优化 (生成 MJ 指令) ---
    if st.button("👤 按钮：生成模特佩戴建议"):
        with st.status("🎭 正在配置模特及妆造...", expanded=True) as s:
            add_log(f"设置{'水光肌' if gender=='女性' else '麦色皮肤'}模型参数...")
            prompt = f"""
            设计{gender}模特佩戴这款{category}的拍摄方案。
            要求：
            - 女性：水光肌、温柔背光、大面积留白。
            - 男性：麦色皮肤、黑针织衫、侧逆光立体感。
            返回：详细的拍摄指令及 2 组 MJ 提示词。
            """
            st.session_state.data["model_shot"] = call_deepseek(prompt)
            s.update(label="✅ 模特方案已生成！", state="complete")

with col_right:
    st.subheader("📋 优化结果展示")
    
    # 日志监控
    if st.session_state.data["logs"]:
        with st.expander("👁️ 实时进度与模型思考", expanded=False):
            for log in st.session_state.data["logs"]:
                st.caption(log)

    # SEO 展示
    if st.session_state.data["seo"]:
        st.markdown(f'<div class="result-card">{st.session_state.data["seo"]}</div>', unsafe_allow_html=True)

    # 视觉方案展示
    if st.session_state.data["visual"]:
        st.markdown(f'<div class="result-card"><b>📸 拍摄与 MJ 指令：</b><br>{st.session_state.data["visual"]}</div>', unsafe_allow_html=True)

    # 模特方案展示
    if st.session_state.data["model_shot"]:
        st.markdown(f'<div class="result-card"><b>👤 模特佩戴方案：</b><br>{st.session_state.data["model_shot"]}</div>', unsafe_allow_html=True)

    # 原图预览
    if uploaded_files:
        st.divider()
        st.caption("🖼️ 原始商品预览")
        cols = st.columns(3)
        for i, file in enumerate(uploaded_files):
            cols[i % 3].image(file, use_container_width=True)

# 页脚
st.markdown("---")
st.caption(f"TikTok Shop AI Expert | {datetime.now().strftime('%Y-%m-%d')}")
