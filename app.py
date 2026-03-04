import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
from io import BytesIO

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="工厂流程审核评分系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 数据初始化 ====================
DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "evaluations.db")

# 创建数据目录
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==================== 数据模型 ====================
class DataStore:
    """数据存储管理类"""
    
    def __init__(self):
        self.users = self._init_users()
        self.factories = self._init_factories()
        self.modules = self._init_modules()
        self.evaluations = self._load_evaluations()
        self.scores = self._load_scores()
    
    def _init_users(self):
        """初始化用户数据"""
        return [
            {"id": 1, "username": "admin", "password": "admin123", "role": "管理员", "name": "管理员"},
            {"id": 2, "username": "evaluator", "password": "eval123", "role": "评估员", "name": "张三"},
        ]
    
    def _init_factories(self):
        """初始化工厂数据"""
        return [
            {"id": 1, "name": "深圳XX服装厂", "contact": "张经理", "phone": "13800138000"},
            {"id": 2, "name": "广州XX制衣厂", "contact": "李经理", "phone": "13800138001"},
            {"id": 3, "name": "东莞XX服装公司", "contact": "王经理", "phone": "13800138002"},
            {"id": 4, "name": "佛山XX服饰", "contact": "刘经理", "phone": "13800138003"},
            {"id": 5, "name": "珠海XX制衣", "contact": "陈经理", "phone": "13800138004"},
        ]
    
    def _init_modules(self):
        """初始化8大评估模块及小项"""
        return {
            "纸样": {
                "items": [
                    {"id": "paper_1", "name": "纸样尺寸准确，符合设计要求", "type": "重点", "score": 3,
                     "detail": ["尺寸偏差>3mm", "尺寸偏差>5mm"], "comment": "纸样是生产的基础，尺寸偏差会影响成衣质量"},
                    {"id": "paper_2", "name": "纸样缝份标注清晰完整", "type": "非重点", "score": 1,
                     "detail": ["缝份未标注", "缝份标注错误"], "comment": "缝份标注不清会导致车缝错误"},
                    {"id": "paper_3", "name": "纸样保存完好，无破损变形", "type": "非重点", "score": 1,
                     "detail": ["纸样破损", "纸样变形"], "comment": "纸样损坏会导致批量生产问题"},
                ]
            },
            "样衣制作": {
                "items": [
                    {"id": "sample_1", "name": "样衣尺寸符合纸样要求", "type": "重点", "score": 3,
                     "detail": ["尺寸偏差>5mm", "尺寸偏差>10mm"], "comment": "样衣尺寸偏差会影响大货生产"},
                    {"id": "sample_2", "name": "样衣工艺符合设计要求", "type": "重点", "score": 3,
                     "detail": ["工艺偏差", "工艺错误"], "comment": "样衣工艺是大货生产的标准"},
                    {"id": "sample_3", "name": "样衣面料使用正确", "type": "非重点", "score": 1,
                     "detail": ["面料错误", "面料代用"], "comment": "面料错误会导致成本和质量问题"},
                ]
            },
            "面辅料品质控制": {
                "items": [
                    {"id": "material_1", "name": "面辅料检验报告完整", "type": "重点", "score": 3,
                     "detail": ["检验报告缺失", "检验报告不全"], "comment": "检验报告是质量控制的重要依据"},
                    {"id": "material_2", "name": "面辅料规格符合标准", "type": "重点", "score": 3,
                     "detail": ["规格不符", "规格偏差"], "comment": "规格不符会导致生产问题"},
                    {"id": "material_3", "name": "面辅料色号、缸号标识清晰", "type": "非重点", "score": 1,
                     "detail": ["标识不清", "标识错误"], "comment": "标识不清会导致混用"},
                    {"id": "material_4", "name": "温湿度计及记录 (湿度<65%)", "type": "非重点", "score": 1,
                     "detail": ["温湿度记录缺失", "湿度超标"], "comment": "监控湿度的变化，便于采取相应的解决方案（如抽湿）"},
                ]
            },
            "产前会议控制": {
                "items": [
                    {"id": "pre_meeting_1", "name": "产前会议记录完整", "type": "重点", "score": 3,
                     "detail": ["会议记录缺失", "会议记录不全"], "comment": "产前会议是解决生产问题的关键"},
                    {"id": "pre_meeting_2", "name": "生产技术要求明确传达", "type": "重点", "score": 3,
                     "detail": ["要求未传达", "传达不清"], "comment": "技术要求未传达会导致批量质量问题"},
                    {"id": "pre_meeting_3", "name": "质量问题解决方案确认", "type": "非重点", "score": 1,
                     "detail": ["方案未确认", "方案不完整"], "comment": "质量问题的解决方案必须明确"},
                ]
            },
            "裁剪品质控制": {
                "items": [
                    {"id": "cut_1", "name": "裁片尺寸符合纸样要求", "type": "重点", "score": 3,
                     "detail": ["尺寸偏差>3mm", "尺寸偏差>5mm"], "comment": "裁片尺寸偏差会影响缝制质量"},
                    {"id": "cut_2", "name": "裁片层次对齐整齐", "type": "重点", "score": 3,
                     "detail": ["层次不对齐", "裁片歪斜"], "comment": "层次不对齐会导致成衣左右不对称"},
                    {"id": "cut_3", "name": "裁片编号标识清晰", "type": "非重点", "score": 1,
                     "detail": ["编号不清", "编号错误"], "comment": "编号不清会导致混淆"},
                ]
            },
            "缝制工艺品质控制": {
                "items": [
                    {"id": "sew_1", "name": "缝制线迹均匀，无跳线、断线", "type": "重点", "score": 3,
                     "detail": ["跳线", "断线", "线迹不匀"], "comment": "线迹问题会影响成衣外观和强度"},
                    {"id": "sew_2", "name": "缝份宽度符合工艺要求", "type": "非重点", "score": 1,
                     "detail": ["缝份过宽", "缝份过窄"], "comment": "缝份不符合要求会影响外观和成本"},
                    {"id": "sew_3", "name": "压脚压力调节适当", "type": "非重点", "score": 1,
                     "detail": ["压力过大", "压力过小"], "comment": "压力不当会导致缝制质量问题"},
                    {"id": "sew_4", "name": "针距密度符合标准", "type": "重点", "score": 3,
                     "detail": ["针距过密", "针距过疏"], "comment": "针距不符合标准会影响缝制强度和外观"},
                    {"id": "sew_5", "name": "特殊部位缝制质量", "type": "重点", "score": 3,
                     "detail": ["领口不平", "袖口起皱"], "comment": "特殊部位是质量控制的重点"},
                    {"id": "sew_6", "name": "线头清理干净", "type": "非重点", "score": 1,
                     "detail": ["线头未清理"], "comment": "线头影响成衣外观"},
                    {"id": "sew_7", "name": "缝制张力均匀", "type": "非重点", "score": 1,
                     "detail": ["张力不匀"], "comment": "张力不匀会导致波浪纹"},
                    {"id": "sew_8", "name": "对位准确，无错位", "type": "重点", "score": 3,
                     "detail": ["对位错误", "错位"], "comment": "对位错误会导致成衣不对称"},
                ]
            },
            "后道品质控制": {
                "items": [
                    {"id": "post_1", "name": "熨烫平整，无亮光", "type": "重点", "score": 3,
                     "detail": ["不平整", "有亮光"], "comment": "熨烫质量直接影响成衣外观"},
                    {"id": "post_2", "name": "纽扣/拉链等配件安装牢固", "type": "重点", "score": 3,
                     "detail": ["松动", "脱落"], "comment": "配件不牢固是严重的质量问题"},
                    {"id": "post_3", "name": "包装符合要求", "type": "非重点", "score": 1,
                     "detail": ["包装不当", "包装破损"], "comment": "包装问题会影响产品形象"},
                ]
            },
            "质量部门品质控制/其他": {
                "items": [
                    {"id": "quality_1", "name": "质量检验流程规范", "type": "重点", "score": 3,
                     "detail": ["流程不规范", "检验缺失"], "comment": "检验流程不规范会导致质量问题漏检"},
                    {"id": "quality_2", "name": "质量记录完整可追溯", "type": "重点", "score": 3,
                     "detail": ["记录缺失", "记录不全"], "comment": "质量记录是追溯的重要依据"},
                    {"id": "quality_3", "name": "不合格品标识和隔离", "type": "非重点", "score": 1,
                     "detail": ["标识不清", "未隔离"], "comment": "不合格品必须明确标识并隔离"},
                ]
            },
        }
    
    def _load_evaluations(self):
        """加载评估记录"""
        evaluations_file = os.path.join(DATA_DIR, "evaluations.json")
        if os.path.exists(evaluations_file):
            with open(evaluations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_evaluations(self):
        """保存评估记录"""
        evaluations_file = os.path.join(DATA_DIR, "evaluations.json")
        with open(evaluations_file, 'w', encoding='utf-8') as f:
            json.dump(self.evaluations, f, ensure_ascii=False, indent=2)
    
    def _load_scores(self):
        """加载评分明细"""
        scores_file = os.path.join(DATA_DIR, "scores.json")
        if os.path.exists(scores_file):
            with open(scores_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_scores(self):
        """保存评分明细"""
        scores_file = os.path.join(DATA_DIR, "scores.json")
        with open(scores_file, 'w', encoding='utf-8') as f:
            json.dump(self.scores, f, ensure_ascii=False, indent=2)
    
    def add_evaluation(self, evaluation):
        """添加评估记录"""
        evaluation['id'] = len(self.evaluations) + 1
        evaluation['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.evaluations.append(evaluation)
        self._save_evaluations()
        return evaluation
    
    def update_evaluation(self, evaluation_id, data):
        """更新评估记录"""
        for i, ev in enumerate(self.evaluations):
            if ev['id'] == evaluation_id:
                self.evaluations[i].update(data)
                self._save_evaluations()
                return True
        return False
    
    def get_evaluation(self, evaluation_id):
        """获取评估记录"""
        for ev in self.evaluations:
            if ev['id'] == evaluation_id:
                return ev
        return None
    
    def get_evaluations(self, factory_id=None, start_date=None, end_date=None, status=None):
        """获取评估记录列表"""
        filtered = self.evaluations.copy()
        
        if factory_id:
            filtered = [ev for ev in filtered if ev['factory_id'] == factory_id]
        
        if start_date:
            filtered = [ev for ev in filtered if ev['date'] >= start_date]
        
        if end_date:
            filtered = [ev for ev in filtered if ev['date'] <= end_date]
        
        if status:
            filtered = [ev for ev in filtered if ev['status'] == status]
        
        return sorted(filtered, key=lambda x: x['date'], reverse=True)
    
    def save_scores(self, evaluation_id, scores):
        """保存评分明细"""
        # 删除旧的评分
        self.scores = [s for s in self.scores if s['evaluation_id'] != evaluation_id]
        
        # 添加新评分
        for item_id, score_data in scores.items():
            self.scores.append({
                'evaluation_id': evaluation_id,
                'item_id': item_id,
                'passed': score_data['passed'],
                'details': score_data.get('details', []),
                'score': score_data['score']
            })
        
        self._save_scores()
    
    def get_scores(self, evaluation_id):
        """获取评估的评分明细"""
        return {s['item_id']: s for s in self.scores if s['evaluation_id'] == evaluation_id}
    
    def get_comment_summary(self, evaluation_id):
        """生成评估摘要"""
        scores = self.get_scores(evaluation_id)
        evaluation = self.get_evaluation(evaluation_id)
        
        key_comments = []
        other_comments = []
        
        for module_name, module_data in self.modules.items():
            for item in module_data['items']:
                item_id = item['id']
                if item_id in scores:
                    score_data = scores[item_id]
                    if not score_data['passed']:
                        # 构建comment
                        comment_parts = [item['name']]
                        
                        # 添加details
                        if score_data.get('details'):
                            comment_parts.extend(score_data['details'])
                        
                        # 添加comment
                        if item.get('comment'):
                            comment_parts.append(item['comment'])
                        
                        comment_text = "；".join(comment_parts)
                        
                        if item['type'] == '重点':
                            key_comments.append({
                                'module': module_name,
                                'item': item['name'],
                                'comment': comment_text
                            })
                        else:
                            other_comments.append({
                                'module': module_name,
                                'item': item['name'],
                                'comment': comment_text
                            })
        
        return {
            'key_comments': key_comments,
            'other_comments': other_comments
        }

# ==================== 会话状态管理 ====================
def init_session_state():
    """初始化会话状态"""
    if 'data_store' not in st.session_state:
        st.session_state.data_store = DataStore()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'current_evaluation' not in st.session_state:
        st.session_state.current_evaluation = None
    
    if 'selected_modules' not in st.session_state:
        st.session_state.selected_modules = []

# ==================== 认证功能 ====================
def login_page():
    """登录页面"""
    st.title("🏭 工厂流程审核评分系统")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("用户登录")
        
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        if st.button("登录", use_container_width=True):
            data_store = st.session_state.data_store
            user = next((u for u in data_store.users if u['username'] == username), None)
            
            if user and user['password'] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.success(f"欢迎回来，{user['name']}！")
                st.rerun()
            else:
                st.error("用户名或密码错误！")
        
        st.markdown("---")
        st.info("**默认账号**\n\n- 管理员：admin / admin123\n- 评估员：evaluator / eval123")

def logout():
    """退出登录"""
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.current_evaluation = None
    st.rerun()

# ==================== 侧边栏 ====================
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🏭 工厂审核系统")
        
        # 用户信息
        if st.session_state.logged_in:
            user = st.session_state.current_user
            st.info(f"**当前用户**\n\n{user['name']}\n{user['role']}")
            
            if st.button("退出登录", use_container_width=True):
                logout()
        
        st.markdown("---")
        
        # 导航菜单
        if st.session_state.logged_in:
            page = st.radio(
                "功能导航",
                ["🏠 首页", "📝 开始评估", "📋 历史记录", "📊 对比分析", "⚙️ 系统设置"],
                label_visibility="collapsed"
            )
            return page
        else:
            return None

# ==================== 首页 ====================
def render_dashboard():
    """首页"""
    st.title("🏠 首页")
    
    data_store = st.session_state.data_store
    evaluations = data_store.get_evaluations()
    
    # 统计卡片
    col1, col2, col3 = st.columns(3)
    
    # 待完成评估（未提交的）
    pending_count = len([e for e in evaluations if e['status'] == '进行中'])
    with col1:
        st.metric("📋 待完成评估", pending_count)
    
    # 本月评估数量
    current_month = datetime.now().month
    month_evaluations = [e for e in evaluations if datetime.strptime(e['date'], '%Y-%m-%d').month == current_month]
    with col2:
        st.metric("📅 本月评估", len(month_evaluations))
    
    # 平均分
    completed_evaluations = [e for e in evaluations if e['status'] == '已完成' and e['total_score'] > 0]
    avg_score = sum(e['total_score'] for e in completed_evaluations) / len(completed_evaluations) if completed_evaluations else 0
    with col3:
        st.metric("📊 平均得分", f"{avg_score:.1f}分")
    
    st.markdown("---")
    
    # 问题预警
    st.subheader("⚠️ 问题预警")
    
    pending_evaluations = [e for e in evaluations if e['status'] == '进行中']
    if pending_evaluations:
        for ev in pending_evaluations[:3]:
            factory = next((f for f in data_store.factories if f['id'] == ev['factory_id']), None)
            st.warning(f"📍 {factory['name'] if factory else '未知工厂'} - {ev['modules_str']} 评估进行中")
    else:
        st.info("暂无待处理问题")
    
    st.markdown("---")
    
    # 最近评估记录
    st.subheader("📝 最近评估记录")
    
    if evaluations:
        # 准备数据
        df_data = []
        for ev in evaluations[:10]:
            factory = next((f for f in data_store.factories if f['id'] == ev['factory_id']), None)
            df_data.append({
                "工厂名称": factory['name'] if factory else '未知',
                "评估日期": ev['date'],
                "评估模块": ev['modules_str'],
                "总分": ev['total_score'],
                "状态": ev['status']
            })
        
        df = pd.DataFrame(df_data)
        
        # 状态颜色
        def highlight_status(val):
            if val == '优秀':
                return 'background-color: #d4edda'
            elif val == '合格':
                return 'background-color: #fff3cd'
            elif val == '待改进':
                return 'background-color: #f8d7da'
            return ''
        
        styled_df = df.style.applymap(highlight_status, subset=['状态'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无评估记录，点击'开始评估'创建新评估")

# ==================== 开始评估 ====================
def render_evaluation_create():
    """创建评估"""
    st.title("📝 开始评估")
    
    data_store = st.session_state.data_store
    
    # 步骤1：选择工厂和日期
    st.subheader("第一步：选择工厂")
    
    factories = {f['id']: f['name'] for f in data_store.factories}
    factory_id = st.selectbox("选择工厂", options=list(factories.keys()), format_func=lambda x: factories[x])
    
    evaluation_date = st.date_input("评估日期", value=datetime.now().date())
    
    # 步骤2：选择评估模块
    st.subheader("第二步：选择评估模块（可多选）")
    
    selected_modules = st.multiselect(
        "选择要评估的模块",
        options=list(data_store.modules.keys()),
        default=[],
        help="选择本次评估需要检查的模块"
    )
    
    if selected_modules:
        st.info(f"已选择 {len(selected_modules)} 个模块：{', '.join(selected_modules)}")
    
    # 创建评估
    if st.button("开始评估", type="primary", use_container_width=True):
        if not selected_modules:
            st.error("请至少选择一个评估模块！")
        else:
            # 计算总分
            total_score = 0
            key_score = 0
            for module in selected_modules:
                for item in data_store.modules[module]['items']:
                    total_score += item['score']
                    if item['type'] == '重点':
                        key_score += item['score']
            
            # 创建评估记录
            evaluation = {
                'factory_id': factory_id,
                'factory_name': factories[factory_id],
                'date': evaluation_date.strftime('%Y-%m-%d'),
                'modules': selected_modules,
                'modules_str': '、'.join(selected_modules),
                'total_score': total_score,
                'key_score': key_score,
                'current_score': 0,
                'current_key_score': 0,
                'status': '进行中',
                'evaluator': st.session_state.current_user['name']
            }
            
            evaluation = data_store.add_evaluation(evaluation)
            st.session_state.current_evaluation = evaluation
            st.session_state.selected_modules = selected_modules
            
            st.success(f"评估创建成功！评估ID：{evaluation['id']}")
            st.rerun()

def render_evaluation_detail():
    """评估详情"""
    st.title("📝 评估详情")
    
    if not st.session_state.current_evaluation:
        st.warning("请先创建评估")
        return
    
    evaluation = st.session_state.current_evaluation
    data_store = st.session_state.data_store
    
    # 评估信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"🏭 工厂：{evaluation['factory_name']}")
    with col2:
        st.info(f"📅 日期：{evaluation['date']}")
    with col3:
        st.info(f"👤 评估员：{evaluation['evaluator']}")
    with col4:
        st.info(f"📊 模块：{evaluation['modules_str']}")
    
    st.markdown("---")
    
    # 进度条
    scores = data_store.get_scores(evaluation['id'])
    total_items = sum(len(data_store.modules[module]['items']) for module in evaluation['modules'])
    scored_items = len(scores)
    progress = scored_items / total_items if total_items > 0 else 0
    
    st.progress(progress)
    st.caption(f"当前进度：{scored_items}/{total_items} 项 ({progress*100:.1f}%)")
    
    # 当前得分
    current_score = evaluation['current_score']
    total_possible = evaluation['total_score']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("当前得分", f"{current_score}分")
    with col2:
        st.metric("总分", f"{total_possible}分")
    
    st.markdown("---")
    
    # 评分表单
    st.subheader("评分详情")
    
    # 按模块显示
    for module_name in evaluation['modules']:
        st.markdown(f"### {module_name}")
        
        module_data = data_store.modules[module_name]
        
        for item in module_data['items']:
            item_id = item['id']
            existing_score = scores.get(item_id, {})
            
            # 获取之前的评分状态
            passed = existing_score.get('passed', True) if existing_score else True
            selected_details = existing_score.get('details', []) if existing_score else []
            
            # 评分行
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"{'🔴' if item['type'] == '重点' else '⚪'} {item['name']}")
            
            with col2:
                passed = st.checkbox(
                    "通过",
                    value=passed,
                    key=f"passed_{item_id}",
                    label_visibility="collapsed"
                )
            
            with col3:
                st.write(f"{item['score']}分")
            
            with col4:
                if st.button("详情", key=f"detail_{item_id}"):
                    pass
            
            # 如果不通过，显示detail选项
            if not passed:
                if item.get('detail'):
                    st.markdown("**问题详情（可多选）：**")
                    selected_details = st.multiselect(
                        "选择发现的问题",
                        options=item['detail'],
                        default=selected_details,
                        key=f"details_{item_id}",
                        label_visibility="collapsed"
                    )
                
                # 显示comment
                if item.get('comment'):
                    st.markdown(f"*💡 {item['comment']}*")
            
            # 保存评分到临时状态
            st.session_state[f"score_{item_id}"] = {
                'passed': passed,
                'details': selected_details,
                'score': item['score'] if passed else 0
            }
        
        st.markdown("---")
    
    # 保存按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 保存进度", use_container_width=True):
            # 收集所有评分
            all_scores = {}
            for module_name in evaluation['modules']:
                for item in data_store.modules[module_name]['items']:
                    item_id = item['id']
                    if f"score_{item_id}" in st.session_state:
                        all_scores[item_id] = st.session_state[f"score_{item_id}"]
            
            # 计算当前得分
            current_score = sum(s['score'] for s in all_scores.values())
            current_key_score = sum(
                s['score'] for s in all_scores.values()
                if data_store.modules[[m for m in evaluation['modules'] 
                    if any(i['id'] == s.split('_')[1] for i in data_store.modules[m]['items'])][0]]['items'][0]['type'] == '重点'
            ) if all_scores else 0
            
            # 更新评估
            data_store.update_evaluation(evaluation['id'], {
                'current_score': current_score
            })
            
            # 保存评分明细
            data_store.save_scores(evaluation['id'], all_scores)
            
            # 更新会话状态
            st.session_state.current_evaluation = data_store.get_evaluation(evaluation['id'])
            
            st.success("✅ 保存成功！")
            st.rerun()
    
    with col2:
        if st.button("✅ 提交评估", type="primary", use_container_width=True):
            # 计算得分
            all_scores = {}
            for module_name in evaluation['modules']:
                for item in data_store.modules[module_name]['items']:
                    item_id = item['id']
                    if f"score_{item_id}" in st.session_state:
                        all_scores[item_id] = st.session_state[f"score_{item_id}"]
            
            current_score = sum(s['score'] for s in all_scores.values())
            
            # 计算合格率
            pass_rate = (current_score / evaluation['total_score']) * 100 if evaluation['total_score'] > 0 else 0
            
            # 判断状态
            if pass_rate >= 90:
                status = '优秀'
            elif pass_rate >= 80:
                status = '合格'
            else:
                status = '待改进'
            
            # 更新评估
            data_store.update_evaluation(evaluation['id'], {
                'current_score': current_score,
                'status': status
            })
            
            # 保存评分明细
            data_store.save_scores(evaluation['id'], all_scores)
            
            st.success(f"✅ 评估提交成功！最终得分：{current_score}分，状态：{status}")
            st.session_state.current_evaluation = None
            st.rerun()
    
    with col3:
        if st.button("❌ 取消评估", use_container_width=True):
            st.session_state.current_evaluation = None
            st.rerun()

def render_evaluation():
    """评估页面"""
    if st.session_state.current_evaluation:
        render_evaluation_detail()
    else:
        render_evaluation_create()

# ==================== 历史记录 ====================
def render_history():
    """历史记录"""
    st.title("📋 历史记录")
    
    data_store = st.session_state.data_store
    
    # 筛选条件
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        factories = {"全部": None}
        factories.update({f['id']: f['name'] for f in data_store.factories})
        selected_factory = st.selectbox("工厂", options=list(factories.keys()))
    
    with col2:
        start_date = st.date_input("开始日期", value=datetime.now().replace(day=1).date())
    
    with col3:
        end_date = st.date_input("结束日期", value=datetime.now().date())
    
    with col4:
        statuses = ["全部", "优秀", "合格", "待改进", "进行中"]
        selected_status = st.selectbox("状态", options=statuses)
    
    # 查询
    factory_id = factories[selected_factory]
    if selected_status == "全部":
        status = None
    else:
        status = selected_status
    
    evaluations = data_store.get_evaluations(
        factory_id=factory_id,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        status=status
    )
    
    # 显示结果
    if evaluations:
        # 准备数据
        df_data = []
        for ev in evaluations:
            factory = next((f for f in data_store.factories if f['id'] == ev['factory_id']), None)
            df_data.append({
                "ID": ev['id'],
                "工厂名称": factory['name'] if factory else '未知',
                "评估日期": ev['date'],
                "评估模块": ev['modules_str'],
                "总分": ev['total_score'],
                "得分": ev['current_score'],
                "状态": ev['status'],
                "评估员": ev['evaluator']
            })
        
        df = pd.DataFrame(df_data)
        
        # 数据表格
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 导出按钮
        if st.button("📥 导出Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='历史记录')
            st.download_button(
                "下载Excel文件",
                output.getvalue(),
                "评估历史记录.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("暂无符合条件的评估记录")

# ==================== 对比分析 ====================
def render_compare():
    """对比分析"""
    st.title("📊 对比分析")
    
    data_store = st.session_state.data_store
    evaluations = data_store.get_evaluations()
    
    completed_evaluations = [e for e in evaluations if e['status'] != '进行中']
    
    if len(completed_evaluations) < 2:
        st.warning("需要至少2条已完成的评估记录才能进行对比分析")
        return
    
    # 选择对比对象
    st.subheader("选择对比工厂")
    
    factories = {}
    for ev in completed_evaluations:
        factory = next((f for f in data_store.factories if f['id'] == ev['factory_id']), None)
        if factory:
            if factory['name'] not in factories:
                factories[factory['name']] = []
            factories[factory['name']].append(ev)
    
    selected_factory = st.selectbox("选择工厂", options=list(factories.keys()))
    
    if selected_factory:
        factory_evaluations = factories[selected_factory]
        
        if len(factory_evaluations) >= 2:
            # 时间趋势图
            st.subheader(f"📈 {selected_factory} 评估得分趋势")
            
            df_data = []
            for ev in sorted(factory_evaluations, key=lambda x: x['date']):
                df_data.append({
                    "日期": ev['date'],
                    "得分": ev['current_score'],
                    "总分": ev['total_score'],
                    "状态": ev['status']
                })
            
            df = pd.DataFrame(df_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['日期'],
                y=df['得分'],
                mode='lines+markers',
                name='得分',
                line=dict(color='#2196F3', width=3)
            ))
            
            fig.update_layout(
                title="评估得分趋势",
                xaxis_title="日期",
                yaxis_title="得分",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 详细对比表
            st.subheader("📊 详细对比")
            
            comparison_data = []
            for i, ev in enumerate(sorted(factory_evaluations, key=lambda x: x['date'])[-5:]):
                factory = next((f for f in data_store.factories if f['id'] == ev['factory_id']), None)
                comparison_data.append({
                    "评估日期": ev['date'],
                    "工厂名称": factory['name'] if factory else '未知',
                    "评估模块": ev['modules_str'],
                    "得分": ev['current_score'],
                    "总分": ev['total_score'],
                    "合格率": f"{(ev['current_score']/ev['total_score']*100):.1f}%",
                    "状态": ev['status']
                })
            
            df_compare = pd.DataFrame(comparison_data)
            st.dataframe(df_compare, use_container_width=True, hide_index=True)
            
            # 模块得分对比
            st.subheader("🎯 各模块得分对比")
            
            module_scores = {}
            for ev in factory_evaluations[-5:]:
                module_scores[ev['date']] = {}
                
                # 获取该评估的评分明细
                scores = data_store.get_scores(ev['id'])
                
                for module in ev['modules']:
                    module_total = sum(item['score'] for item in data_store.modules[module]['items'])
                    module_earned = 0
                    
                    for item in data_store.modules[module]['items']:
                        item_id = item['id']
                        if item_id in scores and scores[item_id]['passed']:
                            module_earned += scores[item_id]['score']
                    
                    module_scores[ev['date']][module] = {
                        'earned': module_earned,
                        'total': module_total
                    }
            
            # 转换为DataFrame
            module_df_data = []
            modules = set()
            for date_scores in module_scores.values():
                modules.update(date_scores.keys())
            
            for module in sorted(modules):
                row = {"模块": module}
                for date, scores in sorted(module_scores.items()):
                    if module in scores:
                        row[date] = f"{scores[module]['earned']}/{scores[module]['total']}"
                    else:
                        row[date] = "-"
                module_df_data.append(row)
            
            if module_df_data:
                module_df = pd.DataFrame(module_df_data)
                st.dataframe(module_df, use_container_width=True, hide_index=True)
            
        else:
            st.info(f"{selected_factory} 需要至少2条评估记录才能进行对比分析")

# ==================== 系统设置 ====================
def render_settings():
    """系统设置"""
    st.title("⚙️ 系统设置")
    
    data_store = st.session_state.data_store
    
    tab1, tab2, tab3 = st.tabs(["工厂管理", "用户管理", "系统信息"])
    
    with tab1:
        st.subheader("工厂列表")
        
        factory_data = []
        for factory in data_store.factories:
            # 统计该工厂的评估次数
            eval_count = len(data_store.get_evaluations(factory_id=factory['id']))
            factory_data.append({
                "ID": factory['id'],
                "工厂名称": factory['name'],
                "联系人": factory['contact'],
                "电话": factory['phone'],
                "评估次数": eval_count
            })
        
        df = pd.DataFrame(factory_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 添加新工厂（演示功能）
        st.subheader("添加新工厂")
        
        with st.expander("展开添加工厂表单"):
            new_name = st.text_input("工厂名称")
            new_contact = st.text_input("联系人")
            new_phone = st.text_input("联系电话")
            
            if st.button("添加工厂"):
                st.info("（演示版本）工厂添加功能待完善")
    
    with tab2:
        st.subheader("用户列表")
        
        user_data = []
        for user in data_store.users:
            user_data.append({
                "ID": user['id'],
                "用户名": user['username'],
                "姓名": user['name'],
                "角色": user['role']
            })
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.info("（演示版本）用户管理功能待完善")
    
    with tab3:
        st.subheader("系统信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**系统版本**\n\n工厂流程审核评分系统 v1.0.0")
            st.info(f"**部署方式**\n\nStreamlit Cloud")
        
        with col2:
            # 统计信息
            evaluations = data_store.evaluations
            completed = [e for e in evaluations if e['status'] != '进行中']
            
            st.metric("总评估数", len(evaluations))
            st.metric("已完成评估", len(completed))
            st.metric("注册工厂数", len(data_store.factories))
            st.metric("注册用户数", len(data_store.users))

# ==================== 主程序 ====================
def main():
    """主函数"""
    # 初始化会话状态
    init_session_state()
    
    # 渲染侧边栏
    page = render_sidebar()
    
    # 根据页面路由
    if st.session_state.logged_in:
        if page == "🏠 首页":
            render_dashboard()
        elif page == "📝 开始评估":
            render_evaluation()
        elif page == "📋 历史记录":
            render_history()
        elif page == "📊 对比分析":
            render_compare()
        elif page == "⚙️ 系统设置":
            render_settings()
    else:
        login_page()

if __name__ == "__main__":
    main()
