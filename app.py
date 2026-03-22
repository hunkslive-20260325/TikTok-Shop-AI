import streamlit as st
import requests
import base64
import traceback
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：深度优化 Payload 与 异常捕获 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V36"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def get_key_status(self):
        """精准余额解析"""
        try:
            res = requests.get("https://openrouter.ai/api/v1/key", headers=self.headers, timeout=5)
            if res.status_code == 200:
                d = res.json().get('data', {})
                return f"{round(d.get('limit', 0) - d.get('usage', 0), 4)} USD"
            return f"Error: {res.status_code}"
        except: return "Connection Timeout"

    def run_vision_seo(self, model_id, prompt, uploaded_file):
        """符合规范的识图 Payload"""
        content = [{"type": "text", "text": prompt}]
        if uploaded_file:
            b64_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })
        
        payload = {"model": model_id, "messages": [{"role": "user", "content": content}]}
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json=payload, timeout=60)
            self.log("DEBUG", f"SEO API Status: {res.status_code}")
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            self.log("ERROR", f"SEO Failed: {str(e)}")
            return f"❌ 识图失败: {str(e)}"

    def run_gen_image(self, model_id, prompt):
        """修正后的绘图 Payload 与 Fallback 逻辑"""
        # 按照你的建议：采用标准的 [{"type": "text", "text": "..."}] 结构
        fallbacks = [model_id, "black-forest-labs/flux-schnell", "openai/dall-e-3"]
        
        for mid in fallbacks:
            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "modalities": ["image"]
            }
            try:
                self.log("INFO", f"Trying Model: {mid}")
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers=self.headers, json=payload, timeout=60)
                
                # 打印调试信息到日志
                self.log("DEBUG", f"{mid} Response: {res.status_code}")
                
                if res.status_code == 200:
                    data = res.json()
                    msg = data['choices'][0]['message']
                    img_data = msg.get("images", [None])[0] or msg.get("content", "")
                    if len(str(img_url := img_data)) > 50:
                        return img_url, mid
                else:
                    self.log("WARN", f"{mid} failed: {res.text[:100]}")
            except Exception as e:
                self.log("ERROR", f"Exception on {mid}: {str(e)}")
                continue
        return None, "None"

# --- 2. 前端展示：增强 Base64 处理 ---
def display_image(img_raw, caption):
    """处理 URL 或 Base64 字符串的兼容显示"""
    try:
        if str(img_raw).startswith("http"):
            st.image(img_raw, caption=caption, use_container_width=True)
        else:
            # 自动处理带前缀或不带前缀的 base64
            pure_base64 = str(img_raw).split(",")[-1]
            img_bytes = base64.b64decode(pure_base64)
            st.image(Image.open(BytesIO(img_bytes)), caption=caption, use_container_width=True)
    except Exception as e:
        st.error(f"图片渲染失败: {str(e)}")

# --- 3. 主页面布局 ---
st.set_page_config(page_title="饰品专家 V36", layout="wide")
if "seo_res" not in st.session_state: st.session_state.seo_res = ""
if "img_res" not in st.session_state: st.session_state.img_res = []

with st.sidebar:
    st.title("🛡️ 饰品 AI 控制台")
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    engine = JewelryAIEngine(api_key)
    
    # 余额显示
    bal_container = st.empty()
    if st.button("🔄 刷新 API 余额"):
        st.session_state.bal_val = engine.get_key_status()
    bal_container.metric("API 余额", st.session_state.get("bal_val", "未查询"))

    st.divider()
    txt_m = st.selectbox("识图模型", ["google/gemini-2.0-flash-001", "anthropic/claude-3-haiku"])
    img_m = st.selectbox("绘图模型", ["black-forest-labs/flux-schnell", "openai/dall-e-3"])

    st.divider()
    u_title = st.text_input("原始标题", "心形项链")
    u_cat = st.selectbox("类型", ["项链", "手链", "耳环", "戒指"])
    u_file = st.file_uploader("📸 上传原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), use_container_width=True)

st.header("💎 TikTok Shop 饰品全能 AI (V36 排障增强版)")
c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 专家指令")
    if st.button("✨ 1. 识图并优化标题", use_container_width=True):
        st.session_state.seo_res = engine.run_vision_seo(txt_m, f"优化饰品标题: {u_title}", u_file)
        
    if st.button("🖼️ 2. 生成莫兰迪主图", use_container_width=True):
        url, mod = engine.run_gen_image(img_m, f"Jewelry photography of {u_cat}, Morandi cream background, 8k")
        if url: st.session_state.img_res.append({"u": url, "m": mod, "t": "主图"})
        else: st.error("绘图引擎尝试后全部失败，请看下方日志")

    if st.button("👤 3. 生成模特效果图", use_container_width=True):
        url, mod = engine.run_gen_image(img_m, f"Model wearing {u_cat}, TikTok style, 8k")
        if url: st.session_state.img_res.append({"u": url, "m": mod, "t": "模特图"})
        else: st.error("绘图引擎尝试后全部失败，请看下方日志")

with c2:
    st.subheader("📊 成果展示")
    if st.session_state.seo_res: st.markdown(st.session_state.seo_res)
    if st.session_state.img_res:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_res):
            with grid[i % 2]:
                display_image(item['u'], f"{item['t']} ({item['m']})")

# 底部调试区
with st.expander("🛠️ 系统调试日志 (报错请点开看这个)"):
    logs = "\n".join(st.session_state.get("logs", [])[::-1])
    st.text_area("Debug Logs", logs, height=300)import streamlit as st
import requests
import base64
import traceback
from PIL import Image
from io import BytesIO
from datetime import datetime

