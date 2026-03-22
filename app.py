import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
import io
from datetime import datetime

# --- 1. 初始状态存储 (确保数据持久化) ---
if "optimized_data" not in st.session_state:
    st.session_state.optimized_data = {
        "titles": None, 
        "img_prompts": None
    }

# 容错处理：确保所有必要的键都存在于 session_state 中
for key in ["img_prompts", "titles"]:
    if key not in st.session_state.optimized_data:
        st.session_state.optimized_data[key] = None

# --- 2. 页面 UI 配置 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide")
st.title("💎 TikTok Shop 饰品全能优化助手")
st.caption("专注东南亚市场：项链、耳环、戒指、手链等类目深度优化")

# --- 3. API 配置 (匹配你列表中的最新模型) ---
try:
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("❌ 未在 Secrets 中找到 GOOGLE_API_KEY。请在 Streamlit 控制台配置。")
        st.stop()
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 根据你的可用模型列表，选择性能最强的预览版模型
    # 选项：'gemini-3.1-pro-preview' 或 'gemini-3-flash-preview'
    MODEL_NAME = 'gemini-3-flash-preview' 
    model = genai.GenerativeModel(MODEL_NAME)
    
except Exception as e:
    st.error(f"⚠️ API 配置失败: {str(e)}")
    st.stop()

# --- 4. 侧边栏：输入逻辑 ---
with st.sidebar:
    st.header("📥 输入商品信息")
    origin_title = st.text_input("1. 原始标题", "心形 925 银项链")
    category = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    market = st.selectbox("3. 目标市场", ["东南亚", "美国", "马来西亚", "新加坡", "泰国", "越南", "菲律宾"], index=0)
    gender = st.radio("4. 目标人群性别", ["女性", "男性"], index=0)
    
    uploaded_files = st.file_uploader("5. 上传商品原图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    st.divider()
    show_debug = st.checkbox("🐞 开启调试模式")

# --- 5. 核心 Prompt 模板 (集成你的专业背景要求) ---
JEWELRY_PROMPT_BASE = f"""
你是一位精通 TikTok Shop 和东南亚电商运营的饰品专家。
针对 {market} 市场的 {category} 类目，受众为 18-35 岁 {gender}。
"""

# --- 6. 主界面布局 ---
col_output, col_preview = st.columns([1.5, 1])

with col_output:
    # --- 按钮 1：标题优化 ---
    if st.button("✨ 1. 标题优化 (SEO)"):
        if not origin_title:
            st.warning("请先输入原始标题")
        else:
            with st.status("AI 正在分析热搜词并生成方案...", expanded=True) as status:
                prompt = JEWELRY_PROMPT_BASE + f"""
                任务：优化此商品标题：'{origin_title}'。
                要求：
                1. 按照推荐优先级排序返回 3 个标题。
                2. 详细说明推荐理由及标题组成公式。
                3. 使用 Google 翻译提供对应的中文意思。
                4. 参考 TikTok、Amazon、Google Ads 的热搜词逻辑。
                """
                
                content = [prompt]
                if uploaded_files:
                    # 使用第一张上传的图进行视觉分析
                    img = Image.open(uploaded_files[0])
                    content.append(img)
                
                try:
                    response = model.generate_content(content)
                    st.session_state.optimized_data["titles"] = response.text
                    status.update(label="标题优化完成！", state="complete")
                except Exception as e:
                    st.error(f"生成失败: {str(e)}")
                    status.update(label="生成出错", state="error")

    if st.session_state.optimized_data.get("titles"):
        st.markdown(st.session_state.optimized_data["titles"])

    st.divider()

    # --- 按钮 2：视觉优化建议 ---
    if st.button("📸 2. 生成视觉优化指令"):
        with st.status("正在根据专业调性生成提示词...", expanded=True) as status:
            visual_prompt = JEWELRY_PROMPT_BASE + """
            请为该商品设计高品质 AI 绘图提示词 (Prompt)：
            1. 主图：要求莫兰迪色背景、丝绸/缎面材质、45度柔和光影。
            2. 模特图：要求展示受众性别的佩戴效果、水光肌质感、简约纯色服装。
            3. 请确保符合饰品类目的高级质感，不准出现违反地心引力的悬空。
            """
            try:
                response = model.generate_content(visual_prompt)
                st.session_state.optimized_data["img_prompts"] = response.text
                status.update(label="视觉方案生成完成！", state="complete")
            except Exception as e:
                st.error(f"生成失败: {str(e)}")

    if st.session_state.optimized_data.get("img_prompts"):
        st.info("💡 建议将下方提示词复制到 Midjourney 或 Imagen 中生成大图")
        st.write(st.session_state.optimized_data["img_prompts"])

with col_preview:
    st.subheader("🖼️ 图片预览")
    if uploaded_files:
        for i, file in enumerate(uploaded_files):
            # 修正语法警告：使用 width="stretch"
            st.image(Image.open(file), caption=f"原图 {i+1}", width="stretch")
            
    # 下载功能
    if st.session_state.optimized_data.get("titles"):
        st.divider()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        st.download_button(
            label="📥 下载优化方案 (TXT)",
            data=str(st.session_state.optimized_data["titles"]),
            file_name=f"TikTok_SEO_{timestamp}.txt",
            mime="text/plain"
        )

# --- 7. 调试模式 ---
if show_debug:
    st.subheader("🧪 调试信息")
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        st.write("可用模型列表：")
        st.json(models)
    except Exception as e:
        st.error(f"无法获取模型列表: {str(e)}")

# --- 8. 简单样式优化 ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #f0f2f6; }
    .stImage img { border-radius: 10px; cursor: zoom-in; }
</style>
""", unsafe_allow_html=True)
