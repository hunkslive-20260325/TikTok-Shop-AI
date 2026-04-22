import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import random
import zipfile

# ==========================================
# 核心配置
# ==========================================
DEFAULT_MODEL = "google/gemini-2.5-flash-image"

# ==========================================
# 工具函数
# ==========================================
def safe_post(url, headers, json_data, timeout=150):
    """带异常处理的 POST 请求"""
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_image_bytes(img_data):
    """将不同格式的 AI 返回数据统一转为字节流"""
    if not img_data: 
        return None
    try:
        # 如果是 URL 链接
        if isinstance(img_data, str) and img_data.startswith("http"):
            return requests.get(img_data, timeout=30).content
        # 如果是带前缀的 Base64
        elif isinstance(img_data, str) and "base64," in img_data:
            return base64.b64decode(img_data.split(",")[1])
        # 如果是纯 Base64
        elif isinstance(img_data, str):
            return base64.b64decode(img_data)
    except Exception as e:
        st.error(f"转换图片字节流时出错: {e}")
        return None
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
            "X-Title": "AM_Jewelry_V48_Final"
        }
  
    def run_smart_gen(self, mode, gender, category, file_bytes):
        """调用 AI 生成单张图片"""
        try:
            b64_in = base64.b64encode(file_bytes).decode('utf-8')
            
            # 环境随机化：提升批量生成的多样性
            props = random.choice(["minimalist marble", "brushed concrete", "soft organic stone"])
            decor = random.choice(["gentle palm shadows", "silk fabric folds", "a hint of dried botanicals"])

            if mode == "模特图":
                prompt = (f"Close-up high-end fashion photography of a {gender} model wearing {category}. "
                          f"The {category} should be the focal point with crystal clear detail. "
                          f"Professional studio lighting, aesthetic skin texture, 8k realistic.")
            else:
                prompt = (f"Luxury macro product photography of {category}. "
                          f"The item is elegantly displayed on {props} with {decor} in the background. "
                          f"Cinematic lighting, sharp focus, anisotropic reflections on metal surfaces, 8k.")

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
            
            # 健壮性检查：从返回包中提取图片数据
            if res_json and 'choices' in res_json:
                message = res_json['choices'][0].get('message', {})
                # OpenRouter 某些模型图片在 images 字段，某些在 content
                img_data = message.get('images', [None])[0]
                return img_data
            return None
        except Exception as e:
            return None

# ==========================================
# Streamlit 界面
# ==========================================
st.set_page_config(page_title="AM JEWELRY Pro", layout="wide")

# 自定义 CSS
st.markdown("""
    <style>
    .log-container {
        background-color: #0e1117; color: #00ff00; padding: 15px;
        border-radius: 8px; border: 1px solid #30363d;
        font-family: 'Courier New', monospace; font-size: 0.85rem;
    }
    .stButton>button { border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# API 认证
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 状态初始化
if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

# --- 侧边栏 ---
with st.sidebar:
    st.title("💎 AM JEWELRY")
    st.caption("Batch Pro v4.8 | Gemini 2.5")
    
    u_category = st.selectbox("饰品类型", [
        "项项链", "耳环", "脚链", "戒指", "手环与手链", 
        "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装"
    ])
    u_gender = st.radio("目标人群", ["女性", "男性"])
    
    st.divider()
    u_files = st.file_uploader("上传原图 (上限10张)", type=["jpg","png","jpeg"], accept_multiple_files=True)
    if u_files and len(u_files) > 10:
        u_files = u_files[:10]

    u_img_count = st.select_slider("每张图生成变体数", options=[1, 2, 4], value=1)
    
    st.divider()
    c1, c2 = st.columns(2)
    btn_prod = c1.button("批量生成商品图", use_container_width=True, type="primary")
    btn_mod = c2.button("批量生成模特图", use_container_width=True)
    
    if st.button("🗑️ 清空所有结果", use_container_width=True):
        st.session_state.p_imgs = []
        st.session_state.m_imgs = []
        st.rerun()

# --- 主逻辑处理 ---
log_area = st.empty()

def update_log(msg, icon="⏳"):
    log_area.markdown(f'<div class="log-container">{icon} {msg}</div>', unsafe_allow_html=True)

def run_batch_process(mode):
    if not u_files:
        st.error("请先上传图片文件！")
        return
    
    temp_list = []
    total = len(u_files) * u_img_count
    count = 0
    
    for f in u_files:
        f_bytes = f.getvalue()
        base_name = f.name.split('.')[0]
        
        for i in range(u_img_count):
            count += 1
            update_log(f"正在处理: {f.name} ({count}/{total})")
            
            img_res = engine.run_smart_gen(mode, u_gender, u_category, f_bytes)
            
            if img_res:
                temp_list.append((f"{mode}_{base_name}_v{i+1}.png", img_res))
            else:
                st.warning(f"跳过生成失败的图片: {f.name} v{i+1}")
                
    if mode == "商品图": st.session_state.p_imgs = temp_list
    else: st.session_state.m_imgs = temp_list
    update_log(f"任务结束：成功生成 {len(temp_list)} 张图片", icon="✅")

if btn_prod: run_batch_process("商品图")
if btn_mod: run_batch_process("模特图")

# --- 结果展示与 ZIP 下载 ---
if st.session_state.p_imgs or st.session_state.m_imgs:
    st.divider()
    
    def prepare_zip(image_list):
        """批量压缩"""
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, data in image_list:
                b_data = get_image_bytes(data)
                if b_data:
                    z.writestr(name, b_data)
        return buf.getvalue()

    col_dl1, col_dl2 = st.columns(2)
    if st.session_state.p_imgs:
        p_zip = prepare_zip(st.session_state.p_imgs)
        col_dl1.download_button(f"📥 下载商品图 (ZIP)", p_zip, "products.zip", use_container_width=True)
    if st.session_state.m_imgs:
        m_zip = prepare_zip(st.session_state.m_imgs)
        col_dl2.download_button(f"📥 下载模特图 (ZIP)", m_zip, "models.zip", use_container_width=True)

    t1, t2 = st.tabs(["🖼️ 商品展示", "👤 模特展示"])
    with t1:
        if st.session_state.p_imgs:
            cols = st.columns(3)
            for idx, (name, data) in enumerate(st.session_state.p_imgs):
                if data:
                    cols[idx % 3].image(data, caption=name, use_container_width=True)
    with t2:
        if st.session_state.m_imgs:
            cols = st.columns(3)
            for idx, (name, data) in enumerate(st.session_state.m_imgs):
                if data:
                    cols[idx % 3].image(data, caption=name, use_container_width=True)
