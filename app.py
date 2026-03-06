import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="工厂流程审核评分系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.dialog("查看原图")
def show_full_image(image_path):
    st.image(image_path, use_container_width=True)

def inject_custom_css():
    st.markdown("""
        <style>
        [data-testid="stFileUploadDropzone"] div div { display: none !important; }
        [data-testid="stFileUploadDropzone"] { padding: 0px !important; min-height: 45px !important; border: 1px dashed #ccc; }
        .stPopover [data-testid="stBaseButton-secondary"] { width: 100%; }
        [data-testid="stExpander"] [data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
        hr { margin: 0.4rem 0 !important; }
        </style>
    """, unsafe_allow_html=True)
# ==================== 字体配置 - 使用上传的SimSun.ttf ====================
def setup_chinese_font():
    font_path = os.path.join(os.path.dirname(__file__), "SimSun.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SimSun', font_path))
        return 'SimSun'
    else:
        st.warning("未找到SimSun.ttf字体文件，PDF中文可能显示异常")
        return 'Helvetica'

CHINESE_FONT = setup_chinese_font()

# ==================== 数据初始化 ====================
DATA_DIR = "data"
MEDIA_DIR = os.path.join(DATA_DIR, "media") # 新增：图片存储目录
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# ==================== 评分体系数据模型 ====================
class DataStore:
    def __init__(self):
        self.users = [{"id": 1, "username": "admin", "password": "admin123", "name": "管理员"}]
        self.factories = [{"id": 1, "name": "深圳XX服装厂"}, {"id": 2, "name": "广州XX制衣厂"}]
        self.modules = self._init_modules()
        self.evaluations = self._load_evaluations()
        self.total_system_score = 177

    def _init_modules(self):
        return {
            "纸样、样衣制作": {
                "total_score": 14,
                "sub_modules": {
                    "纸样开发标准": {
                        "total_score": 6,
                        "items": [
                            {"id": "p1_1", "name": "使用CAD软件制作/修改纸样", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p1_2", "name": "缝份清晰标记应合规", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p1_3", "name": "布纹线，剪口标注合规并清晰", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p1_4", "name": "放码标准（尺寸增量）遵守客户要求，并文档化", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p1_5", "name": "技术包（Tech Pack）应明确标注尺寸表、工艺说明与特殊工艺说明", "score": 3, "is_key": True, "details": [], "comment": ""},
                        ]
                    },
                    "版本控制与追溯性": {
                        "total_score": 3,
                        "items": [
                            {"id": "p2_1", "name": "纸样版本控制系统（确保最新、准确、可追溯）", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p2_2", "name": "文档记录：纸样历史、修订、批准", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p2_3", "name": "物理纸样及数字备份的安全存储", "score": 1, "is_key": False, "details": [], "comment": ""},
                        ]
                    }
                }
            },
            "面辅料品质控制": {
                "total_score": 34,
                "sub_modules": {
                    "面料仓库检查": {
                        "total_score": 5,
                        "items": [
                            {
                                "id": "m1_1",
                                "name": "合格/不合格品/待检标识应明确，分开堆放",
                                "score": 1,
                                "is_key": False,
                                "details": ["标识不明确", "未分开堆放"],
                                "comment": ""
                            },
                            {
                                "id": "m1_2",
                                "name": "面料不可“井”字堆放，高度不可过高（建议<1.5m）",
                                "score": 1,
                                "is_key": False,
                                "details": ["面料井字堆放", "堆放高度过高"],
                                "comment": ""
                            },
                            {
                                "id": "m1_3",
                                "name": "不同颜色及批次（缸号）分开堆放",
                                "score": 1,
                                "is_key": False,
                                "details": [],
                                "comment": ""
                            },
                            {
                                "id": "m1_4",
                                "name": "托盘存放不靠墙、不靠窗、避光储存及防潮防霉",
                                "score": 1,
                                "is_key": False,
                                "details": ["靠墙", "靠窗", "未避光储存", "未防潮防霉"],
                                "comment": ""
                            },
                            {
                                "id": "m1_5",
                                "name": "温湿度计及记录（湿度<65%）",
                                "score": 1,
                                "is_key": True,
                                "details": ["无温湿度计", "无记录", "湿度超标"],
                                "comment": "监控湿度的变化，便于采取相应的解决方案（如抽湿）"
                            },
                        ]
                    },
                    "面料入库记录": {
                        "total_score": 2,
                        "items": [
                            {
                                "id": "m2_1",
                                "name": "面料厂验布记录/测试记录/缸差布",
                                "score": 1,
                                "is_key": False,
                                "details": ["无验布记录", "无测试记录", "无缸差布"],
                                "comment": "测试记录和缸差布可预防面料品质问题和色差问题"
                            },
                            {
                                "id": "m2_2",
                                "name": "入库单（卷数，米数，克重等）",
                                "score": 1,
                                "is_key": False,
                                "details": ["无入库单", "信息不全"],
                                "comment": ""
                            },
                        ]
                    }
                }
            }
        }

    def _load_evaluations(self):
        f = os.path.join(DATA_DIR, "evaluations.json")
        return json.load(open(f, 'r', encoding='utf-8')) if os.path.exists(f) else []

    def _save_evaluations(self):
        with open(os.path.join(DATA_DIR, "evaluations.json"), 'w', encoding='utf-8') as f:
            json.dump(self.evaluations, f, ensure_ascii=False, indent=2)

    def add_evaluation(self, ev):
        ev['id'] = len(self.evaluations) + 1
        ev['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.evaluations.append(ev)
        self._save_evaluations()
        return ev

# ==================== 初始化 ====================
db = DataStore()

# ==================== PDF生成工具 ====================
def generate_pdf(evaluation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    chinese_styles = {
        'Heading1': ParagraphStyle(
            'CustomHeading1', parent=styles['Heading1'], fontName=CHINESE_FONT,
            fontSize=18, spaceAfter=20, alignment=1
        ),
        'Heading2': ParagraphStyle(
            'CustomHeading2', parent=styles['Heading2'], fontName=CHINESE_FONT,
            fontSize=14, spaceAfter=12
        ),
        'Normal': ParagraphStyle(
            'CustomNormal', parent=styles['Normal'], fontName=CHINESE_FONT,
            fontSize=12, spaceAfter=6
        ),
        'TotalScore': ParagraphStyle(
            'CustomTotalScore', parent=styles['Normal'], fontName=CHINESE_FONT,
            fontSize=16, spaceAfter=12, textColor='red', bold=True
        ),
        'KeyProcess': ParagraphStyle(
            'CustomKeyProcess', parent=styles['Normal'], fontName=CHINESE_FONT,
            fontSize=12, spaceAfter=6, textColor='#FF8C00'
        )
    }

    elements = []
    elements.append(Paragraph("工厂流程审核报告", chinese_styles['Heading1']))
    factory_name = next(f['name'] for f in db.factories if f['id'] == evaluation['factory_id'])
    elements.extend([
        Paragraph(f"工厂名称：{factory_name}", chinese_styles['Normal']),
        Paragraph(f"评估日期：{evaluation['eval_date']}", chinese_styles['Normal']),
        Paragraph(f"评估人员：{evaluation['evaluator']}", chinese_styles['Normal']),
        Paragraph(f"工厂总分：{evaluation['overall_percent']:.2f}%", chinese_styles['TotalScore']),
        Spacer(1, 12)
    ])

    elements.append(Paragraph("一、存在问题汇总", chinese_styles['Heading2']))
    elements.append(Paragraph("经评估，请该工厂注意以下方面：", chinese_styles['Normal']))

    key_items = []
    other_items = []

    for mod_name in evaluation['selected_modules']:
        mod = db.modules[mod_name]
        for sub_name, sub_mod in mod['sub_modules'].items():
            for item in sub_mod['items']:
                res = evaluation['results'].get(item['id'], {})
                if not res.get('is_checked', False):
                    item_text = f"【{mod_name}-{sub_name}】{item['name']}"
                    if res.get('details'):
                        item_text += f"（问题详情：{', '.join(res['details'])}）"
                    if item['comment']:
                        item_text += f" 改进建议：{item['comment']}"

                    if item.get('is_key', False):
                        key_items.append(item_text)
                    else:
                        other_items.append(item_text)

    if key_items:
        elements.append(Paragraph("（一）重点工序", chinese_styles['KeyProcess']))
        for i, text in enumerate(key_items, 1):
            elements.append(Paragraph(f"{i}. {text}", chinese_styles['KeyProcess']))
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("（一）重点工序：本次评估未发现重点工序问题", chinese_styles['KeyProcess']))
        elements.append(Spacer(1, 6))

    if other_items:
        elements.append(Paragraph("（二）其他工序", chinese_styles['Normal']))
        for i, text in enumerate(other_items, 1):
            elements.append(Paragraph(f"{i}. {text}", chinese_styles['Normal']))
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("（二）其他工序：本次评估未发现其他工序问题", chinese_styles['Normal']))
        elements.append(Spacer(1, 6))

    elements.append(Paragraph("二、评估者评论", chinese_styles['Heading2']))
    if evaluation['comments']:
        elements.append(Paragraph(evaluation['comments'], chinese_styles['Normal']))
    else:
        elements.append(Paragraph("无评论", chinese_styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================== 页面路由 ====================
def main():
    if 'user' not in st.session_state:
        st.title("工厂流程审核评分系统")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            if st.button("登录", type="primary"):
                if next((u for u in db.users if u['username'] == username and u['password'] == password), None):
                    st.session_state['user'] = username
                    st.rerun()
                else:
                    st.error("账号或密码错误")
        return

    st.sidebar.title(f"欢迎，{st.session_state['user']}")
    if st.sidebar.button("退出登录"):
        del st.session_state['user']
        if 'eval_results' in st.session_state:
            del st.session_state['eval_results']
        st.rerun()

    menu = st.sidebar.radio("功能菜单", ["开始评估", "历史记录", "对比分析"])

    if menu == "开始评估":
        start_evaluation()
    elif menu == "历史记录":
        show_history()
    elif menu == "对比分析":
        st.subheader("对比分析")
        st.info("功能开发中...")

# ==================== 核心评估页面（一键全选/清空 修复版） ====================
# ==================== 核心评估页面（优化版：拍照/缩略图/大图） ====================
def start_evaluation():
    inject_custom_css()
    st.subheader("工厂流程评估")

    # 定义系统固定总分分母
    SYSTEM_TOTAL_FIXED = 177

    # --- 1. 基础配置 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        factory_id = st.selectbox("评估工厂", [(f['id'], f['name']) for f in db.factories], format_func=lambda x: x[1])[0]
    with col2:
        eval_date = st.date_input("评估日期", date.today())
    with col3:
        evaluator = st.text_input("评估员", value=st.session_state.get('user', ''))
    with col4:
        eval_type = st.selectbox("审核性质", ["常规审核", "整改复查"])

    all_modules = list(db.modules.keys())
    selected_modules = all_modules if eval_type == "常规审核" else st.multiselect("选择复查模块", all_modules)
    
    if not selected_modules:
        st.info("请选择上方模块开始评分")
        return

    # --- 2. 状态初始化 ---
    if 'eval_results' not in st.session_state:
        st.session_state.eval_results = {}
    
    for mod_name in selected_modules:
        for sub_mod in db.modules[mod_name]['sub_modules'].values():
            for it in sub_mod['items']:
                if it['id'] not in st.session_state.eval_results:
                    st.session_state.eval_results[it['id']] = {"is_checked": False, "details": [], "image_path": None}

    # 一键操作逻辑
    col_a, col_b, _ = st.columns([1, 1, 6])
    with col_a:
        if st.button("✅ 一键全选"):
            for mod_name in selected_modules:
                for sub in db.modules[mod_name]['sub_modules'].values():
                    for it in sub['items']:
                        st.session_state.eval_results[it['id']]["is_checked"] = True
                        st.session_state[f"chk_{it['id']}"] = True
            st.rerun()
    with col_b:
        if st.button("❌ 一键清空"):
            for mod_name in selected_modules:
                for sub in db.modules[mod_name]['sub_modules'].values():
                    for it in sub['items']:
                        st.session_state.eval_results[it['id']]["is_checked"] = False
                        st.session_state[f"chk_{it['id']}"] = False
            st.rerun()

    st.divider()

    # --- 3. 核心评分循环 ---
    total_system_earned = 0

    for mod_name in selected_modules:
        mod_data = db.modules[mod_name]
        
        # 计算该模块实时总分
        mod_earned = 0
        for sub in mod_data['sub_modules'].values():
            mod_earned += sum(it['score'] for it in sub['items'] if st.session_state.get(f"chk_{it['id']}", False))
        
        # 换算百分比 (基于177)
        mod_score_percent = (mod_earned / SYSTEM_TOTAL_FIXED * 100)
        total_system_earned += mod_earned

        # 模块层：静态标题，防止勾选后自动收起
        with st.expander(f"📦：{mod_name}", expanded=True):
            # 仅显示百分比
            st.write(f"**模块得分: :blue[{mod_score_percent:.1f}%]**")
            
            for sub_name, sub_mod in mod_data['sub_modules'].items():
                # 计算子项实时总分
                sub_earned = sum(it['score'] for it in sub_mod['items'] if st.session_state.get(f"chk_{it['id']}", False))
                # 换算百分比 (基于177)
                sub_score_percent = (sub_earned / SYSTEM_TOTAL_FIXED * 100)

                # 子项层：使用固定 Key 锁定展开状态
                sub_key = f"exp_{factory_id}_{mod_name}_{sub_name}"
                with st.expander(f"🔹 {sub_name}", expanded=False, key=sub_key):
                    # 仅显示百分比
                    st.write(f"**子项得分: :green[{sub_score_percent:.1f}%]**")
                    st.write("") 

                    for it in sub_mod['items']:
                        it_id = it['id']
                        c1, c2, c3 = st.columns([0.65, 0.2, 0.15])
                        
                        with c1:
                            # 关键项全橙色 (包括文字和括号)
                            label = f":orange[{it['name']} (关键项)]" if it.get('is_key') else it['name']
                            is_checked = st.checkbox(label, key=f"chk_{it_id}")
                            st.session_state.eval_results[it_id]['is_checked'] = is_checked

                        with c2:
                            with st.popover("📸 拍照上传"):
                                img_file = st.file_uploader("拍照", type=['jpg','png','jpeg'], key=f"up_{it_id}", label_visibility="collapsed")
                                if img_file:
                                    file_ext = img_file.name.split('.')[-1]
                                    file_name = f"{it_id}_{datetime.now().strftime('%H%M%S')}.{file_ext}"
                                    save_path = os.path.join(MEDIA_DIR, file_name)
                                    with open(save_path, "wb") as f:
                                        f.write(img_file.getbuffer())
                                    st.session_state.eval_results[it_id]['image_path'] = save_path
                                    st.rerun()

                        with c3:
                            img_path = st.session_state.eval_results[it_id].get('image_path')
                            if img_path and os.path.exists(img_path):
                                st.image(img_path, width=40)
                                sc1, sc2 = st.columns(2)
                                with sc1:
                                    if st.button("👁️", key=f"v_{it_id}"): show_full_image(img_path)
                                with sc2:
                                    if st.button("🗑️", key=f"d_{it_id}"):
                                        if os.path.exists(img_path): os.remove(img_path)
                                        st.session_state.eval_results[it_id]['image_path'] = None
                                        st.rerun()

                        if not is_checked:
                            if it['details']:
                                st.session_state.eval_results[it_id]['details'] = st.multiselect(
                                    "缺陷选择", it['details'],
                                    default=st.session_state.eval_results[it_id]['details'],
                                    key=f"det_{it_id}", label_visibility="collapsed"
                                )
                            if it['comment']:
                                st.caption(f"💡 建议：{it['comment']}")
                        st.divider()

    # --- 4. 总结区 ---
    st.subheader("评估汇总")
    overall_percent = (total_system_earned / SYSTEM_TOTAL_FIXED * 100)
    st.metric("总得分率", f"{overall_percent:.2f}%")
    comments = st.text_area("综合评估意见", height=80)

    if st.button("💾 保存并生成报告", type="primary", use_container_width=True):
        ev_data = {
            "factory_id": factory_id, 
            "evaluator": evaluator, 
            "eval_date": eval_date.strftime("%Y-%m-%d"),
            "eval_type": eval_type, 
            "selected_modules": selected_modules, 
            "overall_percent": overall_percent,
            "results": st.session_state.eval_results, 
            "comments": comments
        }
        saved = db.add_evaluation(ev_data)
        st.success(f"保存成功！当前总得分率：{overall_percent:.2f}%")
# ==================== 历史记录 ====================
def show_history():
    st.subheader("历史记录")
    if not db.evaluations:
        st.info("暂无记录")
        return
    for ev in reversed(db.evaluations):
        factory_name = next(f['name'] for f in db.factories if f['id'] == ev['factory_id'])
        with st.expander(f"📅 {ev['eval_date']} | {factory_name} | {ev['eval_type']}"):
            c1,c2,c3 = st.columns([2,2,1])
            with c1: st.write(f"评估人：{ev['evaluator']}")
            with c2: st.write(f"得分：{ev['overall_percent']:.2f}%")
            with c3:
                pdf_buf = generate_pdf(ev)
                st.download_button("下载报告", pdf_buf, f"报告_{ev['id']}.pdf", key=f"dl{ev['id']}")
            st.write(f"评论：{ev['comments']}")

if __name__ == "__main__":
    main()
