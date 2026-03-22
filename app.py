import streamlit as st
import requests
import re
import time
from PIL import Image

# --- 1. 物理层缓存清理 (针对 NameError: AEST_CORE 的必杀技) ---
# 这个逻辑会在程序启动时检查并强制删除所有旧变量
if "clear_cache_v21" not in st.session_state:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.clear_cache_v21 = True

# 初始化干净的状态
if "seo_data" not in st.session_state: st.session_state.seo_data = None
if "img_list" not in st.session_state: st.session_state.img_list = []

# --- 2. 核心 AI 引擎 (完全硬编码，不引用任何外部变量) ---
def run_jewelry_ai_v21(task_type, cat, market, gender, title=""):
    # 从 Secrets 获取 Key
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io" 
    }
    
    # 逻辑锁死：Prompt 直接定义在函数内
    if task_type == "SEO":
        prompt = f"TikTok饰品专家任务：为{market}的{gender}优化{cat}标题。原始：{title}。请用Markdown表格输出3个建议。"
        models = ["deepseek/deepseek-chat"]
    elif task_type == "MAIN":
        prompt = f"Jewelry photography of {cat}. Warm Morandi cream background, matte texture, 45-degree soft lighting, 8k, photorealistic. Direct URL only."
        models = ["openai/dall-e-3"] # 这里先用最稳的 DALL-E 3
    else:
        prompt = f"Macro photo of {gender} model wearing {cat}. High-end fashion style, 45-degree lighting, 8k. Direct URL only."
        models = ["openai/dall-e-3"]

    for mid in models:
        try:
            payload = {"model": mid, "messages": [{"role": "user", "content": prompt}]}
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"], mid
        except Exception as e:
            continue
    return "❌ 呼叫模型失败，请检查 API Key 余额或权限", "None"

# --- 3. 界面布局 ---
st.set_page_config(page_title="TikTok饰品AI V21", layout="wide")
st.title("💎 TikTok Shop 饰品全能 AI 专家")
st.warning("V21.0：环境已强制初始化。若仍报旧错，请执行 Reboot App。")

with st.sidebar:
    st.header("📥 经营信息")
    u_title = st.text_input("1. 原始标题", "心形饰品")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("3. 目标市场", ["东南亚", "美国", "英国"])
    u_gen = st.radio("4. 目标性别", ["女性", "男性"], horizontal=True)
    st.divider()
    f = st.file_uploader("🖼️ 上传原图", type=["jpg", "png", "jpeg"])
    if f: st.image(Image.open(f), width='stretch')

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 指令执行")
    if st.button("✨ 1. 标题 SEO 优化"):
        with st.status("生成中..."):
            st.session_state.seo_data, _ = run_jewelry_ai_v21("SEO", u_cat, u_mkt, u_gen, u_title)
            
    if st.button("🖼️ 2. 生成莫兰迪主图"):
        with st.status("出图中..."):
            res, mod = run_jewelry_ai_v21("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"type": "主图", "url": res, "mod": mod})

    if st.button("👤 3. 生成模特实拍图"):
        with st.status("生成中..."):
            res, mod = run_jewelry_ai_v21("MODEL", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"type": "模特图", "url": res, "mod": mod})

with c2:
    st.subheader("📋 成果展示")
    if st.session_state.seo_data:
        st.markdown(st.session_state.seo_data)
    
    if st.session_state.img_list:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_list):
            with grid[i % 2]:
                st.caption(f"📡 {item['mod']}")
                # 提取返回内容中的 URL
                urls = re.findall(r'(https?://[^\s)"]+)', str(item["url"]))
                if urls:
                    st.image(urls[0], caption=item["type"], width='stretch')
                else:
                    st.error(f"模型未返回有效图片: {item['url']}")
