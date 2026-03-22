import streamlit as st
import requests
import traceback
import time
from datetime import datetime
from PIL import Image
import io

# ==========================================
# 1. 后端核心类：带日志与余额监控
# ==========================================
class OpenRouterManager:
    def __init__(self):
        self.api_key = st.secrets.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://streamlit.io",
            "X-Title": "Jewelry_AI_Pro_V30"
        }

    def log_event(self, level, message):
        """记录服务日志到 session_state"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        if "service_logs" not in st.session_state:
            st.session_state.service_logs = []
        st.session_state.service_logs.append(entry)

    def get_balance(self):
        """查询 Key 余额"""
        try:
            res = requests.get(f"{self.base_url}/key", headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # 2026 官方返回结构：data['data']['usage'] 或 'limit'
                balance = data.get('data', {}).get('limit', 0) - data.get('data', {}).get('usage', 0)
                return round(balance, 4)
            return "N/A"
        except Exception:
            return "Error"

    def execute_task(self, model_id, messages, is_image=False):
        """通用执行器，带详细报错定位"""
        if not self.api_key:
            return False, "⚠️ 未配置 OPENROUTER_API_KEY", None

        payload = {"model": model_id, "messages": messages}
        if is_image:
            payload["modalities"] = ["image"] # 对齐 2026 绘图规范

        start_time = time.time()
        try:
            self.log_event("INFO", f"开始调用模型: {model_id}")
            response = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=90)
            
            # 增加严谨的 HTTP 状态校验
            if response.status_code != 200:
                err_raw = response.text
                self.log_event("ERROR", f"API 返回非200状态: {err_raw}")
                return False, f"API 状态错误 ({response.status_code}): {err_raw}", model_id

            data = response.json()
            if "choices" in data:
                msg = data['choices'][0]['message']
                # 处理图片
                if is_image:
                    img_data = msg.get("images", [None])[0] or msg.get("content", "")
                    if len(str(img_data)) < 100 and not str(img_data).startswith("http"):
                        return False, f"模型未返回有效图片，仅返回文本: {img_data}", model_id
                    self.log_event("SUCCESS", f"图片生成成功，耗时 {round(time.time()-start_time, 2)}s")
                    return True, img_data, model_id
                
                self.log_event("SUCCESS", "文案生成成功")
                return True, msg.get("content", ""), model_id
            
            return False, f"数据结构异常: {str(data)}", model_id

        except Exception as e:
            # 核心：捕获具体代码位置
            full_error = traceback.format_exc()
            self.log_event("CRITICAL", f"代码执行崩溃:\n{full_error}")
            return False, f"程序内部错误，请检查日志末尾。\n类型: {type(e).__name__}", model_id

# ==========================================
# 2. 前端 UI 层
# ==========================================
def main():
    st.set_page_config(page_title="饰品专家 V30", layout="wide", initial_sidebar_state="expanded")
    
    # 初始化
    if "data_store" not in st.session_state:
        st.session_state.data_store = {"seo": "", "imgs": []}
    if "service_logs" not in st.session_state:
        st.session_state.service_logs = [f"[{datetime.now()}] 系统初始化完毕"]

    mgr = OpenRouterManager()

    # --- 侧边栏 ---
    with st.sidebar:
        st.title("🛡️ 控制台")
        
        # 余额反显
        with st.container(border=True):
            col_b1, col_b2 = st.columns([2, 1])
            col_b1.metric("API 余额 (USD)", mgr.get_balance())
            if col_b2.button("🔄 刷新"): st.rerun()

        st.divider()
        st.header("⚙️ 模型配置")
        txt_mod = st.selectbox("文案模型", ["google/gemini-2.0-flash-001", "deepseek/deepseek-chat"])
        img_mod = st.selectbox("绘图模型", ["black-forest-labs/flux-schnell", "openai/dall-e-3", "google/imagen-3"])
        
        st.divider()
        st.header("📋 任务参数")
        u_title = st.text_input("1. 原始标题", value="S925银心形项链")
        u_cat = st.selectbox("2. 商品类型", ["项链", "手链", "耳环", "戒指"])
        u_mkt = st.selectbox("3. 目标市场", ["东南亚总区", "美国", "英国"])
        u_gen = st.radio("4. 目标性别趋势", ["女性", "男性"], horizontal=True)

    # --- 主界面 ---
    st.header("💎 TikTok Shop 饰品全能 AI 专家 (监控版)")
    
    t1, t2, t3 = st.tabs(["🚀 任务执行", "📜 服务日志", "📦 历史记录"])

    with t1:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            if st.button("✨ 执行：标题 SEO 优化", use_container_width=True):
                with st.spinner("请求中..."):
                    ok, res, _ = mgr.execute_task(txt_mod, [{"role": "user", "content": f"优化饰品标题: {u_title}"}])
                    if ok: st.session_state.data_store["seo"] = res
                    else: st.error(res)
            
            if st.button("🖼️ 执行：商品图优化", use_container_width=True):
                with st.spinner("绘图中..."):
                    ok, res, mod = mgr.execute_task(img_mod, [{"role": "user", "content": f"Jewelry photo of {u_cat}"}], is_image=True)
                    if ok: st.session_state.data_store["imgs"].append({"u": res, "m": mod, "t": "主图"})
                    else: st.error(res)

            if st.button("👤 执行：模特图优化", use_container_width=True):
                with st.spinner("生成模特..."):
                    ok, res, mod = mgr.execute_task(img_mod, [{"role": "user", "content": f"Model wearing {u_cat}"}], is_image=True)
                    if ok: st.session_state.data_store["imgs"].append({"u": res, "m": mod, "t": "模特图"})
                    else: st.error(res)

        with c2:
            if st.session_state.data_store["seo"]:
                st.info("SEO 建议结果")
                st.markdown(st.session_state.data_store["seo"])
            
            if st.session_state.data_store["imgs"]:
                grid = st.columns(2)
                for i, item in enumerate(st.session_state.data_store["imgs"]):
                    with grid[i % 2]:
                        st.image(item["u"], caption=f"{item['t']} ({item['m']})")

    with t2:
        st.subheader("🛠️ 实时服务日志")
        log_text = "\n".join(st.session_state.service_logs[::-1]) # 倒序显示最新内容
        st.text_area("Log Output", log_text, height=400)
        st.download_button("📥 下载完整日志", data=log_text, file_name=f"service_log_{datetime.now().strftime('%m%d_%H%M')}.txt")

    with t3:
        if st.button("🗑️ 清空当前所有缓存"):
            st.session_state.data_store = {"seo": "", "imgs": []}
            st.rerun()

if __name__ == "__main__":
    main()
