import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
import io
from datetime import datetime

# --- 1. 初始状态存储 ---
if "optimized_data" not in st.session_state:
    st.session_state.optimized_data = {"titles": None, "img_prompts": None}

# 容错处理：确保键值对存在
for key in ["img_prompts", "titles"]:
    if key not in st.session_state.optimized_data:
        st.session_state.optimized_data[key] = None

# --- 2. 页面 UI 配置 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide")
st.title("💎 TikTok Shop 饰品全能优化助手")
st.caption("基于你的可用模型列表定制 - 稳定版")

# --- 3. API 配置 (严格匹配你的列表) ---
try:
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("❌ 请先在 Streamlit Secrets 中配置 GOOGLE_API_KEY")
        st.stop()
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 严格匹配你列表中的第 14 项: models/gemini-flash-latest
    # 如果这个还报 429，建议切换到第 15 项: gemini-flash-lite-latest
    MODEL_NAME = 'gemini-flash-latest' 
    model = genai.GenerativeModel(MODEL_NAME)
    
except Exception as e:
    st.error(f"⚠️ API 配置失败: {str(e)}")
    st.stop()

# --- 4. 侧边栏 ---
with st.sidebar:
    st.header("📥 输入商品信息")
    origin_title = st.text_input("1. 原始标题", "心形 925 银项链")
    category = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"])
    market = st.selectbox("3. 目标市场", ["东南亚", "美国", "马来西亚", "新加坡", "泰国", "越南", "菲律宾"])
    gender = st.radio("4. 目标人群性别", ["女性", "男性"])
    uploaded_files = st.file_uploader("5. 上传商品原图", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    st.divider()
    show_debug = st.checkbox("🐞 查看当前可用模型列表")

# --- 5. 核心逻辑：带重试机制的请求 ---
def generate_with_retry(content, max_retries=3):
    for i in range(max_retries):
        try:
            return model.generate_content(content)
        except Exception as e:
            if "429" in str(e) and i < max_retries - 1:
                time.sleep(2) # 遇到 429 稍微等一下再试
                continue
            else:
                raise e

# --- 6. 主界面 ---
col_output, col_preview = st.columns([1.5, 1])

with col_output:
    if st.button("✨ 1. 标题优化 (SEO)"):
        if not origin_title:
            st.warning("请输入标题")
        else:
            with st.status("正在分析 (模型: gemini-flash)...", expanded=True) as status:
                prompt = f"针对 {market} 18-35 岁 {gender}，优化 {category} 标题: '{origin_title}'。给出推荐理由和中文翻译。"
                content = [prompt]
                if uploaded_files:
                    content.append(Image.open(uploaded_files[0]))
                
                try:
                    response = generate_with_retry(content)
                    st.session_state.optimized_data["titles"] = response.text
                    status.update(label="完成！", state="complete")
                except Exception as e:
                    st.error(f"生成失败 (可能是额度超限): {str(e)}")

    if st.session_state.optimized_data.get("titles"):
        st.markdown(st.session_state.optimized_data["titles"])

    st.divider()

    if st.button("📸 2. 生成视觉优化指令"):
        with st.status("正在思考方案...", expanded=True) as status:
            v_prompt = f"为 {gender} 佩戴的 {category} 设计 AI 绘图提示词。背景要求: 莫兰迪色、哑光质感。模特要求: 水光肌、高质感。"
            try:
                response = generate_with_retry(v_prompt)
                st.session_state.optimized_data["img_prompts"] = response.text
                status.update(label="完成！", state="complete")
            except Exception as e:
                st.error(f"失败: {str(e)}")

    if st.session_state.optimized_data.get("img_prompts"):
        st.write(st.session_state.optimized_data["img_prompts"])

with col_preview:
    st.subheader("🖼️ 图片预览")
    if uploaded_files:
        for i, file in enumerate(uploaded_files):
            st.image(Image.open(file), caption=f"原图 {i+1}", width="stretch")
    
    if st.session_state.optimized_data.get("titles"):
        st.download_button("📥 下载结果", st.session_state.optimized_data["titles"], f"SEO_{datetime.now().strftime('%H%M%S')}.txt")

# --- 7. 调试模式 ---
if show_debug:
    try:
        models = [m.name for m in genai.list_models()]
        st.json(models)
    except:
        st.write("无法获取列表")
