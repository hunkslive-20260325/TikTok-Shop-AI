import streamlit as st
import requests
import re
import time
import zipfile
import io
from datetime import datetime

# --- 1. 审美灵魂锁死 (变量名全局严格对齐，禁止修改) ---
AESTHETIC_CORE = "Warm Morandi cream background, matte texture, geometric blocks, 45-degree soft lighting, cinematic shadows."
FEMALE_AESTHETIC = "Female model, high-glow glass skin, water-like texture, white silk outfit, soft window light."
MALE_AESTHETIC = "Male model, tanned skin, sharp jawline, stubbles, black crew neck, side lighting."

# --- 2. 内存强制初始化 (根治所有 KeyError) ---
if "seo_res" not in st.session_state: st.session_state.seo_res = None
if "img_res" not in st.session_state: st.session_state.img_res = []
if "log_res" not in st.session_state: st.session_state.log_res = []

# --- 3. UI 视觉设置 ---
st.set_page_config(page_title="TikTok饰品AI专家 V10", layout="wide", page_icon="💎")
st.markdown("""
    <style>
    .stButton>button { width:100%; border-radius:12px; height:3.5em; background:#1a1a1a; color:white; font-weight:bold; }
    .status-tag { background:#e8f5e9; color:#2e7d32; padding:2px 10px; border-radius:15px; font-size:0.8em; font-weight:bold; }
    .err-box { padding:10px; background:#fff1f0; border:1px solid #ffa39e; border-radius:8px; color:#cf1322; font-family:monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 智能请求引擎 (自动接力逻辑) ---
def smart_call(prompt, model_list):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.time()
    for mid in model_list:
        try:
            # 自动纠错 ID 格式
            full_id = f"openai/{mid}" if mid == "dall-e-3" else mid
            res = requests.post(url, headers=headers, json={"model": full_id, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"], full_id, round(time.time()-start, 1)
        except:
            continue
    return "❌ 所有模型尝试均失败，请检查网络或API额度", "None", 0

# --- 5. 侧边栏：配置面板 ---
with st.sidebar:
    st.header("📥 经营信息")
    u_title = st.text_input("原始标题", placeholder="例：S925银心形项链")
    u_cat = st.selectbox("商品类型", ["项链", "手链", "耳环", "戒指", "脚链"])
    u_market = st.selectbox("目标市场", ["东南亚总区", "美国", "英国", "泰国"])
    u_gender = st.radio("目标性别趋势", ["女性", "男性"], horizontal=True)
    st.divider()
    st.header("🤖 模型配置")
    t_mod = st.text_input("文案模型 ID", "deepseek/deepseek-chat")
    i_mod_1 = st.text_input("首选绘图 ID", "openai/dall-e-3")
    i_mod_2 = st.text_input("备选绘图 ID", "black-forest-labs/flux-schnell")
    st.caption("注：若 DALL-E 3 报错，系统将自动使用备选模型。")

# --- 6. 主界面：三步走专家系统 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.info(f"💡 当前审美标准：莫兰迪色调 | 45度柔光 | {u_gender}专享方案")

col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.subheader("🚀 指令执行台")
    
    # 任务 1：SEO
    if st.button("✨ 1. 执行：标题 SEO 优化"):
        with st.status("SEO 方案生成中...") as s:
            p = f"你作为TikTok饰品专家，为{u_market}市场的{u_gender}优化{u_cat}标题。原始：{u_title}。返回3个含公式、理由和翻译的建议。表格输出。"
            res, mod, dur = smart_call(p, [t_mod, "google/gemini-flash-1.5"])
            st.session_state.seo_res = res
            st.session_state.log_res.append(f"SEO完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 方案已就绪", state="complete")

    # 任务 2：商品图 (修正 AESTHETIC_CORE)
    if st.button("🖼️ 2. 执行：商品图优化"):
        with st.status("执行莫兰迪摄影视觉方案...") as s:
            p = f"Professional jewelry photography of {u_cat}. {AESTHETIC_CORE} 8k, photorealistic, cinematic shadows. Direct Image URL."
            res, mod, dur = smart_call(p, [i_mod_1, i_mod_2])
            st.session_state.img_res.append({"type": "AI 优化主图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"图生成完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 商品图生成完成", state="complete")

    # 任务 3：模特图 (变量名完全对齐修正)
    if st.button("👤 3. 执行：模特图优化"):
        with st.status(f"匹配{u_gender}模特视觉模组...") as s:
            # 这里的变量名已经和顶部完全对齐
            m_p = FEMALE_AESTHETIC if u_gender == "女性" else MALE_AESTHETIC
            p = f"Macro fashion photography of a {u_gender} model wearing {u_cat}. {m_p} 8k, magazine style. Direct Image URL."
            res, mod, dur = smart_call(p, [i_mod_1, i_mod_2])
            st.session_state.img_res.append({"type": f"{u_gender}模特图", "url": res, "mod": mod})
            st.session_state.log_res.append(f"模特图完成 | 模型: {mod} | 耗时: {dur}s")
            s.update(label="✅ 模特图优化完成", state="complete")

with col_r:
    st.subheader("📊 实时成果预览")
    
    if st.session_state.seo_res:
        with st.expander("📝 查看爆款标题方案", expanded=True):
            st.markdown(st.session_state.seo_res)

    if st.session_state.img_res:
        grid = st.columns(2)
        for idx, item in enumerate(st.session_state.img_res):
            with grid[idx % 2]:
                st.markdown(f'<span class="status-tag">📡 {item["mod"]}</span>', unsafe_allow_html=True)
                # 增强 URL 提取逻辑
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls:
                    st.image(urls[0], caption=item["type"], use_container_width=True)
                else:
                    st.markdown(f'<div class="err-box">{item["url"]}</div>', unsafe_allow_html=True)
        
        # 打包逻辑
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w") as z:
            z.writestr("log.txt", f"Generation Data: {datetime.now()}")
        st.download_button("📥 打包下载结果 (ZIP)", data=zip_io.getvalue(), file_name=f"export_{datetime.now().strftime('%m%d%H%M')}.zip")

    if st.session_state.log_res:
        with st.expander("👁️ 运行日志与耗时追踪"):
            for log in st.session_state.log_res: st.caption(log)

st.markdown("---")
st.caption("TikTok Shop AI Expert v10.0 | 核心参数持久化锁定 | 多模型容错接力系统已启用")
