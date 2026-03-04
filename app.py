import streamlit as st
import pandas as pd
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

# ==================== 177分评分体系数据模型 ====================
class DataStore:
    """数据存储管理类（整合177分评分体系）"""
    
    def __init__(self):
        self.users = self._init_users()
        self.factories = self._init_factories()
        self.modules = self._init_177_modules()  # 使用177分评分体系
        self.evaluations = self._load_evaluations()
        self.scores = self._load_scores()
        self.total_system_score = 177  # 总分177分
    
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
    
    def _init_177_modules(self):
        """初始化177分完整评分体系（8大项+所有小项）"""
        return {
            # 第一大项：纸样、样衣制作（总分：14分）
            "纸样、样衣制作": {
                "total_score": 14,
                "items": [
                    # 小项1. 纸样开发标准（6分）
                    {"id": "p1_1", "name": "使用CAD软件制作/修改纸样", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p1_2", "name": "缝份清晰标记应合规", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p1_3", "name": "布纹线，剪口标注合规并清晰", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p1_4", "name": "放码标准（尺寸增量）遵守客户要求，并文档化", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p1_5", "name": "技术包（Tech Pack）应明确标注尺寸表、工艺说明与要求，及特殊工艺说明（尤其是特殊面料或设计）", "type": "重点", "score": 3,
                     "detail": [], "comment": "", "unqualified": []},
                    
                    # 小项2. 版本控制与追溯性（3分）
                    {"id": "p2_1", "name": "纸样版本控制系统（确保最新、准确、可追溯）", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p2_2", "name": "文档记录：纸样历史、修订、批准", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p2_3", "name": "物理纸样（平放/悬挂）及数字备份的安全存储", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    
                    # 小项3. 初版审核与文档化（5分）
                    {"id": "p3_1", "name": "尺寸与工艺审核，应符合技术包要求（检验记录）", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "p3_2", "name": "面辅料核对，并按要求进行功能性检测（检验记录）", "type": "重点", "score": 3,
                     "detail": [], "comment": "", "unqualified": []},
                ]
            },
            
            # 第二大项：面辅料品质控制（总分：34分）
            "面辅料品质控制": {
                "total_score": 34,
                "items": [
                    # 小项1. 面料仓库检查（5分）
                    {"id": "m1_1", "name": "合格/不合格品/待检标识应明确，分开堆放", "type": "非重点", "score": 1,
                     "detail": ["标识不明确", "未分开堆放"], "comment": "", "unqualified": ["标识不明确", "未分开堆放"]},
                    {"id": "m1_2", "name": "面料不可“井”字堆放，高度不可过高（建议<1.5m）（针织面料除外）", "type": "非重点", "score": 1,
                     "detail": ["面料井字堆放", "堆放高度过高"], "comment": "", "unqualified": ["面料井字堆放", "堆放高度过高"]},
                    {"id": "m1_3", "name": "不同颜色及批次（缸号）分开堆放", "type": "非重点", "score": 1,
                     "detail": [], "comment": "", "unqualified": []},
                    {"id": "m1_4", "name": "托盘存放不靠墙、不靠窗、避光储存及防潮防霉", "type": "非重点", "score": 1,
                     "detail": ["靠墙", "靠窗", "未避光储存", "未防潮防霉"], "comment": "", "unqualified": ["靠墙", "靠窗", "未避光储存", "未防潮防霉"]},
                    {"id": "m1_5", "name": "温湿度计及记录（湿度<65%）", "type": "非重点", "score": 1,
                     "detail": ["无温湿度计", "无记录", "湿度超标"], "comment": "监控湿度的变化，便于采取相应的解决方案（如抽湿）", "unqualified": []},
                    
                    # 小项2. 面料入库记录（2分）
                    {"id": "m2_1", "name": "面料厂验布记录/测试记录/缸差布", "type": "非重点", "score": 1,
                     "detail": ["无验布记录", "无测试记录", "无缸差布"], "comment": "测试记录和缸差布可预防面料品质问题和色差问题", "unqualified": ["无验布记录", "无测试记录", "无缸差布"]},
                    {"id": "m2_2", "name": "入库单（卷数，米数，克重等）", "type": "非重点", "score": 1,
                     "detail": ["无入库单", "信息不全"], "comment": "", "unqualified": []},
                    
                    # 小项3. 面料检验（织成试样检验）（5分）
                    {"id": "m3_1", "name": "四分制验布及现场演示", "type": "非重点", "score": 1,
                     "detail": ["无记录", "现场工人操作不规范"], "comment": "", "unqualified": ["无记录", "现场工人操作不规范"]},
                    {"id": "m3_2", "name": "500m以下全检，500m以上至少抽检10%（覆盖每缸）", "type": "重点", "score": 3,
                     "detail": ["500m以下未全检", "500m以上抽检不足10%"], "comment": "", "unqualified": ["500m以下未全检", "500m以上抽检不足10%"]},
                    {"id": "m3_3", "name": "核对面料厂缸差布和大货面料（颜色D65，克重，防静电）", "type": "非重点", "score": 1,
                     "detail": ["颜色不匹配", "克重差异", "无防静电检测"], "comment": "缸差核对要在灯箱里进行，灯光要用D65光源", "unqualified": []},
                    
                    # 小项4. 面料测试（1分）
                    {"id": "m4_1", "name": "每缸测试记录（如水洗色牢度，干湿色牢度，PH值）", "type": "非重点", "score": 1,
                     "detail": ["无测试记录", "记录不全"], "comment": "可以控制大货的色牢度，沾色等问题", "unqualified": []},
                    
                    # 小项5. 预缩记录和结果（6分）
                    {"id": "m5_1", "name": "面料缩率要求 ≤ 3%（水洗针织款除外）", "type": "重点", "score": 3,
                     "detail": ["缩率>3%"], "comment": "面料缩率大于3%时，成衣工厂的尺寸控制难度较大", "unqualified": []},
                    {"id": "m5_2", "name": "每缸缩率记录", "type": "重点", "score": 3,
                     "detail": ["无缩率记录", "记录不全"], "comment": "每缸缩率测试可以更好的控制大货成衣尺寸（纸版可以进行放缩率）", "unqualified": []},
                    
                    # 小项6. 面料出库记录及盘点记录（3分）
                    {"id": "m6_1", "name": "出库记录含款号，缸号，米数，色号，时间，领料人等信息", "type": "非重点", "score": 1,
                     "detail": ["信息不全", "无出库记录"], "comment": "", "unqualified": []},
                    {"id": "m6_2", "name": "盘点记录", "type": "非重点", "score": 1,
                     "detail": ["无盘点记录", "记录不全"], "comment": "", "unqualified": []},
                    {"id": "m6_3", "name": "库存1年以上面料不可使用", "type": "非重点", "score": 1,
                     "detail": ["使用库存1年以上面料"], "comment": "盘点一年以上的库存面料禁止使用（成衣撕裂牢度等会受影响）", "unqualified": []},
                    
                    # 小项7. 辅料仓库检查（2分）
                    {"id": "m7_1", "name": "辅料存放标识明确（订单/款号/色号，分类堆放）", "type": "非重点", "score": 1,
                     "detail": ["订单/款号/色号标识不清晰", "分类堆放标识不清晰"], "comment": "以防辅料发放错款", "unqualified": ["订单/款号/色号标识不清晰", "分类堆放标识不清晰"]},
                    {"id": "m7_2", "name": "辅料入库记录（品类，数量）", "type": "非重点", "score": 1,
                     "detail": ["无品类记录", "无数量记录"], "comment": "", "unqualified": ["无品类记录", "无数量记录"]},
                    
                    # 小项8. 辅料检验（1分）
                    {"id": "m8_1", "name": "正确辅料卡核对（型号，颜色，功能，内容，外观）", "type": "非重点", "score": 1,
                     "detail": ["无型号", "无颜色", "无功能", "无内容", "无外观"], "comment": "", "unqualified": ["无型号", "无颜色", "无功能", "无内容", "无外观"]},
                    
                    # 小项9. 辅料测试（3分）
                    {"id": "m9_1", "name": "织带，橡筋，拉链，绳子的预缩测试（水洗缩，烫蒸缩）", "type": "重点", "score": 3,
                     "detail": ["无预缩测试", "测试记录不全"], "comment": "预防做到衣服上起皱，起浪等问题", "unqualified": []},
                    
                    # 小项10. 辅料出库记录及盘点记录（3分）
                    {"id": "m10_1", "name": "出库记录含款号，数量，色号，时间，领料人等信息", "type": "非重点", "score": 1,
                     "detail": ["信息不全", "无出库记录"], "comment": "", "unqualified": []},
                    {"id": "m10_2", "name": "盘点记录", "type": "非重点", "score": 1,
                     "detail": ["无盘点记录", "记录不全"], "comment": "", "unqualified": []},
                    {"id": "m10_3", "name": "库存记录（保留至少1年）", "type": "非重点", "score": 1,
                     "detail": ["无库存记录", "记录保留不足1年"], "comment": "", "unqualified": []},
                ]
            },
            
            # 第三大项：产前会议控制（总分：21分）
            "产前会议控制": {
                "total_score": 21,
                "items": [
                    # 小项1. 参会人员（6分）
                    {"id": "pre1_1", "name": "技术部", "type": "非重点", "score": 1,
                     "detail": ["技术部未参会"], "comment": "技术部对前期开发比较了解，可以规避打样时发生的问题，更好的控制大货品质", "unqualified": []},
                    {"id": "pre1_2", "name": "质检部", "type": "非重点", "score": 1,
                     "detail": ["质检部未参会"], "comment": "质量部门要跟进技术部提出的问题点及大货品质", "unqualified": []},
                    {"id": "pre1_3", "name": "业务部", "type": "非重点", "score": 1,
                     "detail": ["业务部未参会"], "comment": "业务部门告知面辅料情况及订单进度", "unqualified": []},
                    {"id": "pre1_4", "name": "生产部（裁剪，生产主管，生产组长）", "type": "非重点", "score": 1,
                     "detail": ["无裁剪", "无生产主管", "无生产组长"], "comment": "", "unqualified": ["无裁剪", "无生产主管", "无生产组长"]},
                    {"id": "pre1_5", "name": "后道（后道主管）", "type": "非重点", "score": 1,
                     "detail": ["后道主管未参会"], "comment": "", "unqualified": []},
                    {"id": "pre1_6", "name": "二次加工产品（印花/绣花/水洗/烫钻等）各工序负责人必须参会", "type": "非重点", "score": 1,
                     "detail": ["二次加工负责人未参会"], "comment": "二次加工负责人主要时了解二次加工的产品如何控制品质", "unqualified": []},
                    
                    # 小项2. 工艺标准传达及预防措施（10分）
                    {"id": "pre2_1", "name": "客户确认样", "type": "非重点", "score": 1,
                     "detail": ["无客户确认样"], "comment": "", "unqualified": []},
                    {"id": "pre2_2", "name": "确认意见，明确客户要求", "type": "非重点", "score": 1,
                     "detail": ["无确认意见", "客户要求不明确"], "comment": "", "unqualified": []},
                    {"id": "pre2_3", "name": "试生产样（客户确认码，最小码及最大码）和封样", "type": "重点", "score": 3,
                     "detail": ["无客户确认码", "无最大码", "无最小码", "无封样"], "comment": "做最小码和最大码衣服，可提前预知大货可能出现的问题", "unqualified": ["无客户确认码", "无最大码", "无最小码", "无封样"]},
                    {"id": "pre2_4a", "name": "工艺单需覆盖：重点工序难点（制作领子，门襟等小样）及解决方案", "type": "非重点", "score": 1,
                     "detail": ["无重点工序难点说明", "无解决方案"], "comment": "给车间生产员工一个质量标准参照", "unqualified": []},
                    {"id": "pre2_4b", "name": "工艺单需覆盖：试生产样的外观/尺寸/克重/试身的问题及解决方案", "type": "非重点", "score": 1,
                     "detail": ["无试生产样问题记录", "无解决方案"], "comment": "", "unqualified": []},
                    {"id": "pre2_4c", "name": "工艺单需覆盖：对条对格，花型定位等要求", "type": "非重点", "score": 1,
                     "detail": ["无对条对格要求", "无花型定位要求"], "comment": "", "unqualified": []},
                    {"id": "pre2_4d", "name": "工艺单需覆盖：特别关注撕裂强度的缝制工艺的风险", "type": "非重点", "score": 1,
                     "detail": ["无撕裂强度风险关注"], "comment": "", "unqualified": []},
                    {"id": "pre2_4e", "name": "工艺单需覆盖：特别关注粘衬环节的风险（颜色差异，透胶，粘衬颜色）", "type": "非重点", "score": 1,
                     "detail": ["无粘衬环节风险关注"], "comment": "", "unqualified": []},
                    {"id": "pre2_4f", "name": "工艺单需覆盖：轻薄产品包装方法风险评估（皱，滑落等）", "type": "非重点", "score": 1,
                     "detail": ["无轻薄产品包装风险评估"], "comment": "", "unqualified": []},
                    
                    # 小项3. 技术难点分析（2分）
                    {"id": "pre3_1", "name": "提出相应的改进建议", "type": "非重点", "score": 1,
                     "detail": ["无改进建议"], "comment": "", "unqualified": []},
                    {"id": "pre3_2", "name": "明确跟进人员及负责人", "type": "非重点", "score": 1,
                     "detail": ["无跟进人员", "无负责人"], "comment": "", "unqualified": []},
                    
                    # 小项4. 会议记录执行（2分）
                    {"id": "pre4_1", "name": "会议记录完整，参会人员签字确认", "type": "非重点", "score": 1,
                     "detail": ["记录不完整", "无签字确认"], "comment": "", "unqualified": []},
                    {"id": "pre4_2", "name": "会议记录随工艺单确认样一起流转至生产各部门", "type": "非重点", "score": 1,
                     "detail": ["未流转至生产部门"], "comment": "", "unqualified": []},
                ]
            },
            
            # 第四大项：裁剪品质控制（总分：30分）
            "裁剪品质控制": {
                "total_score": 30,
                "items": [
                    # 小项1. 面料松布（4分）
                    {"id": "cut1_1", "name": "面料不可捆扎", "type": "非重点", "score": 1,
                     "detail": ["面料捆扎"], "comment": "放缩后困扎面料，会影响面料的回缩", "unqualified": []},
                    {"id": "cut1_2", "name": "面料不可多卷混放", "type": "非重点", "score": 1,
                     "detail": ["多卷混放"], "comment": "多卷放在一起，会影响压在下方面料的回缩，敏感面料会产生压痕", "unqualified": []},
                    {"id": "cut1_3", "name": "面料不可落地摆放", "type": "非重点", "score": 1,
                     "detail": ["面料落地"], "comment": "预防脏污，潮湿等问题", "unqualified": []},
                    {"id": "cut1_4", "name": "现场标识清晰（订单号，缸号/卷号，开始及结束时间）", "type": "重点", "score": 3,
                     "detail": ["订单号标识不清晰", "缸号/卷号不清晰", "开始及结束时间不清晰"], "comment": "", "unqualified": ["订单号标识不清晰", "缸号/卷号不清晰", "开始及结束时间不清晰"]},
                    
                    # 小项2. 待裁（3分）
                    {"id": "cut2_1", "name": "复核面料测试报告，松布时效", "type": "非重点", "score": 1,
                     "detail": ["未复核面料测试报告", "松布时效不足"], "comment": "", "unqualified": []},
                    {"id": "cut2_2", "name": "裁剪计划单及签字", "type": "非重点", "score": 1,
                     "detail": ["无裁剪计划单", "无签字"], "comment": "", "unqualified": []},
                    {"id": "cut2_3", "name": "唛架的核对（是否缺失，对码）", "type": "非重点", "score": 1,
                     "detail": ["唛架缺失", "对码错误"], "comment": "", "unqualified": []},
                    
                    # 小项3. 铺布（7分）
                    {"id": "cut3_1", "name": "确认铺布方式（单向/双向/定位），确保一件一方向", "type": "非重点", "score": 1,
                     "detail": ["铺布方式错误", "方向不一致"], "comment": "预防大货有色差，色光", "unqualified": []},
                    {"id": "cut3_2", "name": "要求面料平整，无褶皱，无拉伸变形，无纬斜，且布边对齐", "type": "非重点", "score": 1,
                     "detail": ["面料不平整有褶皱", "拉伸变形", "纬斜", "布边未对齐"], "comment": "", "unqualified": ["面料不平整有褶皱", "拉伸变形", "纬斜", "布边未对齐"]},
                    {"id": "cut3_3", "name": "铺布层数（50-80层）薄料高度<5cm，其他面料最高不能超过12cm（自动裁床根据裁床限定高度）", "type": "非重点", "score": 1,
                     "detail": ["层数超标", "高度超标"], "comment": "控制裁片的精准度，（层高太高容易偏刀，尺寸控制不准确）", "unqualified": []},
                    {"id": "cut3_4", "name": "每卷面料需要用隔层纸或面料隔开", "type": "非重点", "score": 1,
                     "detail": ["未用隔层纸/面料隔开"], "comment": "", "unqualified": []},
                    {"id": "cut3_5", "name": "弹力面料铺布后须静置2小时", "type": "重点", "score": 3,
                     "detail": ["未静置", "静置时间不足2小时"], "comment": "以防铺布时把面料拉伸", "unqualified": []},
                    {"id": "cut3_6", "name": "铺布完成后用夹子四周固定，中间用重物压实（自动裁床除外）", "type": "非重点", "score": 1,
                     "detail": ["未固定", "未压实"], "comment": "", "unqualified": []},
                    {"id": "cut3_7", "name": "剩余面料布头需标识清晰以备换片", "type": "非重点", "score": 1,
                     "detail": ["布头标识不清晰"], "comment": "控制换片导致色差", "unqualified": []},
                    
                    # 小项4. 裁片（6分）
                    {"id": "cut4_1", "name": "裁片大小的复核（上中下各3片）", "type": "重点", "score": 3,
                     "detail": ["未复核", "复核不全面"], "comment": "复核裁片的精准度", "unqualified": []},
                    {"id": "cut4_2", "name": "验片外观（布疵，勾丝，污渍，印花等）", "type": "重点", "score": 3,
                     "detail": ["未验片", "验片不全面"], "comment": "", "unqualified": []},
                    {"id": "cut4_3", "name": "编号", "type": "非重点", "score": 1,
                     "detail": ["未编号", "编号错误"], "comment": "", "unqualified": []},
                    {"id": "cut4_4", "name": "用捆扎绳卷筒式捆扎（捆扎绳有裁片信息：款号，分包号，件数，缸号，尺码等）", "type": "非重点", "score": 1,
                     "detail": ["未卷筒式捆扎", "捆扎绳信息不全"], "comment": "", "unqualified": []},
                    {"id": "cut4_5", "name": "分码分色存放（浅色需覆盖分开放置），禁止落地", "type": "非重点", "score": 1,
                     "detail": ["裁片未分码分色存放", "裁片落地", "浅色未覆盖"], "comment": "预防沾色，脏污等", "unqualified": ["裁片未分码分色存放", "裁片落地"]},
                    
                    # 小项5. 粘衬（5分）
                    {"id": "cut5_1", "name": "粘衬机清洁和机器维护", "type": "非重点", "score": 1,
                     "detail": ["粘衬机不清洁", "无维护记录"], "comment": "", "unqualified": []},
                    {"id": "cut5_2", "name": "粘衬机参数（衬厂提供）和工艺单吻合", "type": "非重点", "score": 1,
                     "detail": ["参数不吻合"], "comment": "", "unqualified": []},
                    {"id": "cut5_3", "name": "粘衬丝缕方向同面料丝缕方向", "type": "非重点", "score": 1,
                     "detail": ["丝缕方向不一致"], "comment": "", "unqualified": []},
                    {"id": "cut5_4", "name": "入粘衬机时按丝缕方向送入", "type": "非重点", "score": 1,
                     "detail": ["未按丝缕方向送入"], "comment": "预防裁片粘衬后变形", "unqualified": []},
                    {"id": "cut5_5", "name": "首批粘衬的裁片，需做剥离测试，是否透胶等评估风险", "type": "非重点", "score": 1,
                     "detail": ["未做剥离测试", "未评估风险"], "comment": "如有问题，立即会报裁剪主管跟进解决", "unqualified": []},
                ]
            },
            
            # 第五大项：缝制工艺品质控制（总分：36分）
            "缝制工艺品质控制": {
                "total_score": 36,
                "items": [
                    # 小项1. 缝制设备/特种设备（4分）
                    {"id": "sew1_1", "name": "定期维护保养记录", "type": "非重点", "score": 1,
                     "detail": ["无维护保养记录", "记录不全"], "comment": "", "unqualified": []},
                    {"id": "sew1_2", "name": "压脚类型与面料是否匹配", "type": "非重点", "score": 1,
                     "detail": ["压脚类型不匹配"], "comment": "控制缝制起皱，磨破面料等问题", "unqualified": []},
                    {"id": "sew1_3", "name": "针距/针型号是否匹配", "type": "非重点", "score": 1,
                     "detail": ["针距不匹配", "针型号不匹配"], "comment": "", "unqualified": []},
                    {"id": "sew1_4", "name": "缝纫线硅油用量及线迹张力核查（线迹平整度等）", "type": "非重点", "score": 1,
                     "detail": ["硅油用量不当", "线迹张力不合适", "线迹不平整"], "comment": "", "unqualified": []},
                    
                    # 小项2. 点位及小烫（9分）
                    {"id": "sew2_1", "name": "禁止使用高温消色笔", "type": "重点", "score": 3,
                     "detail": ["使用高温消色笔"], "comment": "高温消色笔在低温（零下）会显现出来", "unqualified": []},
                    {"id": "sew2_2", "name": "核查丝缕方向是否与纸样标注的方向一致", "type": "非重点", "score": 1,
                     "detail": ["丝缕方向不一致"], "comment": "", "unqualified": []},
                    {"id": "sew2_3", "name": "点位前确保裁片和纸样吻合，避免偏移", "type": "非重点", "score": 1,
                     "detail": ["裁片和纸样不吻合", "点位偏移"], "comment": "", "unqualified": []},
                    {"id": "sew2_4", "name": "烫台用白布包裹及台面干净整洁，定期更换", "type": "非重点", "score": 1,
                     "detail": ["未用白布包裹", "台面不干净", "未定期更换"], "comment": "", "unqualified": []},
                    {"id": "sew2_5", "name": "烫斗温度和面料匹配（建议真丝面料低于110度）", "type": "非重点", "score": 1,
                     "detail": ["温度不匹配"], "comment": "", "unqualified": []},
                    {"id": "sew2_6", "name": "烫工的操作手法是否正确（见指南）", "type": "非重点", "score": 1,
                     "detail": ["操作手法不正确"], "comment": "", "unqualified": []},
                    {"id": "sew2_7", "name": "是否有激光印/透胶", "type": "非重点", "score": 1,
                     "detail": ["有激光印", "有透胶"], "comment": "", "unqualified": []},
                    {"id": "sew2_8", "name": "是否变型/变色", "type": "非重点", "score": 1,
                     "detail": ["变型", "变色"], "comment": "", "unqualified": []},
                    {"id": "sew2_9", "name": "粘衬牢固度", "type": "非重点", "score": 1,
                     "detail": ["粘衬不牢固"], "comment": "", "unqualified": []},
                    
                    # 小项3. 缝制中（8分）
                    {"id": "sew3_1", "name": "重点工序悬挂指示牌及标准小样（领子，口袋，门襟，袖口等）", "type": "非重点", "score": 1,
                     "detail": ["无指示牌", "无标准小样"], "comment": "", "unqualified": []},
                    {"id": "sew3_2", "name": "重点工序是否有辅助工具提高质量稳定性（压脚，鱼骨，模版等）", "type": "非重点", "score": 1,
                     "detail": ["无辅助工具"], "comment": "", "unqualified": []},
                    {"id": "sew3_3", "name": "现场是否有首件样及资料（工艺单，辅料卡，产前会议记录等）", "type": "非重点", "score": 1,
                     "detail": ["无首件样", "资料不全"], "comment": "", "unqualified": []},
                    {"id": "sew3_4", "name": "线上车工技能评估（半成品的质量-皱/对称等）", "type": "重点", "score": 3,
                     "detail": ["未评估", "评估不合格"], "comment": "", "unqualified": []},
                    {"id": "sew3_5", "name": "巡检是否定时巡查重点工序质量", "type": "非重点", "score": 1,
                     "detail": ["未定时巡检", "巡检不全面"], "comment": "", "unqualified": []},
                    {"id": "sew3_6", "name": "线头是否随做随剪", "type": "非重点", "score": 1,
                     "detail": ["线头未随做随剪"], "comment": "", "unqualified": []},
                    {"id": "sew3_7", "name": "半成品不可捆扎过紧，避免褶皱", "type": "非重点", "score": 1,
                     "detail": ["捆扎过紧", "有褶皱"], "comment": "", "unqualified": []},
                    {"id": "sew3_8", "name": "流转箱用布包裹，半成品分色分码区分", "type": "非重点", "score": 1,
                     "detail": ["未用布包裹", "未分色分码"], "comment": "预防半成品衣服在流转过程中勾纱，脏污", "unqualified": []},
                    
                    # 小项4. 线上检验（9分）
                    {"id": "sew4_1", "name": "尺寸检验 每色每码 >10% 并记录", "type": "重点", "score": 3,
                     "detail": ["检验比例不足10%", "未记录"], "comment": "", "unqualified": []},
                    {"id": "sew4_2", "name": "外观检验 每色每码 > 10% 并记录", "type": "重点", "score": 3,
                     "detail": ["检验比例不足10%", "未记录"], "comment": "", "unqualified": []},
                    {"id": "sew4_3", "name": "试身小中大码和封样/首件样 对比外观及功能性（特别是重点工序），并记录", "type": "重点", "score": 3,
                     "detail": ["未试身", "未对比", "未记录"], "comment": "", "unqualified": []},
                    {"id": "sew4_4", "name": "中检合格品/非合格品分开摆放", "type": "非重点", "score": 1,
                     "detail": ["未分开摆放"], "comment": "", "unqualified": []},
                    {"id": "sew4_5", "name": "不合格品需立即退回对应工序翻修，并有组长跟进", "type": "非重点", "score": 1,
                     "detail": ["未退回翻修", "无组长跟进"], "comment": "", "unqualified": []},
                    {"id": "sew4_6", "name": "中检检验按工序记录疵点类型及比例，以便车工技能提升", "type": "非重点", "score": 1,
                     "detail": ["未记录疵点类型", "未记录比例"], "comment": "", "unqualified": []},
                    
                    # 小项5. 唛头（3分）
                    {"id": "sew5_1", "name": "按裁剪数量尺码数领取主标，尺码表，洗标", "type": "非重点", "score": 1,
                     "detail": ["领取数量不符", "漏领"], "comment": "", "unqualified": []},
                    {"id": "sew5_2", "name": "尺码表，洗标顺序不可错乱，以阅读方向缝制", "type": "非重点", "score": 1,
                     "detail": ["顺序错乱", "缝制方向错误"], "comment": "", "unqualified": []},
                    {"id": "sew5_3", "name": "一码一清，一款一清，如有剩余唛头，需追溯原因，并有组长跟进解决", "type": "非重点", "score": 1,
                     "detail": ["未一码一清", "未一款一清", "剩余唛头未追溯"], "comment": "预防大货衣服错码", "unqualified": []},
                ]
            },
            
            # 第六大项：后道品质控制（总分：28分）
            "后道品质控制": {
                "total_score": 28,
                "items": [
                    # 小项1. 后道区域（3分）
                    {"id": "post1_1", "name": "后道区域划分明确，并有清晰标识", "type": "非重点", "score": 1,
                     "detail": ["区域划分不明确", "无清晰标识"], "comment": "", "unqualified": []},
                    {"id": "post1_2", "name": "中转箱需要明确标识", "type": "非重点", "score": 1,
                     "detail": ["中转箱无标识", "标识不清晰"], "comment": "", "unqualified": []},
                    {"id": "post1_3", "name": "样衣和资料悬挂在后道区域", "type": "非重点", "score": 1,
                     "detail": ["样衣未悬挂", "资料未悬挂"], "comment": "供后道核对品质和尺寸等", "unqualified": []},
                    
                    # 小项2. 锁眼钉扣（4分）
                    {"id": "post2_1", "name": "按纸样点位，（禁止使用高温消色笔）", "type": "非重点", "score": 1,
                     "detail": ["未按纸样点位", "使用高温消色笔"], "comment": "", "unqualified": []},
                    {"id": "post2_2", "name": "每码一纸样，标识对应尺码", "type": "非重点", "score": 1,
                     "detail": ["非每码一纸样", "无尺码标识"], "comment": "", "unqualified": []},
                    {"id": "post2_3", "name": "核对锁眼纽扣的大小，位置；钉扣的牢度和纽扣的吻合度；锁眼线迹需干净整洁", "type": "非重点", "score": 1,
                     "detail": ["大小/位置不符", "牢度和吻合度差", "线迹不干净整洁"], "comment": "", "unqualified": ["大小/位置", "牢度和吻合度", "线迹不干净整洁"]},
                    {"id": "post2_4", "name": "核查功能性", "type": "非重点", "score": 1,
                     "detail": ["功能性异常"], "comment": "", "unqualified": []},
                    
                    # 小项3. 整烫（4分）
                    {"id": "post3_1", "name": "是否有摇臂烫台（胸省，袖笼等）", "type": "非重点", "score": 1,
                     "detail": ["无摇臂烫台"], "comment": "", "unqualified": []},
                    {"id": "post3_2", "name": "是否过度压烫，是否有激光印", "type": "非重点", "score": 1,
                     "detail": ["过度压烫", "有激光印"], "comment": "", "unqualified": ["过度压烫", "有激光印"]},
                    {"id": "post3_3", "name": "整烫后合理放置（轻薄款建议悬挂防皱）", "type": "非重点", "score": 1,
                     "detail": ["放置不合理", "轻薄款未悬挂"], "comment": "", "unqualified": []},
                    {"id": "post3_4", "name": "平放不易过高，底层不可以明显褶皱", "type": "非重点", "score": 1,
                     "detail": ["平放过高", "底层有明显褶皱"], "comment": "", "unqualified": []},
                    
                    # 小项4. 总检（11分）
                    {"id": "post4_1", "name": "检验区域光源不得低于750LUX，温湿度计及记录（室内湿度超过65%，关注产品潮湿度）", "type": "非重点", "score": 1,
                     "detail": ["光源低于750LUX", "无温湿度计及记录"], "comment": "", "unqualified": ["光源低于750LUX", "无温湿度计及记录"]},
                    {"id": "post4_2", "name": "按码数100%检验（尺寸，标，外观，功能，湿度，试身效果等），后道主管/质量经理需抽查合格品（建议抽查每人员5%）", "type": "重点", "score": 3,
                     "detail": ["未按码数100%检验", "未按要求抽查"], "comment": "", "unqualified": ["未按码数100%检验", "未按要求抽查"]},
                    {"id": "post4_3", "name": "疵点问题需清晰标识", "type": "非重点", "score": 1,
                     "detail": ["疵点未标识", "标识不清晰"], "comment": "", "unqualified": []},
                    {"id": "post4_4", "name": "待检品/合格品/不合格品分开放置", "type": "非重点", "score": 1,
                     "detail": ["未分开放置"], "comment": "", "unqualified": []},
                    {"id": "post4_5", "name": "污渍清理需在指定区域清理（确保返工后无水印，无变色，无异味）", "type": "非重点", "score": 1,
                     "detail": ["未在指定区域清理", "返工后有水印/变色/异味"], "comment": "", "unqualified": []},
                    {"id": "post4_6", "name": "总检跟踪翻修品，当天款当天结束", "type": "非重点", "score": 1,
                     "detail": ["未跟踪翻修品", "当天款未当天结束"], "comment": "", "unqualified": []},
                    {"id": "post4_7", "name": "总检汇总100%检验记录（报告）和疵点问题（建议汇总次品率），并反馈生产部门改进", "type": "重点", "score": 3,
                     "detail": ["未汇总检验记录", "未汇总疵点问题", "未反馈改进"], "comment": "后续提升大货的品质的依据", "unqualified": []},
                    
                    # 小项5. 包装（5分）
                    {"id": "post5_1", "name": "是否有标准包装样", "type": "非重点", "score": 1,
                     "detail": ["无标准包装样"], "comment": "", "unqualified": []},
                    {"id": "post5_2", "name": "分色分码分区包装（潮湿度需达到客户要求）", "type": "非重点", "score": 1,
                     "detail": ["未分色分码分区", "潮湿度未达标"], "comment": "", "unqualified": []},
                    {"id": "post5_3", "name": "胶袋贴纸和裁剪数尺码吻合，一码一清，分码入筐", "type": "重点", "score": 3,
                     "detail": ["贴纸和裁剪数不吻合", "未一码一清", "未分码入筐"], "comment": "预防包装错码", "unqualified": []},
                    {"id": "post5_4", "name": "一款一清，如有剩余贴纸，需追溯原因，并由组长跟进解决", "type": "非重点", "score": 1,
                     "detail": ["未一款一清", "剩余贴纸未追溯"], "comment": "", "unqualified": []},
                    {"id": "post5_5", "name": "9点测试记录及检针报告", "type": "非重点", "score": 1,
                     "detail": ["无9点测试记录", "无检针报告"], "comment": "控制衣服内的金属和安全性", "unqualified": []},
                    
                    # 小项6. 装箱（4分）
                    {"id": "post6_1", "name": "按装箱单装箱（业务部门评估复核）", "type": "非重点", "score": 1,
                     "detail": ["未按装箱单装箱", "未复核"], "comment": "", "unqualified": []},
                    {"id": "post6_2", "name": "纸箱尺寸和质量是否按客人要求", "type": "非重点", "score": 1,
                     "detail": ["尺寸不符合要求", "质量不符合要求"], "comment": "", "unqualified": ["尺寸不符合要求", "质量不符合要求"]},
                    {"id": "post6_3", "name": "纸箱外观（不可鼓箱，不可超重，不可空箱）", "type": "非重点", "score": 1,
                     "detail": ["鼓箱", "超重", "空箱"], "comment": "", "unqualified": ["鼓箱", "超重", "空箱"]},
                    {"id": "post6_4", "name": "箱唛贴纸信息核对，里外一致（与箱单/订单）", "type": "非重点", "score": 1,
                     "detail": ["信息不一致", "里外不一致"], "comment": "", "unqualified": []},
                ]
            },
            
            # 第七大项：质量部门品质控制（总分：1分）
            "质量部门品质控制": {
                "total_score": 1,
                "items": [
                    # 小项1. AQL抽检（1分）
                    {"id": "q1_1", "name": "按AQL4.0/L2检验", "type": "非重点", "score": 1,
                     "detail": ["未按AQL4.0/L2检验"], "comment": "", "unqualified": []},
                ]
            },
            
            # 第八大项：其他评分（总分：5分）
            "其他评分": {
                "total_score": 5,
                "items": [
                    # 小项1. Dummy（1分）
                    {"id": "o1_1", "name": "是否有标准Dummy", "type": "非重点", "score": 1,
                     "detail": ["无标准Dummy"], "comment": "", "unqualified": []},
                    
                    # 小项2. 利器管控（3分）
                    {"id": "o2_1", "name": "是否专人专管（如裁剪刀等）", "type": "非重点", "score": 1,
                     "detail": ["非专人专管"], "comment": "", "unqualified": []},
                    {"id": "o2_2", "name": "是否有完整的换针记录", "type": "非重点", "score": 1,
                     "detail": ["无换针记录", "记录不完整"], "comment": "", "unqualified": []},
                    {"id": "o2_3", "name": "小剪刀等是否捆绑固定", "type": "非重点", "score": 1,
                     "detail": ["未捆绑固定"], "comment": "", "unqualified": []},
                    
                    # 小项3. 其他（1分）
                    {"id": "o3_1", "name": "个人生活物品食物等禁止出现在生产区域", "type": "非重点", "score": 1,
                     "detail": ["生产区域有生活物品", "生产区域有食物"], "comment": "", "unqualified": []},
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
        evaluation['system_total_score'] = self.total_system_score  # 177分体系
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
            filtered = [ev for ev in filtered if ev
