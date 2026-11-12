# -*- coding: utf-8 -*-
"""
双行业晨报 生成器（单文件 HTML 输出）
====================================
包含两个模块：
  1) 家纺行业      —— 真实网页检索聚合，覆盖 7 个重点家纺品牌
  2) 商业零售洞察  —— 真实网页检索聚合，覆盖 6 个重点零售品牌

版块结构（2026-11-06 重构，用户确认）：
  每个模块仅分「两大块」：
    · 品牌动作  —— 内含 4 个子分组：新品上市 / 品牌战略与动态 / 渠道与门店 / 内容声量
    · 行业研究  —— 第三方研报 / 宏观趋势 / 榜单排行（非品牌自身动作）
  文档末尾独立大块：
    · 今日金句提炼（10 句，基于真实报道的洞察提炼，非逐字引用）

说明：品牌非每日发稿，看板聚合「近 2~3 个月」真实动态，并非严格同日新闻。
      每次重跑前请用 WebSearch 刷新下方 DATA 列表。

用法：
  python 家纺晨报生成器.py
输出：
  双行业晨报_<日期>.html （单文件，样式/脚本内联，无外部依赖）
"""

import datetime, html, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATE_STR = datetime.date.today().isoformat()          # 日报日期（生成当天）
REPORT_DATE = datetime.date.fromisoformat(DATE_STR)
WEEKDAYS = ["周一","周二","周三","周四","周五","周六","周日"]
HERO_DATE = f"{REPORT_DATE.year}年{REPORT_DATE.month}月{REPORT_DATE.day}日 · {WEEKDAYS[REPORT_DATE.weekday()]} · 北京时间"

def esc(s):
    return html.escape(str(s), quote=True)

def clip(s, n=60):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n-1] + "…"

# =====================================================================
# 子分组（品牌动作内部）与图标
# =====================================================================
SUBGROUPS = [
    ("新品上市", "sg-new",
     '<svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>'),
    ("品牌战略与动态", "sg-strategy",
     '<svg viewBox="0 0 24 24"><path d="M3 3v18h18" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/><path d="M7 14l3-3 3 3 5-6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    ("渠道与门店", "sg-store",
     '<svg viewBox="0 0 24 24"><path d="M3 9l1-5h16l1 5M4 9v11h16V9M9 20v-6h6v6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    ("内容声量", "sg-media",
     '<svg viewBox="0 0 24 24"><path d="M5 4h14a1 1 0 011 1v14a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1zM10 9l5 3-5 3z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>'),
]
SG_NAMES = [n for n, _, _ in SUBGROUPS]
INDUSTRY = ("行业研究", "sec-industry",
     '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><path d="M14 2v6h6M9 13h6M9 17h6" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>')

def block_of(section):
    return "品牌动作" if section in SG_NAMES else "行业研究"

