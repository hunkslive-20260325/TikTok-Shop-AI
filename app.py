import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import json
import datetime

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

ALL_TEXT_MODELS = ["openrouter/auto", "deepseek/deepseek-v3.2", "deepseek/deepseek-chat", "openai/gpt-5.4"]

# ==========================================
# UI 样式定制 (CSS)
# ==========================================
st.set_page_config(page_title="AM JEWELRY V48-20260324", layout="wide")

st.markdown("""
    <style>
    /* 1. 实时日志控制台样式 */
    .console-box {
        height: 180px;
        background-color: #1e1e1e;
        color: #00e676; /* 工业绿 */
        border-radius: 4px;
        padding: 10px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        overflow-y: auto;
        border: 1px solid #333;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    .log-entry { margin-bottom: 4px; border-bottom: 1px solid #2a2a2a; padding-bottom: 2px; }
    .log-ts { color: #888; font-size: 11px; margin-right: 8px; }
    .log-msg-info { color: #00e676; }
    .log-msg-error { color: #ff5252; }

    /* 2. 占位符与侧边栏 */
    .empty-placeholder {
        height: 300px; background-color: #f8f9fa; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        color: #adb5bd; border: 1px dashed #ced4da;
    }
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
    div[data-testid="stFileUploader"] section { padding: 0.5rem; min-height: 80px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 日志记录辅助函数
# ==========================================
def write_log(message, is_error=False):
    if "event_log" not in st.session_state:
        st.session_state.event_log = []
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    msg_class = "log-msg-error" if is_error else "log-msg-info"
    log_html = f'<div class="log-entry"><span class="log-ts">[{ts}]</span><span class="{msg_class}">{message}</span></div>'
    st.session_state.event_log.insert(0, log_html) # 最新的日志在最上面

# ==========================================
# 核心功能逻辑
# ==========================================
def safe_post(url, headers, json_data):
    try:
        res = requests.post(url, headers=headers, json=json_data, timeout=120)
        res_json = res.json()
        return res_json, res_json
    except Exception as e:
        err = {"error": str(e), "status": "failed"}
        return err, err

class JewelryAIEngineV48:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "X-Title": "Jewelry_V48"}

    def run_smart_gen(self, mid_key, p_type, title, gender, category, file):
        mid = ALL_DRAWING_MODELS.get(mid_key)
        b64_in = base64.b64encode(file.getvalue()).decode('utf-8')
        prompt = f"Jewelry photography of {title} {category}, {'female' if gender=='女性' else 'male'} style, 8k."
        payload = {
            "model": mid,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_in}"}}]}],
            "modalities": ["image"]
        }
        return safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, payload)

    def run_seo(self, model_id, title, market, gender, category):
        prompt = f"针对{market}市场生成3个{gender}{category}的SEO标题。"
        return safe_post("https://openrouter.ai/api/v1/chat/completions", self.headers, {"model": model_id, "messages":[{"role":"user","content":prompt}]})

# ==========================================
# 主界面逻辑
# ==========================================
api_key = st.secrets.get("OPENROUTER_API_KEY", "")
engine = JewelryAIEngineV48(api_key)

# 初始化 Session State
if "event_log" not in st.session_state: st.session_state.event_log = []
if "full_history_raw" not in st.session_state: st.session_state.full_history_raw = []
if "seo_res" not in st.session_state: st.session_state.seo_res = ""
if "p_imgs" not in st.session_state: st.session_state.p_imgs = []
if "m_imgs" not in st.session_state: st.session_state.m_imgs = []

with st.sidebar:
    st.subheader("💎 AM JEWELRY V48-20260324")
    u_title = st.text_input("原始标题", "心形项链")
    u_market = st.selectbox("目标市场", ["东南亚","美国","日韩","拉美"])
    u_category = st.selectbox("饰品类型", ["项链","戒指","手链","耳钉","头饰"])
    u_gender = st.radio("目标人群", ["女性","男性"])
    u_file = st.file_uploader("上传图片", type=["jpg","png","jpeg"])
    st.divider()
    c1, c2, c3 = st.columns(3)
    btn_seo, btn_prod, btn_mod = c1.button("✨ 标题"), c2.button("🖼️ 商品"), c3.button("👤 模特")
    u_img_count = st.selectbox("生成数量", [1, 2, 4], index=1)
    model_text = st.selectbox("标题模型", ALL_TEXT_MODELS)
    model_img = st.selectbox("图片模型", list(ALL_DRAWING_MODELS.keys()), index=4)

# --- 右侧布局 ---

# 1. 顶部折叠日志区 (监控中心)
with st.expander("🛠️ 系统运行日志与 API 监控 (Console)", expanded=True):
    # 渲染控制台
    log_content = "".join(st.session_state.event_log) if st.session_state.event_log else "<div>Waiting for command...</div>"
    st.markdown(f'<div class="console-box">{log_content}</div>', unsafe_allow_html=True)
    
    # 打印原始返参历史
    if st.session_state.full_history_raw:
        st.write("**最新 API 响应报文 (JSON):**")
        st.json(st.session_state.full_history_raw[0]) # 只显示最近的一次

# 2. 结果选项卡
t_seo, t_prod, t_mod = st.tabs(["📝 优化标题", "🖼️ 优化商品图", "👤 优化模特图"])

def render_image(img_data, cap, idx):
    try:
        if isinstance(img_data, str) and img_data.startswith("http"): target = img_data
        else:
            if isinstance(img_data, str) and "base64," in img_data: img_data = img_data.split("base64,")[1]
            target = Image.open(BytesIO(base64.b64decode(img_data))).resize((800, 800), Image.Resampling.LANCZOS)
        st.image(target, width=800, caption=cap)
    except Exception as e: st.error(f"Render Error: {e}")

with t_seo:
    if st.session_state.seo_res: st.info(st.session_state.seo_res)
    else: st.markdown('<div class="empty-placeholder">No Data</div>', unsafe_allow_html=True)

with t_prod:
    if st.session_state.p_imgs:
        for i, img in enumerate(st.session_state.p_imgs): render_image(img, f"Prod_{i+1}", f"p_{i}")
    else: st.markdown('<div class="empty-placeholder">No Data</div>', unsafe_allow_html=True)

with t_mod:
    if st.session_state.m_imgs:
        for i, img in enumerate(st.session_state.m_imgs): render_image(img, f"Mod_{i+1}", f"m_{i}")
    else: st.markdown('<div class="empty-placeholder">No Data</div>', unsafe_allow_html=True)

# --- 执行逻辑 ---

if btn_seo:
    write_log(f"正在调用 [{model_text}] 优化标题...")
    data, raw = engine.run_seo(model_text, u_title, u_market, u_gender, u_category)
    st.session_state.full_history_raw.insert(0, raw)
    st.session_state.seo_res = data.get('choices',[{}])[0].get('message',{}).get('content', "生成失败")
    write_log("标题生成成功。")
    st.rerun()

if (btn_prod or btn_mod) and u_file:
    target_key = "p_imgs" if btn_prod else "m_imgs"
    st.session_state[target_key] = []
    
    write_log(f"开始批量图片生成任务 (数量: {u_img_count})...")
    
    with st.status("🚀 引擎处理中...") as status:
        for i in range(u_img_count):
            write_log(f"正在处理第 {i+1} 张图片...")
            data, raw = engine.run_smart_gen(model_img, ("商品图" if btn_prod else "模特图"), u_title, u_gender, u_category, u_file)
            st.session_state.full_history_raw.insert(0, raw)
            
            img_url = data.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
            if img_url:
                st.session_state[target_key].append(img_url)
                write_log(f"第 {i+1} 张图片成功接收。")
            else:
                write_log(f"第 {i+1} 张图片失败: {data.get('error', '未知错误')}", is_error=True)
        
        status.update(label="生成序列结束", state="complete", expanded=False)
    
    write_log("所有任务已完成。")
    st.rerun()
