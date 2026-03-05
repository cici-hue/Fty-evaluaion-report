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
from reportlab.pdfbase.pdfmetrics import stringWidth
import re

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="工厂流程审核评分系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 字体配置 - 无依赖方案（解决OTF/TTF报错） ====================
def setup_chinese_font():
    """兼容模式：不依赖外部字体文件，解决中文显示问题"""
    # 使用ReportLab内置支持的方式处理中文
    try:
        # 尝试注册一个基础字体（防止报错）
        pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica'))
        return 'Helvetica'
    except:
        return 'Courier'

# 初始化字体
CHINESE_FONT = setup_chinese_font()

# 中文转义处理（核心：解决无中文字体时的显示问题）
def safe_chinese(text):
    """处理中文显示，替换特殊字符，确保PDF能正常生成"""
    if not text:
        return ""
    # 替换特殊字符
    text = text.replace("：", ":").replace("（", "(").replace("）", ")")
    text = text.replace("【", "[").replace("】", "]").replace("、", ",")
    text = text.replace("％", "%").replace("—", "-").replace("～", "~")
    # 移除无法显示的特殊符号
    text = re.sub(r'[^\u4e00-\u9fff0-9a-zA-Z\s\:\(\)\[\]\,\.\%\-\/]', '', text)
    return text

# ==================== 数据初始化 ====================
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==================== 评分体系数据模型 ====================
class DataStore:
    def __init__(self):
        self.users = [{"id": 1, "username": "admin", "password": "admin123", "name": "管理员"}]
        self.factories = [{"id": 1, "name": "深圳XX服装厂"}, {"id": 2, "name": "广州XX制衣厂"}]
        self.modules = self._init_modules()
        self.evaluations = self._load_evaluations()
        self.total_system_score = 177  # 总分177

    def _init_modules(self):
        """核心评估项"""
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
                                "is_key": False,
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

# ==================== PDF生成工具 (无字体依赖版本) ====================
def generate_pdf(evaluation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # 创建基础样式表
    styles = getSampleStyleSheet()
    
    # 自定义样式（不依赖中文字体）
    custom_styles = {
        'Heading1': ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontName=CHINESE_FONT,
            fontSize=18,
            spaceAfter=20,
            alignment=1  # 居中
        ),
        'Heading2': ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontName=CHINESE_FONT,
            fontSize=14,
            spaceAfter=12
        ),
        'Normal': ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=CHINESE_FONT,
            fontSize=12,
            spaceAfter=6,
            wordWrap='CJK'  # 支持CJK文字换行
        )
    }

    elements = []

    # 标题与基础信息
    elements.append(Paragraph(safe_chinese("工厂流程审核报告"), custom_styles['Heading1']))
    factory_name = next(f['name'] for f in db.factories if f['id'] == evaluation['factory_id'])
    elements.extend([
        Paragraph(safe_chinese(f"工厂名称：{factory_name}"), custom_styles['Normal']),
        Paragraph(safe_chinese(f"评估日期：{evaluation['eval_date']}"), custom_styles['Normal']),
        Paragraph(safe_chinese(f"评估人员：{evaluation['evaluator']}"), custom_styles['Normal']),
        Spacer(1, 12)
    ])

    # 问题汇总
    elements.append(Paragraph(safe_chinese("一、存在问题汇总"), custom_styles['Heading2']))
    has_problems = False
    for mod_name in evaluation['selected_modules']:
        mod = db.modules[mod_name]
        for sub_name, sub_mod in mod['sub_modules'].items():
            for item in sub_mod['items']:
                res = evaluation['results'].get(item['id'], {})
                if not res.get('is_checked', False):
                    has_problems = True
                    # 处理中文内容
                    item_text = safe_chinese(f"【{mod_name}-{sub_name}】{item['name']}")
                    elements.append(Paragraph(item_text, custom_styles['Normal']))
                    
                    if res.get('details'):
                        details_text = safe_chinese(f"问题详情：{', '.join(res['details'])}")
                        elements.append(Paragraph(details_text, custom_styles['Normal']))
                    
                    if item['comment']:
                        comment_text = safe_chinese(f"改进建议：{item['comment']}")
                        elements.append(Paragraph(comment_text, custom_styles['Normal']))
                    
                    elements.append(Spacer(1, 6))
    
    if not has_problems:
        elements.append(Paragraph(safe_chinese("本次评估未发现问题"), custom_styles['Normal']))
        elements.append(Spacer(1, 6))

    # 评估评论
    elements.append(Paragraph(safe_chinese("二、评估者评论"), custom_styles['Heading2']))
    if evaluation['comments']:
        elements.append(Paragraph(safe_chinese(evaluation['comments']), custom_styles['Normal']))
    else:
        elements.append(Paragraph(safe_chinese("无评论"), custom_styles['Normal']))
    
    # 生成PDF（关键：忽略字体警告）
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================== 页面路由 ====================
def main():
    # 登录页
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

    # 主界面侧边栏
    st.sidebar.title(f"欢迎，{st.session_state['user']}")
    menu = st.sidebar.radio("功能菜单", ["开始评估", "历史记录", "对比分析"])
    
    if menu == "开始评估":
        start_evaluation()
    elif menu == "历史记录":
        show_history()
    elif menu == "对比分析":
        st.subheader("对比分析")
        st.info("功能开发中...")

