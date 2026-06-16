"""
根据车型和热点生成内容角度建议（增强版）
"""
from typing import Dict, List

from data import ANGLE_TEMPLATES, VEHICLES


def _topic_keyword(topic_text: str, max_len: int = 10) -> str:
    """提取话题关键词，避免太长"""
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
            "template": "《别人在聊{keyword}，{vehicle}守住{image0}》",
            "type": "图文",
            "platform": "微博 / 知乎",
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
            "template": "《用{vehicle}的{image0}，重新理解{keyword}》",
            "type": "短视频",
            "platform": "抖音 / 视频号",
        },
        {
            "template": "《{keyword}之后，{vehicle}给{audience}的一个选择》",
            "type": "图文",
            "platform": "小红书 / 微博",
            "requires": ["audience"],
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
            "template": "《{vehicle}车主视角：{keyword}下的{scene0}》",
            "type": "小红书笔记",
            "platform": "小红书",
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
