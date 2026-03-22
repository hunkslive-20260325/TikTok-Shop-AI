import streamlit as st
import requests
import re
import time
import zipfile
import io
from datetime import datetime

# --- 1. 核心业务逻辑锁死 (确保变量名全局统一，根治 NameError) ---
AESTHETIC_CORE = "Warm Morandi cream/beige background, matte texture, geometric blocks, 45-degree soft lighting, cinematic shadows."
FEMALE_PROMPT = "Female model, high-glow glass skin, water-like texture, white silk outfit, soft window light."
MALE_PROMPT = "Male model, tanned skin, sharp jawline, stubbles, black crew neck, side lighting."

# --- 2. 彻底初始化 (必须在最前面，防止 KeyError) ---
if "seo_data" not in st.session_state: st.session_state.seo_data = None
if "img_data" not in st.session_state: st.session_state.img_data = []
if "run_logs" not in st.session_state: st.session_state.run_logs = []

# --- 3. 样式配置 ---
st.set_page_config(page_title="TikTok饰品AI专家 V9.0", layout="wide", page_icon="💎")
st.markdown("""
    <style>
    .stButton>button { width:100%; border-radius:12px; height:3.5em; background:#1a1a1a; color:white; font-weight:bold; }
    .status-tag { background:#e8f5e9; color:#2e7d32; padding:2px 10px; border-radius:15px; font-size:0.8em; font-weight:bold; }
    .err-card { padding:10px; background:#fff1f0; border:1px solid #ffa39e; border-radius:8px; color:#cf1322; font-size:0.9em; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 带自动兜底的请求引擎 (解决 Model ID 无效问题) ---
def smart_call(prompt, model_list):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    start_time = time.time()
    for model_id in model_list:
        try:
            if not model_id or len(model_id) < 3: continue
            res = requests.post(url, headers=headers, json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}]
            }, timeout=60)
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"], model_id, round(time.time()-start_time, 1)
        except:
            continue
    return "❌ 呼叫所有模型均失败，请检查 API Key 余额或网络", "Error", 0

# --- 5. 侧边栏 ---
with st.sidebar:
    st.header("📥 经营信息输入")
    u_title = st.text_input("1. 原始标题", placeholder="例：S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"])
    u_market = st.selectbox("3. 目标市场", ["东南亚总区", "马来西亚", "泰国", "越南", "新加坡", "美国"])
    u_gender = st.radio("4. 目标性别", ["女性", "男性"], horizontal=True)
    st.file_uploader("5. 上传原图 (支持多张)", accept_multiple_files=True)

    st.divider()
    st.header("🤖 模型选型 (自动接力系统)")
    t_mod = st.text_input("文案模型 ID", "deepseek/deepseek-chat")
    i_mod_primary = st.text_input("首选绘图 ID", "openai/dall-e-3")
    i_mod_backup = "google/gemini-2.0-flash-exp:free" # 自动兜底模型

# --- 6. 主界面 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.info(f"💡 核心审美已锁死：莫兰迪色调 | 45度柔光 | {u_gender}专用模组")

c_left, c_right = st.columns([1, 1.2])

with c_left:
    st.subheader("🚀 指令执行台")
    
    # SEO 优化
    if st.button("✨ 执行：标题 SEO 优化"):
        with st.status("正在检索 TikTok 热搜关键词...") as s:
            prompt = f"你作为TikTok饰品专家，为{u_market}市场的{u_gender}优化{u_cat}标题。原始：{u_title}。返回3个含公式、理由和翻译的建议。表格输出。"
            res, mod, dur = smart_call(prompt, [t_mod, "google/gemini-flash-1.5"])
            st.session_state.seo_data = res
            st.session_state.run_logs.append(f"SEO完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 标题优化完成", state="complete")

    # 商品图生成 (修正了 AESTHETIC_CORE 调用)
    if st.button("🖼️ 执行：商品图优化 (主图+细节)"):
        with st.status("正在执行莫兰迪视觉方案...") as s:
            prompt = f"Professional jewelry photography: {u_cat}. {AESTHETIC_CORE} 8k, photorealistic. Direct Image URL."
            res, mod, dur = smart_call(prompt, [i_mod_primary, i_mod_backup, "black-forest-labs/flux-schnell"])
            st.session_state.img_data.append({"type": "AI 优化主图", "url": res, "mod": mod})
            st.session_state.run_logs.append(f"图生成完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 商品图生成完成", state="complete")

    # 模特图生成
    if st.button("👤 执行：模特图优化"):
        with st.status(f"匹配{u_gender}模特方案...") as s:
            m_p = FEMALE_PROMPT if u_gender == "女性" else MALE_PROMPT
            prompt = f"Macro photo of {u_gender} model wearing {u_cat}. {m_p} 8k, fashion style. Direct Image URL."
            res, mod, dur = smart_call(prompt, [i_mod_primary, i_mod_backup])
            st.session_state.img_data.append({"type": f"{u_gender}模特图", "url": res, "mod": mod})
            st.session_state.run_logs.append(f"模特图完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 模特图生成完成", state="complete")

with c_right:
    st.subheader("📋 实时生成结果")
    
    if st.session_state.seo_data:
        with st.expander("📝 爆款标题建议方案", expanded=True):
            st.markdown(st.session_state.seo_data)

    if st.session_state.img_data:
        img_grid = st.columns(2)
        for idx, item in enumerate(st.session_state.img_data):
            with img_grid[idx % 2]:
                st.markdown(f'<span class="status-tag">📡 {item["mod"]}</span>', unsafe_allow_html=True)
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls:
                    st.image(urls[0], caption=item["type"], use_container_width=True)
                else:
                    st.markdown(f'<div class="err-card">{item["url"]}</div>', unsafe_allow_html=True)

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("info.txt", f"Generation Log: {datetime.now()}")
        st.download_button("📥 全部图片打包 (ZIP)", data=zip_buf.getvalue(), file_name=f"export_{datetime.now().strftime('%m%d%H%M')}.zip")

    if st.session_state.run_logs:
        with st.expander("👁️ 运行日志与耗时追踪"):
            for log in st.session_state.run_logs: st.caption(log)
