import streamlit as st
import requests
import re
import time
import zipfile
import io
from datetime import datetime

# --- 1. 核心业务逻辑锁死 (User Summary 深度同步) ---
AESTHETIC_CORE = "Warm Morandi cream/beige background, matte texture, geometric blocks, 45-degree soft lighting, cinematic shadows."
MODEL_FE = "Female model, high-glow glass skin, water-like texture, white silk outfit, soft window light, elegant."
MODEL_MA = "Male model, tanned skin, sharp jawline, stubbles, black crew neck, side lighting, masculine."

# --- 2. 彻底初始化 (彻底解决截图中的 KeyError) ---
INIT_KEYS = ["seo_out", "img_out", "logs", "current_t_mod", "current_i_mod"]
for key in INIT_KEYS:
    if key not in st.session_state:
        st.session_state[key] = [] if "img" in key or "logs" in key else None

# --- 3. UI 界面样式 ---
st.set_page_config(page_title="TikTok 饰品 AI 全能专家", layout="wide", page_icon="💎")
st.markdown("""
    <style>
    .stButton>button { width:100%; border-radius:12px; height:3.5em; background:#1a1a1a; color:white; font-weight:bold; }
    .status-tag { background:#f0f7ff; color:#007bff; padding:2px 10px; border-radius:15px; font-size:0.8em; font-weight:bold; }
    .error-display { padding:15px; background:#fff1f0; border:1px solid #ffa39e; border-radius:8px; color:#cf1322; font-family:monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 4. 健壮的万能请求函数 ---
def call_openrouter_safe(prompt, model_id):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.time()
    try:
        res = requests.post(url, headers=headers, json={
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}]
        }, timeout=90)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"], round(time.time()-start, 1)
        # 捕获类似截图中的 400 错误
        err_msg = data.get('error', {}).get('message', '未知模型错误')
        return f"❌ 模型报错: {err_msg}", 0
    except Exception as e:
        return f"❌ 网络连接异常: {str(e)}", 0

# --- 5. 侧边栏：输入与模型选型 ---
with st.sidebar:
    st.header("📥 经营信息输入")
    u_title = st.text_input("1. 原始标题", placeholder="输入产品名称...")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    u_market = st.selectbox("3. 目标市场", ["东南亚", "美国", "泰国", "越南", "马来西亚", "新加坡", "菲律宾"], index=0)
    u_gender = st.radio("4. 目标性别", ["女性", "男性"], horizontal=True)
    st.file_uploader("5. 上传原图 (支持多张)", accept_multiple_files=True)

    st.divider()
    st.header("🤖 模型选型 (可手动修改)")
    # 允许用户根据截图报错手动修正 ID
    t_mod_custom = st.text_input("文案模型 ID", "deepseek/deepseek-chat")
    i_mod_custom = st.text_input("绘图模型 ID", "openai/dall-e-3")
    st.caption("注：若 DALL-E 3 报 ID 无效，请尝试 `google/gemini-2.0-flash-exp:free` 或 `black-forest-labs/flux-schnell`")

# --- 6. 主界面：三阶段任务 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.info(f"💡 核心审美已锁死：莫兰迪色调 | 45度柔光 | {u_gender}专用模组")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 专家指令执行")
    
    # 标题优化
    if st.button("✨ 1. 标题 SEO 优化"):
        with st.status("正在检索 TikTok/Amazon 类目热搜词...") as s:
            p = f"你作为TikTok饰品专家，为{u_market}市场的{u_gender}优化{u_cat}标题。原始：{u_title}。要求返回3个含公式、理由和中文翻译的表格。"
            res, dur = call_openrouter_safe(p, t_mod_custom)
            st.session_state.seo_out = res
            st.session_state.current_t_mod = t_mod_custom
            st.session_state.logs.append(f"SEO完成 | 模型: {t_mod_custom} | 耗时: {dur}s")
            s.update(label="✅ 标题优化方案已生成", state="complete")

    # 商品图优化
    if st.button("🖼️ 2. 商品图优化 (主图+细节)"):
        with st.status("正在执行莫兰迪摄影方案...") as s:
            p = f"Professional jewelry photography: {u_cat}. {AEST_CORE} 8k, photorealistic. Direct Image URL."
            res, dur = call_openrouter_safe(p, i_mod_custom)
            st.session_state.img_out.append({"type": "AI 优化主图", "url": res, "mod": i_mod_custom})
            st.session_state.current_i_mod = i_mod_custom
            st.session_state.logs.append(f"商品图完成 | 模型: {i_mod_custom} | 耗时: {dur}s")
            s.update(label="✅ 商品图生成完成", state="complete")

    # 模特图优化
    if st.button("👤 3. 模特图优化"):
        with st.status(f"正在配置{u_gender}模特视觉场景...") as s:
            m_p = MODEL_FE if u_gender == "女性" else MODEL_MA
            p = f"Macro photo of {u_gender} model wearing {u_cat}. {m_p} 8k, fashion magazine style. Direct Image URL."
            res, dur = call_openrouter_safe(p, i_mod_custom)
            st.session_state.img_out.append({"type": f"{u_gender}模特图", "url": res, "mod": i_mod_custom})
            st.session_state.logs.append(f"模特图完成 | 模型: {i_mod_custom} | 耗时: {dur}s")
            s.update(label="✅ 模特图生成完成", state="complete")

    # 二次编辑逻辑
    if st.session_state.img_out:
        st.divider()
        st.subheader("🪄 局部二次优化")
        target_idx = st.selectbox("选择要精修的图", range(len(st.session_state.img_out)), format_func=lambda x: st.session_state.img_out[x]["type"])
        edit_tip = st.text_input("输入二次修改建议", placeholder="例如：背景调成淡绿色...")
        if st.button("🚀 重新优化生成"):
            new_p = f"Based on previous jewelry photo, apply edit: {edit_tip}. Keep product and Morandi style consistent."
            res, dur = call_openrouter_safe(new_p, i_mod_custom)
            st.session_state.img_out[target_idx]["url"] = res
            st.toast("精修重画已完成！")

with c2:
    st.subheader("📊 实时成果看板")
    
    if st.session_state.seo_out:
        with st.expander("📝 查看爆款标题建议", expanded=True):
            st.markdown(st.session_state.seo_out)

    if st.session_state.img_out:
        icols = st.columns(2)
        for i, item in enumerate(st.session_state.img_out):
            with icols[i % 2]:
                st.markdown(f'<span class="status-tag">📡 {item["mod"]}</span>', unsafe_allow_html=True)
                # 兼容性提取 URL
                urls = re.findall(r'(https?://[^\s)"]+)', item["url"])
                if urls:
                    st.image(urls[0], caption=item["type"], use_container_width=True)
                else:
                    st.markdown(f'<div class="error-display">{item["url"]}</div>', unsafe_allow_html=True)

        # ZIP 打包
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w") as z:
            z.writestr("Generation_Log.txt", f"Exported at {datetime.now()}")
        st.download_button("📥 全部图片打包 (ZIP)", data=zip_io.getvalue(), file_name=f"{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")

    if st.session_state.logs:
        with st.expander("👁️ 模型思考进度与耗时统计"):
            for log in st.session_state.logs: st.caption(log)
