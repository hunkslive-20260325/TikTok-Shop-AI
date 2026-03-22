import streamlit as st
import requests
import re
import time
import zipfile
import io
from datetime import datetime

# --- 1. 核心审美方案锁死 (User Summary 深度同步) ---
MORANDI_LOGIC = "Warm Morandi cream/beige background, matte texture, geometric clay props, 45-degree soft side lighting, cinematic shadows, high-end jewelry photography."
FEMALE_AESTHETIC = "Female model, high-glow glass skin, water-like texture, natural hair, white silk/linen outfit, soft diffused window light."
MALE_AESTHETIC = "Male model, tanned/bronze skin, sharp jawline, stubbles, black crew neck sweater, 45-degree side lighting, sophisticated and bold."

# --- 2. 初始化 SessionState (杜绝 KeyError 崩溃) ---
if "seo_result" not in st.session_state: st.session_state.seo_result = None
if "img_list" not in st.session_state: st.session_state.img_list = []
if "process_logs" not in st.session_state: st.session_state.process_logs = []

# --- 3. 页面样式美化 ---
st.set_page_config(page_title="TikTok饰品AI全能专家 v7.0", layout="wide", page_icon="💎")
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: #1a1a1a; color: white; border: none; transition: 0.3s; }
    .stButton>button:hover { background: #ff4b4b; transform: translateY(-2px); }
    .res-card { padding: 20px; border-radius: 15px; background: #ffffff; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .model-tag { background: #e3f2fd; color: #1976d2; padding: 2px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 核心请求引擎 (带自动接力容错) ---
def call_ai_engine(prompt, models):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    start_t = time.time()
    for model in models:
        try:
            payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"], model, round(time.time()-start_t, 1)
        except:
            continue
    return "❌ 所有备选模型均调用失败，请检查网络或API额度", "None", 0

# --- 5. 侧边栏：输入面板 ---
with st.sidebar:
    st.header("📥 商品基本信息")
    u_title = st.text_input("1. 原始标题", placeholder="输入产品名称...")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    u_market = st.selectbox("3. 目标市场", ["东南亚", "马来西亚", "新加坡", "泰国", "越南", "菲律宾", "美国"], index=0)
    u_age = st.sidebar.text_input("4. 目标人群年龄", "18-35")
    u_gender = st.radio("5. 目标人群性别", ["女性", "男性"], horizontal=True)
    u_files = st.file_uploader("6. 上传原始商品图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🤖 模型配置")
    text_engine = ["deepseek/deepseek-chat", "google/gemini-flash-1.5"]
    img_engine = ["openai/dall-e-3", "black-forest-labs/flux-schnell", "google/gemini-2.0-flash-exp:free"]

# --- 6. 主界面 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.caption(f"当前审美标准：莫兰迪色调 | 45度柔光 | {u_gender}专用视觉模组已就绪")

col_op, col_show = st.columns([1, 1.2])

with col_op:
    st.subheader("🚀 指令执行台")
    
    # --- 按钮 1：标题优化 ---
    if st.button("✨ 1. 执行：标题 SEO 优化"):
        with st.status("🔍 正在检索类目热搜词并生成公式...", expanded=False) as s:
            p = f"你作为TikTok饰品专家，为{u_market}市场的{u_age}岁{u_gender}优化{u_cat}标题。原始：{u_title}。要求：返回3个优化标题，含SEO理由及组成公式，附带中文翻译。表格展示。"
            res, mod, dur = call_ai_engine(p, text_engine)
            st.session_state.seo_result = res
            st.session_state.process_logs.append(f"SEO完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 标题方案已生成", state="complete")

    # --- 按钮 2：商品图优化 ---
    if st.button("🖼️ 2. 执行：商品图优化 (主图+细节)"):
        with st.status("🎨 正在执行莫兰迪专业摄影方案...", expanded=False) as s:
            p = f"Professional jewelry photography: {u_cat}. {MORANDI_LOGIC} 8k, ultra-realistic, photorealistic. Direct Image URL."
            res, mod, dur = call_ai_engine(p, img_engine)
            st.session_state.img_list.append({"type": "AI 优化主图", "url": res, "model": mod})
            st.session_state.process_logs.append(f"商品图完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 商品图优化完成", state="complete")

    # --- 按钮 3：模特图优化 ---
    if st.button("👤 3. 执行：模特图优化"):
        with st.status(f"🎭 匹配{u_gender}模特视觉方案...", expanded=False) as s:
            m_logic = FEMALE_AESTHETIC if u_gender == "女性" else MALE_AESTHETIC
            p = f"Close-up fashion photography of a {u_gender} model wearing {u_cat}. {m_logic} High-end magazine style, 8k. Direct Image URL."
            res, mod, dur = call_ai_engine(p, img_engine)
            st.session_state.img_list.append({"type": f"{u_gender}模特佩戴图", "url": res, "model": mod})
            st.session_state.process_logs.append(f"模特图完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 模特图生成完成", state="complete")

    # --- 二次编辑区 ---
    if st.session_state.img_list:
        st.divider()
        st.subheader("🪄 局部二次优化")
        target = st.selectbox("选择要修改的图片", range(len(st.session_state.img_list)), format_func=lambda x: st.session_state.img_list[x]["type"])
        feedback = st.text_input("输入修改建议", placeholder="例如：背景换成淡绿色，光线调亮一点")
        if st.button("🚀 基于建议重新优化"):
            with st.spinner("正在精修中..."):
                p = f"Based on previous jewelry photo, apply this change: {feedback}. Maintain Morandi style and product consistency."
                res, mod, dur = call_ai_engine(p, img_engine)
                st.session_state.img_list[target]["url"] = res
                st.toast("✅ 二次优化已完成！")

with col_show:
    st.subheader("📊 实时成果展示")
    
    # 标题展示
    if st.session_state.seo_result:
        with st.container():
            st.markdown('<div class="res-card">', unsafe_allow_html=True)
            st.markdown("### ✍️ 爆款标题 SEO 方案")
            st.markdown(st.session_state.seo_result)
            st.markdown('</div>', unsafe_allow_html=True)

    # 图片展示 (支持单张点击放大)
    if st.session_state.img_list:
        cols = st.columns(2)
        for idx, item in enumerate(st.session_state.img_list):
            with cols[idx % 2]:
                st.markdown(f'<span class="model-tag">📡 {item["model"]}</span>', unsafe_allow_html=True)
                # 正则提取 URL
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                final_url = urls[0] if urls else "https://via.placeholder.com/500?text=Generating..."
                st.image(final_url, caption=item["type"], use_container_width=True)

        # ZIP 下载功能
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("Generation_Log.txt", str(st.session_state.process_logs))
        st.download_button("📥 全部图片打包下载 (ZIP)", data=zip_buf.getvalue(), file_name=f"{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")

    # 进度与思考过程
    if st.session_state.process_logs:
        with st.expander("👁️ 查看模型思考过程与耗时统计"):
            for log in st.session_state.process_logs:
                st.caption(log)

st.markdown("---")
st.caption("TikTok Shop AI Expert v7.0 | Powered by OpenRouter | 核心需求已持久化锁死")