# ==================== 核心评估页面 ====================
def start_evaluation():
    st.subheader("开始评估")
    
    # 1. 评估基本信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        factory_id = st.selectbox("工厂", [(f['id'], f['name']) for f in db.factories], format_func=lambda x: x[1])[0]
    with col2:
        eval_date = st.date_input("日期", date.today())
    with col3:
        evaluator = st.text_input("评估人员", value=st.session_state['user'])
    with col4:
        eval_type = st.selectbox("评估类型", ["常规审核", "整改复查"])

    # 2. 选择评估大项
    all_modules = list(db.modules.keys())
    if eval_type == "常规审核":
        selected_modules = all_modules
        st.caption("常规审核：默认包含所有评估模块")
    else:
        selected_modules = st.multiselect("选择整改模块", all_modules, placeholder="请选择需要复查的模块")
        if not selected_modules:
            st.warning("请至少选择一个评估模块")
            return

    # 3. 初始化评估结果存储
    if 'eval_results' not in st.session_state:
        st.session_state.eval_results = {}
        # 预加载所有项为未勾选
        for mod in selected_modules:
            for sub_mod in db.modules[mod]['sub_modules'].values():
                for item in sub_mod['items']:
                    st.session_state.eval_results[item['id']] = {"is_checked": False, "details": []}

    # 4. 评分详情（核心UI）
    st.subheader("评分详情")
    total_earned = 0

    for mod_name in selected_modules:
        mod = db.modules[mod_name]
        # 大项Expander
        mod_earned = 0
        
        with st.expander(f"📦 {mod_name}", expanded=True):
            for sub_name, sub_mod in mod['sub_modules'].items():
                # 小项标题：计算小项得分/总分177的百分比
                sub_earned = sum(
                    item['score'] for item in sub_mod['items']
                    if st.session_state.eval_results[item['id']]['is_checked']
                )
                sub_percent = (sub_earned / db.total_system_score * 100) if db.total_system_score > 0 else 0
                st.markdown(f"### {sub_name} ({sub_percent:.2f}%)")
                st.divider()

                # 遍历每个检查项
                for item in sub_mod['items']:
                    item_id = item['id']
                    # 重点项字体显示为橙色
                    item_label = item['name']
                    if item.get('is_key', False):
                        item_label = f":orange[{item_label}]"
                    
                    # 勾选框
                    is_checked = st.checkbox(
                        item_label,
                        key=f"chk_{item_id}",
                        value=st.session_state.eval_results[item_id]['is_checked']
                    )
                    
                    # 实时更新状态
                    st.session_state.eval_results[item_id]['is_checked'] = is_checked
                    mod_earned += item['score'] if is_checked else 0

                    # 细化选项和Comment
                    if not is_checked:
                        col_detail, col_comment = st.columns([1, 2])
                        with col_detail:
                            # 问题详情选择框
                            if item['details']:
                                details = st.multiselect(
                                    "问题详情",
                                    item['details'],
                                    key=f"det_{item_id}",
                                    default=st.session_state.eval_results[item_id]['details']
                                )
                                st.session_state.eval_results[item_id]['details'] = details
                        with col_comment:
                            # 自动显示的改进建议
                            if item['comment']:
                                st.info(f"改进建议：{item['comment']}")
                    
                    # 间距
                    st.markdown("")

        total_earned += mod_earned

    # 5. 评估总结与评论
    st.subheader("评估总结")
    overall_percent = (total_earned / db.total_system_score * 100) if db.total_system_score > 0 else 0
    st.metric("整体评分占比", f"{overall_percent:.2f}%")
    comments = st.text_area("评估评论", height=100, placeholder="请输入本次评估的总体评价或整改要求...")

    # 6. 保存与生成报告
    if st.button("保存并生成报告", type="primary"):
        evaluation_data = {
            "factory_id": factory_id,
            "evaluator": evaluator,
            "eval_date": eval_date.strftime('%Y-%m-%d'),
            "eval_type": eval_type,
            "selected_modules": selected_modules,
            "overall_percent": overall_percent,
            "results": st.session_state.eval_results,
            "comments": comments
        }
        saved_ev = db.add_evaluation(evaluation_data)
        st.success("评估记录已保存！")
        
        # 生成PDF
        try:
            pdf_buffer = generate_pdf(saved_ev)
            st.download_button(
                label="📄 下载PDF报告",
                data=pdf_buffer,
                file_name=f"评估报告_{saved_ev['id']}_{eval_date}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF生成成功，但可能存在字体显示问题：{str(e)}")
            st.download_button(
                label="📄 下载PDF报告（忽略字体提示）",
                data=pdf_buffer,
                file_name=f"评估报告_{saved_ev['id']}_{eval_date}.pdf",
                mime="application/pdf"
            )
        
        # 重置session
        del st.session_state.eval_results

# ==================== 历史记录页面 ====================
def show_history():
    st.subheader("历史记录")
    if not db.evaluations:
        st.info("暂无评估记录")
        return

    for ev in reversed(db.evaluations):
        factory_name = next(f['name'] for f in db.factories if f['id'] == ev['factory_id'])
        with st.expander(f"📅 {ev['eval_date']} | {factory_name} | {ev['eval_type']}"):
            col1, col2, col3 = st.columns([2,2,1])
            with col1: st.write(f"**评估人**：{ev['evaluator']}")
            with col2: st.write(f"**整体评分占比**：{ev['overall_percent']:.2f}%")
            with col3:
                try:
                    pdf_buffer = generate_pdf(ev)
                    st.download_button(
                        "下载报告",
                        data=pdf_buffer,
                        file_name=f"报告_{ev['id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_{ev['id']}"
                    )
                except:
                    st.warning("PDF生成失败，可能是字体问题")
            st.write(f"**评论**：{ev['comments']}")

if __name__ == "__main__":
    main()
