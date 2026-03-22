import streamlit as st
import google.generativeai as genai
from PIL import Image
import time
from datetime import datetime

# --- 1. 初始状态存储 ---
if "optimized_data" not in st.session_state:
    st.session_state.optimized_data = {"titles": None, "img_prompts": None, "active_model": "尚未调用"}

# --- 2. 页面 UI 配置 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide")
st.title("💎 TikTok Shop 饰品全能优化助手")
st.info(f"🤖 当前工作模型：{st.session_state.optimized_data.get('active_model', '等待指令')}")

# --- 3. API 配置 ---
try:
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("❌ 未找到 API KEY，请在 Secrets 中配置。")
        st.stop()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"配置错误: {e}")
    st.stop()

# --- 4. 定义模型推荐优先级梯队 (严格匹配你的可用列表) ---
# 优先级说明：Flash(快) -> Pro(强) -> Lite(稳/高配额)
MODEL_HIERARCHY = [
    'gemini-flash-latest',       # 1. 综合最优
    'gemini-2.0-flash-001',     # 2. 备选新版
    'gemini-flash-lite-latest',  # 3. 最终保底（Lite版最不容易报429）
    'gemini-3-flash-preview'     # 4. 预览版尝试
]

# --- 5. 自动切换逻辑函数 ---
def try_generate_content(content):
    last_error = ""
    # 按照优先级依次尝试每个模型
    for model_name in MODEL_HIERARCHY:
        try:
            with st.spinner(f"正在尝试使用模型: {model_name}..."):
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(content)
                # 如果成功，记录当前使用的模型并返回结果
                st.session_state.optimized_data["active_model"] = model_name
                return response
        except Exception as e:
            last_error = str(e)
            if "429" in last_error:
                st.warning(f"⚠️ {model_name} 配额已满，正在自动切换下一模型...")
                time.sleep(1) # 短暂冷却
                continue
            else:
                st.warning(f"❌ {model_name} 报错: {last_error[:50]}... 尝试切换...")
                continue
    
    # 如果所有模型都失败了
    raise Exception(f"所有模型均尝试失败。最后一次报错: {last_error}")

# --- 6. 侧边栏与主界面 ---
with st.sidebar:
    st.header("📥 商品输入")
    origin_title = st.text_input("原始标题", "心形 925 银项链")
    category = st.selectbox("商品类型", ["项链", "耳环", "戒指", "手链"])
    uploaded_files = st.file_uploader("上传原图", type=["jpg", "png", "jpeg"])
    st.divider()
    if st.button("🔄 重置会话"):
        st.session_state.optimized_data = {"titles": None, "img_prompts": None, "active_model": "尚未调用"}
        st.rerun()

col_left, col_right = st.columns([1.5, 1])

with col_left:
    if st.button("✨ 执行全能优化"):
        if not origin_title:
            st.error("请先输入标题")
        else:
            # 构造 Prompt
            prompt = f"针对东南亚市场，优化{category}标题: '{origin_title}'。请结合热搜词提供3个建议和中文翻译。"
            input_data = [prompt]
            if uploaded_files:
                input_data.append(Image.open(uploaded_files))
            
            try:
                res = try_generate_content(input_data)
                st.session_state.optimized_data["titles"] = res.text
                st.success(f"✅ 调用成功！当前模型: {st.session_state.optimized_data['active_model']}")
            except Exception as final_e:
                st.error(f"🚨 最终失败: {final_e}")

    if st.session_state.optimized_data["titles"]:
        st.markdown("### 📝 优化方案")
        st.write(st.session_state.optimized_data["titles"])

with col_right:
    st.subheader("🖼️ 图片预览")
    if uploaded_files:
        st.image(uploaded_files, width="stretch")

# 样式
st.markdown("<style>.stButton>button { width: 100%; border-radius: 8px; }</style>", unsafe_allow_html=True)
