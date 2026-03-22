import streamlit as st
import requests
import base64
import traceback
from PIL import Image
from datetime import datetime

# --- 1. 后端类：确保所有功能链路完整 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V35"
        }

    def get_key_status(self):
        """反显余额：逻辑对齐 2026 官方接口"""
        try:
            res = requests.get("https://openrouter.ai/api/v1/key", headers=self.headers, timeout=5)
            if res.status_code == 200:
                d = res.json().get('data', {})
                return f"{round(d.get('limit', 0) - d.get('usage', 0), 4)} USD"
            return "Key 校验失败"
        except: return "网络延迟"

    def run_vision_seo(self, model_id, prompt, uploaded_file):
        """图片识别 + SEO 标题 (上传图片需求锁定)"""
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        if uploaded_file:
            b64_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json={"model": model_id, "messages": messages}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 识图失败，请检查 API 或图片格式"

    def run_gen_image(self, model_id, prompt):
        """绘图逻辑：增加自动补位 (Fallback) 机制"""
        # 如果主模型失败，按顺序尝试这些备选
        fallbacks = [model_id, "black-forest-labs/flux-schnell", "openai/dall-e-3", "google/imagen-3"]
        
        for mid in fallbacks:
            payload = {"model": mid, "messages": [{"role": "user", "content": prompt}], "modalities": ["image"]}
            try:
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers=self.headers, json=payload, timeout=60)
                data = res.json()
                img_url = data['choices'][0]['message'].get("images", [None])[0] or data['choices'][0]['message'].get("content", "")
                if len(str(img_url)) > 50: return img_url, mid
            except: continue
        return "❌ 绘图引擎全部失效，请检查额度", "None"

# --- 2. 前端 UI：严格对齐用户需求 ---
st.set_page_config(page_title="饰品专家 V35", layout="wide")
if "seo_res" not in st.session_state: st.session_state.seo_res = ""
if "img_res" not in st.session_state: st.session_state.img_res = []

with st.sidebar:
    st.title("🛡️ 饰品 AI 控制台")
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    engine = JewelryAIEngine(api_key)
    
    # 余额刷新
    c1, c2 = st.columns([2, 1])
    c1.metric("API 余额", st.session_state.get("bal_val", "待刷新"))
    if c2.button("刷新"): st.session_state.bal_val = engine.get_key_status()

    st.divider()
    v_model = st.selectbox("识图/文案模型", ["google/gemini-2.0-flash-001", "deepseek/deepseek-chat"])
    g_model = st.selectbox("绘图模型 (失败将自动切换)", ["black-forest-labs/flux-schnell", "openai/dall-e-3"])

    st.divider()
    u_title = st.text_input("原始标题", "S925银心形项链")
    u_cat = st.selectbox("商品类型", ["项链", "手链", "耳环", "戒指"])
    u_market = st.selectbox("目标市场", ["东南亚总区", "美国", "英国"])
    u_file = st.file_uploader("📸 上传商品原图 (AI 必看)", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), use_container_width=True)

st.header("💎 TikTok Shop 饰品全能 AI (V35.0 识图+主图+模特)")
col_act, col_res = st.columns([1, 1.2])

with col_act:
    st.subheader("🚀 专家指令执行")
    # 按钮 1：识图 SEO (核心需求)
    if st.button("✨ 1. 识图并优化 SEO 标题", use_container_width=True):
        p = f"分析图中饰品细节，结合标题'{u_title}'，针对{u_market}市场输出3个高转化标题。"
        st.session_state.seo_res = engine.run_vision_seo(v_model, p, u_file)
        
    # 按钮 2：商品主图 (莫兰迪风格)
    if st.button("🖼️ 2. 执行：商品主图优化", use_container_width=True):
        p = f"Professional jewelry photography of {u_cat}, Morandi cream background, 8k"
        url, mod = engine.run_gen_image(g_model, p)
        st.session_state.img_res.append({"u": url, "m": mod, "t": "主图"})

    # 按钮 3：模特图 (找回来的需求)
    if st.button("👤 3. 执行：模特实拍优化", use_container_width=True):
        p = f"High-end fashion model wearing {u_cat}, TikTok style lifestyle photography, 8k"
        url, mod = engine.run_gen_image(g_model, p)
        st.session_state.img_res.append({"u": url, "m": mod, "t": "模特图"})

with col_res:
    st.subheader("📊 实时成果展示")
    if st.session_state.seo_res:
        st.info("SEO 优化结果")
        st.markdown(st.session_state.seo_res)
    
    if st.session_state.img_res:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_res):
            with grid[i % 2]:
                if str(item['u']).startswith("http") or len(str(item['u'])) > 100:
                    st.image(item['u'], caption=f"{item['t']} (引擎: {item['m']})")
                else: st.error(item['u'])
