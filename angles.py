"""
根据车型和热点生成内容角度建议（增强版）
"""
from typing import Dict, List

from data import ANGLE_TEMPLATES, VEHICLES


def _topic_keyword(topic_text: str, max_len: int = 30) -> str:
    """提取话题关键词，默认保留完整文本避免截断"""
    t = topic_text.strip()
    if len(t) > max_len:
        return t[:max_len] + "…"
    return t


def generate_content_angles(
    topic_text: str,
    vehicle_key: str,
    topic_labels: Dict[str, str],
    match_types: List[str],
    top_n: int = 8,
) -> List[Dict]:
    """
    基于车型、热点标签、匹配类型，生成多维度的内容角度建议。
    返回包含角度文本、内容形式、推荐平台的字典列表。
    """
    v = VEHICLES[vehicle_key]
    keyword = _topic_keyword(topic_text)
    narrative = topic_labels.get("叙事原型", "")
    emotion = topic_labels.get("价值观/情绪", "")
    field = topic_labels.get("领域/主题域", "")
    audience = topic_labels.get("目标人群重合度", "")

    image0 = v["image"][0] if v["image"] else ""
    scene0 = v["scenes"][0] if v["scenes"] else ""
    positioning = v["positioning"]

    candidates = []

    # 1. 车型 × 叙事/情绪/领域的预设模板
    templates = ANGLE_TEMPLATES.get(vehicle_key, {})
    for key in [narrative, emotion, field, "default"]:
        if key and key in templates:
            for text in templates[key]:
                candidates.append(
                    {
                        "angle": text,
                        "type": "短视频 / 图文",
                        "platform": "全平台",
                        "source": "车型模板",
                    }
                )

    # 2. 通用动态模板（按内容形式/平台分类）
    dynamic_patterns = [
        # ---- 短视频 / 创意视频 ----
        {
            "template": "《当{keyword}刷屏，{vehicle}用{image0}回应》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        {
            "template": "《{keyword}背后，{vehicle}想说的是{image0}》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        {
            "template": "《{vehicle}车主的一天：{keyword}之后，回到{scene0}》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        {
            "template": "《如果{keyword}是一辆车，大概就是{vehicle}的样子》",
            "type": "创意视频",
            "platform": "B站 / 抖音",
        },
        {
            "template": "《把{keyword}拍成一支{vehicle}广告，会是什么样？》",
            "type": "创意视频",
            "platform": "B站 / 抖音",
        },
        {
            "template": "《{vehicle}不是蹭{keyword}，是它本来就这样》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        {
            "template": "《从{keyword}到{vehicle}：{narrative}的两种表达》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
            "requires": ["narrative"],
        },
        {
            "template": "《{vehicle}的{scene0}，刚好装得下{keyword}的{emotion}》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
            "requires": ["emotion"],
        },
        {
            "template": "《挑战：用{vehicle}的{scene0}接住{keyword}》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        {
            "template": "《从{keyword}聊到{vehicle}，{narrative}还能这么拍》",
            "type": "创意视频",
            "platform": "B站",
            "requires": ["narrative"],
        },
        {
            "template": "《用{vehicle}的{image0}，重新理解{keyword}》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        # ---- 图文 / 长图文 / 讨论 ----
        {
            "template": "《别人在聊{keyword}，{vehicle}守住{image0}》",
            "type": "图文",
            "platform": "微博 / 知乎",
        },
        {
            "template": "《为什么{keyword}让{vehicle}有了新话题？》",
            "type": "讨论",
            "platform": "知乎 / 微博",
        },
        {
            "template": "《{keyword}火了，{vehicle}的{image0}刚刚好》",
            "type": "小红书笔记",
            "platform": "小红书",
        },
        {
            "template": "《{vehicle} × {keyword}｜{emotion}出行氛围感》",
            "type": "小红书笔记",
            "platform": "小红书",
            "requires": ["emotion"],
        },
        {
            "template": "《不聊参数，只聊{emotion}：{vehicle}与{keyword}》",
            "type": "图文",
            "platform": "小红书 / 微博",
            "requires": ["emotion"],
        },
        {
            "template": "《这届{audience}都在追{keyword}，{vehicle}怎么接？》",
            "type": "讨论",
            "platform": "知乎 / 微博",
            "requires": ["audience"],
        },
        {
            "template": "《当{field}遇上{vehicle}，{narrative}有了新答案》",
            "type": "图文",
            "platform": "知乎 / 微博",
            "requires": ["field", "narrative"],
        },
        {
            "template": "《{keyword}之后，{vehicle}给{audience}的一个选择》",
            "type": "图文",
            "platform": "小红书 / 微博",
            "requires": ["audience"],
        },
        {
            "template": "《{vehicle}车主视角：{keyword}下的{scene0}》",
            "type": "小红书笔记",
            "platform": "小红书",
        },
        # ---- 新增：微信公众号长图文 / 知乎深度 / 微博 thread ----
        {
            "template": "《从{keyword}看{vehicle}：写给{audience}的深度解读》",
            "type": "长图文",
            "platform": "微信公众号",
            "requires": ["audience"],
        },
        {
            "template": "《{keyword}背后，{vehicle}如何用{image0}回应这个时代？》",
            "type": "长图文",
            "platform": "微信公众号 / 知乎",
        },
        {
            "template": "《知乎回答：如何评价{keyword}与{vehicle}的这次相遇？》",
            "type": "讨论",
            "platform": "知乎",
        },
        {
            "template": "《{keyword}刷屏，{vehicle}做对了什么？一篇微博图文 thread》",
            "type": "图文",
            "platform": "微博",
        },
        {
            "template": "《当{keyword}成为流量密码，{vehicle}选择不硬蹭》",
            "type": "长图文",
            "platform": "微信公众号",
        },
        {
            "template": "《{vehicle} × {keyword}：一份给{audience}的购车参考》",
            "type": "长图文",
            "platform": "微信公众号 / 知乎",
            "requires": ["audience"],
        },
    ]

    context = {
        "keyword": keyword,
        "vehicle": vehicle_key,
        "image0": image0,
        "scene0": scene0,
        "narrative": narrative,
        "emotion": emotion,
        "field": field,
        "audience": audience,
        "positioning": positioning,
    }

    for p in dynamic_patterns:
        reqs = p.get("requires", [])
        if all(context.get(r) for r in reqs):
            try:
                text = p["template"].format(**context)
                candidates.append(
                    {
                        "angle": text,
                        "type": p["type"],
                        "platform": p["platform"],
                        "source": "动态生成",
                    }
                )
            except KeyError:
                continue

    # 3. 按主要匹配类型追加角度
    match_patterns = {
        "功能场景": "《{keyword}发生时，为什么{vehicle}的{scene0}刚刚好？》",
        "价值观/叙事": "《{keyword}的{narrative}，和{vehicle}的{image0}是一种人》",
        "人群兴趣": "《关注{keyword}的人，正好看{vehicle}》",
        "竞品/品类": "《{keyword}之后，再看{vehicle}的{image0}》",
        "文化时刻": "《全民都在看{keyword}，{vehicle}自然出现》",
    }
    for mt in match_types:
        if mt in match_patterns:
            template = match_patterns[mt]
            try:
                text = template.format(**context)
                candidates.append(
                    {
                        "angle": text,
                        "type": "短视频 / 图文",
                        "platform": "全平台",
                        "source": f"匹配类型：{mt}",
                    }
                )
            except KeyError:
                continue

    # 4. 去重并排序：优先保留来源多样的角度
    seen = set()
    unique = []
    sources_seen = set()
    for c in candidates:
        if c["angle"] in seen:
            continue
        seen.add(c["angle"])
        # 简单打散：相同 source 优先保留一个，保证多样性
        c_key = (c["source"], c["type"])
        if c_key not in sources_seen or len(unique) < top_n * 2:
            unique.append(c)
            sources_seen.add(c_key)

    return unique[:top_n]


# 判定为「短视频/视频」的内容形式
_VIDEO_TYPES = {"短视频", "创意视频", "短视频 / 图文"}
# 判定为「图文/长图文/讨论」的内容形式
_GRAPHIC_TYPES = {"图文", "长图文", "讨论", "小红书笔记"}


def _is_video_angle(angle: Dict) -> bool:
    return angle.get("type", "") in _VIDEO_TYPES


def _is_graphic_angle(angle: Dict) -> bool:
    return angle.get("type", "") in _GRAPHIC_TYPES


def generate_classified_angles(
    topic_text: str,
    vehicle_key: str,
    topic_labels: Dict[str, str],
    match_types: List[str],
    video_n: int = 7,
    graphic_n: int = 4,
) -> Dict[str, List[Dict]]:
    """
    生成并按「短视频 / 图文」分类的内容角度。
    保证至少返回 video_n 个视频角度和 graphic_n 个图文角度（含长图文、知乎讨论、小红书等）。
    """
    # 先产生足够多的候选
    all_angles = generate_content_angles(
        topic_text, vehicle_key, topic_labels, match_types, top_n=(video_n + graphic_n) * 3
    )

    video_angles = [a for a in all_angles if _is_video_angle(a)]
    graphic_angles = [a for a in all_angles if _is_graphic_angle(a)]

    # 如果某一类不够，从另一类或通用模板里补
    if len(video_angles) < video_n:
        # 用通用动态模板补视频
        v = VEHICLES[vehicle_key]
        keyword = _topic_keyword(topic_text)
        image0 = v["image"][0] if v["image"] else ""
        scene0 = v["scenes"][0] if v["scenes"] else ""
        backup_video = [
            f"《当{keyword}刷屏，{vehicle_key}用{image0}回应》",
            f"《{keyword}背后，{vehicle_key}想说的是{image0}》",
            f"《{vehicle_key}车主的一天：{keyword}之后，回到{scene0}》",
            f"《把{keyword}拍成一支{vehicle_key}广告，会是什么样？》",
            f"《如果{keyword}是一辆车，大概就是{vehicle_key}的样子》",
            f"《用{vehicle_key}的{image0}，重新理解{keyword}》",
            f"《{vehicle_key}不是蹭{keyword}，是它本来就这样》",
        ]
        for text in backup_video:
            if len(video_angles) >= video_n:
                break
            if not any(a["angle"] == text for a in video_angles):
                video_angles.append(
                    {"angle": text, "type": "短视频", "platform": "抖音 / 视频号", "source": "兜底补充"}
                )

    if len(graphic_angles) < graphic_n:
        v = VEHICLES[vehicle_key]
        keyword = _topic_keyword(topic_text)
        image0 = v["image"][0] if v["image"] else ""
        scene0 = v["scenes"][0] if v["scenes"] else ""
        audience = topic_labels.get("目标人群重合度", "目标用户")
        backup_graphic = [
            {
                "angle": f"《从{keyword}看{vehicle_key}：写给{audience}的深度解读》",
                "type": "长图文",
                "platform": "微信公众号",
            },
            {
                "angle": f"《{keyword}背后，{vehicle_key}如何用{image0}回应这个时代？》",
                "type": "长图文",
                "platform": "微信公众号 / 知乎",
            },
            {
                "angle": f"《知乎回答：如何评价{keyword}与{vehicle_key}的这次相遇？》",
                "type": "讨论",
                "platform": "知乎",
            },
            {
                "angle": f"《{keyword}刷屏，{vehicle_key}做对了什么？一篇微博图文 thread》",
                "type": "图文",
                "platform": "微博",
            },
            {
                "angle": f"《{vehicle_key} × {keyword}：一份给{audience}的购车参考》",
                "type": "长图文",
                "platform": "微信公众号 / 知乎",
            },
        ]
        for item in backup_graphic:
            if len(graphic_angles) >= graphic_n:
                break
            if not any(a["angle"] == item["angle"] for a in graphic_angles):
                graphic_angles.append({**item, "source": "兜底补充"})

    return {
        "video": video_angles[:video_n],
        "graphic": graphic_angles[:graphic_n],
    }
