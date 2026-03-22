import streamlit as st
import requests
import re
import time
import zipfile
import io
from datetime import datetime
from PIL import Image

# --- 1. 审美灵魂：强制硬编码 (确保没有任何 NameError) ---
AESTHETIC_STR = "Warm Morandi cream background, matte texture, geometric blocks, 45-degree soft lighting, cinematic shadows."
FEMALE_STR = "Female model, high-glow glass skin, water-like texture, white silk outfit, soft window light."
MALE_STR = "Male model, tanned bronze skin, sharp jawline, stubbles, black crew neck, 45-degree side lighting."

# --- 2. 内存初始化 ---
for key in ["seo_res", "img_res", "log_res"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "seo_res" else []

# --- 3. 页面配置 (适配 2026 最新语法) ---
st.set_page_config(page_title="TikTok饰品AI专家 V14", layout="wide")
st.markdown("<style>.stButton>button { width:100%; border-radius:12px; height:3.5em; background:#1a1a1a; color:white; font-weight:bold; }</style>", unsafe_allow_html=True)

# --- 4. 请求引擎 ---
def call_api(prompt, model_list):
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
    return "❌ 接口响应异常，请检查 API Key", "None", 0

# --- 5. 侧边栏 ---
with st.sidebar:
    st.header("📥 经营信息")
    u_title = st.text_input("原始标题", "心形手链饰品")
    u_cat = st.selectbox("商品类型", ["项链", "手链", "耳环", "戒指"])
    u_market = st.selectbox("目标市场", ["东南亚总区", "美国", "英国"])
    u_gender = st.radio("目标性别", ["女性", "男性"], horizontal=True)
    st.divider()
    st.subheader("🖼️ 上传原图")
    files = st.file_uploader("上传照片", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if files:
        cols = st.columns(3)
        for i, f in enumerate(files[:3]):
            with cols[i]: st.image(Image.open(f), width='stretch')
    st.divider()
    t_mod = st.text_input("文案 ID", "deepseek/deepseek-chat")
    i_mod_1 = st.text_input("绘图 ID 1", "openai/dall-e-3")
    i_mod_2 = st.text_input("绘图 ID 2", "black-forest-labs/flux-schnell")

# --- 6. 主界面 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.subheader("🚀 专家指令")
    if st.button("✨ 1. 标题 SEO 优化"):
        with st.status("优化中..."):
            p = f"TikTok饰品专家任务：为{u_market}的{u_gender}优化{u_cat}标题。原始：{u_title}。表格输出。"
            res, mod, dur = call_api(p, [t_mod, "google/gemini-flash-1.5"])
            st.session_state.seo_res = res
            st.session_state.log_res.append(f"SEO完成 | {mod} | {dur}s")

    if st.button("🖼️ 2. 商品图优化"):
        with st.status("莫兰迪方案执行中..."):
            # 这里的变量名 AESTHETIC_STR 绝对不可能出错
            p = f"Professional jewelry photography: {u_cat}. {AESTHETIC_STR} 8k, photorealistic. Direct URL."
            res, mod, dur = call_api(p, [i_mod_1, i_mod_2])
            st.session_state.img_res.append({"type": "AI优化主图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"主图完成 | {mod} | {dur}s")

    if st.button("👤 3. 模特图优化"):
        with st.status(f"匹配{u_gender}模特..."):
            m_p = FEMALE_STR if u_gender == "女性" else MALE_STR
            p = f"Macro photo of {u_gender} model wearing {u_cat}. {m_p} 8k, magazine style. Direct URL."
            res, mod, dur = call_api(p, [i_mod_1, i_mod_2])
            st.session_state.img_res.append({"type": f"{u_gender}模特图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"模特完成 | {mod} | {dur}s")

with col_r:
    st.subheader("📋 实时成果")
    if st.session_state.seo_res:
        with st.expander("📝 标题方案", expanded=True): st.markdown(st.session_state.seo_res)
    if st.session_state.img_res:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_res):
            with grid[i % 2]:
                st.caption(f"📡 {item['mod']}")
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls: st.image(urls[0], width='stretch')
                else: st.error("生成失败，请检查余额")
    if st.session_state.log_res:
        with st.expander("👁️ 日志"):
            for log in st.session_state.log_res: st.caption(log)
