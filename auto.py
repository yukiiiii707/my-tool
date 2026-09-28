import os
os.environ["PYTHONUTF8"] = "1"
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import streamlit as st
import urllib.parse
import json
import requests
from duckduckgo_search import DDGS

# ================= 页面配置与炫酷背景 =================
st.set_page_config(page_title="信息素养终极检索助手", layout="wide")

# 炫酷科技感背景
page_bg_img = """
<style>
.stApp {
    background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: #ffffff !important;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
}
.stTextArea textarea {
    background-color: rgba(255, 255, 255, 0.95) !important;
    color: black !important;
    border-radius: 10px;
}
.stAlert { color: black !important; }
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# ================= 侧边栏配置区（安全与高级感） =================
with st.sidebar:
    st.header("⚙️ 系统配置")
    # 【安全升级】API Key 隐藏输入，避免截图泄露！
    API_KEY = st.text_input("请输入你的 DeepSeek API Key (sk-...)", type="password", help="此信息仅在本地保留，不会被截图记录")
    
    MODEL_NAME = st.selectbox("选择模型", ["deepseek-chat", "deepseek-coder"])
    st.markdown("---")
    if st.button("🗑️ 清空历史对话记忆"):
        st.session_state.history = []
        st.success("历史记录已清空！")

# 初始化历史对话记忆（维度：更智能）
if 'history' not in st.session_state:
    st.session_state.history = []

# 预设各大数据库的检索URL模板
DB_URLS = {
    "知网(CNKI)": "https://kns.cnki.net/kns8/defaultresult/index?dbcode=SCDB&kw={}",
    "万方数据": "https://s.wanfangdata.com.cn/paper?q={}",
    "维普期刊": "http://qikan.cqvip.com/Qikan/Search/Index?key={}",
    "百度学术": "https://xueshu.baidu.com/s?wd={}",
}

BASE_URL = "https://api.deepseek.com/v1"

# ================= 主界面 =================
st.title(" 信息素养答题辅助 Q版")
st.info(" 使用说明：粘贴长篇题干 -> AI自动分拣考点与检索式 -> 多库并行跳转 -> 人工核对作答。")

st.markdown("### 📥 第一步：粘贴题目")
query = st.text_area("请在此处粘贴完整题目（可以是长段落）：", height=150)

if st.button("🚀 一键解析题目并生成检索策略", type="primary", use_container_width=True):
    if not API_KEY:
        st.error("⚠️ 请在左侧侧边栏输入你的 DeepSeek API Key！")
    elif not query:
        st.warning("请先提供题目内容！")
    else:
        with st.spinner("🤖 AI 正在深度拆解题干，生成专属检索策略..."):
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json; charset=utf-8"
            }
            
            # 拼接历史记录
            history_context = "\n".join(st.session_state.history[-3:])

            # 【维度：更智能、更精确】升级版提示词
            prompt1 = f"""
            你是一个顶级的信息素养竞赛专家。请阅读以下题目，仔细分析出：
            1. 核心考点（题目到底在考什么，比如：限定字段是篇名还是主题？是否需要限定时间或来源？）
            2. 目标数据库（知网、万方等）
            3. 专属布尔逻辑检索式（针对知网和万方分别生成最标准的语法）
            
            【历史对话】：
            {history_context}
            
            【题目】：
            {query}
            
            请严格输出以下JSON格式（不要有任何markdown代码块标记，直接输出纯JSON）：
            {{
                "database": "从 [知网(CNKI), 万方数据, 维普期刊, 百度学术] 中选择一个最合适的",
                "keywords": "提取核心检索词，空格分隔",
                "exam_point": "这道题的核心考点和解题思路",
                "cnki_syntax": "知网高级检索式，例如：SU=('人工智能'+'信息素养') AND YE BETWEEN 2022 AND 2025",
                "wanfang_syntax": "万方高级检索式，例如：主题:(人工智能) AND 主题:(信息素养)",
                "year_range": "时间范围，例如：2022-2025，无则填 null",
                "source_type": "来源类别，例如：北大核心, CSSCI，无则填 null"
            }}
            """
            
            try:
                data1 = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt1}], "temperature": 0.1}
                payload1 = json.dumps(data1, ensure_ascii=False).encode('utf-8')
                response1 = requests.post(f"{BASE_URL}/chat/completions", headers=headers, data=payload1)
                response1.raise_for_status()
                result1 = response1.json()
                
                res_text = result1['choices'][0]['message']['content'].replace("```json", "").replace("```", "").strip()
                data = json.loads(res_text)
                
                target_db = data.get("database", "通用网页")
                keywords = data.get("keywords", "")
                exam_point = data.get("exam_point", "无")
                cnki_syntax = data.get("cnki_syntax", "")
                wanfang_syntax = data.get("wanfang_syntax", "")
                
                # 记录历史
                st.session_state.history.append(f"用户: {query}\nAI: {exam_point}")

                # 【维度：更智能】展示考点
                st.success(f"🎯 目标数据库：**{target_db}**")
                st.info(f"🧠 **核心考点剖析**：{exam_point}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if data.get("year_range"): st.warning(f"📅 **时间范围**: {data['year_range']}")
                with col2:
                    if data.get("source_type"): st.warning(f"📌 **来源类别**: {data['source_type']}")

                # 【维度：更精确、更便捷】专属检索式一键复制
                st.markdown("### 📋 专属检索式（点击代码块右上角一键复制）")
                if cnki_syntax:
                    st.markdown("**知网检索式：**")
                    st.code(cnki_syntax, language=None)
                if wanfang_syntax:
                    st.markdown("**万方检索式：**")
                    st.code(wanfang_syntax, language=None)
                    
                st.caption("👆 复制对应数据库的检索式，直接粘贴到该数据库的高级检索框内即可。")

                # 【维度：更快捷】多库并行跳转
                st.markdown("### 🔗 一键直达数据库（多库并行）")
                encoded_kw = urllib.parse.quote(keywords)
                cols = st.columns(4)
                for i, (name, url_template) in enumerate(DB_URLS.items()):
                    with cols[i]:
                        target_url = url_template.format(encoded_kw)
                        st.link_button(f"🚀 {name}", target_url, use_container_width=True)

                # 【维度：更节省时间】结合联网资料给出参考答案
                st.markdown("---")
                st.markdown("### 🤖 AI 参考答案（联网辅助核对）")
                
                search_context = []
                try:
                    results = DDGS().text(keywords, max_results=3)
                    search_context = [res['body'] for res in results]
                except: pass
                
                context_text = "\n".join(search_context)
                
                prompt2 = f"""
                请根据题目和联网参考资料，给出这道题的正确答案和解析。
                题目：{query}
                联网资料：{context_text}
                请直接输出答案和简要说明。
                """
                
                data2 = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt2}], "temperature": 0.3}
                payload2 = json.dumps(data2, ensure_ascii=False).encode('utf-8')
                
                response2 = requests.post(f"{BASE_URL}/chat/completions", headers=headers, data=payload2)
                response2.raise_for_status()
                ans_res = response2.json()
                st.write(ans_res['choices'][0]['message']['content'])

            except Exception as e:
                st.error(f"解析失败，请检查API Key余额或网络连接。错误信息：{e}")
