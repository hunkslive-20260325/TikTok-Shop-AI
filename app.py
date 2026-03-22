import streamlit as st
import requests
import re
import time
import zipfile
import io
from datetime import datetime
from PIL import Image

# --- 1. 审美灵魂锁死 (莫兰迪、柔光、水光肌/古铜色) ---
AESTHETIC_CORE = "Warm Morandi cream background, matte texture, geometric blocks, 45-degree soft lighting, cinematic shadows."
FEMALE_AESTHETIC = "Female model, high-glow glass skin, water-like texture, white silk outfit, soft window light."
MALE_AESTHETIC = "Male model, tanned bronze skin, sharp jawline, stubbles, black crew neck, 45-degree side lighting."

# --- 2. 内存强制初始化 ---
if "seo_res" not in st.session_state: st.session_state.seo_res = None
if "img_res" not in st.session_state: st.session_state.img_res = []
if "log_res" not in st.session_state: st.session_state.log_res = []

# --- 3. 页面样式适配 ---
st.set_page_config(page_title="TikTok饰品AI专家 V13", layout="wide", page_icon="💎")
st.markdown("""
    <style>
    .stButton>button { width:100%; border-radius:12px; height:3.5em; background:#1a1a1a; color:white; font-weight:bold; border:none; transition:0.3s; }
    .stButton>button:hover { background:#ff4b4b; transform:translateY(-2px); }
    .status-tag { background:#e8f5e9; color:#2e7d32; padding:2px 10px; border-radius:15px; font-size:0.8em; font-weight:bold; }
    .err-card { padding:10px; background:#fff1f0; border:1px solid #ffa39e; border-radius:8px; color:#cf1322; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 智能请求引擎 (补全 openai/ 前缀逻辑) ---
def smart_call(prompt, model_list):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.time()
    for mid in model_list:
        try:
            full_id = f"openai/{mid}" if mid == "dall-e-3" else mid
            res = requests.post(url, headers=headers, json={"model": full_id, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"], full_id, round(time.time()-start, 1)
        except: continue
    return "❌ 模型调用失败，请检查 API Key 余额", "None", 0

# --- 5. 侧边栏：功能补全 ---
with st.sidebar:
    st.header("📥 经营信息输入")
    u_title = st.text_input("1. 原始标题", placeholder="例：S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指", "手镯"])
    u_market = st.selectbox("3. 目标市场", ["东南亚总区", "美国", "英国", "泰国"])
    u_gender = st.radio("4. 目标性别趋势", ["女性", "男性"], horizontal=True)
    
    st.divider()
    st.subheader("🖼️ 上传原图 (已锁定)")
    uploaded_files = st.file_uploader("拖入商品照片", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if uploaded_files:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files[:3]):
            with cols[idx]:
                st.image(Image.open(file), width='stretch') # 适配 2026 新语法

    st.divider()
    st.header("🤖 模型配置")
    t_mod = st.text_input("文案模型 ID", "deepseek/deepseek-chat")
    i_mod_1 = st.text_input("首选绘图 ID", "openai/dall-e-3")
    i_mod_2 = st.text_input("备选绘图 ID", "black-forest-labs/flux-schnell")

# --- 6. 主界面 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.info(f"💡 需求加固：莫兰迪色 | 45度柔光 | {u_gender}专用方案 (水光肌/古铜色对比)")

col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.subheader("🚀 专家指令执行")
    
    if st.button("✨ 1. 执行：标题 SEO 优化"):
        with st.status("SEO 生成中...") as s:
            p = f"TikTok饰品专家任务：为{u_market}的{u_gender}优化{u_cat}标题。原始：{u_title}。表格输出方案。"
            res, mod, dur = smart_call(p, [t_mod, "google/gemini-flash-1.5"])
            st.session_state.seo_res = res
            st.session_state.log_res.append(f"SEO完成 | 模型: {mod} | {dur}s")
            s.update(label="✅ 标题优化完成", state="complete")

    if st.button("🖼️ 2. 执行：商品图优化"):
        with st.status("执行莫兰迪摄影方案...") as s:
            p = f"Professional jewelry photography: {u_cat}. {AESTHETIC_CORE} 8k, photorealistic. Direct URL."
            res, mod, dur = smart_call(p, [i_mod_1, i_mod_2])
            st.session_state.img_res.append({"type": "AI 优化主图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"主图完成 | 模型: {mod} | {dur}s")
            s.update(label="✅ 图片生成完成", state="complete")

    if st.button("👤 3. 执行：模特图优化"):
        with st.status(f"匹配{u_gender}模特拍摄...") as s:
            m_p = FEMALE_AESTHETIC if u_gender == "女性" else MALE_AESTHETIC
            p = f"Macro photo of a {u_gender} model wearing {u_cat}. {m_p} 8k, fashion style. Direct URL."
            res, mod, dur = smart_call(p, [i_mod_1, i_mod_2])
            st.session_state.img_res.append({"type": f"{u_gender}模特图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"模特完成 | 模型: {mod} | {dur}s")
            s.update(label="✅ 模特图优化完成", state="complete")

with col_r:
    st.subheader("📋 成果实时预览")
    if st.session_state.seo_res:
        with st.expander("📝 标题 SEO 方案", expanded=True): st.markdown(st.session_state.seo_res)
    if st.session_state.img_res:
        grid = st.columns(2)
        for idx, item in enumerate(st.session_state.img_res):
            with grid[idx % 2]:
                st.markdown(f'<span class="status-tag">📡 {item["mod"]}</span>', unsafe_allow_html=True)
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls:
                    st.image(urls[0], caption=item["type"], width='stretch') # 适配 2026 新语法
                else:
                    st.markdown(f'<div class="err-card">{item["url"]}</div>', unsafe_allow_html=True)
        
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w") as z: z.writestr("log.txt", f"Export at {datetime.now()}")
        st.download_button("📥 全部图片打包 (ZIP)", data=zip_io.getvalue(), file_name="export.zip")

    if st.session_state.log_res:
        with st.expander("👁️ 运行日志"):
            for log in st.session_state.log_res: st.caption(log)
