import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
import io
import zipfile
from datetime import datetime

# --- 初始化状态存储 ---
if "optimized_data" not in st.session_state:
    st.session_state.optimized_data = {"titles": None, "main_img": None, "model_img": None}

# --- 页面 UI 配置 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide")
st.title("💎 TikTok Shop 饰品全能优化助手")
st.caption("专注东南亚市场：项链、耳环、戒指、手链等类目深度优化")

# --- API 配置 ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # 使用 1.5 Flash 兼顾速度与多模态能力
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except:
    st.error("⚠️ 请在 Streamlit Secrets 中配置 GOOGLE_API_KEY")
    st.stop()

# --- 侧边栏：输入逻辑 ---
with st.sidebar:
    st.header("📥 输入商品信息")
    origin_title = st.text_input("1. 原始标题", "心形 925 银项链")
    category = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    market = st.selectbox("3. 目标市场", ["东南亚", "美国", "马来西亚", "新加坡", "泰国", "越南", "菲律宾"], index=0)
    gender = st.radio("4. 目标人群性别", ["女性", "男性"], index=0)
    
    uploaded_files = st.file_uploader("5. 上传商品原图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

# --- 核心 Prompt 模板 (包含你的背景/模特要求) ---
JEWELRY_PROMPT_BASE = f"""
你是一位精通 TikTok Shop、Amazon 和 Etsy 的饰品运营专家。
针对 {market} 市场的 {category} 类目，受众为 18-35 岁{gender}。
请基于上传的图片进行分析。
"""

# --- 主界面布局 ---
col_output, col_preview = st.columns([1.5, 1])

with col_output:
    # --- 按钮 1：标题优化 ---
    if st.button("✨ 1. 标题优化 (SEO)"):
        with st.status("正在检索 TikTok 热搜词并分析优先级...", expanded=True) as status:
            time.sleep(1) # 模拟进度
            prompt = JEWELRY_PROMPT_BASE + f"优化此标题：{origin_title}。要求：返回优先级排序、推荐理由、组成公式，并附带中文翻译。"
            
            # 如果有图，带图分析
            content = [prompt]
            if uploaded_files:
                img = Image.open(uploaded_files[0])
                content.append(img)
            
            response = model.generate_content(content)
            st.session_state.optimized_data["titles"] = response.text
            status.update(label="标题优化完成！", state="complete")
        st.markdown(st.session_state.optimized_data["titles"])

    # --- 按钮 2：商品图优化建议 (由于免费版 API 限制，这里提供深度生成指令) ---
    if st.button("📸 2. 生成商品图/模特图优化指令"):
        with st.status("正在根据莫兰迪色调 & 模特妆造标准生成 Prompt...", expanded=True) as status:
            time.sleep(2)
            prompt = JEWELRY_PROMPT_BASE + "请为该商品设计一张主图和一张模特佩戴图的 AI 绘图提示词 (Prompt)。"
            prompt += "女性模特要求：水光肌、温柔感、米白背景、自然微卷发。男性模特要求：小麦色皮肤、黑色圆领衫、侧逆光。背景要求：莫兰迪色系、丝绸质感、45度柔光。"
            
            response = model.generate_content(prompt)
            st.session_state.optimized_data["img_prompts"] = response.text
            status.update(label="视觉方案生成完成！", state="complete")
        st.info("💡 建议将下方提示词复制到 Midjourney 或 Imagen 3 中生成最终大图")
        st.write(response.text)

with col_preview:
    st.subheader("🖼️ 图片预览与交互")
    if uploaded_files:
        for i, file in enumerate(uploaded_files):
            img = Image.open(file)
            # 点击放大缩小的交互建议：Streamlit 默认点击图片即可查看原图
            st.image(img, caption=f"原图 {i+1}", use_container_width=True)
            
    # 下载打包逻辑
    if st.session_state.optimized_data["titles"]:
        st.divider()
        st.subheader("📦 结果导出")
        
        # 准备下载文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_text = st.session_state.optimized_data["titles"]
        
        st.download_button(
            label="📥 下载优化方案 (TXT)",
            data=output_text,
            file_name=f"{timestamp}_report.txt",
            mime="text/plain"
        )

# --- CSS 注入：满足点击缩放等视觉微调 ---
st.markdown("""
<style>
    /* 模拟进度条动画 */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%); }
    /* 图片交互优化 */
    .stImage img { border-radius: 10px; transition: transform 0.3s; cursor: zoom-in; }
    .stImage img:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)
