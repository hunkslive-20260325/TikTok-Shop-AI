import streamlit as st
import requests
import re
from PIL import Image

# --- 1. 物理层内存清理 (针对残留报错的必杀技) ---
if "v24_ready" not in st.session_state:
    for k in list(st.session_state.keys()): 
        del st.session_state[k]
    st.session_state.v24_ready = True
    st.session_state.seo_data = None
    st.session_state.img_list = []

# --- 2. 2026 官方标准 API 调用函数 ---
def call_openrouter_v24(task_type, cat, mkt, gen, title=""):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    
    # 核心适配：文案用 Gemini，绘图用 2026 通用路由
    if task_type == "SEO":
        model_id = "google/gemini-2.0-flash-001" 
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": f"Optimize TikTok Shop title for {gen} {cat} in {mkt}. Original: {title}. Output in Markdown table."}]
        }
    else:
        # 图片生成关键：必须使用官方支持的图片模型 ID
        # 如果 openai/dall-e-3 提示无效，请尝试换成 "black-forest-labs/flux-schnell"
        model_id = "openai/dall-e-3" 
        prompt = f"Jewelry photography, {cat}, Morandi background, 8k" if task_type == "MAIN" else f"Model wearing {cat}, 8k"
        
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image"] # 👈 2026 文档要求的核心参数，漏了必报错
        }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        data = res.json()
        
        if "choices" in data:
            msg = data["choices"][0]["message"]
            # 逻辑：优先提取 2026 标准返回的 images 数组
            if "images" in msg and msg["images"]:
                return msg["images"][0], model_id
            # 逻辑：备选提取 content (文本或 URL)
            return msg.get("content", ""), model_id
        else:
            err_msg = data.get("error", {}).get("message", "Unknown Error")
            return f"❌ 接口报错: {err_msg}", "None"
    except Exception as e:
        return f"❌ 请求异常: {str(e)}", "None"

# --- 3. 极简 UI 布局 ---
st.set_page_config(page_title="TikTok饰品AI V24", layout="wide")
st.title("💎 TikTok Shop 饰品 AI (V24.0 官方规范版)")
st.caption("提示：若图片模型 ID 无效，请进入代码修改 model_id 为 black-forest-labs/flux-schnell")

with st.sidebar:
    st.header("📥 输入信息")
    u_title = st.text_input("原始标题", "心形项链")
    u_cat = st.selectbox("类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("市场", ["东南亚", "美国", "英国"])
    u_gen = st.radio("性别趋势", ["女性", "男性"], horizontal=True)
    st.divider()
    f = st.file_uploader("参考原图", type=["jpg", "png"])
    if f: st.image(Image.open(f), use_container_width=True)

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 指令执行")
    if st.button("✨ 1. 优化标题"):
        with st.status("文案模型工作中..."):
            st.session_state.seo_data, _ = call_openrouter_v24("SEO", u_cat, u_mkt, u_gen, u_title)
            
    if st.button("🖼️ 2. 生成商品图/模特图"):
        with st.status("绘图模型工作中..."):
            res, mod = call_openrouter_v24("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"u": res, "m": mod})

with c2:
    st.subheader("📊 成果展示")
    if st.session_state.seo_data:
        st.markdown(st.session_state.seo_data)
    
    if st.session_state.img_list:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_list):
            with grid[i % 2]:
                st.caption(f"📡 驱动: {item['m']}")
                raw_data = str(item["u"])
                if raw_data.startswith("http") or len(raw_data) > 100:
                    st.image(raw_data, use_container_width=True)
                else:
                    st.error(f"无法解析图片内容: {raw_data}")
