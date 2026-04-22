import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import re
import random
import zipfile  # 用于批量下载

# ==========================================
# 模型库与配置
# ==========================================
ALL_DRAWING_MODELS = {
    "openrouter/auto": "openrouter/auto",
    "google/gemini-3.1-flash-image-preview": "google/gemini-3.1-flash-image-preview",
    "google/gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
    "openai/gpt-5-image": "openai/gpt-5-image",
    "black-forest-labs/flux.2-pro": "black-forest-labs/flux.2-pro"
}

ALL_TEXT_MODELS = [
    "openrouter/auto",
    "deepseek/deepseek-v3.2",
    "openai/gpt-5.4",
    "google/gemini-3.1-pro-preview"
]

# 1. 饰品类型修改 (20260422 更新)
JEWELRY_CATEGORIES = [
    "项链", "耳环", "脚链", "戒指", "手环与手链", 
    "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装"
]

# ------------------------------------------
# 安全请求与辅助函数
# ------------------------------------------
def safe_post(url, headers, json_data, timeout=60):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": f"请求失败: {e}"}

def get_image_bytes(img_data):
    """统一处理不同格式的图片数据转为 Bytes"""
    if isinstance(img_data, str) and img_data.startswith("http"):
        res = requests.get(img_data)
        return res.content
    elif isinstance(img_data, str) and "base64," in img_data:
        return base64.b64decode(img_data.split(",")[1])
    elif isinstance(img_data, str):
        return base64.b64decode(img_data)
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
            "X-Title": "Jewelry_Batch_V48"
        }
  
    def run_smart_gen(self, mid_key, p_type, gender, category, market, file_bytes):
        try:
            mid = ALL_DRAWING_MODELS.get(mid_key)
            b64_in = base64.b64encode(file_bytes).decode('utf-8')

            # 材质与部位增强映射
            mapping = {"项链": "Necklace", "耳环": "Earrings", "脚链": "Anklet", "戒指": "Ring", "手环与手链": "Bracelet/Bangle", "首饰套装": "Jewelry Set"}
            en_category = mapping.get(category, "Jewelry")
            
            market_vibes = {"东南亚": "warm champagne and soft cream", "美国": "cool minimalist grey", "中东": "royal gold"}
            selected_vibe = market_vibes.get(market, "soft neutral tones")

            if p_type == "模特图":
                prompt = f"Professional model wearing {en_category}, {gender}, high fashion photography, {selected_vibe} studio background, 8k."
            else:
                prompt = f"Premium macro product photography of {en_category}, displayed on minimalist stone, {selected_vibe} theme, 8k, razor sharp."

            payload = {
                "model": mid,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}]}],
                "modalities": ["image"]
            }
            res_json = safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload, timeout=120)
            return res_json.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
        except:
            return None

# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="AM JEWELRY V48 批量版", layout="wide")

api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# Session State 初始化
if "p_imgs" not in st.session_state: st.session_state.p_imgs = [] # 存储格式 [(filename, data), ...]
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

with st.sidebar:
    st.subheader("💎 批量生成控制台")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美","中东","非洲"])
    u_category = st.selectbox("饰品类型", JEWELRY_CATEGORIES)
    u_gender = st.radio("目标人群", ["女性","男性"])
    
    # 2. 支持多图上传 (最多10张)
    u_files = st.file_uploader("上传图片 (支持多选，上限10张)", type=["jpg","png","jpeg"], accept_multiple_files=True)
    if u_files and len(u_files) > 10:
        st.warning("已超过10张，系统将仅处理前10张。")
        u_files = u_files[:10]

    st.divider()
    u_img_count = st.selectbox("每张图生成的变体数量", [1, 2, 4], index=0)
    model_img = st.selectbox("优化图片模型", list(ALL_DRAWING_MODELS.keys()), index=4)
    
    c1, c2 = st.columns(2)
    btn_prod = c1.button("批量生成商品图", use_container_width=True)
    btn_mod = c2.button("批量生成模特图", use_container_width=True)

# --- 核心逻辑：批量生成 ---
log_area = st.empty()

def process_batch(mode):
    if not u_files:
        st.error("请先上传图片！")
        return
    
    results = []
    total_tasks = len(u_files) * u_img_count
    current_task = 0
    
    for f_idx, file_obj in enumerate(u_files):
        file_bytes = file_obj.getvalue()
        base_name = file_obj.name.split('.')[0]
        
        for v_idx in range(u_img_count):
            current_task += 1
            log_area.info(f"正在处理: {file_obj.name} (进度: {current_task}/{total_tasks})")
            
            res = engine.run_smart_gen(model_img, mode, u_gender, u_category, u_market, file_bytes)
            if res:
                # 记录文件名和图片数据
                results.append((f"{mode}_{base_name}_v{v_idx+1}.png", res))
    
    if mode == "商品图": st.session_state.p_imgs = results
    else: st.session_state.m_imgs = results
    log_area.success(f"✅ {mode}批量处理完成！共生成 {len(results)} 张。")

if btn_prod: process_batch("商品图")
if btn_mod: process_batch("模特图")

# --- 批量下载函数 ---
def create_zip(image_list):
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for filename, data in image_list:
            img_bytes = get_image_bytes(data)
            if img_bytes:
                z.writestr(filename, img_bytes)
    return buf.getvalue()

# --- 展示与批量下载区 ---
if st.session_state.p_imgs or st.session_state.m_imgs:
    st.divider()
    col_dl1, col_dl2 = st.columns(2)
    
    if st.session_state.p_imgs:
        zip_data = create_zip(st.session_state.p_imgs)
        col_dl1.download_button("📥 一键下载所有商品图 (ZIP)", data=zip_data, file_name="batch_products.zip", mime="application/zip")
        
    if st.session_state.m_imgs:
        zip_data = create_zip(st.session_state.m_imgs)
        col_dl2.download_button("📥 一键下载所有模特图 (ZIP)", data=zip_data, file_name="batch_models.zip", mime="application/zip")

    # 预览
    t1, t2 = st.tabs(["🖼️ 商品预览", "👤 模特预览"])
    with t1:
        cols = st.columns(3)
        for idx, (name, data) in enumerate(st.session_state.p_imgs):
            with cols[idx % 3]:
                st.image(data, caption=name, use_container_width=True)
    with t2:
        cols = st.columns(3)
        for idx, (name, data) in enumerate(st.session_state.m_imgs):
            with cols[idx % 3]:
                st.image(data, caption=name, use_container_width=True)
