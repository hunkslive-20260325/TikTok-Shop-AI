import streamlit as st
import requests
import re
import time
from datetime import datetime
from PIL import Image

# --- 1. 内存初始化 (确保 session_state 永远可用) ---
for key in ["seo_res", "img_res", "log_res"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "seo_res" else []

# --- 2. 页面基础配置 (适配 2026 最新语法) ---
st.set_page_config(page_title="TikTok饰品AI专家 V17", layout="wide")
st.markdown("""
    <style>
    .stButton>button { width:100%; border-radius:12px; height:3.5em; background:#1a1a1a; color:white; font-weight:bold; }
    .status-tag { background:#f0f2f5; color:#1a1a1a; padding:2px 10px; border-radius:15px; font-size:0.8em; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心请求引擎 (暴力注入所有审美描述，彻底杜绝变量丢失) ---
def call_ai_engine(task, u_cat, u_market, u_gender, u_title=""):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # 逻辑锁死：不再引用外部变量，直接在这里定义 Prompt
    if task == "SEO":
        prompt = f"TikTok饰品专家任务：为{u_market}的{u_gender}优化{u_cat}标题。原始：{u_title}。请返回3个含爆款公式和翻译的建议，用Markdown表格输出。"
        models = ["deepseek/deepseek-chat"]
    elif task == "MAIN_IMG":
        # 莫兰迪色调、45度柔光描述直接硬编码
        prompt = f"Professional jewelry photography of {u_cat}. Warm Morandi cream background, matte texture, geometric blocks, 45-degree soft lighting, cinematic shadows, 8k, photorealistic. Direct URL only."
        models = ["openai/dall-e-3", "black-forest-labs/flux-schnell"]
    else: # 模特图
        skin_desc = "high-glow glass skin, white silk outfit" if u_gender == "女性" else "tanned bronze skin, sharp jawline, black crew neck"
        prompt = f"Macro fashion photo of {u_gender} model wearing {u_cat}. {skin_desc}, 45-degree side lighting, magazine style, 8k. Direct URL only."
        models = ["openai/dall-e-3", "black-forest-labs/flux-schnell"]

    start = time.time()
    for mid in models:
        try:
            res = requests.post(url, headers=headers, json={"model": mid, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            data = res.json()
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                return content, mid, round(time.time()-start, 1)
        except: continue
    return "❌ 生成失败，请检查 API Key 余额或模型 ID", "None", 0

# --- 4. 侧边栏：经营信息输入 ---
with st.sidebar:
    st.header("📥 经营信息")
    u_title = st.text_input("1. 原始标题", "心形饰品")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指", "手镯"])
    u_market = st.selectbox("3. 目标市场", ["东南亚总区", "美国", "英国"])
    u_gender = st.radio("4. 目标性别", ["女性", "男性"], horizontal=True)
    
    st.divider()
    st.subheader("🖼️ 上传原图 (已锁定)")
    files = st.file_uploader("支持多张拖入", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if files:
        cols = st.columns(3)
        for i, f in enumerate(files[:3]):
            with cols[i]: st.image(Image.open(f), width='stretch')

# --- 5. 主界面：执行与预览 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.caption("V17.0 逻辑加固版 | 2026 语法适配 | 审美描述已锁死")

col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.subheader("🚀 指令执行台")
    
    if st.button("✨ 1. 执行：标题 SEO 优化"):
        with st.status("正在检索 TikTok 热搜词..."):
            res, mod, dur = call_ai_engine("SEO", u_cat, u_market, u_gender, u_title)
            st.session_state.seo_res = res
            st.session_state.log_res.append(f"SEO完成 | {mod} | {dur}s")

    if st.button("🖼️ 2. 执行：商品图优化"):
        with st.status("应用莫兰迪暖色调摄影方案..."):
            res, mod, dur = call_ai_engine("MAIN_IMG", u_cat, u_market, u_gender)
            st.session_state.img_res.append({"type": "AI优化主图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"主图完成 | {mod} | {dur}s")

    if st.button("👤 3. 执行：模特图优化"):
        with st.status(f"匹配{u_gender}模特视觉方案..."):
            res, mod, dur = call_ai_engine("MODEL_IMG", u_cat, u_market, u_gender)
            st.session_state.img_res.append({"type": f"{u_gender}模特图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"模特完成 | {mod} | {dur}s")

with col_r:
    st.subheader("📋 实时工作成果")
    
    if st.session_state.seo_res:
        with st.expander("📝 标题 SEO 建议", expanded=True): st.markdown(st.session_state.seo_res)
    
    if st.session_state.img_res:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_res):
            with grid[i % 2]:
                st.markdown(f'<span class="status-tag">📡 {item["mod"]}</span>', unsafe_allow_html=True)
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls:
                    st.image(urls[0], caption=item["type"], width='stretch')
                else:
                    st.error(f"模型报错: {item['url']}")
    
    if st.session_state.log_res:
        with st.expander("👁️ 运行日志"):
            for log in st.session_state.log_res: st.caption(log)
