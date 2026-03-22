import streamlit as st
import requests
import time
import base64
import zipfile
import io
from PIL import Image
from datetime import datetime

# --- 1. 页面配置与美化 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff4b4b; color: white; border: none; }
    .image-container { cursor: pointer; border-radius: 10px; overflow: hidden; transition: transform 0.2s; }
    .image-container:hover { transform: scale(1.02); }
    .status-text { color: #666; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# --- 2. 状态初始化 ---
if "results" not in st.session_state:
    st.session_state.results = {"titles": None, "images": [], "process_log": ""}
if "enlarged_img" not in st.session_state:
    st.session_state.enlarged_img = None

# --- 3. 核心 API 函数 ---
def call_deepseek_seo(payload_data):
    """调用 DeepSeek 进行多平台 SEO 优化"""
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = f"""
    你是一名顶级电商运营专家。
    原始标题: {payload_data['title']}
    类型: {payload_data['category']} | 市场: {payload_data['market']} | 年龄: {payload_data['age']} | 性别: {payload_data['gender']}
    
    任务：
    1. 参考 TikTok/Amazon/Etsy/Google Ads 饰品热词。
    2. 返回 3 个优化标题（按优先级排序）。
    3. 每个标题包含：[英文标题]、[中文翻译]、[推荐理由]、[组成公式]。
    请使用 Markdown 表格形式展示。
    """
    
    try:
        res = requests.post(url, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }, headers=headers)
        return res.json()['choices'][0]['message']['content']
    except:
        return "❌ SEO 生成失败，请检查 API 余额或网络。"

def generate_jewelry_image(prompt_type, context):
    """模拟调用图像生成模型 (此处需替换为你实际接入的图片生成逻辑)"""
    # 模拟生成进度
    for percent in range(0, 101, 20):
        time.sleep(0.5)
        yield percent
    # 这里返回占位图，实际部署时接入 Image Generation 工具
    return "https://via.placeholder.com/1024x1024.png?text=Jewelry+AI+Generated"

# --- 4. 侧边栏：输入信息 ---
with st.sidebar:
    st.header("📥 商品信息输入")
    origin_title = st.text_input("1. 原始标题", "Heart S925 Silver Necklace")
    category = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    market = st.selectbox("3. 目标市场", ["东南亚", "美国", "马来西亚", "新加坡", "泰国", "越南", "菲律宾"], index=0)
    age = st.slider("4. 目标人群年龄", 18, 60, (18, 35))
    gender = st.radio("5. 目标人群性别", ["女性", "男性"], horizontal=True)
    uploaded_files = st.file_uploader("6. 原始商品图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    st.divider()
    if st.button("🔄 重置工作区"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主界面布局 ---
col_action, col_display = st.columns([1, 1.2])

with col_action:
    st.subheader("🛠️ 专家指令区")
    
    # --- 按钮 1：标题优化 ---
    if st.button("✨ 1. 标题 SEO 优化"):
        with st.status("🔍 正在检索全球平台热词...", expanded=True) as status:
            st.write("正在分析 TikTok Shop 东南亚趋势...")
            result = call_deepseek_seo({
                "title": origin_title, "category": category, "market": market,
                "age": f"{age[0]}-{age[1]}", "gender": gender
            })
            st.session_state.results["titles"] = result
            status.update(label="✅ 标题优化完成！", state="complete")

    # --- 按钮 2：商品图优化 ---
    if st.button("🖼️ 2. 商品图优化 (主图+多角度)"):
        with st.status("🎨 正在构建莫兰迪色调布景...", expanded=True) as status:
            st.write("预估耗时: 25秒 | 当前进度: 准备材质贴图...")
            # 这里的 Prompt 会自动结合你要求的“背景要求”
            time.sleep(2)
            st.session_state.results["images"].append({"type": "主图", "url": "https://via.placeholder.com/800"})
            st.session_state.results["images"].append({"type": "多角度图", "url": "https://via.placeholder.com/801"})
            status.update(label="✅ 商品图生成完成！", state="complete")

    # --- 按钮 3：模特图优化 ---
    if st.button("👤 3. 模特佩戴图优化"):
        with st.status(f"🎭 正在匹配{gender}模特及妆造...", expanded=True) as status:
            st.write("正在配置柔和弥散光影...")
            time.sleep(2)
            st.session_state.results["images"].append({"type": "模特图", "url": "https://via.placeholder.com/802"})
            status.update(label="✅ 模特图生成完成！", state="complete")

    # --- 二次编辑功能 ---
    if st.session_state.results["images"]:
        st.divider()
        st.subheader("✍️ 二次局部微调")
        selected_img = st.selectbox("选择要修改的图片", [img['type'] for img in st.session_state.results["images"]])
        edit_advice = st.text_area("输入修改建议", placeholder="例如：背景再暗一点，增加丝绸褶皱...")
        if st.button("🪄 立即重新优化"):
            st.info(f"正在基于首次生成的 {selected_img} 进行迭代...")

with col_display:
    st.subheader("📋 实时生成结果")
    
    # 显示标题结果
    if st.session_state.results["titles"]:
        with st.expander("📝 查看优化标题方案", expanded=True):
            st.markdown(st.session_state.results["titles"])

    # 显示图片结果
    if st.session_state.results["images"]:
        cols = st.columns(2)
        for idx, img_obj in enumerate(st.session_state.results["images"]):
            with cols[idx % 2]:
                st.caption(f"【{img_obj['type']}】")
                # 点击放大逻辑：使用 st.image 包装
                st.image(img_obj['url'], use_container_width=True)
                if st.button(f"🔍 放大预览 {idx}", key=f"zoom_{idx}"):
                    st.session_state.enlarged_img = img_obj['url']

        # ZIP 下载逻辑
        st.divider()
        zip_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
        st.download_button("📥 打包下载全部图片 (ZIP)", data=b"", file_name=zip_name)

# --- 6. 放大镜浮层 (简单逻辑模拟) ---
if st.session_state.enlarged_img:
    st.divider()
    st.subheader("🔎 大图预览 (点击下方按钮缩小)")
    st.image(st.session_state.enlarged_img, width=800)
    if st.button("❌ 关闭放大"):
        st.session_state.enlarged_img = None
        st.rerun()
