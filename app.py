import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="工厂流程审核评分系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 数据初始化 ====================
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==================== 177分评分体系数据模型 ====================
class DataStore:
    def __init__(self):
        self.users = self._init_users()
        self.factories = self._init_factories()
        self.modules = self._init_modules()
        self.evaluations = self._load_evaluations()
        self.total_system_score = 177

    def _init_users(self):
        return [
            {"id": 1, "username": "admin", "password": "admin123", "role": "管理员", "name": "管理员"},
            {"id": 2, "username": "evaluator", "password": "eval123", "role": "评估员", "name": "张三"},
        ]

    def _init_factories(self):
        return [
            {"id": 1, "name": "深圳XX服装厂", "contact": "张经理", "phone": "13800138000"},
            {"id": 2, "name": "广州XX制衣厂", "contact": "李经理", "phone": "13800138001"},
        ]

    def _init_modules(self):
        return {
            "纸样、样衣制作": {
                "total_score": 14,
                "sub_modules": {
                    "纸样开发标准": {
                        "items": [
                            {
                                "id": "p1_1", "name": "使用CAD软件制作/修改纸样",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p1_2", "name": "缝份清晰标记应合规",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p1_3", "name": "布纹线，剪口标注合规并清晰",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p1_4", "name": "放码标准（尺寸增量）遵守客户要求，并文档化",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p1_5", "name": "技术包（Tech Pack）应明确标注尺寸表、工艺说明与要求，及特殊工艺说明",
                                "type": "重点", "score": 3,
                                "details": [], "comment": "", "unqualified": []
                            },
                        ]
                    },
                    "版本控制与追溯性": {
                        "items": [
                            {
                                "id": "p2_1", "name": "纸样版本控制系统（确保最新、准确、可追溯）",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p2_2", "name": "文档记录：纸样历史、修订、批准",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p2_3", "name": "物理纸样（平放/悬挂）及数字备份的安全存储",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                        ]
                    },
                    "初版审核与文档化": {
                        "items": [
                            {
                                "id": "p3_1", "name": "尺寸与工艺审核，应符合技术包要求（检验记录）",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "p3_2", "name": "面辅料核对，并按要求进行功能性检测（检验记录）",
                                "type": "重点", "score": 3,
                                "details": [], "comment": "", "unqualified": []
                            },
                        ]
                    }
                }
            },
            "面辅料品质控制": {
                "total_score": 34,
                "sub_modules": {
                    "面料仓库检查": {
                        "items": [
                            {
                                "id": "m1_1", "name": "合格/不合格品/待检标识应明确，分开堆放",
                                "type": "非重点", "score": 1,
                                "details": ["标识不明确", "未分开堆放"], "comment": "",
                                "unqualified": ["标识不明确", "未分开堆放"]
                            },
                            {
                                "id": "m1_2", "name": "面料不可“井”字堆放，高度不可过高（建议<1.5m）（针织面料除外）",
                                "type": "非重点", "score": 1,
                                "details": ["面料井字堆放", "堆放高度过高"], "comment": "",
                                "unqualified": ["面料井字堆放", "堆放高度过高"]
                            },
                            {
                                "id": "m1_3", "name": "不同颜色及批次（缸号）分开堆放",
                                "type": "非重点", "score": 1,
                                "details": [], "comment": "", "unqualified": []
                            },
                            {
                                "id": "m1_4", "name": "托盘存放不靠墙、不靠窗、避光储存及防潮防霉",
                                "type": "非重点", "score": 1,
                                "details": ["靠墙", "靠窗", "未避光储存", "未防潮防霉"], "comment": "",
                                "unqualified": ["靠墙", "靠窗", "未避光储存", "未防潮防霉"]
                            },
                            {
                                "id": "m1_5", "name": "温湿度计及记录（湿度<65%）",
                                "type": "非重点", "score": 1,
                                "details": ["无温湿度计", "无记录", "湿度超标"],
                                "comment": "监控湿度的变化，便于采取相应的解决方案（如抽湿）",
                                "unqualified": []
                            },
                        ]
                    },
                    "面料入库记录": {
                        "items": [
                            {
                                "id": "m2_1", "name": "面料厂验布记录/测试记录/缸差布",
                                "type": "非重点", "score": 1,
                                "details": ["无验布记录", "无测试记录", "无缸差布"],
                                "comment": "测试记录和缸差布可预防面料品质问题和色差问题",
                                "unqualified": ["无验布记录", "无测试记录", "无缸差布"]
                            },
                            {
                                "id": "m2_2", "name": "入库单（卷数，米数，克重等）",
                                "type": "非重点", "score": 1,
                                "details": ["无入库单", "信息不全"], "comment": "", "unqualified": []
                            },
                        ]
                    },
                    # ... 其他子模块和项目可以按同样方式扩展
                }
            },
            # ... 其他大项可以按同样方式扩展
        }

    def _load_evaluations(self):
        evaluations_file = os.path.join(DATA_DIR, "evaluations.json")
        if os.path.exists(evaluations_file):
            with open(evaluations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_evaluations(self):
        evaluations_file = os.path.join(DATA_DIR, "evaluations.json")
        with open(evaluations_file, 'w', encoding='utf-8') as f:
            json.dump(self.evaluations, f, ensure_ascii=False, indent=2)

    def add_evaluation(self, evaluation):
        evaluation['id'] = len(self.evaluations) + 1
        evaluation['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.evaluations.append(evaluation)
        self._save_evaluations()
        return evaluation

# ==================== 初始化数据存储 ====================
db = DataStore()

# ==================== 页面路由和UI ====================
def main():
    st.title("🏭 工厂流程审核评分系统")

    # 登录界面
    if 'user' not in st.session_state:
        st.subheader("用户登录")
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.button("登录"):
            user = next((u for u in db.users if u['username'] == username and u['password'] == password), None)
            if user:
                st.session_state['user'] = user
                st.success(f"欢迎 {user['name']}（{user['role']}）")
                st.rerun()
            else:
                st.error("用户名或密码错误")
        return

    # 侧边栏导航
    menu = ["开始评估", "历史记录", "对比分析"]
    choice = st.sidebar.radio("功能菜单", menu)

    if choice == "开始评估":
        start_evaluation()
    elif choice == "历史记录":
        show_history()
    elif choice == "对比分析":
        show_comparison()

def start_evaluation():
    st.subheader("✍️ 开始评估")

    # 基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        factory_id = st.selectbox(
            "选择工厂",
            [(f['id'], f['name']) for f in db.factories],
            format_func=lambda x: x[1]
        )[0]
    with col2:
        eval_date = st.date_input("评估日期", date.today())
    with col3:
        evaluator = st.text_input("评估人员", value=st.session_state['user']['name'])

    # 评估类型
    eval_type = st.selectbox("评估类型", ["常规审核", "整改复查"])

    # 选择评估模块
    if eval_type == "常规审核":
        selected_modules = list(db.modules.keys())
    else:
        selected_modules = st.multiselect("选择评估模块（可多选）", list(db.modules.keys()))

    if not selected_modules:
        st.warning("请至少选择一个评估模块")
        return

    # 评分详情
    st.subheader("📊 评分详情")

    total_score = 0
    evaluation_data = {
        "factory_id": factory_id,
        "evaluator": evaluator,
        "eval_date": eval_date.strftime('%Y-%m-%d'),
        "eval_type": eval_type,
        "selected_modules": selected_modules,
        "scores": {},
        "comments": ""
    }

    for module_name in selected_modules:
        module_data = db.modules[module_name]
        with st.expander(f"🔍 {module_name} ({module_data['total_score']/177*100:.2f}%)", expanded=True):
            for sub_module_name, sub_module_data in module_data['sub_modules'].items():
                st.markdown(f"**{sub_module_name}**")
                for item in sub_module_data['items']:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        is_checked = st.checkbox(f"{item['name']} ({item['type']}, {item['score']}分)", key=f"check_{item['id']}")
                    with col2:
                        if not is_checked and item['details']:
                            selected_details = st.multiselect("问题详情", item['details'], key=f"details_{item['id']}")
                        else:
                            selected_details = []
                    with col3:
                        if not is_checked and item['comment']:
                            st.info(item['comment'])

                    if is_checked:
                        total_score += item['score']
                        evaluation_data['scores'][item['id']] = {
                            "score": item['score'],
                            "details": [],
                            "comment": ""
                        }
                    else:
                        evaluation_data['scores'][item['id']] = {
                            "score": 0,
                            "details": selected_details,
                            "comment": item['comment']
                        }

    # 评估者评论
    evaluation_data['comments'] = st.text_area("评估者评论", height=100)

    # 保存评估
    if st.button("💾 保存评估", type="primary"):
        evaluation_data['total_score'] = total_score
        evaluation_data['overall_percentage'] = (total_score / 177) * 100
        db.add_evaluation(evaluation_data)
        st.success("评估保存成功！")
        # 生成PDF报告
        pdf_buffer = generate_pdf_report(evaluation_data)
        st.download_button(
            label="📄 下载评估报告",
            data=pdf_buffer,
            file_name=f"评估报告_{evaluation_data['id']}_{eval_date}.pdf",
            mime="application/pdf"
        )

def show_history():
    st.subheader("📋 历史记录")

    # 查询条件
    col1, col2, col3 = st.columns(3)
    with col1:
        factory_filter = st.selectbox(
            "工厂名称",
            ["全部"] + [f['name'] for f in db.factories],
            index=0
        )
    with col2:
        start_date = st.date_input("开始时间", date.today().replace(day=1))
    with col3:
        end_date = st.date_input("结束时间", date.today())

    # 筛选记录
    filtered_evals = []
    for ev in db.evaluations:
        factory_name = next(f['name'] for f in db.factories if f['id'] == ev['factory_id'])
        if (factory_filter == "全部" or factory_name == factory_filter) and \
           (start_date.strftime('%Y-%m-%d') <= ev['created_at'] <= end_date.strftime('%Y-%m-%d')):
            filtered_evals.append(ev)

    # 显示记录
    if filtered_evals:
        for ev in filtered_evals:
            factory_name = next(f['name'] for f in db.factories if f['id'] == ev['factory_id'])
            with st.expander(f"{factory_name} - {ev['eval_type']} - {ev['created_at']}"):
                st.write(f"**评估人员**: {ev['evaluator']}")
                st.write(f"**总得分率**: {ev['overall_percentage']:.2f}%")
                st.write(f"**评估模块**: {', '.join(ev['selected_modules'])}")
                if st.button("下载报告", key=f"download_{ev['id']}"):
                    pdf_buffer = generate_pdf_report(ev)
                    st.download_button(
                        label="📄 下载PDF报告",
                        data=pdf_buffer,
                        file_name=f"评估报告_{ev['id']}_{ev['eval_date']}.pdf",
                        mime="application/pdf"
                    )
    else:
        st.info("暂无历史记录")

def show_comparison():
    st.subheader("📈 对比分析")
    st.info("对比分析功能正在开发中...")

def generate_pdf_report(evaluation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']

    elements = []

    # 标题
    elements.append(Paragraph("工厂评估报告", title_style))
    elements.append(Spacer(1, 12))

    # 基本信息
    elements.append(Paragraph("一、基本信息", subtitle_style))
    factory_name = next(f['name'] for f in db.factories if f['id'] == evaluation['factory_id'])
    elements.append(Paragraph(f"工厂名称: {factory_name}", normal_style))
    elements.append(Paragraph(f"评估日期: {evaluation['eval_date']}", normal_style))
    elements.append(Paragraph(f"评估人员: {evaluation['evaluator']}", normal_style))
    elements.append(Paragraph(f"评估类型: {evaluation['eval_type']}", normal_style))
    elements.append(Paragraph(f"总得分率: {evaluation['overall_percentage']:.2f}%", normal_style))
    elements.append(Spacer(1, 12))

    # 重点工序问题
    elements.append(Paragraph("二、重点工序问题", subtitle_style))
    for module_name in evaluation['selected_modules']:
        module_data = db.modules[module_name]
        for sub_module_name, sub_module_data in module_data['sub_modules'].items():
            for item in sub_module_data['items']:
                if item['id'] in evaluation['scores'] and evaluation['scores'][item['id']]['score'] == 0 and item['type'] == '重点':
                    elements.append(Paragraph(f"**{module_name} - {sub_module_name} - {item['name']}**", normal_style))
                    if evaluation['scores'][item['id']]['details']:
                        elements.append(Paragraph(f"问题详情: {', '.join(evaluation['scores'][item['id']]['details'])}", normal_style))
                    if evaluation['scores'][item['id']]['comment']:
                        elements.append(Paragraph(f"说明: {evaluation['scores'][item['id']]['comment']}", normal_style))
                    elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 12))

    # 其他工序问题
    elements.append(Paragraph("三、其他工序问题", subtitle_style))
    for module_name in evaluation['selected_modules']:
        module_data = db.modules[module_name]
        for sub_module_name, sub_module_data in module_data['sub_modules'].items():
            for item in sub_module_data['items']:
                if item['id'] in evaluation['scores'] and evaluation['scores'][item['id']]['score'] == 0 and item['type'] == '非重点':
                    elements.append(Paragraph(f"**{module_name} - {sub_module_name} - {item['name']}**", normal_style))
                    if evaluation['scores'][item['id']]['details']:
                        elements.append(Paragraph(f"问题详情: {', '.join(evaluation['scores'][item['id']]['details'])}", normal_style))
                    if evaluation['scores'][item['id']]['comment']:
                        elements.append(Paragraph(f"说明: {evaluation['scores'][item['id']]['comment']}", normal_style))
                    elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 12))

    # 评估者评论
    elements.append(Paragraph("四、评估者评论", subtitle_style))
    elements.append(Paragraph(evaluation['comments'], normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================== 启动应用 ====================
if __name__ == "__main__":
    main()