# --- 1. 后端类：深度优化 Payload 与 异常捕获 ---
class JewelryAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_V36"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def get_key_status(self):
        """精准余额解析"""
        try:
            res = requests.get("https://openrouter.ai/api/v1/key", headers=self.headers, timeout=5)
            if res.status_code == 200:
                d = res.json().get('data', {})
                return f"{round(d.get('limit', 0) - d.get('usage', 0), 4)} USD"
            return f"Error: {res.status_code}"
        except: return "Connection Timeout"

    def run_vision_seo(self, model_id, prompt, uploaded_file):
        """符合规范的识图 Payload"""
        content = [{"type": "text", "text": prompt}]
        if uploaded_file:
            b64_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })
        
        payload = {"model": model_id, "messages": [{"role": "user", "content": content}]}
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                headers=self.headers, json=payload, timeout=60)
            self.log("DEBUG", f"SEO API Status: {res.status_code}")
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            self.log("ERROR", f"SEO Failed: {str(e)}")
            return f"❌ 识图失败: {str(e)}"

    def run_gen_image(self, model_id, prompt):
        """修正后的绘图 Payload 与 Fallback 逻辑"""
        # 按照你的建议：采用标准的 [{"type": "text", "text": "..."}] 结构
        fallbacks = [model_id, "black-forest-labs/flux-schnell", "openai/dall-e-3"]
        
        for mid in fallbacks:
            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                "modalities": ["image"]
            }
            try:
                self.log("INFO", f"Trying Model: {mid}")
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers=self.headers, json=payload, timeout=60)
                
                # 打印调试信息到日志
                self.log("DEBUG", f"{mid} Response: {res.status_code}")
                
                if res.status_code == 200:
                    data = res.json()
                    msg = data['choices'][0]['message']
                    img_data = msg.get("images", [None])[0] or msg.get("content", "")
                    if len(str(img_url := img_data)) > 50:
                        return img_url, mid
                else:
                    self.log("WARN", f"{mid} failed: {res.text[:100]}")
            except Exception as e:
                self.log("ERROR", f"Exception on {mid}: {str(e)}")
                continue
        return None, "None"

# --- 2. 前端展示：增强 Base64 处理 ---
def display_image(img_raw, caption):
    """处理 URL 或 Base64 字符串的兼容显示"""
    try:
        if str(img_raw).startswith("http"):
            st.image(img_raw, caption=caption, use_container_width=True)
        else:
            # 自动处理带前缀或不带前缀的 base64
            pure_base64 = str(img_raw).split(",")[-1]
            img_bytes = base64.b64decode(pure_base64)
            st.image(Image.open(BytesIO(img_bytes)), caption=caption, use_container_width=True)
    except Exception as e:
        st.error(f"图片渲染失败: {str(e)}")

# --- 3. 主页面布局 ---
st.set_page_config(page_title="饰品专家 V36", layout="wide")
if "seo_res" not in st.session_state: st.session_state.seo_res = ""
if "img_res" not in st.session_state: st.session_state.img_res = []

with st.sidebar:
    st.title("🛡️ 饰品 AI 控制台")
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    engine = JewelryAIEngine(api_key)
    
    # 余额显示
    bal_container = st.empty()
    if st.button("🔄 刷新 API 余额"):
        st.session_state.bal_val = engine.get_key_status()
    bal_container.metric("API 余额", st.session_state.get("bal_val", "未查询"))

    st.divider()
    txt_m = st.selectbox("识图模型", ["google/gemini-2.0-flash-001", "anthropic/claude-3-haiku"])
    img_m = st.selectbox("绘图模型", ["black-forest-labs/flux-schnell", "openai/dall-e-3"])

    st.divider()
    u_title = st.text_input("原始标题", "心形项链")
    u_cat = st.selectbox("类型", ["项链", "手链", "耳环", "戒指"])
    u_file = st.file_uploader("📸 上传原图", type=["jpg", "png", "jpeg"])
    if u_file: st.image(Image.open(u_file), use_container_width=True)

st.header("💎 TikTok Shop 饰品全能 AI (V36 排障增强版)")
c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("🚀 专家指令")
    if st.button("✨ 1. 识图并优化标题", use_container_width=True):
        st.session_state.seo_res = engine.run_vision_seo(txt_m, f"优化饰品标题: {u_title}", u_file)
        
    if st.button("🖼️ 2. 生成莫兰迪主图", use_container_width=True):
        url, mod = engine.run_gen_image(img_m, f"Jewelry photography of {u_cat}, Morandi cream background, 8k")
        if url: st.session_state.img_res.append({"u": url, "m": mod, "t": "主图"})
        else: st.error("绘图引擎尝试后全部失败，请看下方日志")

    if st.button("👤 3. 生成模特效果图", use_container_width=True):
        url, mod = engine.run_gen_image(img_m, f"Model wearing {u_cat}, TikTok style, 8k")
        if url: st.session_state.img_res.append({"u": url, "m": mod, "t": "模特图"})
        else: st.error("绘图引擎尝试后全部失败，请看下方日志")

with c2:
    st.subheader("📊 成果展示")
    if st.session_state.seo_res: st.markdown(st.session_state.seo_res)
    if st.session_state.img_res:
        grid = st.columns(2)
        for i, item in enumerate(st.session_state.img_res):
            with grid[i % 2]:
                display_image(item['u'], f"{item['t']} ({item['m']})")

# 底部调试区
with st.expander("🛠️ 系统调试日志 (报错请点开看这个)"):
    logs = "\n".join(st.session_state.get("logs", [])[::-1])
    st.text_area("Debug Logs", logs, height=300)