# =====================================================================
# 模块一：家纺行业
# =====================================================================
HOME_BRANDS = {
    "无印良品": "#8B6F47",
    "全棉时代": "#3A9D6E",
    "松山棉店": "#C0623D",
    "艾美家":   "#9B6FB0",
    "季米":     "#D98E2B",
    "奥莱渠道": "#6B7280",
    "水星家纺": "#2F6FB0",
}
HOME_DATA = [
    # —— 品牌动作 / 新品上市 ——
    dict(brand="无印良品", section="新品上市",
         title="MUJI 2026 秋冬居家織品系列",
         summary="推出絎縫與法蘭絨織品系列，含薄被/蓋毯/抱枕套，9-10月陸續上市。",
         source="MUJI Taiwan", date="2026年9-10月",
         url="https://www.muji.tw/muji-journal/news/news/260910.html"),
    dict(brand="全棉时代", section="新品上市",
         title="全棉時代×與輝同行 雲葉棉紗衛生巾",
         summary="10月聯合「與輝同行」推定制衛生巾及安睡褲，首發即登直播銷售良好。",
         source="稳健医疗/搜狐", date="2026年10月",
         url="https://m.sohu.com/a/1088500544_114984"),
    dict(brand="松山棉店", section="新品上市",
         title="松山棉店 小暖羊保暖系列升級",
         summary="9/22發布小暖羊保暖打底褲升級，17.5微米美利奴羊毛，累售300萬+條。",
         source="中国经济新闻网", date="2026年9月22日",
         url="https://www.cet.com.cn/zhpd/zxsdv2/10585191.shtml"),
    dict(brand="艾美家", section="新品上市",
         title="艾美家 2026 新款全棉床品套件",
         summary="推出蕾絲/水洗棉/磨毛夾棉床裙三四件套，覆蓋多花色床品套件矩陣。",
         source="找家纺网", date="2026年",
         url="https://www.zhaojiafang.com/shop/index.php?act=show_store&op=goods_all&store_id=18685&time="),
    dict(brand="季米", section="新品上市",
         title="季米家居 秋冬四件套上新（買一贈一）",
         summary="全棉/噴氣/浮雕提花/生態棉絨四件套上線，199-299元價格帶主打性價比。",
         source="季米官方微信", date="2026年秋冬",
         url="http://mp.weixin.qq.com/s?__biz=MzIxMDI0ODg3OA==&mid=2649546698&idx=4&sn=5320d0a7c9162e97a184691ed080d924&chksm=8e2fed4edcfd850e7eb658b06bb48f6303561426a9eb4448f4809e8746ec7057f8d24cc350c6#rd"),
    dict(brand="水星家纺", section="新品上市",
         title="水星家紡 氣絨蓬暖被 3.0",
         summary="CLIMORA氣絨系統+三項專利可機洗，15分升溫5.6℃、90分升12℃。",
         source="水星家纺", date="2026年",
         url="https://www.shuixing.com/ketangs/2949.html"),
    dict(brand="水星家纺", section="新品上市",
         title="水星家紡 御·小杏福 非遺剪紙床品",
         summary="攜手非遺剪紙（金壇刻紙）推御·小杏福系列，AB版60S長絨棉緞紋三色。",
         source="水星家纺", date="2026年9月30日",
         url="https://shuixing.com/ketangs/"),
    dict(brand="水星家纺", section="新品上市",
         title="水星家紡 2026 秋冬產品結構",
         summary="雪糕/閃睡家族/牛皮席系列，融入石墨烯導電絲與茶氨酸植萃抗菌科技。",
         source="水星家纺官网", date="2026年",
         url="http://www.shuixing.com.cn/"),
    # —— 品牌动作 / 渠道与门店 ——
    dict(brand="全棉时代", section="渠道与门店",
         title="全棉時代 廣州白鵝潭旗艦店開業",
         summary="9/30廣州白鵝潭萬象城店開業；同期官宣趙今麥為奈絲公主品牌代言人。",
         source="新华财经/稳健医疗", date="2026年9-10月",
         url="https://www.cnfin.com/announ/detail/index.html?dannoun=lcdetail&id=845718435433"),
    dict(brand="松山棉店", section="渠道与门店",
         title="松山棉店 董潔代言+全國拓店",
         summary="9/22官宣董潔出任品牌代言人；上半年蘇州/上海/北京/瀋陽等多城新店落地。",
         source="中国经济新闻网/中国日报", date="2026年9月22日",
         url="https://www.cet.com.cn/zhpd/zxsdv2/10585191.shtml"),
    # —— 品牌动作 / 品牌战略与动态 ——
    dict(brand="水星家紡", section="品牌战略与动态",
         title="水星家紡 王濛代言「穩躺贏」快閃",
         summary="代言人王濛空降快閃解鎖睡眠密碼，展示睡眠密碼系列核心產品矩陣。",
         source="水星家纺", date="2026年",
         url="https://shuixing.com/news/2800.html"),
    dict(brand="水星家紡", section="品牌战略与动态",
         title="水星家紡 攜手君智戰略諮詢",
         summary="與君智戰略合作，系統塑造專業創新引領增長路徑，提振經銷商信心。",
         source="水星家纺官网", date="2026年",
         url="http://www.shuixing.com.cn/"),
    dict(brand="无印良品", section="品牌战略与动态",
         title="MUJI 2026 秋冬商品展示會",
         summary="舉辦秋冬商品展示會，集中展示法蘭絨床品與雙層紗織家居服等新品。",
         source="GRAZIA中文网", date="2026年",
         url="https://chinagrazia.com/article/186497.html"),
    # —— 品牌动作 / 内容声量 ——
    dict(brand="无印良品", section="内容声量",
         title="MUJI 風衣 9月小紅書刷屏「Lemaire平替」",
         summary="今秋立領風衣小紅書高熱筆記密集，被喊「Lemaire平替」，討論與爭議齊飛。",
         source="什么值得买/小红书", date="2026年9月",
         url="https://post.smzdm.com/p/aggqrgm7/"),
    dict(brand="水星家紡", section="内容声量",
         title="水星「穩躺贏」體驗展 100+達人探店種草",
         summary="上海互動體驗展超100位達人探店，小紅書/抖音種草聯動線下門店打卡。",
         source="水星家纺官网", date="2026年9月",
         url="http://www.shuixing.com.cn/news_2"),
    dict(brand="松山棉店", section="内容声量",
         title="松山棉店 秋季家居服新浪#穿搭指南#推廣",
         summary="新浪#穿搭指南#推秋季家居服；全國已開360+門店，線上種草帶動線下。",
         source="新浪/买购网", date="2026年",
         url="https://www.sina.cn/news/detail/5340104588788379.html"),
    dict(brand="季米", section="内容声量",
         title="季米 小紅書/ins 輕奢種草 原創設計",
         summary="主打法式簡約、ins輕奢原創花色，小眾不撞款，年輕租房改造群體種草。",
         source="敬慕百科/hqwc", date="2026年",
         url="http://www.hqwc.cn/a/1263312.html"),
    # —— 行业研究 ——
    dict(brand="奥莱渠道", section="行业研究",
         title="信達證券 家紡行業景氣度報告",
         summary="1-2月抖音銷售羅萊+51%/水星+6%/富安娜+224%；奧萊模式釋放彈性。",
         source="发现报告/信达证券", date="2026年",
         url="http://fxbaogao.com/detail/5283819"),
    dict(brand="奥莱渠道", section="行业研究",
         title="人民日報 聚焦南通家紡新質躍遷",
         summary="報道南通家紡以涼感/冰絲科技產品創新供給，傳統產業煥新升級。",
         source="中国纺织工业联合会", date="2026年8月13日",
         url="https://cntac.org.cn/zixun/hangye/202608/t20260819_4419927.html"),
    dict(brand="奥莱渠道", section="行业研究",
         title="家紡奧萊渠道成增長主力",
         summary="羅萊/水星加速佈局購物中心與奥特萊斯，奧萊店型成直營增長主力。",
         source="同花顺/中财网", date="2026年8月26日",
         url="https://basic.10jqka.com.cn/144/002327/worth.html"),
    dict(brand="季米", section="行业研究",
         title="季米家紡 九大四件套系列詳解",
         summary="選購指南重點詳寫季米，299-1299元價格帶覆蓋全屋床品九大系列。",
         source="凤凰网山东", date="2026年",
         url="https://sd.ifeng.com/c/8tIpxOPuZvS"),
    dict(brand="季米", section="行业研究",
         title="2026 四件套測評排行 季米居 TOP1",
         summary="橫向實測6大家紡品牌，季米憑多元面料體系與全線A類標準登頂。",
         source="第一纺织网", date="2026年",
         url="http://quota.webtex.cn/info/info_view.asp?Infoid=735064"),
]
HOME_NOTICE = '''<div class="notice">
  <strong>🔍 家纺信源与口径说明：</strong>
  本模块已接入<strong>真实家纺行业垂直信源</strong>——通过实时网页检索（WebSearch）对 7 个重点品牌逐一抓取，内容来自品牌官网、权威媒体与券商研报，<strong>非 AI 资讯源</strong>。
  家纺品牌并非每日发稿，故聚合的是<strong>近 2~3 个月（2026 年 8–10 月）真实动态</strong>，非严格同日新闻；如需严格「当日」口径，建议每日定时复跑本生成器。
  <br><strong>关于「奥莱家纺/奥莱渠道」：</strong>经检索，它<strong>并非独立注册品牌</strong>，而是家纺品牌（罗莱/水星/富安娜等）的<strong>奥特莱斯折扣渠道形态</strong>，本模块将其归入「行业研究·奥莱渠道趋势」并标注为「奥莱渠道」。
  <br><strong>结构说明：</strong>本模块仅分「品牌动作」（含新品上市 / 品牌战略与动态 / 渠道与门店 / 内容声量 四子分组）与「行业研究」两大块。
</div>'''

