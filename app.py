import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import random
import zipfile

# ==========================================
# 配置：仅保留指定模型
# ==========================================
DEFAULT_MODEL = "google/gemini-2.5-flash-image"

# ==========================================
# 工具函数
# ==========================================
def safe_post(url, headers, json_data, timeout=120):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"请求失败: {e}")
        return None

def get_image_bytes(img_data):
    if isinstance(img_data, str) and img_data.startswith("http"):
        return requests.get(img_data).content
    elif isinstance(img_data, str) and "base64," in img_data:
        return base64.b64decode(img_data.split(",")[1])
    elif isinstance(img_data, str):
        return base64.b64decode(img_data)
    return None

# ==========================================
# AI 引擎 (专注于图像生成)
# ==========================================
class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Batch_Lite"
        }
  
    def run_smart_gen(self, mode, gender, category, file_bytes):
        try:
            b64_in = base64.b64encode(file_bytes).decode('utf-8')
            
            # 随机环境元素增加多样性
            support = random.choice(["travertine pedestal", "ceramic slab", "linen block"])
            organic = random.choice(["silk ribbon", "dried petals", "monstera leaf"])

            if mode == "模特图":
                prompt = f"Professional {gender} model wearing {category}. High-end fashion editorial style, soft studio lighting, sharp focus on the jewelry, 8k photorealistic."
            else:
                prompt = f"Premium macro product photography of {category}. Item placed on {support} with {organic} in background. Natural sunlight, anisotropic reflections on metal, 8k."

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
            
            res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload)
            if res_json:
                return res_json.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
        except:
            return None

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="AM JEWELRY Lite", layout="wide")

# 自定义日志样式
st.markdown("""
    <style>
    .log-container {
        background-color: #1e1e1e; color: #00ff00; padding: 15px;
        border-radius: 8px; border-left: 5px solid #0d47a1; margin-bottom: 20px;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 状态管理
if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

# --- 侧边栏 ---
with st.sidebar:
    st.subheader("💎 图像批量生成")
    
    u_category = st.selectbox("饰品类型", [
        "项链", "耳环", "脚链", "戒指", "手环与手链", 
        "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装"
    ])
    u_gender = st.radio("目标人群", ["女性", "男性"])
    
    u_files = st.file_uploader("上传原图 (支持多选，上限10张)", type=["jpg","png","jpeg"], accept_multiple_files=True)
    if u_files and len(u_files) > 10:
        u_files = u_files[:10]

    st.divider()
    u_img_count = st.select_slider("每张图生成数量", options=[1, 2, 4], value=1)
    
    c1, c2 = st.columns(2)
    btn_prod = c1.button("批量商品图", use_container_width=True)
    btn_mod = c2.button("批量模特图", use_container_width=True)
    
    if st.button("🗑️ 清除所有结果", use_container_width=True):
        st.session_state.p_imgs = []
        st.session_state.m_imgs = []
        st.rerun()

# --- 主界面逻辑 ---
log_area = st.empty()

def update_log(msg, icon="⏳"):
    log_area.markdown(f'<div class="log-container">{icon} {msg}</div>', unsafe_allow_html=True)

def run_batch(mode):
    if not u_files:
        st.error("请先上传图片")
        return
    
    results = []
    total = len(u_files) * u_img_count
    curr = 0
    
    for f in u_files:
        f_bytes = f.getvalue()
        base_name = f.name.split('.')[0]
        for v in range(u_img_count):
            curr += 1
            update_log(f"正在生成 {mode}: {f.name} ({curr}/{total})")
            img_res = engine.run_smart_gen(mode, u_gender, u_category, f_bytes)
            if img_res:
                results.append((f"{mode}_{base_name}_v{v+1}.png", img_res))
    
    if mode == "商品图": st.session_state.p_imgs = results
    else: st.session_state.m_imgs = results
    update_log(f"✅ {mode}批量处理完成！", icon="✨")

if btn_prod: run_batch("商品图")
if btn_mod: run_batch("模特图")

# --- 展示与批量下载 ---
if st.session_state.p_imgs or st.session_state.m_imgs:
    st.divider()
    
    # 批量打包逻辑
    def download_zip(image_list, zip_name):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, data in image_list:
                b = get_image_bytes(data)
                if b: z.writestr(name, b)
        return buf.getvalue()

    col_dl1, col_dl2 = st.columns(2)
    if st.session_state.p_imgs:
        col_dl1.download_button("📥 下载全部商品图 (ZIP)", download_zip(st.session_state.p_imgs, "p"), "products.zip", use_container_width=True)
    if st.session_state.m_imgs:
        col_dl2.download_button("📥 下载全部模特图 (ZIP)", download_zip(st.session_state.m_imgs, "m"), "models.zip", use_container_width=True)

    t1, t2 = st.tabs(["🖼️ 商品展示", "👤 模特展示"])
    with t1:
        cols = st.columns(3)
        for i, (name, data) in enumerate(st.session_state.p_imgs):
            cols[i % 3].image(data, caption=name)
    with t2:
        cols = st.columns(3)
        for i, (name, data) in enumerate(st.session_state.m_imgs):
            cols[i % 3].image(data, caption=name)
