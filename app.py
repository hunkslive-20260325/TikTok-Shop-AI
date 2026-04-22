import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import random
import zipfile
import json

# ==========================================
# 核心配置
# ==========================================
DEFAULT_MODEL = "google/gemini-2.5-flash-image"

# ==========================================
# 工具函数
# ==========================================
def safe_post(url, headers, json_data, timeout=150):
    """请求 API 并返回 JSON 或 错误信息"""
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        if res.status_code != 200:
            return {"error": f"API 状态码异常: {res.status_code}", "detail": res.text}
        return res.json()
    except Exception as e:
        return {"error": "网络请求异常", "detail": str(e)}

def get_image_bytes(img_data):
    """转换图片字节流"""
    if not img_data or not isinstance(img_data, str): 
        return None
    try:
        if img_data.startswith("http"):
            res = requests.get(img_data, timeout=30)
            return res.content if res.status_code == 200 else None
        elif "base64," in img_data:
            return base64.b64decode(img_data.split(",")[1])
        else:
            return base64.b64decode(img_data)
    except:
        return None

# ==========================================
# AI 引擎
# ==========================================
class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "AM_Jewelry_V48_Debug"
        }
  
    def run_smart_gen(self, mode, gender, category, file_bytes):
        """调用 AI 生成单张图片，返回 (结果数据, 错误日志)"""
        try:
            b64_in = base64.b64encode(file_bytes).decode('utf-8')
            prompt = f"Premium photography of {category} for {gender}. 8k, sharp focus."

            payload = {
                "model": DEFAULT_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}
                    ]
                }],
                "modalities": ["image"]
            }
            
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            res_json = safe_post(api_url, self.headers, payload)
            
            # 如果开启调试模式，在页面输出原始数据
            if st.session_state.get('debug_mode'):
                with st.expander("🔍 原始 API 回包内容", expanded=False):
                    st.json(res_json)

            if "error" in res_json:
                return None, f"请求失败: {res_json.get('error')} | 详情: {res_json.get('detail')}"

            if 'choices' in res_json:
                msg = res_json['choices'][0].get('message', {})
                img_data = msg.get('images', [None])[0]
                if not img_data and "data:image" in str(msg.get('content', '')):
                    img_data = msg['content']
                
                if img_data:
                    return img_data, None
                else:
                    return None, f"API 未返回图像数据。回包内容: {json.dumps(msg)}"
            
            return None, f"未知回包结构: {json.dumps(res_json)}"
        except Exception as e:
            return None, f"本地代码执行异常: {str(e)}"

# ==========================================
# Streamlit 界面
# ==========================================
st.set_page_config(page_title="AM JEWELRY Pro Debug", layout="wide")

# CSS
st.markdown("""
    <style>
    .log-container { background-color: #0e1117; color: #00ff00; padding: 15px; border-radius: 8px; font-family: monospace; }
    .err-container { background-color: #2e0000; color: #ff9999; padding: 15px; border-radius: 8px; font-family: monospace; margin-top: 10px; border: 1px solid red; }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

with st.sidebar:
    st.title("💎 AM JEWELRY")
    st.checkbox("🛠 开启调试模式 (显示原始日志)", key="debug_mode")
    
    u_category = st.selectbox("饰品类型", ["项链", "耳环", "脚链", "戒指", "手环与手链", "身体饰品", "首饰套装"])
    u_gender = st.radio("目标人群", ["女性", "男性"])
    u_files = st.file_uploader("上传原图 (Max 10)", type=["jpg","png","jpeg"], accept_multiple_files=True)
    u_img_count = st.select_slider("每张图变体数", options=[1, 2, 4], value=1)
    
    st.divider()
    c1, c2 = st.columns(2)
    btn_prod = c1.button("批量商品图", type="primary")
    btn_mod = c2.button("批量模特图")

# --- 逻辑处理 ---
log_placeholder = st.container()

def run_batch(mode):
    if not u_files: return st.error("请先上传图片")
    
    success_list = []
    total = len(u_files) * u_img_count
    idx = 0
    
    for f in u_files:
        f_bytes = f.getvalue()
        for i in range(u_img_count):
            idx += 1
            with log_placeholder:
                st.markdown(f'<div class="log-container">⏳ 正在处理 ({idx}/{total}): {f.name}</div>', unsafe_allow_html=True)
            
            data, err = engine.run_smart_gen(mode, u_gender, u_category, f_bytes)
            
            if err:
                with log_placeholder:
                    st.markdown(f'<div class="err-container">❌ 错误报告 [{f.name}]:<br>{err}</div>', unsafe_allow_html=True)
            if data:
                success_list.append((f"{mode}_{f.name.split('.')[0]}_{i}.png", data))
                
    if mode == "商品图": st.session_state.p_imgs = success_list
    else: st.session_state.m_imgs = success_list

if btn_prod: run_batch("商品图")
if btn_mod: run_batch("模特图")

# --- 结果与下载 ---
if st.session_state.p_imgs or st.session_state.m_imgs:
    st.divider()
    
    def prepare_zip(image_list):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, data in image_list:
                b = get_image_bytes(data)
                if b: z.writestr(name, b)
        return buf.getvalue()

    col_dl1, col_dl2 = st.columns(2)
    if st.session_state.p_imgs:
        col_dl1.download_button("📥 下载商品图 (ZIP)", prepare_zip(st.session_state.p_imgs), "p.zip")
    if st.session_state.m_imgs:
        col_dl2.download_button("📥 下载模特图 (ZIP)", prepare_zip(st.session_state.m_imgs), "m.zip")

    t1, t2 = st.tabs(["🖼 商品", "👤 模特"])
    with t1:
        cols = st.columns(3)
        for i, (name, data) in enumerate(st.session_state.p_imgs):
            b = get_image_bytes(data)
            if b: cols[i%3].image(Image.open(BytesIO(b)), caption=name)
    with t2:
        cols = st.columns(3)
        for i, (name, data) in enumerate(st.session_state.m_imgs):
            b = get_image_bytes(data)
            if b: cols[i%3].image(Image.open(BytesIO(b)), caption=name)