# =====================================================================
# 模块二：商业零售洞察
# =====================================================================
RETAIL_BRANDS = {
    "奥乐齐":   "#1A7D5A",
    "胖东来":   "#E4572E",
    "山姆":     "#C0392B",
    "盒马":     "#2E86C1",
    "名创优品": "#E84393",
    "优衣库":   "#34495E",
}
RETAIL_DATA = [
    # —— 品牌动作 / 品牌战略与动态 ——
    dict(brand="奥乐齐", section="品牌战略与动态",
         title="奥乐齐年底冲150店，CEO陈佳首度受访",
         summary="年底门店将达150家；CEO陈佳首度受访，称自有品牌占比90%是商业模式内核。",
         source="中国零售业博览会/今日头条", date="2026年11月",
         url="https://www.toutiao.com/article/7703415697778442788"),
    dict(brand="胖东来", section="品牌战略与动态",
         title="胖东来前8月卖195亿，却关年利超1亿老店",
         summary="14家店前8月销售195亿同比+27%；主动关闭年利超1亿、经营24年的生活广场老店。",
         source="东方快消品中心/今日头条", date="2026年9月",
         url="https://www.toutiao.com/article/7680878336951845418/"),
    dict(brand="山姆", section="品牌战略与动态",
         title="山姆2026财年销售破1400亿，贡献沃尔玛中国超80%",
         summary="2026财年全渠道销售破1400亿，贡献沃尔玛中国超80%营收；付费会员破1070万。",
         source="正观新闻", date="2026年7月",
         url="https://www.zhengguannews.cn/zghnews/420954.html"),
    dict(brand="盒马", section="品牌战略与动态",
         title="盒马2026财年GMV破1070亿，设AI委员会",
         summary="2026财年GMV破1070亿连续两年盈利；4月设AI委员会，选品补货定价由AI主导。",
         source="百度百科/财经", date="2026年3月",
         url="https://baike.baidu.com/item/%E7%9B%92%E9%A9%AC/68625265"),
    dict(brand="名创优品", section="品牌战略与动态",
         title="名创优品26Q3内地GMV+25%~30%，YOYO前9月破10亿",
         summary="26Q3内地GMV同比+25%~30%；自有IP YOYO前9月GMV破10亿进全球十亿俱乐部。",
         source="MINISO IR/搜狐", date="2026年10月",
         url="https://ir-tc.miniso.com/2026-10-09-MINISO-Groups-Latest-Business-Update"),
    dict(brand="优衣库", section="品牌战略与动态",
         title="优衣库大中华区收益7240亿日元+11.3%，净关74店",
         summary="大中华区收益7240亿日元+11.3%；中国大陆门店净关74家至852家，利润反增。",
         source="证券时报", date="2026年10月",
         url="https://www.stcn.com/article/detail/4225007.html"),
    # —— 品牌动作 / 渠道与门店 ——
    dict(brand="奥乐齐", section="渠道与门店",
         title="奥乐齐11月进安徽、2027年1月落杭州",
         summary="11月以6店同开进驻安徽，2027年1月落杭州；南京物流中心启用加密华东供应链。",
         source="今日头条", date="2026年10月",
         url="https://www.toutiao.com/article/7703415697778442788"),
    dict(brand="胖东来", section="渠道与门店",
         title="胖东来科技广场店在建，梦之城/郑州店筹备",
         summary="科技广场店在建（约5万㎡）承接老店员工平移；梦之城、郑州店筹备，暂停对外帮扶。",
         source="大象网", date="2026年10月",
         url="https://www.hntv.tv/50rd/article/1/2113110432017408001?from=dxlist"),
    dict(brand="山姆", section="渠道与门店",
         title="山姆2026计划新开13家冲百店，严打黄牛",
         summary="2026计划新开13家冲百店；修改会员章程，同实名一年仅绑两次亲友卡打击黄牛。",
         source="今日头条", date="2026年10月",
         url="https://m.toutiao.com/article/7694584673704264218"),
    dict(brand="盒马", section="渠道与门店",
         title="盒马超盒算NB一年新开约200家进33城",
         summary="平价硬折扣超盒算NB一年新开约200家进33城；简阳双业态（折扣+前置仓）开业。",
         source="财经/今日头条", date="2026年10月",
         url="https://news.caijingmobile.com/article/detail/586559"),
    dict(brand="名创优品", section="渠道与门店",
         title="名创优品海外SUPER MINISO / MINISO LAND落地",
         summary="10月加拿大首间海外SUPER MINISO、美国首间MINISO LAND相继开业，IP大店加速出海。",
         source="MINISO 品牌新闻", date="2026年10月",
         url="https://resmaworoningrum@miniso.com/brand/news_206.html"),
    dict(brand="优衣库", section="渠道与门店",
         title="优衣库中国关低效开旗舰，转向个店经营",
         summary="中国净关74家低效店，转开一线及省会旗舰店；推行“个店经营”打磨单店效益。",
         source="界面新闻", date="2026年8月",
         url="https://www.toutiao.com/article/7694970914345091620/"),
    # —— 品牌动作 / 新品上市 ——
    dict(brand="奥乐齐", section="新品上市",
         title="奥乐齐鱼子精华“奥家特卖”魔性主题曲病毒传播",
         summary="LACURA鱼子精华“奥家特卖”配《ALDI WOW》主题曲，社媒曝光723万+引爆声量。",
         source="广告门", date="2026年",
         url="https://m.adquan.com/detail/7-363421"),
    dict(brand="胖东来", section="新品上市",
         title="胖东来网红大月饼转线上限购自提",
         summary="网红大月饼转线上同城限购+到店自提，会员码每分钟刷新防代购囤货。",
         source="焦作广播电视台/今日头条", date="2026年9月",
         url="https://www.toutiao.com/article/7684817566853841442/"),
    dict(brand="名创优品", section="新品上市",
         title="名创优品毛绒节田曦薇代言“甜品厨房”",
         summary="毛绒节官宣田曦薇代言“甜品厨房”；抖音峰值2.5万人在线，微博话题阅读4.7亿。",
         source="联商网", date="2026年10月",
         url="http://www.linkshop.cn/news/2026553163.shtml"),
    dict(brand="优衣库", section="新品上市",
         title="优衣库双联名：JWA × F.RISSO 秋冬发售",
         summary="秋冬双联名：JW Anderson 10/16发售，前Marni总监Risso针织系列10/30发售。",
         source="今日头条", date="2026年10月",
         url="https://m.toutiao.com/article/7699042923342299683"),
    dict(brand="盒马", section="新品上市",
         title="盒马抹茶椰椰高钾水登新品榜+回购榜双第一",
         summary="抹茶椰椰高钾水上线半月登水饮新品榜+回购榜双第一，小红书抖音刷屏成爆款。",
         source="网易/每日食品", date="2026年10月",
         url="https://www.163.com/dy/article/LAD4Q0MK0514HDQI.html"),
    # —— 品牌动作 / 内容声量 ——
    dict(brand="奥乐齐", section="内容声量",
         title="奥乐齐小红书“大牌平替”、抖音探店成话题",
         summary="小红书“大牌平替”、抖音探店开箱成消费话题，从折扣超市变“网红超市”。",
         source="搜狐新闻", date="2026年9月",
         url="https://news.sohu.com/a/1076693603_115479"),
    dict(brand="胖东来", section="内容声量",
         title="胖东来国庆400万人挤进，抖音榜零直播进前十",
         summary="国庆400万人挤进称“不挂牌6A景区”；抖音小店榜零直播进前十，品牌溢出型增长。",
         source="大数跨境/蝉妈妈", date="2026年10月",
         url="https://www.10100.com/article/152902208"),
    dict(brand="山姆", section="内容声量",
         title="山姆县城“分姆”代购抖音小红书疯传",
         summary="县城“分姆”代购集合店抖音小红书疯传，单条采购视频播放超百万引创业潮。",
         source="新食界/今日头条", date="2026年",
         url="https://m.toutiao.com/article/7683851067435614783"),
    dict(brand="名创优品", section="内容声量",
         title="名创优品YOYO“举万物”UGC，小玉从小红书走红",
         summary="YOYO“举万物”小红书UGC裂变；素人IP小玉从小红书走红，国庆上海老洋房排队。",
         source="搜狐/DT商业观察", date="2026年",
         url="https://m.sohu.com/a/1087497688_100024718"),
    dict(brand="优衣库", section="内容声量",
         title="优衣库“平替”浏览破亿，JWA货号单蹲点刷屏",
         summary="“优衣库平替”社交平台浏览破亿；JWA联名货号单蹲点、廓形神裤小红书刷屏。",
         source="腾讯财经/什么值得买", date="2026年10月",
         url="https://gu.qq.com/resources/shy/news/detail-v2/index.html?id=SN202610211645589540ba6e"),
    dict(brand="盒马", section="内容声量",
         title="盒马“8毛虾”登上海热搜TOP2，油烟换海鲜抖音4226万",
         summary="“8毛虾”省心价登上海同城热搜TOP2阅读1.6亿；老板电器“油烟换海鲜”抖音4226万。",
         source="广告门", date="2026年",
         url="https://m.adquan.com/detail/7-363927"),
    # —— 行业研究 ——
    dict(brand="奥乐齐", section="行业研究",
         title="硬折扣三强混战：盒马领跑、奥乐齐提速、快乐猴猛追",
         summary="硬折扣三强混战：盒马超盒算NB领跑、奥乐齐提速、美团快乐猴猛追，10元成价格锚点。",
         source="联商网", date="2026年10月",
         url="https://www.linkshop.com/news/2026553617.shtml"),
    dict(brand="山姆", section="行业研究",
         title="会员制经济分化：山姆守价值，胖东来成样本",
         summary="会员制经济分化：山姆高速扩张守会员价值；胖东来不卷价格卷服务成价值回归样本。",
         source="央广网", date="2026年11月",
         url="https://www.cnr.cn/mspd/jrhm/20261102/t20261102_527859837.shtml"),
    dict(brand="盒马", section="行业研究",
         title="内容种草驱动零售，抖音小红书成第一推手",
         summary="内容种草改写零售：抖音/小红书成县域创业与爆品孵化第一推手，UGC闭环主导选品。",
         source="今日头条/行业媒体", date="2026年",
         url="https://m.toutiao.com/article/7696343010199470628"),
]
RETAIL_NOTICE = '''<div class="notice notice-retail">
  <strong>🔍 零售信源与口径说明：</strong>
  本模块已接入<strong>真实商业零售垂直信源</strong>——通过实时网页检索（WebSearch）对 6 个重点零售品牌逐一抓取，内容来自品牌官网、权威媒体与行业研报，<strong>非 AI 资讯源</strong>。
  零售品牌动态密集，本模块聚合的是<strong>近 2~3 个月（2026 年 8–11 月）真实动态</strong>，非严格同日新闻。
  <br><strong>结构说明：</strong>本模块仅分「品牌动作」（含新品上市 / 品牌战略与动态 / 渠道与门店 / 内容声量 四子分组）与「行业研究」两大块；「内容声量」专追抖音/小红书/视频号等社媒话题、探店、代购生态与 UGC 种草。
</div>'''

