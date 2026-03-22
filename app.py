import streamlit as st
import requests
from PIL import Image

# --- 1. 参数锁死逻辑 (确保你的输入不再因为报错而丢失) ---
if "store" not in st.session_state:
    st.session_state.store = {
        "seo": "",
        "imgs": []
    }

# --- 2. 文档对齐：OpenRouter 核心调用函数 ---
def call_ai_engine(task, cat, mkt, gen, title=""):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://streamlit.io", # 官方文档要求
        "X-Title": "Jewelry AI Optimizer"
    }

    if task == "SEO":
        # 文案使用标准文本模型
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [{"role": "user", "content": f"TikTok饰品专家：为{mkt}的{gen}优化{cat}标题。原始：{title}。用Markdown表格输出建议。"}]
        }
    else:
        # 图片生成：严格遵循 Quickstart 绘图协议
        # 针对你之前的报错，第一顺位强制使用兼容性最高的 Flux
        payload = {
            "model": "black-forest-labs/flux-schnell", 
            "messages": [{"role": "user", "content": f"Jewelry photography of {cat}, Morandi background, 8k" if task=="MAIN" else f"Fashion model wearing {cat}, 8k"}],
            "modalities": ["image"] # 👈 这是文档要求的绘图门槛
        }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=90)
        data = res.json()
        
        if "choices" in data:
            msg = data['choices'][0]['message']
            # 图片模型返回逻辑：优先找 images 数组，找不到再找 content
            if "images" in msg and msg["images"]:
                return msg["images"][0], payload["model"]
            return msg.get("content", ""), payload["model"]
        else:
            return f"❌ 接口反馈: {data.get('error', {}).get('message', '未知错误')}", "Error"
    except Exception as e:
        return f"❌ 链接异常: {str(e)}", "Error"

# --- 3. 界面布局 (严格保留你的输入参数与按钮名称) ---
st.set_page_config(page_title="饰品 AI 专家 V27", layout="wide")
st.title("💎 TikTok Shop 饰品全能 AI 专家")

with st.sidebar:
    st.header("📋 经营信息输入")
    # 锁定参数名称
    u_title = st.text_input("1. 原始标题", value="S925银心形项链")
    u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指"])
    u_mkt = st.selectbox("3. 目标市场", ["东南亚总区", "美国", "英国"])
    u_gen = st.radio("4. 目标性别趋势", ["女性", "男性"], horizontal=True)
    st.divider()
    f = st.file_uploader("🖼️ 上传原图", type=["jpg", "png", "jpeg"])
    if f: st.image(Image.open(f), use_container_width=True)

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 专家指令执行")
    # 按钮名称锁定
    if st.button("✨ 1. 执行：标题 SEO 优化"):
        with st.spinner("正在生成..."):
            res, _ = call_ai_engine("SEO", u_cat, u_mkt, u_gen, u_title)
            st.session_state.store["seo"] = res
            
    if st.button("🖼️ 2. 执行：商品图优化"):
        with st.spinner("正在绘图..."):
            res, mod = call_ai_engine("MAIN", u_cat, u_mkt, u_gen)
            st.session_state.store["imgs"].append({"url": res, "mod": mod, "type": "主图"})

    if st.button("👤 3. 执行：模特图优化"):
        with st.spinner("正在匹配模特..."):
            res, mod = call_ai_engine("MODEL", u_cat, u_mkt, u_gen)
            st.session_state.store["imgs"].append({"url": res, "mod": mod, "type": "模特图"})

with c2:
    st.subheader("📊 实时成果展示")
    if st.session_state.store["seo"]:
        st.markdown(st.session_state.store["seo"])
    
    if st.session_state.store["imgs"]:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.store["imgs"]):
            with grid[i % 2]:
                st.caption(f"驱动: {item['mod']} | 类型: {item['type']}")
                raw = str(item['url'])
                if raw.startswith("http") or len(raw) > 100:
                    st.image(raw, use_container_width=True)
                else:
                    st.error(raw)
