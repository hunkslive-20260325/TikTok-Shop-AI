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
    /* 升级版多行日志控制台 */
    .console-box {
        height: 200px;
        background-color: #212529; /* 深色工业背景 */
        color: #00ff41; /* 经典黑客绿文字 */
        border-radius: 5px;
        padding: 12px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        overflow-y: auto;
        border: 1px solid #495057;
        line-height: 1.5;
        margin-bottom: 20px;
    }
    .log-time { color: #888; margin-right: 10px; }
    .log-info { color: #0d6efd; }
    .log-success { color: #28a745; }
    .log-error { color: #dc3545; }

    /* 选项卡占位符 */
    .empty-placeholder {
        height: 300px;
        background-color: #f8f9fa;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #adb5bd;
        border: 1px dashed #ced4da;
    }

    /* 侧边栏布局 */
    div[data-testid="stWidgetLabel"] + div { flex-direction: row !important; }
    div[data-testid="stFileUploader"] section { padding: 0.5rem; min-height: 80px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 辅助函数：日志追加
# ==========================================
def add_log(message, type="info"):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    if "full_logs" not in st.session_state:
        st.session_state.full_logs = []
    
    color_class = f"log-{type}"
    log_entry = f'<div><span class="log-time">[{now}]</span><span class="{color_class}">{message}</span></div>'
    st.session_state.full_logs.append(log_entry)
    # 保持最近 50 条记录
    if len(st.session_state.full_logs) > 50:
        st.session_state.full_logs.pop(0)

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
if "full_logs" not in st.session_state: st.session_state.full_logs = ['<div><span class="log-time">[System]</span><span class="log-info">初始化完成，准备就绪。</span></div>']
if "raw_response" not in st.session_state: st.session_state.raw_response = None
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

# 1. 扩容后的日志监控台
log_html = f'<div class="console-box">{"".join(st.session_state.full_logs)}</div>'
st.markdown(log_html, unsafe_allow_html=True)

# 2. 原始返参 (Debug Mode)
if st.session_state.raw_response:
    with st.expander("🛠️ 查看最近一次 API 原始响应报文 (JSON)", expanded=False):
        st.json(st.session_state.raw_response)

# 3. 结果展示选项卡
t_seo, t_prod, t_mod = st.tabs(["📝 优化标题", "🖼️ 优化商品图", "👤 优化模特图"])

# (展示逻辑保持不变，确保 2026 width 参数正确)
def process_and_display(img_data, caption, idx):
    try:
        if isinstance(img_data, str) and img_data.startswith("http"): target = img_data
        else:
            if isinstance(img_data, str) and "base64," in img_data: img_data = img_data.split("base64,")[1]
            target = Image.open(BytesIO(base64.b64decode(img_bytes))).resize((800, 800), Image.Resampling.LANCZOS)
        st.image(target, width=800, caption=caption)
    except Exception as e: st.error(f"显示失败: {e}")

with t_seo:
    if st.session_state.seo_res: st.info(st.session_state.seo_res)
    else: st.markdown('<div class="empty-placeholder">暂无标题</div>', unsafe_allow_html=True)

with t_prod:
    if st.session_state.p_imgs:
        for i, img in enumerate(st.session_state.p_imgs): process_and_display(img, f"Prod_{i+1}", f"p_{i}")
    else: st.markdown('<div class="empty-placeholder">暂无商品图</div>', unsafe_allow_html=True)

with t_mod:
    if st.session_state.m_imgs:
        for i, img in enumerate(st.session_state.m_imgs): process_and_display(img, f"Mod_{i+1}", f"m_{i}")
    else: st.markdown('<div class="empty-placeholder">暂无模特图</div>', unsafe_allow_html=True)

# --- 执行逻辑 ---
if btn_seo:
    add_log("开始优化标题模型请求...", "info")
    data, raw = engine.run_seo(model_text, u_title, u_market, u_gender, u_category)
    st.session_state.seo_res = data.get('choices',[{}])[0].get('message',{}).get('content', "生成失败")
    st.session_state.raw_response = raw
    add_log("标题生成成功！已更新至选项卡。", "success")
    st.rerun()

if (btn_prod or btn_mod) and u_file:
    key = "p_imgs" if btn_prod else "m_imgs"
    st.session_state[key] = []
    add_log(f"启动批量任务：生成 {u_img_count} 张{'商品' if btn_prod else '模特'}图", "info")
    
    with st.status("工作站运行中...") as status:
        all_raws = []
        for i in range(u_img_count):
            msg = f"正在请求第 {i+1} 张图片参数..."
            add_log(msg, "info")
            st.write(msg)
            
            data, raw = engine.run_smart_gen(model_img, ("商品图" if btn_prod else "模特图"), u_title, u_gender, u_category, u_file)
            img = data.get('choices', [{}])[0].get('message', {}).get('images', [None])[0]
            
            if img:
                st.session_state[key].append(img)
                add_log(f"第 {i+1} 张生成成功。", "success")
            else:
                add_log(f"第 {i+1} 张生成失败，请查阅下方 JSON。", "error")
            all_raws.append(raw)
            
        st.session_state.raw_response = {"batch_results": all_raws}
        status.update(label="任务完成", state="complete")
    
    add_log("全量生成序列结束。", "success")
    st.rerun()