# =====================================================================
# 今日金句提炼（10 句，基于真实报道的洞察提炼，非逐字引用）
# =====================================================================
QUOTES = [
    dict(text="胖东来前8月卖195亿，却主动关停年利过亿的老店——它算的不是坪效，是「幸福账」。",
         source="据 东方快消品中心 报道提炼"),
    dict(text="山姆2026财年破1400亿、付费会员破1070万，会员制经济的护城河，仍是「信任」二字。",
         source="据 正观新闻 报道提炼"),
    dict(text="盒马GMV破1070亿、设立AI委员会，零售下一战，是算法替你选品。",
         source="据 财经报道 提炼"),
    dict(text="奥乐齐自有品牌占90%才敢打硬折扣，折扣战的本质，是供应链。",
         source="据 中国零售业博览会 报道提炼"),
    dict(text="优衣库大中华区收益+11.3%却净关74店，关低效、开旗舰，是「个店经营」的转向。",
         source="据 证券时报 报道提炼"),
    dict(text="名创优品自有IP YOYO前9月破10亿，IP大店出海，成新增长极。",
         source="据 MINISO IR 业务更新 提炼"),
    dict(text="家纺奥莱渠道成直营增长主力，罗莱、水星加速围猎购物中心的折扣流量。",
         source="据 同花顺/中财网 研报 提炼"),
    dict(text="水星家纺前三季扣非利润+6.62%，科技被芯把「材质叙事」升级成「睡眠科技叙事」。",
         source="据 水星家纺 IR活动记录 提炼"),
    dict(text="内容种草改写零售，抖音、小红书成县域创业与爆品孵化第一推手。",
         source="据 行业媒体 报道 提炼"),
    dict(text="硬折扣三强混战，10元成价格锚点，性价比回归主流消费的C位。",
         source="据 联商网 报道 提炼"),
]

# 数据外部化：优先读取同目录 data.json（由每日自动化刷新）；下方内嵌数据作为离线兜底
import json as _json
try:
    with open(os.path.join(BASE, "data.json"), encoding="utf-8") as _f:
        _D = _json.load(_f)
    HOME_DATA = _D["HOME_DATA"]
    RETAIL_DATA = _D["RETAIL_DATA"]
    QUOTES = _D["QUOTES"]
except FileNotFoundError:
    pass  # 使用内嵌兜底数据

