import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import base64

# ==================== 页面配置 & 现代感样式 ====================
st.set_page_config(
    page_title="工厂流程审核评分系统",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义现代感CSS
def add_custom_css():
    st.markdown("""
    <style>
    /* 整体样式优化 */
    .stApp {
        background-color: #f8f9fa;
    }
    /* 卡片样式 */
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }
    /* 按钮样式 */
    .stButton>button {
        border-radius: 8px;
        height: 38px;
        font-weight: 500;
    }
    /* 输入框样式 */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stDateInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        box-shadow: 2px 0 10px rgba(0,0,0,0.03);
    }
    /* 展开框样式 */
    [data-testid="stExpander"] {
        border-radius: 12px;
        background-color: white;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    /* 标题样式 */
    h1, h2, h3, h4 {
        color: #1e293b;
        font-weight: 600;
    }
    /* 橙色重点文字 */
    .orange-text {
        color: #f97316;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

add_custom_css()

# ==================== 数据初始化 ====================
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==================== 完整8大项评分体系数据模型 ====================
class DataStore:
    def __init__(self):
        self.users = [{"id": 1, "username": "admin", "password": "admin123", "name": "管理员"}]
        self.factories = [
            {"id": 1, "name": "深圳XX服装厂"}, 
            {"id": 2, "name": "广州XX制衣厂"},
            {"id": 3, "name": "东莞XX服饰厂"},
            {"id": 4, "name": "佛山XX针织厂"}
        ]
        self.modules = self._init_modules()
        self.evaluations = self._load_evaluations()
        self.total_system_score = 177  # 总分177

    def _init_modules(self):
        """完整的8大项评估体系（严格保留原始项，无新增/修改）"""
        return {
            # 1. 纸样、样衣制作 (14分)
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
                            {"id": "p1_5", "name": "技术包（Tech Pack）应明确标注尺寸表、工艺说明与特殊工艺说明", "score": 3, "is_key": True, "details": [], "comment": "清晰的技术包可确保生产符合客户要求，减少返工"},
                        ]
                    },
                    "版本控制与追溯性": {
                        "total_score": 3,
                        "items": [
                            {"id": "p2_1", "name": "纸样版本控制系统（确保最新、准确、可追溯）", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p2_2", "name": "文档记录：纸样历史、修订、批准", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "p2_3", "name": "物理纸样及数字备份的安全存储", "score": 1, "is_key": False, "details": [], "comment": ""},
                        ]
                    },
                    "初版审核与文档化": {
                        "total_score": 5,
                        "items": [
                            {"id": "p3_1", "name": "尺寸与工艺审核，应符合技术包要求（检验记录）", "score": 2, "is_key": True, "details": [], "comment": "尺寸审核可提前发现问题，避免批量生产错误"},
                            {"id": "p3_2", "name": "面辅料核对，并按要求进行功能性检测（检验记录）", "score": 3, "is_key": True, "details": [], "comment": "面辅料检测可确保产品品质符合标准"},
                        ]
                    }
                }
            },

            # 2. 面辅料品质控制 (34分)
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
                    },
                    "辅料品质控制": {
                        "total_score": 15,
                        "items": [
                            {"id": "m3_1", "name": "辅料采购符合环保要求（有检测报告）", "score": 2, "is_key": True, "details": ["无检测报告", "不符合环保要求"], "comment": "环保检测可确保产品符合出口标准"},
                            {"id": "m3_2", "name": "辅料储存条件符合要求（防潮、防霉、防蛀）", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "m3_3", "name": "辅料批次管理可追溯", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "m3_4", "name": "拉链、纽扣等功能性测试记录完整", "score": 3, "is_key": True, "details": ["无测试记录", "测试项目不全"], "comment": "功能性测试可确保辅料耐用性"},
                            {"id": "m3_5", "name": "印花/绣花打样确认流程规范", "score": 3, "is_key": True, "details": [], "comment": ""},
                            {"id": "m3_6", "name": "洗水标/吊牌内容符合客户要求", "score": 2, "is_key": True, "details": ["信息错误", "材质不符"], "comment": ""},
                            {"id": "m3_7", "name": "包装辅料（胶袋、纸箱）符合环保标准", "score": 3, "is_key": True, "details": [], "comment": "环保包装是出口产品的基本要求"},
                        ]
                    },
                    "面料检验": {
                        "total_score": 12,
                        "items": [
                            {"id": "m4_1", "name": "面料克重、幅宽抽检记录完整", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "m4_2", "name": "色牢度测试（水洗、摩擦、日晒）", "score": 3, "is_key": True, "details": ["未测试", "测试结果不达标"], "comment": "色牢度是面料品质的核心指标"},
                            {"id": "m4_3", "name": "缩水率测试记录", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "m4_4", "name": "外观检验（破洞、跳纱、污渍）", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "m4_5", "name": "面料功能性测试（防水、透气等）", "score": 3, "is_key": True, "details": [], "comment": "功能性测试确保产品符合设计要求"},
                        ]
                    }
                }
            },

            # 3. 产前会议 (10分)
            "产前会议": {
                "total_score": 10,
                "sub_modules": {
                    "会议组织": {
                        "total_score": 4,
                        "items": [
                            {"id": "c1_1", "name": "产前会议参会人员齐全（技术、生产、品管）", "score": 2, "is_key": True, "details": [], "comment": "全员参与可确保信息传递准确"},
                            {"id": "c1_2", "name": "会议记录完整并签字确认", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    },
                    "技术交底": {
                        "total_score": 6,
                        "items": [
                            {"id": "c2_1", "name": "工艺难点提前识别并制定解决方案", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "c2_2", "name": "客户特殊要求传达至所有相关人员", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "c2_3", "name": "首件确认标准明确", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    }
                }
            },

            # 4. 裁剪 (25分)
            "裁剪": {
                "total_score": 25,
                "sub_modules": {
                    "排料与唛架": {
                        "total_score": 8,
                        "items": [
                            {"id": "cut1_1", "name": "唛架制作优化（提高面料利用率）", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "cut1_2", "name": "唛架经审核批准后使用", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "cut1_3", "name": "不同尺码、颜色分开排料", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "cut1_4", "name": "布纹方向符合工艺要求", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    },
                    "裁剪操作": {
                        "total_score": 9,
                        "items": [
                            {"id": "cut2_1", "name": "面料松布时间符合要求（至少24小时）", "score": 2, "is_key": True, "details": [], "comment": "松布可减少面料张力，降低缩水率"},
                            {"id": "cut2_2", "name": "裁剪精度控制（误差±0.5cm）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "cut2_3", "name": "裁片数量核对准确", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "cut2_4", "name": "裁片标识清晰（款号、尺码、颜色、裁片名称）", "score": 2, "is_key": True, "details": ["标识缺失", "信息错误"], "comment": ""},
                            {"id": "cut2_5", "name": "刀口、定位孔位置准确", "score": 2, "is_key": False, "details": [], "comment": ""},
                        ]
                    },
                    "裁片管理": {
                        "total_score": 8,
                        "items": [
                            {"id": "cut3_1", "name": "裁片分类堆放，防止混淆", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "cut3_2", "name": "裁片检验（疵点、色差）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "cut3_3", "name": "裁片送车间交接记录完整", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "cut3_4", "name": "余料管理规范（标识、储存）", "score": 2, "is_key": False, "details": [], "comment": ""},
                        ]
                    }
                }
            },

            # 5. 缝制 (35分)
            "缝制": {
                "total_score": 35,
                "sub_modules": {
                    "工序安排": {
                        "total_score": 8,
                        "items": [
                            {"id": "sew1_1", "name": "工序流程图清晰并严格执行", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "sew1_2", "name": "员工技能与工序匹配", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "sew1_3", "name": "瓶颈工序识别并优化", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "sew1_4", "name": "生产线平衡率≥85%", "score": 2, "is_key": True, "details": [], "comment": "生产线平衡可提高整体效率"},
                        ]
                    },
                    "缝制工艺": {
                        "total_score": 15,
                        "items": [
                            {"id": "sew2_1", "name": "针距密度符合工艺要求（平车12-14针/3cm）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "sew2_2", "name": "线迹平整，无跳线、浮线、断线", "score": 2, "is_key": True, "details": ["跳线", "浮线", "断线"], "comment": ""},
                            {"id": "sew2_3", "name": "缝份大小均匀一致", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "sew2_4", "name": "止口顺直，无起皱、扭曲", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "sew2_5", "name": "袋位、扣位、袖笼等关键部位定位准确", "score": 3, "is_key": True, "details": [], "comment": "关键部位定位直接影响产品版型"},
                            {"id": "sew2_6", "name": "锁边/包边工艺符合要求", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "sew2_7", "name": "打结、回针牢固（起止针处）", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    },
                    "质量控制": {
                        "total_score": 12,
                        "items": [
                            {"id": "sew3_1", "name": "首件确认制度执行到位", "score": 3, "is_key": True, "details": [], "comment": "首件确认可提前发现工艺问题"},
                            {"id": "sew3_2", "name": "巡检频次合理（每2小时/次）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "sew3_3", "name": "返修品标识、记录、重检流程规范", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "sew3_4", "name": "成品尺寸抽检（关键尺寸）", "score": 3, "is_key": True, "details": [], "comment": ""},
                            {"id": "sew3_5", "name": "员工自检、互检制度落实", "score": 2, "is_key": False, "details": [], "comment": ""},
                        ]
                    }
                }
            },

            # 6. 后整 (25分)
            "后整": {
                "total_score": 25,
                "sub_modules": {
                    "整烫": {
                        "total_score": 8,
                        "items": [
                            {"id": "fin1_1", "name": "整烫温度、压力、时间符合面料要求", "score": 2, "is_key": True, "details": [], "comment": "合适的整烫参数可避免面料损伤"},
                            {"id": "fin1_2", "name": "成品定型效果良好（无烫痕、极光）", "score": 2, "is_key": True, "details": ["有烫痕", "有极光"], "comment": ""},
                            {"id": "fin1_3", "name": "整烫后尺寸符合规格", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin1_4", "name": "蒸汽品质符合要求（无杂质）", "score": 2, "is_key": False, "details": [], "comment": ""},
                        ]
                    },
                    "检验": {
                        "total_score": 9,
                        "items": [
                            {"id": "fin2_1", "name": "终检标准明确并培训到位", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin2_2", "name": "检验项目完整（外观、尺寸、工艺、功能）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin2_3", "name": "检验记录完整可追溯", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin2_4", "name": "不合格品处理流程规范（标识、隔离、返工）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin2_5", "name": "客户验货标准明确并执行", "score": 1, "is_key": False, "details": [], "comment": ""},
                        ]
                    },
                    "包装": {
                        "total_score": 8,
                        "items": [
                            {"id": "fin3_1", "name": "折叠标准符合客户要求", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin3_2", "name": "吊牌、洗水标位置准确", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "fin3_3", "name": "包装辅料（胶袋、纸箱）符合要求", "score": 2, "is_key": False, "details": [], "comment": ""},
                            {"id": "fin3_4", "name": "装箱单信息准确，外箱标识清晰", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    }
                }
            },

            # 7. 社会责任 (15分)
            "社会责任": {
                "total_score": 15,
                "sub_modules": {
                    "劳动合规": {
                        "total_score": 8,
                        "items": [
                            {"id": "soc1_1", "name": "工作时间符合劳动法规定（每周≤60小时）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "soc1_2", "name": "工资按时足额发放，有工资条", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "soc1_3", "name": "社保缴纳合规", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "soc1_4", "name": "无童工、强迫劳动", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    },
                    "工作环境": {
                        "total_score": 7,
                        "items": [
                            {"id": "soc2_1", "name": "消防设施齐全有效，消防通道畅通", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "soc2_2", "name": "车间通风、照明符合标准", "score": 1, "is_key": False, "details": [], "comment": ""},
                            {"id": "soc2_3", "name": "职业健康防护措施到位（口罩、手套等）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "soc2_4", "name": "应急预案及演练记录", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    }
                }
            },

            # 8. 管理体系 (19分)
            "管理体系": {
                "total_score": 19,
                "sub_modules": {
                    "质量管理": {
                        "total_score": 10,
                        "items": [
                            {"id": "mg1_1", "name": "有完善的质量管理手册/程序文件", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg1_2", "name": "内部审核计划及记录完整", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg1_3", "name": "客户投诉处理流程规范，有记录", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg1_4", "name": "持续改进措施及效果验证", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg1_5", "name": "员工培训计划及记录（品质、工艺）", "score": 2, "is_key": True, "details": [], "comment": ""},
                        ]
                    },
                    "文件管理": {
                        "total_score": 9,
                        "items": [
                            {"id": "mg2_1", "name": "技术文件受控管理（发放、回收、作废）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg2_2", "name": "生产记录完整可追溯（生产日报、检验记录）", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg2_3", "name": "供应商评估及管理记录", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg2_4", "name": "设备维护保养计划及记录", "score": 2, "is_key": True, "details": [], "comment": ""},
                            {"id": "mg2_5", "name": "记录保存期限符合要求（至少2年）", "score": 1, "is_key": False, "details": [], "comment": ""},
                        ]
                    }
                }
            }
        }

    def _load_evaluations(self):
        """加载已保存的评估记录"""
        eval_file = os.path.join(DATA_DIR, "evaluations.json")
        if os.path.exists(eval_file):
            try:
                with open(eval_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

# ==================== 核心功能函数 ====================
def save_evaluation(evaluation_data):
    """保存评估记录"""
    eval_file = os.path.join(DATA_DIR, "evaluations.json")
    evaluations = []
    if os.path.exists(eval_file):
        with open(eval_file, "r", encoding="utf-8") as f:
            evaluations = json.load(f)
    
    # 生成唯一ID
    new_id = 1
    if evaluations:
        new_id = max([e["id"] for e in evaluations]) + 1
    evaluation_data["id"] = new_id
    evaluation_data["create_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    evaluations.append(evaluation_data)
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump(evaluations, f, ensure_ascii=False, indent=2)
    return new_id

def generate_pdf_report(evaluation_data, data_store):
    """生成PDF评估报告"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # 标题
    elements.append(Paragraph("工厂流程审核评分报告", styles['Title']))
    elements.append(Spacer(1, 20))

    # 基本信息
    elements.append(Paragraph("一、基本信息", styles['Heading2']))
    elements.append(Paragraph(f"审核工厂：{evaluation_data['factory_name']}", styles['Normal']))
    elements.append(Paragraph(f"审核日期：{evaluation_data['evaluation_date']}", styles['Normal']))
    elements.append(Paragraph(f"审核人员：{evaluation_data['evaluator_name']}", styles['Normal']))
    elements.append(Spacer(1, 10))

    # 总分统计
    total_score = sum([float(v) for k, v in evaluation_data['scores'].items()])
    elements.append(Paragraph(f"二、总分统计", styles['Heading2']))
    elements.append(Paragraph(f"本次审核总分：{total_score} / {data_store.total_system_score}", styles['Normal']))
    elements.append(Paragraph(f"得分率：{total_score/data_store.total_system_score*100:.1f}%", styles['Normal']))
    elements.append(Spacer(1, 10))

    # 各模块得分详情
    elements.append(Paragraph("三、各模块得分详情", styles['Heading2']))
    for module_name, module_data in data_store.modules.items():
        module_score = evaluation_data['scores'].get(module_name, 0)
        elements.append(Paragraph(f"{module_name}：{module_score} / {module_data['total_score']}", styles['Normal']))
    elements.append(Spacer(1, 10))

    # 详细评分项
    elements.append(Paragraph("四、详细评分项", styles['Heading2']))
    for module_name, module_data in data_store.modules.items():
        elements.append(Paragraph(f"★ {module_name}", styles['Heading3']))
        for sub_module_name, sub_module_data in module_data['sub_modules'].items():
            elements.append(Paragraph(f"  {sub_module_name}", styles['Heading4']))
            if 'items' in sub_module_data:
                for item in sub_module_data['items']:
                    item_score = evaluation_data['item_scores'].get(item['id'], 0)
                    elements.append(Paragraph(f"    {item['name']}：{item_score} / {item['score']}", styles['Normal']))
            else:
                for sub_sub_name, sub_sub_data in sub_module_data.items():
                    if 'items' in sub_sub_data:
                        elements.append(Paragraph(f"    {sub_sub_name}", styles['Normal']))
                        for item in sub_sub_data['items']:
                            item_score = evaluation_data['item_scores'].get(item['id'], 0)
                            elements.append(Paragraph(f"      {item['name']}：{item_score} / {item['score']}", styles['Normal']))
        elements.append(Spacer(1, 5))

    # 审核评语
    elements.append(Paragraph("五、审核评语", styles['Heading2']))
    elements.append(Paragraph(evaluation_data['comment'], styles['Normal']))

    # 生成PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================== 页面渲染 ====================
def main():
    st.title("🏭 工厂流程审核评分系统")
    
    # 初始化数据存储
    data_store = DataStore()

    # 侧边栏 - 功能导航
    menu = st.sidebar.selectbox("功能菜单", ["新建审核", "审核记录", "数据统计"])

    if menu == "新建审核":
        st.header("新建审核评估")
        
        # 基本信息录入
        col1, col2, col3 = st.columns(3)
        with col1:
            factory_id = st.selectbox("选择工厂", [f["id"] for f in data_store.factories], format_func=lambda x: [f["name"] for f in data_store.factories if f["id"] == x][0])
            factory_name = [f["name"] for f in data_store.factories if f["id"] == factory_id][0]
        with col2:
            evaluation_date = st.date_input("审核日期", value=date.today())
        with col3:
            evaluator_name = st.text_input("审核人员", value="")

        # 评分区域
        st.subheader("评分项（共8大项，总分177分）")
        scores = {}
        item_scores = {}

        # 遍历8大模块
        for module_name, module_data in data_store.modules.items():
            with st.expander(f"{module_name}（总分{module_data['total_score']}分）", expanded=False):
                module_total = 0
                # 遍历子模块
                for sub_module_name, sub_module_data in module_data['sub_modules'].items():
                    st.write(f"### {sub_module_name}")
                    # 处理子模块下的评分项
                    if 'items' in sub_module_data:
                        items = sub_module_data['items']
                    else:
                        items = []
                        for sub_sub in sub_module_data.values():
                            if 'items' in sub_sub:
                                items.extend(sub_sub['items'])
                    
                    # 渲染每个评分项
                    for item in items:
                        col_a, col_b = st.columns([8, 2])
                        with col_a:
                            key_text = "🔑 " if item['is_key'] else ""
                            st.write(f"{key_text}{item['name']}（{item['score']}分）")
                            if item['comment']:
                                st.caption(f"备注：{item['comment']}")
                        with col_b:
                            score = st.number_input(f"得分", min_value=0.0, max_value=float(item['score']), step=0.5, key=item['id'])
                            item_scores[item['id']] = score
                            module_total += score
                    
                    st.divider()
                
                scores[module_name] = module_total
                st.write(f"**{module_name} 小计：{module_total} / {module_data['total_score']} 分**")

        # 审核评语
        comment = st.text_area("审核评语/总结", height=100)

        # 提交按钮
        if st.button("提交审核", type="primary"):
            if not evaluator_name:
                st.error("请填写审核人员姓名！")
                return
            
            # 组装审核数据
            evaluation_data = {
                "factory_id": factory_id,
                "factory_name": factory_name,
                "evaluation_date": evaluation_date.strftime("%Y-%m-%d"),
                "evaluator_name": evaluator_name,
                "scores": scores,
                "item_scores": item_scores,
                "comment": comment,
                "total_score": sum(scores.values())
            }

            # 保存数据
            eval_id = save_evaluation(evaluation_data)
            
            # 生成PDF报告
            pdf_buffer = generate_pdf_report(evaluation_data, data_store)
            
            st.success(f"审核提交成功！审核ID：{eval_id}")
            
            # 显示总分
            total_score = sum(scores.values())
            st.metric("本次审核总分", f"{total_score} / 177", f"{total_score/177*100:.1f}%")
            
            # 下载PDF报告
            st.download_button(
                label="下载PDF报告",
                data=pdf_buffer,
                file_name=f"工厂审核报告_{factory_name}_{evaluation_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )

    elif menu == "审核记录":
        st.header("审核记录查询")
        
        # 加载所有审核记录
        evaluations = data_store.evaluations
        if not evaluations:
            st.info("暂无审核记录")
            return
        
        # 显示记录列表
        eval_df = pd.DataFrame(evaluations)
        eval_df = eval_df[['id', 'factory_name', 'evaluation_date', 'evaluator_name', 'total_score', 'create_time']]
        eval_df.columns = ['ID', '工厂名称', '审核日期', '审核人员', '总分', '创建时间']
        
        # 显示表格
        st.dataframe(eval_df, use_container_width=True)
        
        # 选择查看详情
        eval_ids = [e['id'] for e in evaluations]
        selected_id = st.selectbox("选择审核记录查看详情", eval_ids)
        selected_eval = [e for e in evaluations if e['id'] == selected_id][0]
        
        # 显示详情
        st.subheader("审核详情")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**工厂名称：** {selected_eval['factory_name']}")
            st.write(f"**审核日期：** {selected_eval['evaluation_date']}")
        with col2:
            st.write(f"**审核人员：** {selected_eval['evaluator_name']}")
            st.write(f"**总分：** {selected_eval['total_score']} / 177")
        with col3:
            st.write(f"**创建时间：** {selected_eval['create_time']}")
        
        # 显示评语
        st.write(f"**审核评语：** {selected_eval['comment']}")
        
        # 重新生成PDF
        pdf_buffer = generate_pdf_report(selected_eval, data_store)
        st.download_button(
            label="重新下载PDF报告",
            data=pdf_buffer,
            file_name=f"工厂审核报告_{selected_eval['factory_name']}_{selected_eval['evaluation_date']}.pdf",
            mime="application/pdf"
        )

    elif menu == "数据统计":
        st.header("审核数据统计分析")
        
        evaluations = data_store.evaluations
        if not evaluations:
            st.info("暂无审核记录，无法统计")
            return
        
        # 1. 工厂得分统计
        st.subheader("1. 各工厂平均得分")
        factory_scores = {}
        for eval in evaluations:
            factory = eval['factory_name']
            if factory not in factory_scores:
                factory_scores[factory] = []
            factory_scores[factory].append(eval['total_score'])
        
        # 计算平均分
        factory_avg = {k: sum(v)/len(v) for k, v in factory_scores.items()}
        factory_df = pd.DataFrame(list(factory_avg.items()), columns=['工厂名称', '平均得分'])
        factory_df['得分率'] = (factory_df['平均得分'] / 177 * 100).round(1).astype(str) + '%'
        
        st.dataframe(factory_df, use_container_width=True)
        
        # 可视化
        st.bar_chart(factory_df.set_index('工厂名称')['平均得分'])
        
        # 2. 模块得分统计
        st.subheader("2. 各模块平均得分率")
        module_avg = {}
        total_evals = len(evaluations)
        
        # 初始化模块得分
        for module_name in data_store.modules.keys():
            module_avg[module_name] = 0
        
        # 累加所有审核的模块得分
        for eval in evaluations:
            for module_name, score in eval['scores'].items():
                module_total = data_store.modules[module_name]['total_score']
                module_avg[module_name] += (score / module_total) * 100
        
        # 计算平均分
        for module_name in module_avg.keys():
            module_avg[module_name] = module_avg[module_name] / total_evals
        
        # 显示模块得分率
        module_df = pd.DataFrame(list(module_avg.items()), columns=['模块名称', '平均得分率(%)'])
        module_df['平均得分率(%)'] = module_df['平均得分率(%)'].round(1)
        st.dataframe(module_df, use_container_width=True)
        
        # 可视化
        st.bar_chart(module_df.set_index('模块名称')['平均得分率(%)'])

if __name__ == "__main__":
    main()
