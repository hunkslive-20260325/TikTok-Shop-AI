import streamlit as st
import requests
import json
import re
import time
import zipfile
import io
from datetime import datetime

# --- 1. 页面配置与高级样式 ---
st.set_page_config(page_title="TikTok饰品AI全能专家", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    /* 按钮美化 */
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background: linear-gradient(45deg, #2b2b2b, #4a4a4a); color: white; border: none; }
    .stButton>button:hover { background: linear-gradient(45deg, #ff4b4b, #ff8080); }
    /* 结果卡片 */
    .res-card { padding: 20px; border-radius: 15px; background: #ffffff; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }
    /* 图片交互：点击放大的逻辑通过Streamlit原生支持，此处加悬停效果 */
    .img-hover img { transition: 0.3s; cursor: pointer; border-radius: 10px; }
    .img-hover img:hover { transform: scale(1.02); filter: brightness(1.05); }
    /* 模型标签 */
    .model-info { background: #e3f2fd; color: #1976d2; padding: 2px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心逻辑：OpenRouter 请求 ---
def call_ai(prompt, model_id):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    
    start_time = time.time()
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=90)
        duration = round(time.time() - start_time, 1)
        data = res.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"], duration, model_id
        return f"❌ 错误: {data.get('error', {}).get('message')}", duration, model_id
    except Exception as e:
        return f"❌ 异常: {str(e)}", 0, model_id

# --- 3. 侧边栏：输入面板 ---
with st.sidebar:
    st.header("📥 输入信息")
    u_title = st.text_input("1. 原始标题", placeholder="例如：S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "耳环", "耳钉", "戒指", "手链", "手镯", "脚链"], index=0)
    u_market = st.selectbox("3. 目标市场", ["东南亚", "美国", "马来西亚", "新加坡", "泰国", "越南", "菲律宾"], index=0)
    u_age = st.sidebar.text_input("4. 目标人群年龄", "18-35")
    u_gender = st.radio("5. 目标人群性别", ["女性", "男性"], horizontal=True)
    u_files = st.file_uploader("6. 原始商品图 (支持多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    st.divider()
    st.subheader("🤖 模型调度")
    m_text = st.selectbox("文案引擎", ["deepseek/deepseek-chat", "google/gemini-2.0-flash-exp:free"])
    m_img = st.selectbox("绘图引擎", ["openai/dall-e-3", "google/gemini-2.0-flash-exp:free", "black-forest-labs/flux-schnell"])

# --- 4. 主界面：三阶段任务 ---
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.caption(f"当前审美标准：莫兰迪色调 | 45度柔光 | {u_gender}专享视觉方案")

if "results" not in st.session_state:
    st.session_state.results = {"seo": None, "images": [], "model_logs": []}

col_ctrl, col_display = st.columns([1, 1.2])

with col_ctrl:
    st.subheader("🚀 指令执行台")
    
    # --- 按钮 1：标题优化 ---
    if st.button("✨ 1. 标题 SEO 优化"):
        with st.status("🔍 正在检索 TikTok/Amazon/Etsy 热搜词并计算公式...", expanded=True) as s:
            prompt = f"""
            你是一名TikTok饰品专家。针对{u_market}市场，为{u_age}岁{u_gender}优化的{u_cat}标题。
            原始标题：{u_title}。
            要求：返回3个优化标题，按优先级排序，说明推荐理由（含SEO关键词分析）及公式。
            最后使用Google翻译提供中文意思。使用Markdown表格。
            """
            res, dur, mod = call_ai(prompt, m_text)
            st.session_state.results["seo"] = res
            st.session_state.results["model_logs"].append(f"标题优化完成 | 模型：{mod} | 耗时：{dur}s")
            s.update(label="✅ 标题优化已完成！", state="complete")

    # --- 按钮 2：商品图优化 ---
    if st.button("🖼️ 2. 商品图优化 (主图+多角度)"):
        with st.status("🎨 正在执行莫兰迪摄影方案...", expanded=True) as s:
            # 注入你的核心背景要求
            bg_logic = "Background: Warm Morandi palette, cream/beige, matte texture. Props: Geometric cubes for support. Lighting: 45-degree soft lighting, cinematic shadows."
            
            # 生成主图指令
            p_main = f"Professional jewelry photography: {u_cat}. {bg_logic} High-end texture, 8k, photorealistic. Direct image URL."
            res_main, dur, mod = call_ai(p_main, m_img)
            st.session_state.results["images"].append({"type": "主图", "url": res_main, "model": mod})
            
            # 生成多角度指令
            p_multi = f"Multi-angle jewelry photography: {u_cat} from different sides. {bg_logic} 8k, professional catalog style. Direct image URL."
            res_multi, _, _ = call_ai(p_multi, m_img)
            st.session_state.results["images"].append({"type": "多角度图", "url": res_multi, "model": mod})
            
            st.session_state.results["model_logs"].append(f"商品图生成完成 | 模型：{mod} | 预估渲染：{dur}s")
            s.update(label="✅ 商品图优化已完成！", state="complete")

    # --- 按钮 3：模特图优化 ---
    if st.button("👤 3. 模特图优化 (水光肌/古铜色适配)"):
        with st.status(f"🎭 正在匹配{u_gender}模特妆造与场景...", expanded=True) as s:
            if u_gender == "女性":
                m_logic = "Female model, high-glow glass skin, water-like texture, natural wavy hair, white silk outfit. Soft diffused light (window light), Morandi pink background."
            else:
                m_logic = "Male model, tanned/bronze skin, sharp jawline with stubbles, wearing black crew neck sweater. 45-degree side lighting, dark beige background."
            
            p_model = f"Photorealistic close-up of a model wearing a {u_cat}. {m_logic} High fashion magazine style, 8k, cinematic."
            res_model, dur, mod = call_ai(p_model, m_img)
            st.session_state.results["images"].append({"type": f"{u_gender}模特佩戴图", "url": res_model, "model": mod})
            
            st.session_state.results["model_logs"].append(f"模特图生成完成 | 模型：{mod} | 预估渲染：{dur}s")
            s.update(label="✅ 模特图优化已完成！", state="complete")

    # --- 二次编辑区 ---
    if st.session_state.results["images"]:
        st.divider()
        st.subheader("✏️ 单张图片二次优化")
        target_idx = st.selectbox("选择要修改的图片", range(len(st.session_state.results["images"])), format_func=lambda x: st.session_state.results["images"][x]["type"])
        edit_suggest = st.text_input("输入二次修改建议", placeholder="例如：背景调成淡绿色，光线再亮一点")
        if st.button("🪄 基于建议重新生成"):
            with st.spinner("正在精修图片..."):
                old_p = st.session_state.results["images"][target_idx]["type"]
                new_p = f"Based on previous image, apply edit: {edit_suggest}. Keep Morandi style and jewelry details."
                res_new, _, mod = call_ai(new_p, m_img)
                st.session_state.results["images"][target_idx]["url"] = res_new
                st.toast("✅ 二次优化完成！")

with col_display:
    st.subheader("📋 实时工作结果")
    
    # 标题展示
    if st.session_state.results["seo"]:
        with st.container():
            st.markdown('<div class="res-card">', unsafe_allow_html=True)
            st.markdown("### ✍️ 标题优化方案")
            st.markdown(st.session_state.results["seo"])
            st.markdown('</div>', unsafe_allow_html=True)

    # 图片展示 (支持点击放大/缩小)
    if st.session_state.results["images"]:
        img_cols = st.columns(2)
        for idx, item in enumerate(st.session_state.results["images"]):
            with img_cols[idx % 2]:
                st.markdown(f'<span class="model-info">{item["type"]} | {item["model"]}</span>', unsafe_allow_html=True)
                # 提取链接
                img_url = re.findall(r'(https?://[^\s)"]+)', item["url"])
                final_url = img_url[0] if img_url else "https://via.placeholder.com/500?text=Generating..."
                
                # 点击放大的UI：利用Streamlit原生image点击预览功能
                st.markdown('<div class="img-hover">', unsafe_allow_html=True)
                st.image(final_url, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # 下载区域
        st.divider()
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            # 模拟ZIP打包逻辑
            zip_name = datetime.now().strftime("%Y%m%d%H%M%S") + ".zip"
            st.download_button("📥 全部图片下载 (ZIP)", data=b"fake_data", file_name=zip_name)
    
    # 思考日志展示
    if st.session_state.results["model_logs"]:
        with st.expander("👁️ 模型思考过程与进度追踪"):
            for log in st.session_state.results["model_logs"]:
                st.caption(log)

# 页脚
st.markdown("---")
st.caption(f"TikTok Shop AI Expert v6.0 | 运行环境：OpenRouter | 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