# =====================================================================
# 组装模块
# =====================================================================
MODULES = [
    dict(key="home", name="家纺行业", tagline="覆盖无印良品 / 全棉时代 / 松山棉店 / 艾美家 / 季米 / 水星家纺 / 奥莱渠道",
         brands=HOME_BRANDS, data=HOME_DATA, notice=HOME_NOTICE,
         accent="#B5651D", grad="linear-gradient(135deg,#B5651D 0%,#D98E2B 100%)"),
    dict(key="retail", name="商业零售洞察", tagline="覆盖奥乐齐 / 胖东来 / 山姆 / 盒马 / 名创优品 / 优衣库",
         brands=RETAIL_BRANDS, data=RETAIL_DATA, notice=RETAIL_NOTICE,
         accent="#1A7D5A", grad="linear-gradient(135deg,#1A7D5A 0%,#2E86C1 100%)"),
]

# 全局连续编号（跨模块、跨版块不重新计数）—— 仅新闻卡片
# 按实际渲染顺序编号：模块顺序 → 品牌动作(四子分组) → 行业研究，保证阅读顺序与编号一致单调
_RENDER_ORDER = []
for _mod in MODULES:
    for _sg_name, _, _ in SUBGROUPS:
        _RENDER_ORDER += [d for d in _mod["data"] if d["section"] == _sg_name]
    _RENDER_ORDER += [d for d in _mod["data"] if block_of(d["section"]) == "行业研究"]
for i, d in enumerate(_RENDER_ORDER, 1):
    d["num"] = i
ALL = _RENDER_ORDER
TOTAL = len(ALL)

def block_count(mod, block):
    return sum(1 for d in mod["data"] if block_of(d["section"]) == block)

# ===== 卡片渲染（带 data-brand / data-module 供筛选）=====
def card_html(c, mkey):
    bcolor = MODULES[0]["brands"].get(c["brand"]) or MODULES[1]["brands"].get(c["brand"], "#888")
    return f'''      <article class="card" data-brand="{esc(c['brand'])}" data-module="{mkey}">
        <span class="card-num">{c['num']:02d}</span>
        <span class="brand-chip" style="background:{bcolor}">{esc(c['brand'])}</span>
        <h3 class="card-title">{esc(c['title'])}</h3>
        <span class="card-source"><svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg><span>{esc(c['source'])}</span></span>
        <p class="card-summary">{esc(clip(c['summary'], 60))}</p>
        <div class="card-meta"><span class="card-time">📅 {esc(c['date'])}</span></div>
        <a class="card-link" href="{esc(c['url'])}" target="_blank" rel="noopener noreferrer" aria-label="阅读原文：{esc(c['title'])}">阅读原文 <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M9 7h8v8"/></svg></a>
      </article>'''

BRAND_ACTION_ICON = '<svg viewBox="0 0 24 24"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>'

def render_block_brandaction(mod):
    """品牌动作块：内含 4 子分组"""
    mkey = mod["key"]
    parts = []
    parts.append(f'''    <section class="section" id="{mkey}-brand-action">
    <div class="section-inner">
      <div class="section-head">
        <span class="icon brand-action-icon">{BRAND_ACTION_ICON}</span>
        <h2>品牌动作</h2>
        <span class="count">{block_count(mod,'品牌动作')} 条</span>
      </div>''')
    for sg_name, sg_id, sg_icon in SUBGROUPS:
        cards = [c for c in mod["data"] if c["section"] == sg_name]
        if not cards:
            continue
        body = "\n".join(card_html(c, mkey) for c in cards)
        parts.append(f'''      <div class="subhead">
        <span class="subhead-icon">{sg_icon}</span>
        <h3>{esc(sg_name)}</h3>
        <span class="subhead-count">{len(cards)} 条</span>
      </div>
      <div class="cards">
{body}
      </div>''')
    parts.append('    </div>\n    </section>')
    return "\n".join(parts)

def render_block_industry(mod):
    mkey = mod["key"]
    name, sid, icon = INDUSTRY
    cards = [c for c in mod["data"] if block_of(c["section"]) == "行业研究"]
    body = "\n".join(card_html(c, mkey) for c in cards)
    return f'''    <section class="section" id="{mkey}-industry">
    <div class="section-inner">
      <div class="section-head">
        <span class="icon">{icon}</span>
        <h2>{esc(name)}</h2>
        <span class="count">{len(cards)} 条</span>
      </div>
      <div class="cards">
{body}
      </div>
    </div>
    </section>'''

def render_module(mod):
    mkey = mod["key"]
    banner = f'''<div class="module-banner {mkey}">
  <div class="module-banner-inner">
    <h2>{esc(mod['name'])} <span class="m-total">· {len(mod['data'])} 条</span></h2>
    <p class="mtag">{esc(mod['tagline'])}</p>
    <div class="mchips">
      <span class="mchip">品牌动作 {block_count(mod,'品牌动作')}</span>
      <span class="mchip">行业研究 {block_count(mod,'行业研究')}</span>
    </div>
  </div>
</div>'''
    brandbar = '<div class="brandbar">\n  <span class="lbl">按品牌筛选：</span>\n' + "\n".join(
        f'  <button type="button" class="bf" data-module="{mkey}" data-brand="{esc(b)}" style="--bc:{mod["brands"][b]}">{esc(b)}</button>'
        for b in mod["brands"]
    ) + "\n</div>"
    blocks = render_block_brandaction(mod) + "\n" + render_block_industry(mod)
    return f'<div class="module" data-module="{mkey}">\n{banner}\n{brandbar}\n{mod["notice"]}\n{blocks}\n</div>'

MODULES_HTML = "\n".join(render_module(m) for m in MODULES)

# ===== 今日金句 =====
quotes_html_parts = []
for i, q in enumerate(QUOTES, 1):
    quotes_html_parts.append(f'''      <article class="quote-card">
        <span class="quote-num">金句 {i:02d}</span>
        <p class="quote-text">“{esc(q['text'])}”</p>
        <span class="quote-source">{esc(q['source'])}</span>
      </article>''')
QUOTES_HTML = f'''<section class="section quotes-section" id="quotes">
  <div class="section-inner">
    <div class="section-head">
      <span class="icon quote-icon"><svg viewBox="0 0 24 24"><path d="M7 7h4v6H8v-2h2c0 2-1 3-3 3v-2h1V7zm8 0h4v6h-3v-2h2c0 2-1 3-3 3v-2h1V7z" fill="#fff"/></svg></span>
      <h2>今日金句提炼</h2>
      <span class="count">{len(QUOTES)} 句</span>
    </div>
    <div class="quotes-grid">
{"".join(quotes_html_parts)}
    </div>
    <p class="quotes-note">＊ 以上为基于本期真实报道的<strong>洞察提炼</strong>，非逐字引用；每条标注原始信源，便于溯源核对。</p>
  </div>
</section>'''

