import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：增加权限自检与动态发现 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V40"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def fetch_supported_models(self):
        """核心建议 2(1)：实时查询当前 Key 支持的模型列表"""
        try:
            res = requests.get("https://openrouter.ai/api/v1/models", headers=self.headers, timeout=5)
            if res.status_code == 200:
                models = res.json().get('data', [])
                # 过滤出 ID 字符串，供用户选择
                return [m['id'] for m in models]
            return []
        except: return []

    def run_gen_image(self, model_id, prompt):
        """核心建议 3：带状态打印的稳健绘图"""
        # 按照你的建议，我们可以通过多种 ID 尝试，但必须是合法的
        fallbacks = [model_id, "stability-ai/stable-diffusion-xl-base-1.0", "google/palm-2-chat-bison"]
        
        for mid in fallbacks:
            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "modalities": ["image"]
            }
            try:
                self.log("INFO", f"正在敲门: {mid}")
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers=self.headers, json=payload, timeout=60)
                
                # 核心建议 2(3)：加判断，不通则跳过
                if res.status_code != 200:
                    self.log("WARN", f"模型 {mid} 不给面子 ({res.status_code}): {res.text[:100]}")
                    continue

                data = res.json()
                img_data = data.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
                if img_data: 
                    return img_data, mid
            except Exception as e:
                self.log("ERROR", f"调用 {mid} 意外翻车: {str(e)}")
                continue
        return None, "None"

    def run_vision_seo(self, model_id, prompt, uploaded_file):
        """识图文案逻辑"""
        content = [{"type": "text", "text": prompt}]
        if uploaded_file:
            b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json={"model": model_id, "messages": [{"role": "user", "content": content}]}, timeout=60)
            return res.json()['choices'][0]['message']['content']
        except: return "❌ 识图失败，可能该模型不支持视觉或 Key 权限不足"

# --- 2. UI 逻辑 ---
st.set_page_config(page_title="饰品专家 V40", layout="wide")
if "seo" not in st.session_state: st.session_state.seo = ""
if "imgs" not in st.session_state: st.session_state.imgs = []

with st.sidebar:
    st.title("🛡️ 权限诊断版")
    key = st.secrets.get("OPENROUTER_API_KEY", "")
    engine = JewelryAIEngine(key)
    
    # 动态获取模型列表
    if st.button("🔍 1. 第一步：体检并更新模型列表"):
        st.session_state.available_models = engine.fetch_supported_models()
        if st.session_state.available_models: st.success(f"找到 {len(st.session_state.available_models)} 个可用模型")
        else: st.error("没有找到可用模型，请检查 API Key 余额！")

    model_list = st.session_state.get("available_models", ["google/gemini-2.0-flash-exp", "openai/gpt-4o"])
    
    st.divider()
    m_txt = st.selectbox("文案/识图模型 (已体检)", model_list)
    m_img = st.selectbox("绘图首选模型 (已体检)", model_list)

    st.divider()
    u_title = st.text_input("产品标题", "纯银项链")
    u_file = st.file_uploader("上传原图", type=["jpg", "png"])

st.header("💎 TikTok Shop 饰品 AI (V40.0 权限自愈版)")
c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 专家任务")
    if st.button("✨ 优化 SEO 标题", use_container_width=True):
        st.session_state.seo = engine.run_vision_seo(m_txt, f"分析此图并优化标题: {u_title}", u_file)
    
    if st.button("🖼️ 生成莫兰迪主图", use_container_width=True):
        res, mid = engine.run_gen_image(m_img, "Jewelry photography, Morandi background, 8k")
        if res: st.session_state.imgs.append({"u": res, "m": mid, "t": "主图"})
        else: st.error("当前 Key 权限内没有任何模型能绘图，请看日志排查原因。")

with c2:
    if st.session_state.seo: st.markdown(st.session_state.seo)
    if st.session_state.imgs:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.imgs):
            with grid[i%2]:
                pure_b64 = str(item['u']).split(",")[-1]
                st.image(Image.open(BytesIO(base64.b64decode(pure_b64))), caption=f"{item['t']} ({item['m']})", use_container_width=True)

with st.expander("🛠️ 深度权限日志 (报错看这里)"):
    st.text_area("Logs", "\n".join(st.session_state.get("logs", [])[::-1]), height=250)
