import streamlit as st
import plotly.graph_objects as go
import time
import pandas as pd
from datetime import datetime, date
import calendar

# ==========================================
# 核心引擎：高精度命理与心理算法 (V11.0)
# ==========================================
class MasterEngine:
    GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 节气近似表
    TERM_STARTS = [(2,4), (3,6), (4,5), (5,6), (6,6), (7,7), (8,8), (9,8), (10,8), (11,8), (12,7), (1,6)]

    def validate_date(self, year, month, day):
        try:
            date(year, month, day)
            return True
        except ValueError:
            return False

    def get_bazi(self, year, month, day, hour):
        if not self.validate_date(year, month, day):
            day = calendar.monthrange(year, month)[1]
        
        # 1. 年柱
        y_idx = (year - 1984) % 60
        y_gan = self.GAN[y_idx % 10]
        y_zhi = self.ZHI[y_idx % 12]
        
        # 2. 月柱
        if day >= self.TERM_STARTS[(month-2)%12][1]: m_month = month
        else: m_month = month - 1
        if m_month == 0: m_month = 12
        
        m_zhi_idx = {2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:9, 10:10, 11:11, 12:0, 1:1}.get(m_month, 2)
        m_zhi = self.ZHI[m_zhi_idx]
        
        y_gan_idx = self.GAN.index(y_gan)
        m_gan_start = (y_gan_idx % 5) * 2 + 2
        m_gan = self.GAN[(m_gan_start + (m_zhi_idx - 2)) % 10]
        
        # 3. 日柱 (1989-12-23 壬午日为绝对锚点)
        anchor_date = date(1989, 12, 23)
        anchor_gan_idx = 8
        anchor_zhi_idx = 6
        
        curr_date = date(year, month, day)
        days_diff = (curr_date - anchor_date).days
        
        d_gan_idx = (anchor_gan_idx + days_diff) % 10
        d_zhi_idx = (anchor_zhi_idx + days_diff) % 12
        
        d_gan = self.GAN[d_gan_idx]
        d_zhi = self.ZHI[d_zhi_idx]
        
        # 4. 时柱
        actual_hour = hour if hour != 23 else 0
        h_zhi_idx = (actual_hour + 1) // 2 % 12
        h_zhi = self.ZHI[h_zhi_idx]
        h_gan_start = (d_gan_idx % 5) * 2
        h_gan = self.GAN[(h_gan_start + h_zhi_idx) % 10]
        
        # 5. 格局判定
        main_qi_map = {
            "子":"癸", "丑":"己", "寅":"甲", "卯":"乙", 
            "辰":"戊", "巳":"丙", "午":"丁", "未":"己", 
            "申":"庚", "酉":"辛", "戌":"戊", "亥":"壬"
        }
        month_qi = main_qi_map[m_zhi]
        
        ten_gods = ["比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"]
        god_idx = (self.GAN.index(month_qi) - d_gan_idx) % 10
        raw_structure = ten_gods[god_idx]
        
        structure = raw_structure
        if d_gan_idx in [0, 2, 4, 6, 8] and raw_structure == "劫财":
            structure = "羊刃"
        elif raw_structure == "比肩" and m_zhi in ["寅","巳","申","亥","子","午","卯","酉"]:
            structure = "建禄"

        wuxing_map = {"甲":"木", "乙":"木", "丙":"火", "丁":"火", "戊":"土", "己":"土", "庚":"金", "辛":"金", "壬":"水", "癸":"水"}
        day_wuxing = wuxing_map[d_gan]

        return {
            "dm": d_gan,
            "wuxing": day_wuxing,
            "structure": structure,
            "info": f"{y_gan}{y_zhi}年 {m_gan}{m_zhi}月 {d_gan}{d_zhi}日 {h_gan}{h_zhi}时",
            "year": f"{y_gan}{y_zhi}",
            "month": f"{m_gan}{m_zhi}",
            "day": f"{d_gan}{d_zhi}",
            "hour": f"{h_gan}{h_zhi}"
        }

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(page_title="天命智库Pro", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    .result-card {background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border:1px solid #eee;}
    .card-title {font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 15px;}
    .highlight-box {background: #f0f4c3; padding: 15px; border-radius: 8px; border-left: 5px solid #c0ca33; margin-top: 10px;}
    .conflict-box {background: #ffebee; padding: 15px; border-radius: 8px; border-left: 5px solid #e57373; margin-top: 10px;}
    .match-box {background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 5px solid #66bb6a; margin-top: 10px;}
    .talent-tag {background: #e3f2fd; color: #1565c0; padding: 3px 8px; border-radius: 4px; font-size: 13px; margin-right: 5px; display: inline-block; margin-top: 5px;}
    .detail-section {background: #fafafa; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #e0e0e0;}
    .strength-item {background: #e8f5e9; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #66bb6a;}
    .weakness-item {background: #fff3e0; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #ff9800;}
    .action-item {background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #2196f3;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.header("📋 个人档案")

    s_year = st.number_input("📅 公历年份", 1900, 2025, 1990)
    
    c2, c3 = st.columns(2)
    with c2: 
        s_month = st.selectbox("月份", range(1, 13), index=0)
    with c3: 
        max_day = calendar.monthrange(s_year, s_month)[1]
        s_day = st.selectbox("日期", range(1, max_day+1), index=0)
        
    s_hour = st.slider("⏰ 出生时辰", 0, 23, 12)

    st.markdown("---")

    engine = MasterEngine()
    bazi_data = engine.get_bazi(s_year, s_month, s_day, s_hour)
    
    st.success(f"**日主**：{bazi_data['dm']}（{bazi_data['wuxing']}）")
    st.success(f"**格局**：{bazi_data['structure']}")
    
    with st.expander("🔍 查看完整八字"):
        st.write(f"**年柱**：{bazi_data['year']}")
        st.write(f"**月柱**：{bazi_data['month']}")
        st.write(f"**日柱**：{bazi_data['day']}")
        st.write(f"**时柱**：{bazi_data['hour']}")

# ==========================================
# 主界面
# ==========================================
st.markdown("<h2 style='text-align:center;'>🧬 命理与职业潜能深度诊断</h2>", unsafe_allow_html=True)
st.info("💡 请根据实际情况滑动滑块（1=完全不符，5=非常符合）")

questions = {
    "E (企业型)": [
        "我渴望掌控局面，喜欢做决策",
        "我对金钱和地位有强烈的野心",
        "我敢于承担风险，关键时刻能拍板",
        "我擅长说服他人，有较强的谈判能力",
        "我有很强的目标感，为了结果可以忍受压力"
    ],
    "I (研究型)": [
        "我喜欢钻研底层逻辑，刨根问底",
        "我更相信数据和证据，而不是直觉",
        "我享受长时间的独处思考，不喜无效社交",
        "我擅长解决复杂的智力难题或技术bug",
        "我对新知识有极强的学习欲望"
    ],
    "A (艺术型)": [
        "我讨厌机械重复，追求工作中的新鲜感",
        "我有独特的审美，对色彩/声音/文字敏感",
        "我情绪丰富，容易共情，也容易受环境影响",
        "我经常有天马行空的创意，不喜欢被规则束缚",
        "我渴望通过作品来表达自我"
    ],
    "S (社会型)": [
        "我擅长察言观色，能迅速感知他人情绪",
        "我乐于帮助、教导他人，助人让我快乐",
        "我认为维护良好的人际关系很重要",
        "我擅长协调冲突，是团队里的润滑剂",
        "我有很强的亲和力，陌生人也愿意向我倾诉"
    ],
    "C (常规型)": [
        "我是细节控，追求准确无误，难以忍受粗心",
        "做事前我一定要制定详细的计划",
        "我追求稳定和安全感，极度厌恶突发状况",
        "我擅长整理归纳，喜欢把物品分类有序",
        "我尊重规则和流程"
    ],
    "R (实干型)": [
        "我信奉动手实操，不喜欢空谈理论",
        "通过修理物品、运动能让我解压",
        "我喜欢户外工作，不喜欢整天坐办公室",
        "我擅长使用工具、机械设备",
        "看到具体的实物成果让我有成就感"
    ]
}

scores = {k[0]:0 for k in questions.keys()}
tabs = st.tabs([k for k in questions.keys()])

for i, (key, qs) in enumerate(questions.items()):
    with tabs[i]:
        for idx, q in enumerate(qs):
            val = st.slider(q, 1, 5, 3, key=f"{key}_{idx}")
            scores[key[0]] += val

st.write("---")

with st.expander("📊 查看得分分布"):
    fig = go.Figure(data=[go.Bar(x=list(scores.keys()), y=list(scores.values()))])
    fig.update_layout(title="霍兰德六维度得分", xaxis_title="维度", yaxis_title="得分", height=350)
    st.plotly_chart(fig, use_container_width=True)

if st.button("🚀 生成精准分析报告", type="primary", use_container_width=True):
    
    with st.spinner("正在分析..."):
        time.sleep(1.0)
    
    top_items = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    top1, top2 = top_items[0][0], top_items[1][0]
    combo = top1 + top2
    structure = bazi_data['structure']
    
    # 字典库
    holland_dict = {
        "EI": {"name": "战略决策者", "talent": "宏观视野+深度分析", "job": "商业分析师、投资人、战略顾问、产品总监",
               "strength": "能够快速洞察商业本质，擅长数据驱动决策，在复杂环境中保持清晰思维",
               "challenge": "可能过于理性导致忽视人际关系，决策速度快但需注意团队接受度",
               "dev_path": "建议从数据分析师或产品经理起步，积累3-5年后转向战略或投资岗位"},
        "IE": {"name": "技术型领袖", "talent": "专业壁垒+商业嗅觉", "job": "CTO、技术合伙人、创业者",
               "strength": "既懂技术又懂商业，能将技术转化为商业价值，适合技术创业",
               "challenge": "需要平衡技术深度与管理广度，避免陷入技术细节",
               "dev_path": "先成为技术专家，然后承担技术管理，最终走向技术战略或创业"},
        "ES": {"name": "卓越管理者", "talent": "组织能力+人际连接", "job": "销售总监、校长、HR VP",
               "strength": "善于激励团队，建立广泛人脉，推动组织目标达成",
               "challenge": "可能重结果轻过程，需要培养耐心和同理心",
               "dev_path": "从基层管理做起，逐步扩大管辖范围，注重领导力培养"},
        "SE": {"name": "服务型领导", "talent": "同理心+号召力", "job": "客服总监、公益负责人",
               "strength": "以人为本，能够创造温暖的组织文化，擅长危机公关",
               "challenge": "可能在商业决策时过于感性，需要加强数据思维",
               "dev_path": "从一线服务做起，积累用户洞察，逐步走向管理岗位"},
        "EC": {"name": "运营操盘手", "talent": "目标导向+流程控制", "job": "CFO、项目经理",
               "strength": "执行力强，善于把控细节，确保项目按时交付",
               "challenge": "可能过于注重流程而缺乏灵活性，需要平衡效率与创新",
               "dev_path": "从项目助理或财务分析师起步，逐步承担更大项目"},
        "CE": {"name": "风控专家", "talent": "严谨细节+执行魄力", "job": "审计、合规总监",
               "strength": "风险意识强，能够发现隐藏问题，保护组织利益",
               "challenge": "可能过于保守影响创新，需要学会权衡风险与机会",
               "dev_path": "在专业机构积累经验，考取相关证书，成为行业专家"},
        "AI": {"name": "概念设计师", "talent": "审美直觉+逻辑架构", "job": "架构师、游戏策划、UX设计师",
               "strength": "能够创造兼具美感与实用性的作品，思维跨界",
               "challenge": "可能理想主义，需要考虑商业可行性和用户需求",
               "dev_path": "在设计或技术领域深耕，培养跨界能力，成为复合型人才"},
        "IA": {"name": "学者型创作者", "talent": "深度研究+艺术表达", "job": "策展人、作家、研究员",
               "strength": "能够进行深度思考并用优美方式表达，适合知识创作",
               "challenge": "可能过于沉浸自我世界，需要加强与外界连接",
               "dev_path": "在学术或艺术领域建立专业声望，通过作品积累影响力"},
        "AR": {"name": "匠人艺术家", "talent": "艺术感知+动手实操", "job": "珠宝设计、摄影师",
               "strength": "能够将创意转化为实物作品，具有独特审美",
               "challenge": "需要平衡艺术追求与商业变现",
               "dev_path": "在工作室或品牌积累经验，建立个人风格，最终独立创业"},
        "RA": {"name": "技术型匠人", "talent": "机械操作+审美", "job": "整形医生、技师",
               "strength": "手眼协调好，能够精准操作，追求完美细节",
               "challenge": "需要持续学习新技术，避免被时代淘汰",
               "dev_path": "通过大量实操积累经验，考取专业认证，成为领域专家"},
        "SI": {"name": "咨询顾问", "talent": "洞察人性+理性分析", "job": "职业规划师、猎头",
               "strength": "能够快速理解他人需求，提供专业建议，建立信任",
               "challenge": "可能情感消耗大，需要做好自我边界管理",
               "dev_path": "在咨询公司或人力资源领域积累案例，建立个人品牌"},
        "IS": {"name": "专家型导师", "talent": "专业知识+助人", "job": "教授、医生、专家",
               "strength": "既有专业深度又愿意传授，能够培养人才",
               "challenge": "需要平衡研究与教学，避免职业倦怠",
               "dev_path": "在专业领域深耕10年以上，发表研究成果，建立学术地位"},
        "RC": {"name": "精密执行者", "talent": "身体力行+严守规范", "job": "外科医生、飞行员",
               "strength": "在高压环境下保持稳定，严格遵守操作规程",
               "challenge": "需要持续训练保持状态，压力管理很重要",
               "dev_path": "通过严格培训和大量实操，获得资质认证，逐步承担更高责任"},
        "CR": {"name": "后勤管家", "talent": "数据整理+物资管理", "job": "会计、档案管理",
               "strength": "井井有条，确保资源合理配置，支持组织运转",
               "challenge": "工作重复性高，需要寻找成长空间",
               "dev_path": "考取专业证书，从基础岗位做到主管或专家级别"},
        "AS": {"name": "传播者", "talent": "表现力+感染力", "job": "博主、主持人、讲师",
               "strength": "能够吸引注意力，传递信息，影响他人",
               "challenge": "需要持续输出内容，避免灵感枯竭",
               "dev_path": "通过平台积累粉丝，打造个人IP，实现商业变现"},
        "SA": {"name": "疗愈师", "talent": "共情+艺术引导", "job": "心理咨询、幼教",
               "strength": "能够理解他人情感，用温暖方式提供支持",
               "challenge": "情感消耗大，需要做好自我疗愈",
               "dev_path": "考取专业资质，积累个案经验，建立口碑"}
    }
    
    h_res = holland_dict.get(combo, {"name": "综合潜能者", "talent": "多维能力", "job": "综合管理、自由职业",
                                     "strength": "能力均衡，适应性强", "challenge": "需要找到聚焦方向", 
                                     "dev_path": "尝试多个领域后选择深耕方向"})
    
    bazi_dict = {
        "羊刃": {"trait": "极致爆发力", "advantage": "危机决断，越挫越勇", "blindspot": "刚愎自用，关系紧张", "job_fix": "创业、外科、风投",
                 "work_style": "适合独立作战或领导团队，不适合被管束。在危机中最能发挥价值",
                 "growth_advice": "学习柔性沟通，建立战略伙伴关系。避免单打独斗",
                 "career_peak": "35-45岁，经验与魄力达到平衡点时"},
        "七杀": {"trait": "权威魄力", "advantage": "改革者，执行力强", "blindspot": "焦虑急躁", "job_fix": "公检法、高管",
                 "work_style": "需要明确的权责和目标，在制度化环境中更能发挥",
                 "growth_advice": "学会放权和信任下属，避免事必躬亲",
                 "career_peak": "30-40岁，适合在成熟组织中担任高管"},
        "伤官": {"trait": "才华横溢", "advantage": "创意无限，口才好", "blindspot": "恃才傲物", "job_fix": "自由职业、创意总监",
                 "work_style": "需要自由发挥空间，不适合严格层级结构。擅长创新和表达",
                 "growth_advice": "培养情商和团队协作能力。学会包装自己的才华",
                 "career_peak": "持续型，只要保持学习就能长期发展"},
        "食神": {"trait": "温和睿智", "advantage": "宽厚有福，审美好", "blindspot": "缺乏野心", "job_fix": "餐饮、设计、教育",
                 "work_style": "注重过程享受，适合慢节奏深耕领域。重视生活品质",
                 "growth_advice": "设定明确目标，培养竞争意识。不要过于安逸",
                 "career_peak": "40岁后，经验和人脉成熟时价值凸显"},
        "正官": {"trait": "正直守信", "advantage": "大局观强", "blindspot": "墨守成规", "job_fix": "公务员、管理",
                 "work_style": "适合稳定的大组织，按部就班发展。重视规则和程序",
                 "growth_advice": "培养变革思维，学习新技术。不要过于依赖体制",
                 "career_peak": "45岁左右，资历和能力得到充分认可"},
        "正印": {"trait": "仁慈博爱", "advantage": "学习能力强", "blindspot": "依赖心强", "job_fix": "教师、学者",
                 "work_style": "适合学习型组织，需要导师指引。重视知识和文化",
                 "growth_advice": "培养独立思考和决策能力。不要过度依赖他人",
                 "career_peak": "持续成长型，终身学习者"},
        "偏印": {"trait": "独特洞察", "advantage": "直觉敏锐", "blindspot": "性格孤僻", "job_fix": "科研、策划",
                 "work_style": "适合独立工作或小团队。在边缘领域容易出彩",
                 "growth_advice": "加强社交能力，学会团队协作。避免过度孤立",
                 "career_peak": "不定期，灵感和机遇结合时爆发"},
        "正财": {"trait": "勤恳务实", "advantage": "理财能力强", "blindspot": "格局偏小", "job_fix": "会计、实业",
                 "work_style": "注重积累，适合长期投资。追求稳定回报",
                 "growth_advice": "扩大视野，学习战略思维。适度冒险",
                 "career_peak": "40-50岁，财富积累达到高峰"},
        "偏财": {"trait": "豪爽灵活", "advantage": "商业嗅觉好", "blindspot": "花钱大手", "job_fix": "贸易、投资",
                 "work_style": "适合快节奏变化环境。善于抓住机会",
                 "growth_advice": "加强财务管理，做好风险控制。不要过度扩张",
                 "career_peak": "30-40岁，精力和经验达到最佳配比"},
        "建禄": {"trait": "独立自主", "advantage": "意志坚定", "blindspot": "不善合作", "job_fix": "专业技术",
                 "work_style": "适合独立项目或小团队。不喜欢被管束",
                 "growth_advice": "学会合作共赢，建立合作伙伴关系",
                 "career_peak": "35-50岁，专业能力成熟期"}
    }
    
    b_res = bazi_dict.get(structure, {"trait": "平衡", "advantage": "适应力强", "blindspot": "特色不明显", "job_fix": "综合管理",
                                      "work_style": "通用型", "growth_advice": "建立个人特色", "career_peak": "持续发展"})

    # 报告渲染
    st.markdown("### 1. 天赋解码")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class='result-card'>
            <div class='card-title'>🧠 心理天赋 ({combo}型)</div>
            <p><b>角色定位：</b>{h_res['name']}</p>
            <p><b>核心能力：</b>{h_res['talent']}</p>
            <p><b>推荐赛道：</b></p>
            <div>
                {' '.join([f"<span class='talent-tag'>{job.strip()}</span>" for job in h_res['job'].split('、')])}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class='result-card'>
            <div class='card-title'>🔥 命格解码 ({structure}格)</div>
            <p><b>底层特质：</b>{b_res['trait']}</p>
            <p><b>⚡ 优势：</b>{b_res['advantage']}</p>
            <p><b>🌑 盲点：</b>{b_res['blindspot']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 2. 深度分析")
    
    with st.expander("🔍 点击查看详细强弱势分析", expanded=True):
        st.markdown(f"""
        <div class='detail-section'>
            <div class='strength-item'>
                <b>💪 您的核心优势 (Power Zone)：</b><br>
                {h_res['strength']}。结合命格的{b_res['trait']}，您在{b_res['work_style']}。
            </div>
            <div class='weakness-item'>
                <b>⚠️ 潜在挑战 (Risk Zone)：</b><br>
                {h_res['challenge']}。在命理上表现为{b_res['blindspot']}。
            </div>
            <div class='action-item'>
                <b>📈 成长建议 (Growth Path)：</b><br>
                {h_res['dev_path']}。<br>命理建议：{b_res['growth_advice']}。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 3. 博弈分析：心理vs命理")
    
    psy_risk = ["E", "A"]
    psy_safe = ["C", "S"]
    group_wild = ["七杀", "伤官", "羊刃", "偏财"]
    group_civil = ["正官", "正印", "正财", "食神"]
    
    if structure in group_wild and top1 in psy_safe:
        status_class = "conflict-box"
        title = "⚠️ 深度冲突：猛虎困笼"
        content = f"命格【{structure}】激进但心理【{top1}型】求稳。建议：主业稳定+副业冒险释放能量。"
    elif structure in group_wild and top1 in psy_risk:
        status_class = "match-box"
        title = "🔥 能量共振：乱世枭雄"
        content = f"命格与性格统一！适合竞争环境，创业、销售、危机管理是您的舞台。"
    elif structure in group_civil and top1 in psy_risk:
        status_class = "conflict-box"
        title = "⚠️ 深度冲突：风筝线短"
        content = f"心理【{top1}型】求新但命格【{structure}】求稳。建议：体制内创新或业余低成本试错。"
    elif structure in group_civil:
        status_class = "match-box"
        title = "🏔️ 能量共振：中流砥柱"
        content = "您适合深耕积累，时间是朋友。选对平台后长期主义，10年回报惊人。"
    else:
        status_class = "highlight-box"
        title = "⚖️ 独立生长"
        content = "命格独立，以心理兴趣为主导，建立个人IP和专业技能。"

    st.markdown(f"""
    <div class='{status_class}'>
        <h4 style='margin-top:0;'>{title}</h4>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 4. 行动路标")
    
    st.info(f"""
    **🎯 职业修正**：霍兰德推荐【{h_res['job'].split('、')[0]}】，结合【{structure}格】：{b_res['job_fix']}
    """)
    
    st.success(f"""
    **🚀 三年路标**：
    - **2025 (蓄势)**：补齐短板，考取核心证书/技能。
    - **2026 (突破)**：单点突破，建立个人品牌或负责新项目。
    - **2027 (爆发)**：{b_res['career_peak']}，争取职级跃迁或收入翻倍。
    """)
    
    st.success("✅ 报告生成完成！")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;font-size:12px;'><p>天命智库Pro | 仅供参考</p></div>", unsafe_allow_html=True)
