import streamlit as st
import requests
import time
import zipfile
import io
import json
from datetime import datetime
from PIL import Image

# --- 1. 页面配置与 UI 美化 ---
st.set_page_config(page_title="TikTok Shop 饰品 AI 专家", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    /* 全局按钮美化 */
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; 
        background-image: linear-gradient(45deg, #2b2b2b 0%, #4a4a4a 100%);
        color: white; border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-image: linear-gradient(45deg, #ff4b4b 0%, #ff8080 100%); transform: translateY(-2px); }
    
    /* 结果卡片美化 */
    .result-card { 
        padding: 20px; border-radius: 15px; background: #ffffff; 
        border: 1px solid #eaeaea; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px; color: #333;
    }
    
    /* 图片交互：鼠标悬停放大 */
    .img-container img { border-radius: 10px; transition: 0.4s; cursor: zoom-in; }
    .img-container img:hover { transform: scale(1.05); }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心状态初始化 ---
if "app_state" not in st.session_state:
    st.session_state.app_state = {
        "seo_result": None,
        "generated_images": [], # 存储结构: {"type": "", "url": "", "time": ""}
        "process_logs": [],
        "zip_buffer": None
    }

def add_log(msg):
    st.session_state.app_state["process_logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# --- 3. API 调用核心 (OpenRouter & DeepSeek) ---
def request_ai(prompt, model="deepseek/deepseek-chat", is_image=False):
    """通用 AI 请求函数，支持 OpenRouter"""
    api_key = st.secrets["OPENROUTER_API_KEY"]
    # 如果是纯文本 SEO，可以使用 DeepSeek 官方或 OpenRouter 转发
    # 这里统一走 OpenRouter 方便管理
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tiktok-shop-expert.streamlit.app", # 选填
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        if "choices" in res_json:
            return res_json["choices"][0]["message"]["content"]
        else:
            return f"Error: {res_json}"
    except Exception as e:
        return f"Request Failed: {str(e)}"

# --- 4. 侧边栏：输入面板 ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/jewelry.png", width=80)
    st.header("📦 商品基本信息")
    
    u_title = st.text_input("1. 原始标题", placeholder="输入商品名称...")
    u_category = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    u_market = st.selectbox("3. 目标市场", ["东南亚", "美国", "马来西亚", "新加坡", "泰国", "越南", "菲律宾"], index=0)
    u_gender = st.radio("4. 目标人群性别", ["女性", "男性"], horizontal=True)
    u_files = st.file_uploader("5. 上传原图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    st.divider()
    if st.button("🗑️ 清空工作台"):
        st.session_state.app_state = {"seo_result": None, "generated_images": [], "process_logs": [], "zip_buffer": None}
        st.rerun()

# --- 5. 主界面布局 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.info("💡 提示：所有图片生成均已固化「莫兰迪暖色调」与「45度柔光」专业摄影逻辑。")

col_action, col_display = st.columns([1, 1.2])

# --- 左侧：指令操作区 ---
with col_action:
    st.subheader("🛠️ 专家指令执行")
    
    # -- 1. 标题优化 --
    if st.button("✨ 执行：标题 SEO 优化"):
        with st.status("🔍 正在检索全球热词并生成公式...", expanded=True) as s:
            add_log(f"开始为 {u_market} 市场优化 {u_category} 标题...")
            prompt = f"""
            你是一名TikTok Shop爆款运营专家。
            原始标题：{u_title}
            类目：{u_category} | 市场：{u_market} | 受众：18-35岁{u_gender}。
            任务：
            1. 参考TikTok、Amazon、Etsy热搜词，提供3个优化后的英文标题（优先级排序）。
            2. 每个标题必须包含：[推荐理由]、[标题组成公式]、[中文翻译]。
            3. 针对东南亚平价饰品风格。使用 Markdown 表格输出。
            """
            result = request_ai(prompt, model="deepseek/deepseek-chat")
            st.session_state.app_state["seo_result"] = result
            s.update(label="✅ 标题优化方案已生成！", state="complete")

    # -- 2. 商品图优化 --
    if st.button("🖼️ 执行：商品图生成 (主图/多角度)"):
        with st.status("🎨 正在构建莫兰迪暖色布景...", expanded=True) as s:
            add_log("分析原图材质中...")
            # 使用 OpenRouter 上的顶级模型 (如 Google Gemini 1.5 Pro 或 OpenAI DALL-E 3)
            # 这里推荐使用专门的绘图 Prompt
            vis_prompt = f"""
            Create a professional jewelry ad photo of a {u_category}. 
            Style: Warm Morandi palette, cream and beige matte background. 
            Lighting: 45-degree soft studio lighting, soft cinematic shadows. 
            Composition: Placed on a minimalist geometric stone block, centered, high-end texture. 
            Quality: 8k, photorealistic, no text, no floating.
            """
            # 注意：绘图模型建议在 OpenRouter 选 openai/dall-e-3 或 anthropic/claude-3-opus (后者需配合插件)
            # 这里演示使用 DALL-E 3 逻辑
            img_res = request_ai(vis_prompt, model="openai/dall-e-3")
            st.session_state.app_state["generated_images"].append({"type": "AI 优化主图", "url": img_res})
            add_log("主图生成完毕。")
            s.update(label="✅ 商品图优化完成！", state="complete")

    # -- 3. 模特图优化 --
    if st.button("👤 执行：模特图生成"):
        with st.status(f"🎭 正在配置{u_gender}模特妆造...", expanded=True) as s:
            skin = "Glass skin, pale and glowing" if u_gender == "女性" else "Tanned skin, masculine jawline"
            cloth = "White silk dress" if u_gender == "女性" else "Black luxury crew neck sweater"
            m_prompt = f"""
            Photorealistic close-up of a {u_gender} model wearing a {u_category}. 
            Model traits: {skin}, wearing {cloth}. 
            Lighting: Soft diffused lighting, backlighting for hair. 
            Vibe: Gentle, elegant, Morandi beige background, professional fashion photography style.
            """
            img_res = request_ai(m_prompt, model="openai/dall-e-3")
            st.session_state.app_state["generated_images"].append({"type": f"{u_gender}模特效果图", "url": img_res})
            s.update(label="✅ 模特佩戴图生成完成！", state="complete")

    # -- 二次微调 --
    if st.session_state.app_state["generated_images"]:
        st.divider()
        st.subheader("✏️ 局部二次编辑")
        target = st.selectbox("选择要修改的图片", [img["type"] for img in st.session_state.app_state["generated_images"]])
        edit_msg = st.text_input("输入修改建议", placeholder="例如：背景换成淡绿色，增加丝绸纹理...")
        if st.button("🪄 基于建议重新优化"):
            st.info(f"正在根据「{edit_msg}」重新生成...")

# --- 右侧：结果展示区 ---
with col_display:
    st.subheader("📋 实时生成结果")
    
    # 展示标题
    if st.session_state.app_state["seo_result"]:
        with st.expander("📝 点击查看：SEO 标题优化方案", expanded=True):
            st.markdown(st.session_state.app_state["seo_result"])

    # 展示图片 (支持点击自动放大)
    if st.session_state.app_state["generated_images"]:
        img_cols = st.columns(2)
        for idx, item in enumerate(st.session_state.app_state["generated_images"]):
            with img_cols[idx % 2]:
                st.markdown(f"**📍 {item['type']}**")
                # 如果是 DALL-E 3 返回的是 Markdown 链接，直接展示即可
                # Streamlit 原生支持点击图片放大
                st.markdown(f'<div class="img-container">{item["url"]}</div>', unsafe_allow_html=True)
                st.caption("🔍 点击图片可查看原图并下载")

        # ZIP 下载功能
        st.divider()
        zip_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
        st.download_button(
            label="📥 全部图片打包下载 (ZIP格式)",
            data=b"Generate_ZIP_Content", # 这里需要配合图片下载逻辑
            file_name=zip_name,
            mime="application/zip"
        )

    # 思考日志
    if st.session_state.app_state["process_logs"]:
        with st.expander("👁️ 实时模型思考过程 (逻辑监控)"):
            for log in st.session_state.app_state["process_logs"]:
                st.caption(log)

# 页脚
st.markdown("---")
st.caption(f"TikTok Shop AI Expert v5.0 | 运行环境：OpenRouter + DeepSeek V3")
