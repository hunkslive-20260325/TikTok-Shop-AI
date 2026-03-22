import streamlit as st
import requests
import re
import time
from PIL import Image

# --- 1. 强制状态重置 ---
st.set_page_config(page_title="TikTok饰品AI V18", layout="wide")
if "seo_data" not in st.session_state: st.session_state.seo_data = None
if "img_list" not in st.session_state: st.session_state.img_list = []

# --- 2. 暴力 Prompt 引擎 (不引用任何外部变量) ---
def run_ai_task(task_type, cat, market, gender, title=""):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # 彻底硬编码描述
    if task_type == "SEO":
        p = f"TikTok饰品专家任务：为{market}的{gender}优化{cat}标题。原始：{title}。Markdown表格输出。"
        m = ["deepseek/deepseek-chat"]
    elif task_type == "MAIN":
        p = f"Professional jewelry photography: {cat}. Warm Morandi cream background, matte texture, 45-degree soft lighting, 8k. Direct URL."
        m = ["openai/dall-e-3", "black-forest-labs/flux-schnell"]
    else:
        skin = "high-glow glass skin" if gender == "女性" else "tanned bronze skin"
        p = f"Macro photo of {gender} model wearing {cat}. {skin}, 45-degree side lighting, 8k. Direct URL."
        m = ["openai/dall-e-3", "black-forest-labs/flux-schnell"]

    for model_id in m:
        try:
            res = requests.post(url, headers=headers, json={"model": model_id, "messages": [{"role": "user", "content": p}]}, timeout=60)
            res_json = res.json()
            if "choices" in res_json:
                return res_json["choices"][0]["message"]["content"], model_id
        except Exception as e:
            continue
    return f"❌ 无法连接到模型。错误: {str(res.text if 'res' in locals() else 'Unknown')}", "None"

# --- 3. 侧边栏 ---
with st.sidebar:
    st.header("📥 录入信息")
    u_title = st.text_input("标题", "心形饰品")
    u_cat = st.selectbox("类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("市场", ["东南亚", "美国", "英国"])
    u_gen = st.radio("性别", ["女性", "男性"], horizontal=True)
    
    st.divider()
    files = st.file_uploader("上传原图", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if files:
        cols = st.columns(3)
        for i, f in enumerate(files[:3]):
            with cols[i]: st.image(Image.open(f), width='stretch')

# --- 4. 主界面 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("🚀 执行指令")
    if st.button("✨ 1. 优化标题 SEO"):
        with st.status("处理中..."):
            res, mod = run_ai_task("SEO", u_cat, u_mkt, u_gen, u_title)
            st.session_state.seo_data = res
            
    if st.button("🖼️ 2. 生成莫兰迪主图"):
        with st.status("绘图中..."):
            res, mod = run_ai_task("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"type": "主图", "url": res, "mod": mod})

    if st.button("👤 3. 生成模特展示图"):
        with st.status("匹配模特中..."):
            res, mod = run_ai_task("MODEL", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"type": "模特图", "url": res, "mod": mod})

with col2:
    st.subheader("📊 成果展示")
    if st.session_state.seo_data:
        st.markdown(st.session_state.seo_data)
    
    if st.session_state.img_list:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_list):
            with grid[i % 2]:
                st.caption(f"📡 {item['mod']}")
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls: st.image(urls[0], width='stretch')
                else: st.error(item["url"])
