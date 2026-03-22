import streamlit as st
import requests
import re
import time
from PIL import Image

# --- 1. 内存暴力重置 (解决残留的 NameError 问题) ---
st.set_page_config(page_title="TikTok饰品AI V19", layout="wide")
for k in ["seo_data", "img_list"]:
    if k not in st.session_state: st.session_state[k] = None if k == "seo_data" else []

# --- 2. 核心执行引擎 (适配最新 OpenRouter 模型路径) ---
def run_jewelry_ai(task_type, cat, market, gender, title=""):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # 审美 Prompt 锁死逻辑
    if task_type == "SEO":
        p = f"TikTok饰品专家任务：为{market}的{gender}优化{cat}标题。原始：{title}。用Markdown表格输出SEO方案。"
        m_list = ["deepseek/deepseek-chat", "google/gemini-flash-1.5"]
    elif task_type == "MAIN":
        p = f"Jewelry photography of {cat}. Warm Morandi cream background, matte texture, 45-degree soft lighting, 8k, photorealistic. Direct URL only."
        # 修正 ID 路径：确保包含完整前缀
        m_list = ["openai/dall-e-3", "google/imagen-3"]
    else: # 模特图
        skin = "high-glow glass skin" if gender == "女性" else "tanned bronze skin"
        p = f"Macro photo of {gender} model wearing {cat}. {skin}, 45-degree lighting, high-end fashion, 8k. Direct URL only."
        m_list = ["openai/dall-e-3", "anthropic/claude-3-opus"]

    for mid in m_list:
        try:
            payload = {"model": mid, "messages": [{"role": "user", "content": p}]}
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"], mid
        except: continue
    return "❌ 所有模型尝试均失败，请检查 API Key 权限或余额。", "None"

# --- 3. 侧边栏 ---
with st.sidebar:
    st.header("📥 录入信息")
    u_title = st.text_input("1. 原始标题", "心形饰品")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("3. 目标市场", ["东南亚", "美国", "英国"])
    u_gen = st.radio("4. 目标性别", ["女性", "男性"], horizontal=True)
    
    st.divider()
    files = st.file_uploader("🖼️ 上传原图 (已锁定)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if files:
        cols = st.columns(3)
        for i, f in enumerate(files[:3]):
            with cols[i]: st.image(Image.open(f), width='stretch') # 适配 2026 语法

# --- 4. 主界面 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.caption("版本: V19.0 | 状态: 生产环境已加固")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 专家指令执行")
    if st.button("✨ 1. 标题 SEO 优化"):
        with st.status("SEO 方案生成中..."):
            st.session_state.seo_data, _ = run_jewelry_ai("SEO", u_cat, u_mkt, u_gen, u_title)
            
    if st.button("🖼️ 2. 生成莫兰迪主图"):
        with st.status("正在应用摄影方案..."):
            res, mod = run_jewelry_ai("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"type": "AI主图", "url": res, "mod": mod})

    if st.button("👤 3. 生成模特展示图"):
        with st.status(f"匹配{u_gen}模特中..."):
            res, mod = run_jewelry_ai("MODEL", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"type": "模特图", "url": res, "mod": mod})

with c2:
    st.subheader("📊 实时成果展示")
    if st.session_state.seo_data:
        st.markdown(st.session_state.seo_data)
    
    if st.session_state.img_list:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_list):
            with grid[i % 2]:
                st.caption(f"📡 模型: {item['mod']}")
                # 增强型 URL 提取逻辑
                found_urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if found_urls:
                    st.image(found_urls[0], width='stretch')
                else:
                    st.error(f"模型反馈: {item['url']}")