# ===== 导航（跨模块，按模块分组；两大块 + 金句）=====
nav_parts = []
for mod in MODULES:
    nav_parts.append(f'      <span class="nav-group-label" style="color:{mod["accent"]}">{esc(mod["name"])}</span>')
    nav_parts.append(f'      <button type="button" data-target="{mod["key"]}-brand-action">品牌动作</button>')
    nav_parts.append(f'      <button type="button" data-target="{mod["key"]}-industry">行业研究</button>')
nav_parts.append('      <span class="nav-group-label" style="color:#B5651D">提炼</span>')
nav_parts.append('      <button type="button" data-target="quotes">今日金句</button>')
nav_buttons = "\n".join(nav_parts)

# ===== Hero 统计 =====
home_n = len(HOME_DATA)
retail_n = len(RETAIL_DATA)
industry_total = sum(block_count(m, "行业研究") for m in MODULES)
stat_cards = f'      <div class="stat-card"><div class="stat-num" data-target="{TOTAL}">0</div><div class="stat-label">资讯条数</div></div>'
stat_cards += f'\n      <div class="stat-card"><div class="stat-num" data-target="{home_n}">0</div><div class="stat-label">家纺行业</div></div>'
stat_cards += f'\n      <div class="stat-card"><div class="stat-num" data-target="{retail_n}">0</div><div class="stat-label">商业零售</div></div>'
stat_cards += f'\n      <div class="stat-card"><div class="stat-num" data-target="{industry_total}">0</div><div class="stat-label">行业研究</div></div>'
stat_cards += f'\n      <div class="stat-card"><div class="stat-num" data-target="{len(QUOTES)}">0</div><div class="stat-label">今日金句</div></div>'

