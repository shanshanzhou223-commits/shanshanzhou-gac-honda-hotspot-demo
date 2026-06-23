"""
创意内容角度库（Creative Angle Library）
按叙事原型、情绪、领域、人群、平台多维度组织，
为 generate_content_angles 提供几十到上百个可发散的创意角度模板。
"""
from typing import Dict, List

# 每个模板是一个 dict，支持 requires 字段控制必填上下文变量
CreativeAngleTemplate = Dict[str, str]


CREATIVE_ANGLE_TEMPLATES: Dict[str, List[CreativeAngleTemplate]] = {
    # ------------------------------------------------------------------
    # 按叙事原型（Narrative Archetype）
    # ------------------------------------------------------------------
    "探索突破": [
        {"template": "《{keyword}之后，人类下一步会去哪？{vehicle}给出了地面答案》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《从{keyword}到{vehicle}：探索这件事，不一定需要上天》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{vehicle}的{image0}，像{keyword}一样打开新边界》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《如果{keyword}是一次出发，{vehicle}就是路上的状态》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《为什么关注{keyword}的人，也会多看{vehicle}一眼？》", "type": "讨论", "platform": "知乎"},
    ],
    "挑战极限": [
        {"template": "《{keyword}告诉我们：极限是用来刷新的，{vehicle}也是》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从{keyword}到{vehicle}的{scene0}，挑战从未停过》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}火了，{vehicle}用{image0}接住了这份热血》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《不是每个人都去挑战{keyword}，但{vehicle}懂那种想赢的感觉》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{keyword}背后，{vehicle}的{image0}为什么能撑住？》", "type": "长图文", "platform": "微信公众号 / 知乎"},
    ],
    "创新颠覆": [
        {"template": "《{keyword}重新定义了规则，{vehicle}重新定义了{scene0}》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}打破常识，{vehicle}用{image0}接住了下一波》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}不是终点，{vehicle}的{image0}才是开始》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《为什么{keyword}之后，我开始重新看{vehicle}？》", "type": "讨论", "platform": "知乎 / 微博"},
        {"template": "《{keyword}改变了一切，除了{vehicle}对{scene0}的理解》", "type": "长图文", "platform": "微信公众号"},
    ],
    "成长蜕变": [
        {"template": "《{keyword}之后，{vehicle}车主的故事变了》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从追{keyword}到开{vehicle}，成年人的成长有迹可循》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{keyword}是一个节点，{vehicle}是下一个阶段的礼物》", "type": "小红书笔记", "platform": "小红书"},
        {"template": "《看完{keyword}，我才懂{vehicle}为什么叫{positioning}》", "type": "长图文", "platform": "微信公众号 / 知乎"},
    ],
    "责任守护": [
        {"template": "《{keyword}让我们想守护重要的人，{vehicle}正好装得下》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《别人在看{keyword}的热闹，{vehicle}在看家人的需要》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之后，{vehicle}的{scene0}成了一种责任》", "type": "图文", "platform": "微博 / 小红书"},
        {"template": "《对{audience}来说，{keyword}是情绪，{vehicle}是底气》", "type": "长图文", "platform": "微信公众号 / 知乎", "requires": ["audience"]},
        {"template": "《{keyword}提醒我们：有些守护，{vehicle}一直在做》", "type": "小红书笔记", "platform": "小红书"},
    ],
    "自由逃离": [
        {"template": "《{keyword}让人想逃，{vehicle}的{scene0}让人想出发》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}成为枷锁，{vehicle}打开了一扇门》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}之后的周末，我开着{vehicle}去了没有人的地方》", "type": "小红书笔记", "platform": "小红书"},
        {"template": "《{keyword}是城市病，{vehicle}是药方》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《用{vehicle}的{image0}，把{keyword}甩在身后》", "type": "短视频", "platform": "抖音 / 视频号"},
    ],
    "团聚归属": [
        {"template": "《{keyword}让我们想回家，{vehicle}让我们能一起回去》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}的尽头，是一辆{vehicle}和一家人》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}再热闹，也不如{vehicle}里的团圆》", "type": "图文", "platform": "微博 / 小红书"},
        {"template": "《{audience}为什么需要{vehicle}？{keyword}给了答案》", "type": "长图文", "platform": "微信公众号 / 知乎", "requires": ["audience"]},
    ],
    "抗争反叛": [
        {"template": "《{keyword}让人不服，{vehicle}的{image0}也不服》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}说不可能，{vehicle}说再试一次》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}是旧规则，{vehicle}是新选择》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《整顿不了{keyword}，但{vehicle}能整顿你的心情》", "type": "小红书笔记", "platform": "小红书"},
    ],
    "怀旧回归": [
        {"template": "《{keyword}让人想起过去，{vehicle}把人带回现在》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}是回忆，{vehicle}是还能继续的日子》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《小时候看{keyword}，长大后开{vehicle}》", "type": "小红书笔记", "platform": "小红书"},
        {"template": "《{keyword}回不去，但{vehicle}的{scene0}还在》", "type": "长图文", "platform": "微信公众号"},
    ],
    "幽默解构": [
        {"template": "《如果{keyword}是一辆车，那一定是{vehicle}的样子》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}很严肃，但{vehicle}的{image0}有点东西》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《把{keyword}拍成{vehicle}广告，第一秒就绷不住了》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}刷屏，{vehicle}车主的反应be like》", "type": "图文", "platform": "微博 / 小红书"},
    ],

    # ------------------------------------------------------------------
    # 按价值观/情绪
    # ------------------------------------------------------------------
    "好奇心": [
        {"template": "《{keyword}让我好奇，{vehicle}让我想上路》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}是问题，{vehicle}的{image0}是答案的一种》", "type": "图文", "platform": "知乎 / 微博"},
        {"template": "《为什么{keyword}和{vehicle}会同时出现在我首页？》", "type": "讨论", "platform": "知乎"},
    ],
    "自豪感": [
        {"template": "《{keyword}让人骄傲，{vehicle}的{image0}也让人骄傲》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从{keyword}到{vehicle}，属于我们的{emotion}时刻》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{keyword}之后，我更理解{vehicle}为什么叫{positioning}》", "type": "长图文", "platform": "微信公众号 / 知乎"},
    ],
    "焦虑感": [
        {"template": "《{keyword}让人焦虑，{vehicle}的{scene0}让人稳一点》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《面对{keyword}，{vehicle}给了一个确定的选择》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{keyword}之后，我开始重新看{vehicle}的{image0}》", "type": "小红书笔记", "platform": "小红书"},
    ],
    "治愈感": [
        {"template": "《{keyword}很治愈，{vehicle}的{scene0}也是》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}让人放松，{vehicle}让人更放松》", "type": "图文", "platform": "小红书 / 微博"},
        {"template": "《{keyword}之后，我想开着{vehicle}慢慢回家》", "type": "小红书笔记", "platform": "小红书"},
    ],
    "热血": [
        {"template": "《{keyword}让人上头，{vehicle}让人想踩一脚》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}是热血，{vehicle}的{image0}是续杯》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《和{keyword}一样，{vehicle}也讲一个不服输》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}刷屏，{vehicle}用{image0}接住了这份燃》", "type": "图文", "platform": "微博 / 小红书"},
    ],
    "共鸣": [
        {"template": "《{keyword}戳中了很多人，{vehicle}也戳中了同一种人》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之所以火，是因为{vehicle}也懂这种感受》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{audience}看{keyword}，也在看{vehicle}》", "type": "长图文", "platform": "微信公众号 / 知乎", "requires": ["audience"]},
    ],
    "幽默": [
        {"template": "《{keyword}好笑，{vehicle}的{image0}更好笑》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《当{keyword}遇到{vehicle}，画风突然变了》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}太正经，{vehicle}来破个梗》", "type": "图文", "platform": "微博 / 小红书"},
    ],
    "希望": [
        {"template": "《{keyword}之后，{vehicle}的{scene0}多了一种可能》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从{keyword}到{vehicle}，未来不是等来的》", "type": "图文", "platform": "知乎 / 微博"},
        {"template": "《{keyword}给了我们希望，{vehicle}给了我们出发的路》", "type": "长图文", "platform": "微信公众号"},
    ],
    "安全感": [
        {"template": "《{keyword}让人不安，{vehicle}的{image0}让人安心》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《面对{keyword}，{vehicle}给的是一个稳字》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{keyword}之后，我更想要{vehicle}这样的确定感》", "type": "小红书笔记", "platform": "小红书"},
    ],

    # ------------------------------------------------------------------
    # 按领域/主题域
    # ------------------------------------------------------------------
    "体育": [
        {"template": "《{keyword}是赛场，{vehicle}是另一种赛场》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}点燃热血，{vehicle}的{image0}也没落下》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}告诉我们，{vehicle}的{scene0}也需要实力》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《像{keyword}一样，{vehicle}也在刷新自己的记录》", "type": "创意视频", "platform": "B站 / 抖音"},
    ],
    "航天": [
        {"template": "《{keyword}让人仰望星空，{vehicle}让人脚踏实地》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从{keyword}到{vehicle}，探索的终点是回家的路》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}是天空的浪漫，{vehicle}是地面的浪漫》", "type": "图文", "platform": "微博 / 知乎"},
    ],
    "AI": [
        {"template": "《{keyword}能读懂数据，{vehicle}能读懂你》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}学会思考，{vehicle}的{image0}学会了回应》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}改变交互，{vehicle}改变{scene0}》", "type": "长图文", "platform": "微信公众号 / 知乎"},
    ],
    "科技": [
        {"template": "《{keyword}是科技的进步，{vehicle}是科技的落地》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之后，{vehicle}的{image0}有了新解释》", "type": "图文", "platform": "知乎 / 微博"},
        {"template": "《当{keyword}成为日常，{vehicle}已经等在那里》", "type": "长图文", "platform": "微信公众号"},
    ],
    "家庭": [
        {"template": "《{keyword}让我们想回家，{vehicle}让我们能一起出发》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}是家人的话题，{vehicle}是家人的空间》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《对{audience}来说，{keyword}和{vehicle}都是刚需》", "type": "长图文", "platform": "微信公众号 / 知乎", "requires": ["audience"]},
    ],
    "职场": [
        {"template": "《{keyword}是职场的日常，{vehicle}是下班后的出口》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}让人疲惫，{vehicle}的{scene0}让人回血》", "type": "图文", "platform": "微博 / 小红书"},
        {"template": "《面对{keyword}，{vehicle}给成年人留了一个体面》", "type": "长图文", "platform": "微信公众号 / 知乎"},
    ],
    "社会": [
        {"template": "《{keyword}是社会情绪，{vehicle}是个人选择》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}刷屏，{vehicle}选择了自己的回应方式》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《{keyword}是大家都在聊的，{vehicle}是你真正拥有的》", "type": "小红书笔记", "platform": "小红书"},
    ],
    "娱乐": [
        {"template": "《{keyword}是娱乐，{vehicle}是娱乐之外的踏实》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《当{keyword}让人上头，{vehicle}让人落地》", "type": "图文", "platform": "微博 / 小红书"},
    ],
    "财经": [
        {"template": "《{keyword}关乎钱，{vehicle}关乎值不值》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之后，{vehicle}的{image0}成了一种理性选择》", "type": "图文", "platform": "知乎 / 微博"},
    ],
    "文化": [
        {"template": "《{keyword}是文化，{vehicle}是文化里的出行方式》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从{keyword}到{vehicle}，传统和现代可以同路》", "type": "图文", "platform": "微博 / 知乎"},
    ],

    # ------------------------------------------------------------------
    # 按目标人群
    # ------------------------------------------------------------------
    "科技男": [
        {"template": "《{keyword}让科技男兴奋，{vehicle}让科技男想试驾》", "type": "短视频", "platform": "B站 / 抖音"},
        {"template": "《{keyword}是参数，{vehicle}的{image0}是体验》", "type": "图文", "platform": "知乎 / 微博"},
    ],
    "职场中年人": [
        {"template": "《{keyword}是中年人的话题，{vehicle}是中年人的空间》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之后，{vehicle}给了职场人一个喘息》", "type": "图文", "platform": "微博 / 知乎"},
    ],
    "宝爸宝妈": [
        {"template": "《{keyword}让爸妈上心，{vehicle}让爸妈放心》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之后，{vehicle}的{scene0}成了家庭刚需》", "type": "图文", "platform": "小红书 / 微博"},
    ],
    "Z世代": [
        {"template": "《{keyword}是Z世代的梗，{vehicle}是Z世代的座驾》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《这届年轻人追{keyword}，也看{vehicle}》", "type": "图文", "platform": "微博 / 小红书"},
    ],
    "年轻女性": [
        {"template": "《{keyword}让她心动，{vehicle}的{image0}让她动心》", "type": "短视频", "platform": "抖音 / 小红书"},
        {"template": "《{keyword}之后，{vehicle}成了她的氛围感选项》", "type": "小红书笔记", "platform": "小红书"},
    ],
    "汽车玩家": [
        {"template": "《{keyword}是话题，{vehicle}的{image0}是玩点》", "type": "短视频", "platform": "B站 / 抖音"},
        {"template": "《聊{keyword}的人，也会聊{vehicle}的{scene0}》", "type": "讨论", "platform": "知乎 / B站"},
    ],
    "银发族": [
        {"template": "《{keyword}是父母那辈的话题，{vehicle}是那辈人的稳重》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}之后，{vehicle}给了长辈一份安心》", "type": "图文", "platform": "微博 / 小红书"},
    ],

    # ------------------------------------------------------------------
    # 通用兜底 / 创意发散
    # ------------------------------------------------------------------
    "通用": [
        {"template": "《当{keyword}刷屏，{vehicle}用{image0}回应》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{keyword}背后，{vehicle}想说的是{image0}》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《{vehicle}车主的一天：{keyword}之后，回到{scene0}》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《如果{keyword}是一辆车，大概就是{vehicle}的样子》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《把{keyword}拍成一支{vehicle}广告，会是什么样？》", "type": "创意视频", "platform": "B站 / 抖音"},
        {"template": "《{vehicle}回应{keyword}：本色出演》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《用{vehicle}的{image0}，重新理解{keyword}》", "type": "短视频", "platform": "抖音 / 视频号"},
        {"template": "《从{keyword}到{vehicle}：{narrative}的两种表达》", "type": "短视频", "platform": "抖音 / 视频号", "requires": ["narrative"]},
        {"template": "《{vehicle}的{scene0}，刚好装得下{keyword}的{emotion}》", "type": "短视频", "platform": "抖音 / 视频号", "requires": ["emotion"]},
        {"template": "《别人在聊{keyword}，{vehicle}守住{image0}》", "type": "图文", "platform": "微博 / 知乎"},
        {"template": "《为什么{keyword}让{vehicle}有了新话题？》", "type": "讨论", "platform": "知乎 / 微博"},
        {"template": "《{keyword}火了，{vehicle}的{image0}刚刚好》", "type": "小红书笔记", "platform": "小红书"},
        {"template": "《不聊参数，只聊{emotion}：{vehicle}与{keyword}》", "type": "图文", "platform": "小红书 / 微博", "requires": ["emotion"]},
        {"template": "《{vehicle} × {keyword}｜{emotion}出行氛围感》", "type": "小红书笔记", "platform": "小红书", "requires": ["emotion"]},
        {"template": "《{keyword}之后，{vehicle}给{audience}的一个选择》", "type": "图文", "platform": "小红书 / 微博", "requires": ["audience"]},
        {"template": "《从{keyword}看{vehicle}：写给{audience}的深度解读》", "type": "长图文", "platform": "微信公众号", "requires": ["audience"]},
        {"template": "《{keyword}刷屏，{vehicle}做对了什么？》", "type": "长图文", "platform": "微信公众号 / 知乎"},
        {"template": "《知乎回答：如何评价{keyword}与{vehicle}的这次相遇？》", "type": "讨论", "platform": "知乎"},
        {"template": "《当{keyword}成为焦点，{vehicle}选择用实力回应》", "type": "长图文", "platform": "微信公众号"},
    ],
}


def get_creative_templates(
    narrative: str = "",
    emotion: str = "",
    field: str = "",
    audience: str = "",
) -> List[CreativeAngleTemplate]:
    """
    根据热点标签，从创意库中取出相关模板。
    优先顺序：叙事原型 > 情绪 > 领域 > 人群 > 通用。
    """
    templates = []
    for dim, key in [
        ("叙事原型", narrative),
        ("价值观/情绪", emotion),
        ("领域/主题域", field),
        ("目标人群重合度", audience),
    ]:
        if key and key in CREATIVE_ANGLE_TEMPLATES:
            templates.extend(CREATIVE_ANGLE_TEMPLATES[key])

    # 通用兜底
    templates.extend(CREATIVE_ANGLE_TEMPLATES["通用"])

    return templates
