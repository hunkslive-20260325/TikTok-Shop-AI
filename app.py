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
    """将 AI 返回的数据统一转为有效字节流，并进行健壮性校验"""
    if not img_data or not isinstance(img_data, str): 
        return None
    try:
        # 情况1：URL 链接
        if img_data.startswith("http"):
            res = requests.get(img_data, timeout=30)
            return res.content if res.status_code == 200 else None
        # 情况2：带前缀的 Base64
        elif "base64," in img_data:
            return base64.b64decode(img_data.split(",")[1])
        # 情况3：纯 Base64 字符串
        else:
            return base64.b64decode(img_data)
    except Exception:
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
            "X-Title": "AM_Jewelry_V48_Fixed"
        }
  
    def run_smart_gen(self, mode, gender, category, file_bytes):
        """调用 AI 生成单张图片"""
        try:
            b64_in = base64.b64encode(file_bytes).decode('utf-8')
            
            # 环境随机化：提升批量生成的多样性
            props = random.choice(["minimalist marble pedestal", "textured travertine slab", "soft organic stone"])
            decor = random.choice(["gentle palm shadows", "folded silk fabric", "scattered jasmine petals"])

            if mode == "模特图":
                prompt = (f"A high-end professional fashion shot of a {gender} model wearing this {category}. "
                          f"The jewelry must be in sharp focus with exquisite metallic luster. "
                          f"Natural skin texture, clean studio lighting, 8k photorealistic.")
            else:
                prompt = (f"Premium macro product photography of the {category}. "
                          f"The item is elegantly placed on a {props} with {decor} in the background. "
                          f"High-key lighting, anisotropic reflections on metal, razor-sharp focus, 8k.")

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
            
            # 确保 API 路径正确
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            res_json = safe_post(api_url, self.headers, payload)
            
            # 提取数据逻辑
            if res_json and 'choices' in res_json:
                msg = res_json['choices'][0].get('message', {})
                # 兼容不同模型的图片返回位置
                img_data = msg.get('images', [None])[0]
                if not img_data and isinstance(msg.get('content'), str) and "data:image" in msg.get('content'):
                    img_data = msg['content']
                return img_data
            return None
        except Exception:
            return None

# ==========================================
# Streamlit 界面逻辑
# ==========================================
st.set_page_config(page_title="AM JEWELRY Pro", layout="wide")

# 自定义 CSS 提升 UI 质感
st.markdown("""
    <style>
    .log-container {
        background-color: #0e1117; color: #00ff00; padding: 15px;
        border-radius: 8px; border: 1px solid #30363d;
        font-family: 'Courier New', monospace; font-size: 0.85rem;
        margin-bottom: 20px;
    }
    .stButton>button { width: 100%; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# 密钥认证
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 初始化状态保持
if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

# --- 侧边栏 ---
with st.sidebar:
    st.title("💎 AM JEWELRY")
    st.caption("Batch Pro v4.8 | 2026 Edition")
    
    u_category = st.selectbox("饰品类型", [
        "项链", "耳环", "脚链", "戒指", "手环与手链", 
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
    btn_prod = c1.button("批量商品图", type="primary")
    btn_mod = c2.button("批量模特图")
    
    if st.button("🗑️ 清空结果"):
        st.session_state.p_imgs = []
        st.session_state.m_imgs = []
        st.rerun()

# --- 核心业务逻辑 ---
log_area = st.empty()

def update_log(msg, icon="⏳"):
    log_area.markdown(f'<div class="log-container">{icon} {msg}</div>', unsafe_allow_html=True)

def run_batch_process(mode):
    if not u_files:
        st.error("请先上传图片！")
        return
    
    temp_list = []
    total = len(u_files) * u_img_count
    current = 0
    
    for f in u_files:
        f_bytes = f.getvalue()
        base_name = f.name.split('.')[0]
        
        for i in range(u_img_count):
            current += 1
            update_log(f"正在处理 ({current}/{total}): {f.name}")
            
            img_data = engine.run_smart_gen(mode, u_gender, u_category, f_bytes)
            
            # 只有获取到非空数据才存入结果集
            if img_data:
                temp_list.append((f"{mode}_{base_name}_v{i+1}.png", img_data))
            else:
                st.warning(f"图片 {f.name} 生成异常，已跳过。")
                
    if mode == "商品图": st.session_state.p_imgs = temp_list
    else: st.session_state.m_imgs = temp_list
    update_log(f"任务完成！成功生成 {len(temp_list)} 张图片", icon="✅")

if btn_prod: run_batch_process("商品图")
if btn_mod: run_batch_process("模特图")

# --- 渲染与批量下载 ---
def safe_display_image(data, caption, column):
    """安全渲染图片，增加 PIL 校验防止引发 Streamlit 内部错误"""
    if not data: return
    img_bytes = get_image_bytes(data)
    if img_bytes:
        try:
            # 预检：如果字节流无法被 PIL 打开，说明不是有效图片
            img_obj = Image.open(BytesIO(img_bytes))
            column.image(img_obj, caption=caption, use_container_width=True)
        except Exception:
            column.error(f"解析失败: {caption}")
    else:
        column.error("无效的数据流")

if st.session_state.p_imgs or st.session_state.m_imgs:
    st.divider()
    
    def prepare_zip(image_list):
        """批量下载 ZIP 打包逻辑"""
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, data in image_list:
                b_data = get_image_bytes(data)
                if b_data: z.writestr(name, b_data)
        return buf.getvalue()

    col_dl1, col_dl2 = st.columns(2)
    if st.session_state.p_imgs:
        p_zip = prepare_zip(st.session_state.p_imgs)
        col_dl1.download_button("📥 下载全部商品图 (ZIP)", p_zip, "products_batch.zip")
    if st.session_state.m_imgs:
        m_zip = prepare_zip(st.session_state.m_imgs)
        col_dl2.download_button("📥 下载全部模特图 (ZIP)", m_zip, "models_batch.zip")

    t1, t2 = st.tabs(["🖼️ 商品展示", "👤 模特展示"])
    with t1:
        if st.session_state.p_imgs:
            cols = st.columns(3)
            for idx, (name, data) in enumerate(st.session_state.p_imgs):
                safe_display_image(data, name, cols[idx % 3])
    with t2:
        if st.session_state.m_imgs:
            cols = st.columns(3)
            for idx, (name, data) in enumerate(st.session_state.m_imgs):
                safe_display_image(data, name, cols[idx % 3])
