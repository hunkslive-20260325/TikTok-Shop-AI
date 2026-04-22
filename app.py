import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import random
import zipfile
import time

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
    if not img_res: return None
    try:
        if isinstance(img_data, str) and img_data.startswith("http"):
            return requests.get(img_data).content
        elif isinstance(img_data, str) and "base64," in img_data:
            return base64.b64decode(img_data.split(",")[1])
        elif isinstance(img_data, str):
            return base64.b64decode(img_data)
    except:
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
            "X-Title": "AM_Jewelry_Batch_V48"
        }
  
    def run_smart_gen(self, mode, gender, category, file_bytes):
        """调用 AI 生成单张图片"""
        try:
            b64_in = base64.b64encode(file_bytes).decode('utf-8')
            
            # 环境随机化：提升批量生成的多样性
            props = random.choice(["minimalist marble", "brushed concrete", "soft velvet cushion"])
            decor = random.choice(["delicate shadows", "scattered pearls", "a touch of green leaf"])

            if mode == "模特图":
                prompt = (f"A high-end fashion shot of a {gender} model wearing {category}. "
                          f"Sharp focus on jewelry, professional studio lighting, 8k ultra-realistic.")
            else:
                prompt = (f"Luxury macro product photography of {category}. "
                          f"The item is placed on {props} with {decor}. "
                          f"Anisotropic reflections, high-key natural lighting, 8k.")

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
            
            res_json = safe_post("https://openrouter.ai/ai/v1/chat/completions", self.headers, payload)
            
            # 健壮性检查：提取图片数据
            if res_json and 'choices' in res_json:
                img_data = res_json['choices'][0].get('message', {}).get('images', [None])[0]
                return img_data
            return None
        except Exception as e:
            return None

# ==========================================
# Streamlit 界面布局
# ==========================================
st.set_page_config(page_title="AM JEWELRY Pro", layout="wide")

# CSS 注入
st.markdown("""
    <style>
    .log-container {
        background-color: #111; color: #0f0; padding: 12px;
        border-radius: 5px; border-left: 4px solid #007bff;
        font-family: 'Courier New', monospace; font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 4px 4px 0 0; }
    </style>
""", unsafe_allow_html=True)

# API Key 获取
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 初始化状态
if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

# --- 侧边栏控制面板 ---
with st.sidebar:
    st.title("💎 AM JEWELRY")
    st.caption("2026 Batch Edition - Gemini 2.5 Flash")
    
    u_category = st.selectbox("饰品类型", [
        "项链", "耳环", "脚链", "戒指", "手环与手链", 
        "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装"
    ])
    u_gender = st.radio("目标人群", ["女性", "男性"])
    
    st.divider()
    u_files = st.file_uploader("批量上传 (上限10张)", type=["jpg","png","jpeg"], accept_multiple_files=True)
    if u_files and len(u_files) > 10:
        st.warning("仅处理前10张图片")
        u_files = u_files[:10]

    u_img_count = st.select_slider("每张原图生成数量", options=[1, 2, 4], value=1)
    
    st.divider()
    col1, col2 = st.columns(2)
    btn_prod = col1.button("批量商品图", use_container_width=True, type="primary")
    btn_mod = col2.button("批量模特图", use_container_width=True)
    
    if st.button("🗑️ 清空所有结果", use_container_width=True):
        st.session_state.p_imgs = []
        st.session_state.m_imgs = []
        st.rerun()

# --- 主界面核心逻辑 ---
log_area = st.empty()

def update_log(msg, icon="⏳"):
    log_area.markdown(f'<div class="log-container">{icon} {msg}</div>', unsafe_allow_html=True)

def run_batch_process(mode):
    if not u_files:
        st.error("请先上传图片文件！")
        return
    if not api_key:
        st.error("未发现 API Key，请检查 Secrets 配置。")
        return

    temp_results = []
    total_steps = len(u_files) * u_img_count
    step = 0
    
    for f in u_files:
        f_bytes = f.getvalue()
        base_name = f.name.split('.')[0]
        
        for v in range(u_img_count):
            step += 1
            update_log(f"任务中: {f.name} (进度 {step}/{total_steps})")
            
            img_output = engine.run_smart_gen(mode, u_gender, u_category, f_bytes)
            
            # 防御性检查：确保不存入 None
            if img_output:
                temp_results.append((f"{mode}_{base_name}_v{v+1}.png", img_output))
            else:
                st.error(f"图片 {f.name} 生成失败，请检查 API 额度或提示词。")
                
    if mode == "商品图":
        st.session_state.p_imgs = temp_results
    else:
        st.session_state.m_imgs = temp_results
    update_log(f"任务完成！共生成 {len(temp_results)} 张图片。", icon="✅")

if btn_prod: run_batch_process("商品图")
if btn_mod: run_batch_process("模特图")

# --- 结果展示与批量下载 ---
if st.session_state.p_imgs or st.session_state.m_imgs:
    st.divider()
    
    # 内存中创建 ZIP 逻辑
    def prepare_zip(image_list):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as z:
            for filename, img_data in image_list:
                b_data = get_image_bytes(img_data)
                if b_data:
                    z.writestr(filename, b_data)
        return zip_buffer.getvalue()

    # 下载按钮区域
    dl_col1, dl_col2 = st.columns(2)
    if st.session_state.p_imgs:
        p_zip = prepare_zip(st.session_state.p_imgs)
        dl_col1.download_button(
            label=f"📥 下载全部商品图 ({len(st.session_state.p_imgs)}张)",
            data=p_zip,
            file_name="jewelry_products_batch.zip",
            mime="application/zip",
            use_container_width=True
        )
    if st.session_state.m_imgs:
        m_zip = prepare_zip(st.session_state.m_imgs)
        dl_col2.download_button(
            label=f"📥 下载全部模特图 ({len(st.session_state.m_imgs)}张)",
            data=m_zip,
            file_name="jewelry_models_batch.zip",
            mime="application/zip",
            use_container_width=True
        )

    # 选项卡预览
    tab_p, tab_m = st.tabs(["🖼️ 商品预览库", "👤 模特展示库"])
    
    with tab_p:
        if not st.session_state.p_imgs: st.info("暂无生成的商品图")
        cols = st.columns(3)
        for i, (name, data) in enumerate(st.session_state.p_imgs):
            if data:
                with cols[i % 3]:
                    st.image(data, caption=name, use_container_width=True)
                    
    with tab_m:
        if not st.session_state.m_imgs: st.info("暂无生成的模特图")
        cols = st.columns(3)
        for i, (name, data) in enumerate(st.session_state.m_imgs):
            if data:
                with cols[i % 3]:
                    st.image(data, caption=name, use_container_width=True)
