import streamlit as st
import requests
import traceback
import base64
from datetime import datetime
from PIL import Image

# ==========================================
# 1. 后端逻辑：精准余额计算 + 图片视觉处理
# ==========================================
class OpenRouterBackend:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_Visual_Pro_V33"
        }

    def log(self, level, msg):
        if "logs" not in st.session_state: st.session_state.logs = []
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {msg}")

    def get_balance(self):
        """稳健查询余额，防止页面报错"""
        try:
            # 严格遵循 2026 OpenRouter /key 接口规范
            res = requests.get(f"{self.base_url}/key", headers=self.headers, timeout=5)
            if res.status_code == 200:
                data = res.json().get('data', {})
                # 计算逻辑：额度上限 - 已用额度
                limit = data.get('limit', 0)
                usage = data.get('usage', 0)
                return f"{round(limit - usage, 4)} USD"
            return "Key权限受限"
        except:
            return "网络延迟"

    def encode_image(self, uploaded_file):
        """将上传图片转为符合 OpenAI 视觉规范的 Base64"""
        if uploaded_file:
            return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        return None

    def run_task(self, model_id, prompt, image_file=None, is_gen=False):
        """全能执行器：支持识图文案与绘图生成"""
        url = f"{self.base_url}/chat/completions"
        
        # 构建消息体
        content = [{"type": "text", "text": prompt}]
        img_b64 = self.encode_image(image_file)
        
        # 如果有图且不是纯绘图任务，则加入视觉数据
        if img_b64 and not is_gen:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })
            self.log("INFO", "AI 已接收并开始分析上传的图片")

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": content}]
        }
        if is_gen: payload["modalities"] = ["image"]

        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=90)
            data = res.json()
            if res.status_code == 200:
                msg = data['choices'][0]['message']
                if is_gen:
                    return True, msg.get("images", [None])[0] or msg.get("content", "")
                return True, msg.get("content", "")
            return False, f"API 报错: {data.get('error', {}).get('message', '未知错误')}"
        except Exception:
            return False, f"系统崩溃: {traceback.format_exc().splitlines()[-1]}"

# ==========================================
# 2. 前端 UI：布局对齐截图
# ==========================================
def main():
    st.set_page_config(page_title="饰品专家 V33", layout="wide")
    if "store" not in st.session_state:
        st.session_state.store = {"seo": "", "imgs": []}

    # 获取 Secrets
    key = st.secrets.get("OPENROUTER_API_KEY", "")
    backend = OpenRouterBackend(key)

    # --- 侧边栏：控制台 ---
    with st.sidebar:
        st.title("🛡️ 控制台")
        # 实时余额显示
        st.metric("API 剩余额度", backend.get_balance())
        if st.button("🔄 刷新状态"): st.rerun()
        
        st.divider()
        txt_m = st.selectbox("识图/文案模型", ["google/gemini-2.0-flash-001", "anthropic/claude-3-haiku"])
        img_m = st.selectbox("绘图模型", ["black-forest-labs/flux-schnell", "openai/dall-e-3"])
        
        st.divider()
        st.header("📋 经营信息")
        u_title = st.text_input("1. 原始标题", "心形项链")
        u_cat = st.selectbox("2. 类型", ["项链", "手链", "耳环", "戒指"])
        u_mkt = st.selectbox("3. 市场", ["东南亚", "美国", "英国"])
        u_gen = st.radio("4. 性别", ["女性", "男性"], horizontal=True)

        st.divider()
        # 上传组件：回归并锁定
        u_file = st.file_uploader("🖼️ 上传商品原图", type=["jpg", "png", "jpeg"])
        if u_file:
            st.image(Image.open(u_file), caption="原图已锁定", use_container_width=True)

    # --- 主界面 ---
    st.header("💎 TikTok Shop 饰品全能 AI 专家 (V33 终极修正)")
    
    col_run, col_show = st.columns([1, 1.2])

    with col_run:
        st.subheader("🚀 专家指令")
        if st.button("✨ 1. 识图并优化标题", use_container_width=True):
            with st.spinner("AI 正在观察图片..."):
                prompt = f"请分析图片中的饰品，结合原始标题'{u_title}'，针对{u_mkt}{u_gen}市场，输出 3 个高转化 SEO 标题。"
                ok, res = backend.run_task(txt_m, prompt, image_file=u_file)
                if ok: st.session_state.store["seo"] = res
                else: st.error(res)

        if st.button("🖼️ 2. 生成莫兰迪主图", use_container_width=True):
            with st.spinner("绘图中..."):
                prompt = f"Jewelry photo of {u_cat}, Morandi cream background, 8k"
                ok, res = backend.run_task(img_m, prompt, is_gen=True)
                if ok: st.session_state.store["imgs"].append({"u": res, "m": img_m})
                else: st.error(res)

    with col_show:
        st.subheader("📊 成果展示")
        if st.session_state.store["seo"]:
            st.success("SEO 标题建议已生成")
            st.markdown(st.session_state.store["seo"])
        
        if st.session_state.store["imgs"]:
            grid = st.columns(2)
            for i, item in enumerate(st.session_state.store["imgs"]):
                with grid[i % 2]:
                    st.image(item["u"], caption=f"引擎: {item['m']}")

    # 日志区
    with st.expander("🛠️ 开发者调试日志"):
        logs = "\n".join(st.session_state.get("logs", [])[::-1])
        st.text_area("Log Output", logs, height=200)

if __name__ == "__main__":
    main()
