import streamlit as st
import requests
import re
import time
from PIL import Image

# --- 1. 物理层彻底重置 ---
if "v23_fix" not in st.session_state:
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.v23_fix = True
    st.session_state.seo_data = None
    st.session_state.img_list = []

# --- 2. 符合 2026 文档规范的 AI 引擎 ---
def call_openrouter_v23(task_type, cat, market, gender, title=""):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 根据任务调整参数
    if task_type == "SEO":
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": f"Optimize TikTok title for {gender} {cat} in {market}. Original: {title}. Output: Markdown Table."}]
        }
    else:
        # 图片生成：必须包含 modalities 参数
        prompt = f"Professional jewelry photography of {cat}. Morandi background, 8k." if task_type == "MAIN" else f"Photo of {gender} model wearing {cat}, 8k."
        payload = {
            "model": "openai/dall-e-3", # 也可以换成 google/imagen-3
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image"] # 👈 这是文档要求的核心改动
        }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        data = res.json()
        
        if "choices" in data:
            message = data["choices"][0]["message"]
            # 逻辑：如果返回的是图片数组，提取第一张
            if "images" in message and message["images"]:
                return message["images"][0], payload["model"] # 可能是 base64 或 URL
            # 逻辑：如果返回的是普通文本（如 SEO）
            return message.get("content", ""), payload["model"]
        else:
            return f"❌ API 报错: {data.get('error', {}).get('message', '未知错误')}", "None"
    except Exception as e:
        return f"❌ 请求异常: {str(e)}", "None"

# --- 3. 极简 UI ---
st.set_page_config(page_title="TikTok饰品AI V23", layout="wide")
st.title("💎 TikTok Shop 饰品 AI (文档修正版)")

with st.sidebar:
    u_title = st.text_input("1. 原始标题", "心形饰品")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("3. 目标市场", ["东南亚", "美国", "英国"])
    u_gen = st.radio("4. 目标性别", ["女性", "男性"], horizontal=True)
    st.divider()
    f = st.file_uploader("🖼️ 上传原图", type=["jpg", "png", "jpeg"])
    if f: st.image(Image.open(f), use_container_width=True)

c1, c2 = st.columns([1, 1.2])
with c1:
    if st.button("✨ 执行 SEO 优化"):
        with st.status("处理中..."):
            st.session_state.seo_data, _ = call_openrouter_v23("SEO", u_cat, u_mkt, u_gen, u_title)
            
    if st.button("🖼️ 生成 AI 图片 (主图/模特)"):
        with st.status("正在生成图片..."):
            res, mod = call_openrouter_v23("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.img_list.append({"u": res, "m": mod})

with c2:
    if st.session_state.seo_data: st.markdown(st.session_state.seo_data)
    if st.session_state.img_list:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_list):
            with grid[i % 2]:
                st.caption(f"📡 {item['m']}")
                # 处理 base64 或 URL
                img_data = item["u"]
                if img_data.startswith("http"):
                    st.image(img_data, use_container_width=True)
                elif "base64" in img_data or len(img_data) > 100:
                    st.image(img_data, use_container_width=True)
                else:
                    st.error(f"无效内容: {img_data}")