CSS = '''*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg-primary:#FBF7F2; --bg-card:#FFFFFF; --bg-elevated:#F3ECE2;
  --text-primary:#23201C; --text-secondary:#5C554C; --text-muted:#8A8278;
  --accent:#B5651D; --accent-hover:#8F4E15; --accent-light:#F0DEC9;
  --retail:#1A7D5A; --retail-light:#EAF4EF;
  --gradient:linear-gradient(135deg,#B5651D 0%,#D98E2B 100%);
  --gradient-soft:linear-gradient(135deg,#F3ECE2 0%,#F7EEDD 100%);
  --border:#E7DCCB; --border-hover:#D2A878; --radius:14px; --radius-sm:8px;
  --shadow:0 4px 20px rgba(181,101,29,0.08); --shadow-hover:0 8px 28px rgba(181,101,29,0.16);
  --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
  --font-mono:"SF Mono","Fira Code",Menlo,Consolas,monospace;
  --transition:0.25s cubic-bezier(0.4,0,0.2,1);
}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--bg-primary);color:var(--text-primary);line-height:1.6;overflow-x:hidden;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.topnav{position:sticky;top:0;z-index:50;background:rgba(251,247,242,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--border)}
.topnav-inner{max-width:1120px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:18px;overflow-x:auto}
.topnav-brand{font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:8px;white-space:nowrap}
.topnav-brand .dot{width:10px;height:10px;border-radius:50%;background:var(--gradient);box-shadow:0 0 0 3px var(--accent-light);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 3px var(--accent-light)}50%{box-shadow:0 0 0 6px rgba(181,101,29,0.15)}}
.topnav-links{display:flex;gap:6px;flex:1;align-items:center;flex-wrap:nowrap}
.topnav-links .nav-group-label{font-size:0.7rem;font-weight:700;letter-spacing:0.5px;margin:0 4px 0 8px;white-space:nowrap;opacity:0.7}
.topnav-links button{appearance:none;border:0;background:transparent;font:inherit;cursor:pointer;font-size:0.8rem;color:var(--text-secondary);padding:6px 11px;border-radius:999px;white-space:nowrap;transition:var(--transition);min-height:36px;display:inline-flex;align-items:center}
.topnav-links button:hover,.topnav-links button.active{background:var(--accent-light);color:var(--accent)}
.hero{padding:60px 24px 44px;text-align:center;background:var(--gradient-soft);position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;top:-100px;right:-100px;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(181,101,29,0.14) 0%,transparent 70%)}
.hero::after{content:"";position:absolute;bottom:-80px;left:-80px;width:240px;height:240px;border-radius:50%;background:radial-gradient(circle,rgba(26,125,90,0.14) 0%,transparent 70%)}
.hero-inner{max-width:920px;margin:0 auto;position:relative;z-index:1}
.date-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 16px;border-radius:999px;background:var(--bg-card);border:1px solid var(--border);font-size:0.85rem;color:var(--text-secondary);margin-bottom:18px;box-shadow:var(--shadow)}
.date-badge .live{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 0 0 rgba(34,197,94,0.5);animation:live-pulse 1.6s ease-out infinite}
@keyframes live-pulse{0%{box-shadow:0 0 0 0 rgba(34,197,94,0.5)}100%{box-shadow:0 0 0 10px rgba(34,197,94,0)}}
.hero h1{font-size:clamp(2rem,5vw,3.2rem);font-weight:800;letter-spacing:-1px;line-height:1.15;margin-bottom:12px}
.hero h1 .accent{background:var(--gradient);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-tagline{font-size:clamp(0.95rem,1.6vw,1.1rem);color:var(--text-secondary);margin-bottom:30px}
.hero-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:14px;max-width:920px;margin:0 auto}
.stat-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:18px 14px;text-align:center;box-shadow:var(--shadow);transition:var(--transition)}
.stat-card:hover{transform:translateY(-3px);box-shadow:var(--shadow-hover);border-color:var(--border-hover)}
.stat-num{font-size:2.1rem;font-weight:800;font-family:var(--font-mono);background:var(--gradient);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1}
.stat-label{font-size:0.74rem;color:var(--text-muted);margin-top:6px;letter-spacing:0.5px}
.notice,.brandbar{max-width:1120px;margin:0 auto;padding:0 24px}
.notice{margin-top:22px;background:#FBF1DE;border:1px solid #EBD3A8;border-radius:var(--radius);font-size:0.85rem;color:#7A531A;line-height:1.7;padding:16px 20px}
.notice strong{color:#5C3D00}
.notice-retail{background:#EAF4EF;border-color:#BFE0D0;color:#1F5C44}
.notice-retail strong{color:#13402E}
.brandbar{margin-top:18px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.brandbar .lbl{font-size:0.8rem;color:var(--text-muted);margin-right:4px}
.bf{appearance:none;border:1px solid var(--border);background:var(--bg-card);font:inherit;cursor:pointer;font-size:0.8rem;color:var(--text-secondary);padding:5px 14px;border-radius:999px;transition:var(--transition);border-left:4px solid var(--bc,#ccc);min-height:34px;display:inline-flex;align-items:center}
.bf:hover{background:var(--accent-light);color:var(--accent)}
.bf.active{background:var(--bc,#B5651D);color:#fff;border-color:var(--bc,#B5651D)}
.module{padding-top:8px}
.module-banner{max-width:1120px;margin:0 auto;padding:0 24px}
.module-banner-inner{margin-top:34px;padding:22px 24px;border-radius:var(--radius);background:var(--gradient);color:#fff;box-shadow:var(--shadow);position:relative;overflow:hidden}
.module-banner.retail .module-banner-inner{background:linear-gradient(135deg,#1A7D5A 0%,#2E86C1 100%)}
.module-banner h2{font-size:1.6rem;font-weight:800;letter-spacing:-0.5px}
.module-banner h2 .m-total{font-size:1.05rem;font-weight:600;opacity:0.92}
.module-banner .mtag{font-size:0.85rem;opacity:0.92;margin-top:6px}
.module-banner .mchips{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
.module-banner .mchip{background:rgba(255,255,255,0.22);font-size:0.78rem;padding:4px 12px;border-radius:999px}
.section{padding:52px 24px 18px;scroll-margin-top:64px}
.section-inner{max-width:1120px;margin:0 auto}
.section-head{display:flex;align-items:baseline;gap:14px;margin-bottom:20px;padding-bottom:14px;border-bottom:2px dashed var(--border)}
.section-head .icon{width:34px;height:34px;border-radius:10px;background:var(--gradient);display:flex;align-items:center;justify-content:center;flex-shrink:0;align-self:center}
.section-head .icon svg{width:18px;height:18px}
.section-head h2{font-size:1.45rem;font-weight:700;letter-spacing:-0.3px}
.section-head .count{font-size:0.8rem;margin-left:auto;font-family:var(--font-mono);background:var(--accent-light);color:var(--accent);padding:3px 10px;border-radius:999px;align-self:center}
.subhead{display:flex;align-items:center;gap:10px;margin:26px 0 14px;padding:8px 14px;background:var(--bg-elevated);border-radius:10px;border-left:4px solid var(--accent)}
.subhead-icon{width:22px;height:22px;border-radius:6px;background:var(--gradient);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.subhead-icon svg{width:13px;height:13px}
.subhead h3{font-size:1.02rem;font-weight:700;letter-spacing:-0.2px}
.subhead-count{font-size:0.72rem;margin-left:auto;font-family:var(--font-mono);color:var(--text-muted);background:var(--bg-card);padding:2px 8px;border-radius:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:20px 22px;display:flex;flex-direction:column;position:relative;overflow:hidden;transition:var(--transition)}
html.js-ready .card{opacity:0;transform:translateY(16px)}
html.js-ready .card.visible,.card.visible{opacity:1;transform:none}
.card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--gradient);transform:scaleX(0);transform-origin:left;transition:transform 0.3s ease}
.card:hover{border-color:var(--border-hover);box-shadow:var(--shadow-hover);transform:translateY(-3px)}
.card:hover::before{transform:scaleX(1)}
.card-num{position:absolute;top:14px;right:18px;font-family:var(--font-mono);font-size:0.78rem;color:var(--text-muted);background:var(--bg-elevated);padding:2px 8px;border-radius:6px}
.brand-chip{display:inline-block;align-self:flex-start;color:#fff;font-size:0.72rem;font-weight:600;padding:3px 10px;border-radius:999px;margin-bottom:10px}
.card-title{font-size:1.02rem;font-weight:600;line-height:1.45;margin-bottom:12px;padding-right:48px;letter-spacing:-0.2px}
.card-source{display:inline-flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text-muted);margin-bottom:10px;padding:3px 10px;background:var(--bg-elevated);border-radius:999px;align-self:flex-start;max-width:100%}
.card-source svg{width:11px;height:11px;flex-shrink:0;opacity:0.6}
.card-source span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card-summary{font-size:0.88rem;color:var(--text-secondary);line-height:1.6;margin-bottom:12px;flex:1}
.card-meta{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.card-time{font-size:0.74rem;color:var(--text-muted);background:var(--bg-elevated);padding:2px 8px;border-radius:6px}
.card-link{display:inline-flex;align-items:center;gap:6px;font-size:0.82rem;font-weight:500;color:var(--accent);margin-top:auto;align-self:flex-start;transition:var(--transition)}
.card-link svg{width:14px;height:14px;transition:transform 0.2s ease}
.card-link:hover{color:var(--accent-hover)}
.card-link:hover svg{transform:translate(2px,-2px)}
/* 今日金句 */
.quotes-section{background:linear-gradient(135deg,#2B2118 0%,#3A2A1C 100%)}
.quotes-section .section-head{border-bottom:2px dashed rgba(255,255,255,0.18)}
.quotes-section .section-head h2{color:#fff}
.quotes-section .section-head .icon{background:linear-gradient(135deg,#D98E2B 0%,#B5651D 100%)}
.quotes-section .section-head .count{background:rgba(255,255,255,0.15);color:#F0DEC9}
.quotes-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.quote-card{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.14);border-radius:var(--radius);padding:20px 22px;display:flex;flex-direction:column;position:relative;overflow:hidden;transition:var(--transition)}
.quote-card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#D98E2B,#B5651D);transform:scaleX(0);transform-origin:left;transition:transform 0.3s ease}
.quote-card:hover{background:rgba(255,255,255,0.1);transform:translateY(-3px)}
.quote-card:hover::before{transform:scaleX(1)}
.quote-num{font-family:var(--font-mono);font-size:0.72rem;color:#D98E2B;background:rgba(217,142,43,0.15);padding:2px 8px;border-radius:6px;align-self:flex-start;margin-bottom:12px}
.quote-text{font-size:1.02rem;font-weight:600;color:#FDF6EC;line-height:1.7;flex:1;letter-spacing:0.2px}
.quote-source{font-size:0.74rem;color:rgba(255,255,255,0.55);margin-top:14px}
.quotes-note{font-size:0.78rem;color:rgba(255,255,255,0.5);margin-top:22px;text-align:center}
.quotes-note strong{color:#F0DEC9}
footer{margin-top:56px;padding:40px 24px;text-align:center;border-top:1px solid var(--border);background:var(--bg-elevated)}
.footer-stats{display:inline-flex;align-items:center;gap:16px;font-size:0.85rem;color:var(--text-secondary);flex-wrap:wrap;justify-content:center}
.footer-stats .sep{color:var(--text-muted)}
.footer-source{font-size:0.78rem;color:var(--text-muted);margin-top:8px}
.footer-source a{color:var(--accent);font-weight:500}
@media (max-width:768px){.topnav-inner{padding:10px 14px;gap:10px}.topnav-links{overflow-x:auto;-webkit-overflow-scrolling:touch;flex-wrap:nowrap;scrollbar-width:none}.topnav-links::-webkit-scrollbar{display:none}.topnav-links .nav-group-label{display:none}.hero{padding:38px 16px 30px}.hero h1{font-size:clamp(1.7rem,8vw,2.3rem)}.hero-stats{grid-template-columns:repeat(auto-fit,minmax(88px,1fr));gap:10px}.stat-card{padding:13px 8px}.stat-num{font-size:1.6rem}.section{padding:34px 16px 12px;scroll-margin-top:56px}.cards,.quotes-grid{grid-template-columns:1fr;gap:12px}.card{padding:16px}.card-title{font-size:0.98rem;padding-right:44px}.module-banner{padding:0 16px}.module-banner-inner{padding:18px 18px}.module-banner h2{font-size:1.35rem}.brandbar{padding:0 16px}.notice{padding:0 16px}.subhead{flex-wrap:wrap;gap:8px}.section-head{flex-wrap:wrap;gap:8px}.section-head .count{margin-left:0}}'''

JS = '''const supportsObserver='IntersectionObserver' in window;
const sections=document.querySelectorAll('section[id]');
const navLinks=document.querySelectorAll('.topnav-links button');
function setActiveNav(id){navLinks.forEach(b=>b.classList.toggle('active',b.dataset.target===id));}
navLinks.forEach(button=>{button.addEventListener('click',()=>{const s=document.getElementById(button.dataset.target);if(!s)return;setActiveNav(s.id);try{s.scrollIntoView({behavior:'smooth',block:'start'});}catch(_){s.scrollIntoView(true);}});});
function animateNum(el,target,duration){const start=performance.now();function tick(now){const t=Math.min((now-start)/duration,1);const eased=1-Math.pow(1-t,3);el.textContent=Math.round(eased*target);if(t<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}
const statNums=document.querySelectorAll('.stat-num[data-target]');
if(supportsObserver){const o=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){const t=parseInt(e.target.dataset.target,10);if(!isNaN(t))animateNum(e.target,t,1200);o.unobserve(e.target);}});},{threshold:0.4});statNums.forEach(el=>o.observe(el));}
else{statNums.forEach(el=>{const t=parseInt(el.dataset.target,10);if(!isNaN(t))el.textContent=t;});}
const cards=document.querySelectorAll('.card,.quote-card');
if(supportsObserver){const co=new IntersectionObserver((es)=>{es.forEach((e,i)=>{if(e.isIntersecting){e.target.style.transitionDelay=(i%6)*40+'ms';e.target.classList.add('visible');co.unobserve(e.target);}});},{threshold:0.15});cards.forEach(el=>co.observe(el));}
else{cards.forEach(el=>el.classList.add('visible'));}
if(supportsObserver){const spy=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting)setActiveNav(e.target.id);});},{rootMargin:'-40% 0px -55% 0px'});sections.forEach(s=>spy.observe(s));}
// 品牌筛选（按模块作用域隔离）
document.querySelectorAll('.module').forEach(mod=>{
  const mkey=mod.dataset.module;
  const bf=mod.querySelectorAll('.bf');
  const mc=mod.querySelectorAll('.card');
  bf.forEach(btn=>btn.addEventListener('click',()=>{
    const b=btn.dataset.brand;
    const active=btn.classList.contains('active');
    bf.forEach(x=>x.classList.remove('active'));
    if(active){mc.forEach(c=>c.style.display='');return;}
    btn.classList.add('active');
    mc.forEach(c=>{c.style.display=(c.dataset.brand===b)?'':'none';});
  }));
});'''

html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>双行业晨报 · 家纺 + 商业零售 · {DATE_STR}</title>
<script>document.documentElement.classList.add('js-ready');</script>
<style>{CSS}</style>
</head>
<body>
<nav class="topnav" aria-label="版块导航">
  <div class="topnav-inner">
    <div class="topnav-brand"><span class="dot"></span>双行业晨报 · 真实信源</div>
    <div class="topnav-links">
{nav_buttons}
    </div>
  </div>
</nav>

<header class="hero">
  <div class="hero-inner">
    <div class="date-badge"><span class="live"></span>{HERO_DATE}</div>
    <h1>双行业 <span class="accent">晨报</span></h1>
    <p class="hero-tagline">家纺行业 + 商业零售洞察 · 真实垂直信源聚合（WebSearch）</p>
    <div class="hero-stats">
{stat_cards}
    </div>
  </div>
</header>

<main>
{MODULES_HTML}
{QUOTES_HTML}
</main>

<footer>
  <div class="footer-stats">
    <span>资讯 <strong>{TOTAL}</strong> 条</span>
    <span class="sep">·</span>
    <span>家纺 {home_n} 条</span>
    <span class="sep">·</span>
    <span>商业零售 {retail_n} 条</span>
    <span class="sep">·</span>
    <span>今日金句 {len(QUOTES)} 句</span>
    <span class="sep">·</span>
    <span>{HERO_DATE}</span>
  </div>
  <div class="footer-source">数据来源：实时网页检索聚合（WebSearch）· 品牌官网 / 权威媒体 / 券商研报 · 日报日期 {DATE_STR} · 内容版权归原作者所有</div>
</footer>

<script>{JS}</script>
</body>
</html>'''

out = os.path.join(BASE, f"双行业晨报_{DATE_STR}.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html_doc)
# 同时输出固定入口 site/index.html，便于一键发布与每日自动化覆盖
site_dir = os.path.join(BASE, "site")
os.makedirs(site_dir, exist_ok=True)
site_index = os.path.join(site_dir, "index.html")
with open(site_index, "w", encoding="utf-8") as f:
    f.write(html_doc)
print("WROTE:", out)
print("WROTE SITE:", site_index)
print("TOTAL NEWS:", TOTAL, "HOME:", home_n, "RETAIL:", retail_n, "INDUSTRY:", industry_total, "QUOTES:", len(QUOTES))
print("HOME BREAKDOWN:", {block_of(d['section']): sum(1 for x in HOME_DATA if block_of(x['section'])==block_of(d['section'])) for d in HOME_DATA})
print("RETAIL BREAKDOWN:", {block_of(d['section']): sum(1 for x in RETAIL_DATA if block_of(x['section'])==block_of(d['section'])) for d in RETAIL_DATA})
