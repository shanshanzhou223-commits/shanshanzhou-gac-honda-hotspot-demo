"""
车型与热点匹配算法
"""
import re
from typing import Dict, List, Tuple

from data import VEHICLES, NARRATIVE_VEHICLE_MAP, AUDIENCE_VEHICLE_MAP

# 品牌契合分权重
BRAND_FIT_WEIGHTS = {
    "direct_function": 0.30,
    "values_narrative": 0.25,
    "audience": 0.25,
    "competitor_category": 0.15,
    "cultural_moment": 0.05,
}

# 完整契合分权重
FULL_SCORE_WEIGHTS = {
    "heat": 0.25,
    "brand_fit": 0.35,
    "emotion": 0.20,
    "feasibility": 0.10,
    "safety": 0.10,
}

# 情绪共鸣分基础映射
EMOTION_BASE_SCORES = {
    "共鸣": 90,
    "焦虑感": 85,
    "热血": 85,
    "治愈感": 85,
    "自豪感": 85,
    "希望": 85,
    "安全感": 80,
    "好奇心": 70,
    "幽默": 75,
    "争议": 45,
}

# 传播可行性基础映射（按领域/主题域）
FEASIBILITY_FIELD_SCORES = {
    "汽车": 85,
    "社会": 82,
    "职场": 80,
    "家庭": 80,
    "情感": 78,
    "文化": 78,
    "娱乐": 75,
    "体育": 75,
    "消费": 72,
    "科技": 68,
    "AI": 60,
    "航天": 58,
    "财经": 55,
    "国际": 50,
}

# 品牌安全基础映射
SAFETY_BASE_SCORES = {"安全": 90, "谨慎": 65, "风险": 25}


def _contains_any(text: str, keywords: List[str]) -> bool:
    """检查文本中是否包含任一关键词（简单分词）"""
    text = text.lower()
    for kw in keywords:
        if kw.lower() in text:
            return True
    return False


def _scene_overlap(topic_text: str, vehicle_scenes: List[str]) -> float:
    """话题文本与车型场景的简单重合度"""
    if not topic_text or not vehicle_scenes:
        return 0.0
    text = topic_text.lower()
    hits = sum(1 for scene in vehicle_scenes if scene.lower() in text)
    return min(hits / max(len(vehicle_scenes) * 0.5, 1), 1.0)


def compute_brand_fit(
    topic: Dict,
    vehicle_key: str,
) -> Tuple[float, Dict[str, float], List[str]]:
    """
    计算品牌契合分，返回：分数、各项子分、匹配类型列表
    """
    v = VEHICLES[vehicle_key]
    topic_text = topic.get("topic", "")
    topic_field = topic.get("领域/主题域", "")
    topic_narrative = topic.get("叙事原型", "")
    topic_emotion = topic.get("价值观/情绪", "")
    topic_audience = topic.get("目标人群重合度", "")
    lifecycle = topic.get("热度生命周期", "")

    # 1. 直接功能匹配分
    scene_score = _scene_overlap(topic_text, v["scenes"])
    # 汽车领域额外加分
    if topic_field == "汽车":
        scene_score = max(scene_score, 0.7)
    if topic_field in ["家庭"] and ("亲子出行" in v["scenes"] or "家庭" in v["positioning"]):
        scene_score = max(scene_score, 0.8)
    direct_function = 30 + scene_score * 70  # 30-100

    # 2. 价值观/叙事匹配分（使用 NARRATIVE_VEHICLE_MAP，按优先顺序给分）
    narrative_score = 0.0
    if topic_narrative and topic_narrative in NARRATIVE_VEHICLE_MAP:
        matched_models = NARRATIVE_VEHICLE_MAP[topic_narrative]
        if vehicle_key in matched_models:
            idx = matched_models.index(vehicle_key)
            narrative_score = [0.95, 0.70, 0.50][min(idx, 2)]
    # 兜底：检查话题叙事是否出现在车型形象关键词中
    if narrative_score == 0.0 and topic_narrative:
        narrative_keywords = topic_narrative.lower().split("/")
        hits = sum(1 for k in narrative_keywords if any(k in img.lower() for img in v["image"]))
        if hits >= 1:
            narrative_score = 0.6
    # 特殊强化：P7 对探索/创新/挑战
    if vehicle_key == "P7" and topic_narrative in ["探索突破", "创新颠覆", "挑战极限"]:
        narrative_score = max(narrative_score, 0.95)
    # 雅阁 对 成长蜕变/责任守护
    if vehicle_key == "雅阁" and topic_narrative in ["成长蜕变", "责任守护", "成熟自洽"]:
        narrative_score = max(narrative_score, 0.80)
    # 奥德赛 对 责任守护/团聚归属
    if vehicle_key == "奥德赛" and topic_narrative in ["责任守护", "团聚归属"]:
        narrative_score = max(narrative_score, 0.95)
    values_narrative = 30 + narrative_score * 70

    # 3. 人群兴趣匹配分（使用 AUDIENCE_VEHICLE_MAP，按优先顺序给分）
    audience_score = 0.0
    if topic_audience and topic_audience in AUDIENCE_VEHICLE_MAP:
        matched_models = AUDIENCE_VEHICLE_MAP[topic_audience]
        if vehicle_key in matched_models:
            idx = matched_models.index(vehicle_key)
            audience_score = [0.90, 0.60, 0.40][min(idx, 2)]
    # 兜底：车型目标人群文本与话题人群文本重合
    audience_text = topic_audience.lower() if topic_audience else ""
    for aud in v["audience"]:
        if any(part in audience_text for part in aud.lower().split("、")):
            audience_score = max(audience_score, 0.5)
    # 通过关键词再判断
    topic_lower = topic_text.lower()
    age_map = {
        "20-35岁": ["飞度", "型格", "缤智"],
        "25-35岁": ["型格", "缤智", "飞度"],
        "25-40岁": ["P7", "皓影", "缤智"],
        "28-40岁": ["皓影", "雅阁"],
        "30-45岁": ["雅阁", "奥德赛"],
        "35-50岁": ["冠道", "雅阁"],
    }
    for aud in v["audience"]:
        for age_key, models in age_map.items():
            if age_key in aud and vehicle_key in models:
                if any(k in topic_lower for k in ["年轻人", "青年", "中年", "家庭", "职场", "科技"]):
                    audience_score = max(audience_score, 0.5)
    # 车型人设关键词匹配
    persona_keywords = {
        "P7": ["科技", "AI", "智能", "未来", "电动", "新能源", "火箭", "太空", "马斯克"],
        "雅阁": ["职场", "商务", "成熟", "稳定", "中年", "家庭"],
        "型格": ["运动", "改装", "热血", "年轻", "赛车", "潮流"],
        "奥德赛": ["家庭", "孩子", "亲子", "奶爸", "宝妈", "返乡", "团圆"],
        "皓影": ["露营", "周末", "城市", "家用", "小家庭"],
        "冠道": ["豪华", "商务", "大空间", "家庭", "长途"],
        "飞度": ["年轻人", "第一台车", "改装", "经济", "省油", "灵活"],
        "缤智": ["年轻", "时尚", "城市", "通勤", "小家庭"],
    }
    hits = sum(1 for k in persona_keywords.get(vehicle_key, []) if k in topic_lower)
    if hits >= 2:
        audience_score = max(audience_score, 0.9)
    elif hits == 1:
        audience_score = max(audience_score, 0.5)
    audience = 30 + min(audience_score, 1.0) * 70

    # 4. 竞品/品类关联分
    competitor_score = 0.0
    if topic_field == "汽车":
        competitor_score = 0.9
    if vehicle_key == "P7":
        # 电动车、科技、马斯克相关
        if any(k in topic_lower for k in ["特斯拉", "新能源", "电动车", "电动", "马斯克", "续航", "充电", "电池", "智能座舱", "辅助驾驶"]):
            competitor_score = max(competitor_score, 0.9)
        if topic_field in ["AI", "科技"]:
            competitor_score = max(competitor_score, 0.8)
    if vehicle_key in ["雅阁", "冠道"] and topic_field == "汽车":
        competitor_score = max(competitor_score, 0.6)
    competitor_category = 30 + competitor_score * 70

    # 5. 文化时刻适配分
    cultural_score = 0.0
    if lifecycle == "爆发期":
        cultural_score = 1.0
    elif lifecycle == "上升期":
        cultural_score = 0.8
    elif lifecycle == "长尾期":
        cultural_score = 0.5
    elif lifecycle == "萌芽期":
        cultural_score = 0.6
    cultural_moment = 30 + cultural_score * 70

    # 汇总
    brand_fit = (
        direct_function * BRAND_FIT_WEIGHTS["direct_function"]
        + values_narrative * BRAND_FIT_WEIGHTS["values_narrative"]
        + audience * BRAND_FIT_WEIGHTS["audience"]
        + competitor_category * BRAND_FIT_WEIGHTS["competitor_category"]
        + cultural_moment * BRAND_FIT_WEIGHTS["cultural_moment"]
    )

    sub_scores = {
        "直接功能匹配": direct_function,
        "价值观/叙事匹配": values_narrative,
        "人群兴趣匹配": audience,
        "竞品/品类关联": competitor_category,
        "文化时刻适配": cultural_moment,
    }

    match_types = []
    if direct_function >= 60:
        match_types.append("功能场景")
    if values_narrative >= 70:
        match_types.append("价值观/叙事")
    if audience >= 70:
        match_types.append("人群兴趣")
    if competitor_category >= 60:
        match_types.append("竞品/品类")
    if cultural_moment >= 80:
        match_types.append("文化时刻")
    if not match_types:
        match_types.append("弱关联")

    return round(brand_fit, 2), sub_scores, match_types


def compute_full_score(
    topic: Dict,
    vehicle_key: str,
    brand_fit_override: float = None,
    auto_external: bool = False,
) -> Dict:
    """
    计算完整车型-话题契合分

    Args:
        brand_fit_override: 若提供，将覆盖自动计算的品牌契合分（用于 demo 手动调节）
        auto_external: 若为 True，情绪共鸣分、传播可行性分、安全分将由 AI 根据话题标签自动计算
    """
    brand_fit, sub_scores, match_types = compute_brand_fit(topic, vehicle_key)
    if brand_fit_override is not None:
        brand_fit = round(brand_fit_override, 2)

    heat = topic.get("heat", 50)

    if auto_external:
        emotion = compute_emotion_score(topic, vehicle_key)
        feasibility = compute_feasibility_score(topic, vehicle_key)
        safety = compute_safety_score(topic)
    else:
        emotion = topic.get("emotion_score", 70)
        feasibility = topic.get("feasibility_score", 70)
        safety_text = topic.get("品牌安全等级", "安全")
        # 如果用户手动指定了安全分，优先使用；否则按标签映射
        if "safety_override" in topic:
            safety = topic["safety_override"]
        else:
            safety_map = {"安全": 95, "谨慎": 70, "风险": 30}
            safety = safety_map.get(safety_text, 70)

    full = (
        heat * FULL_SCORE_WEIGHTS["heat"]
        + brand_fit * FULL_SCORE_WEIGHTS["brand_fit"]
        + emotion * FULL_SCORE_WEIGHTS["emotion"]
        + feasibility * FULL_SCORE_WEIGHTS["feasibility"]
        + safety * FULL_SCORE_WEIGHTS["safety"]
    )

    tier = determine_tier(full)

    return {
        "vehicle": vehicle_key,
        "brand_fit": brand_fit,
        "full_score": round(full, 2),
        "tier": tier,
        "sub_scores": sub_scores,
        "match_types": match_types,
        "heat": heat,
        "emotion": emotion,
        "feasibility": feasibility,
        "safety": safety,
    }


def determine_tier(score: float) -> str:
    if score >= 85:
        return "S级"
    elif score >= 70:
        return "A级"
    elif score >= 55:
        return "B级"
    else:
        return "C级"


def compute_emotion_score(topic: Dict, vehicle_key: str = None) -> float:
    """
    根据话题情绪标签、生命周期与车型特征，自动计算情绪共鸣分。
    """
    emotion_label = topic.get("价值观/情绪", "共鸣")
    lifecycle = topic.get("热度生命周期", "上升期")
    topic_text = topic.get("topic", "").lower()

    score = EMOTION_BASE_SCORES.get(emotion_label, 70)

    # 生命周期调整：热点越在爆发期，情绪共鸣越强
    lifecycle_adj = {
        "萌芽期": 0,
        "上升期": 3,
        "爆发期": 5,
        "长尾期": -3,
        "回落期": -8,
    }
    score += lifecycle_adj.get(lifecycle, 0)

    # 若传入车型，结合车型形象关键词做微调
    if vehicle_key and vehicle_key in VEHICLES:
        v = VEHICLES[vehicle_key]
        positive_signals = 0
        if emotion_label in ["热血", "挑战极限"]:
            if any(k in topic_text for k in ["运动", "冠军", "赛道", "极限", "挑战"]):
                positive_signals += 1
        if emotion_label in ["安全感", "治愈感"]:
            if any(k in topic_text for k in ["家庭", "孩子", "守护", "安全", "舒适", "团圆"]):
                positive_signals += 1
        if emotion_label in ["科技感", "好奇心"]:
            if any(k in topic_text for k in ["科技", "ai", "智能", "未来", "火箭", "太空"]):
                positive_signals += 1
        if positive_signals:
            score += 5

    return round(max(0, min(100, score)), 2)


def compute_feasibility_score(topic: Dict, vehicle_key: str = None) -> float:
    """
    根据话题领域、叙事原型、品牌安全等级与生命周期，自动计算传播可行性分。
    """
    field = topic.get("领域/主题域", "社会")
    narrative = topic.get("叙事原型", "幽默解构")
    safety = topic.get("品牌安全等级", "安全")
    lifecycle = topic.get("热度生命周期", "上升期")

    score = FEASIBILITY_FIELD_SCORES.get(field, 70)

    narrative_adj = {
        "幽默解构": 10,
        "自由逃离": 8,
        "团聚归属": 8,
        "责任守护": 5,
        "成长蜕变": 3,
        "怀旧回归": 3,
        "探索突破": -2,
        "创新颠覆": -2,
        "挑战极限": -3,
        "抗争反叛": -8,
        "争议": -15,
    }
    score += narrative_adj.get(narrative, 0)

    safety_adj = {"安全": 5, "谨慎": -5, "风险": -20}
    score += safety_adj.get(safety, 0)

    lifecycle_adj = {
        "萌芽期": -2,
        "上升期": 3,
        "爆发期": 5,
        "长尾期": 0,
        "回落期": -5,
    }
    score += lifecycle_adj.get(lifecycle, 0)

    # 若话题文本与车型使用场景直接相关，植入更自然
    if vehicle_key and vehicle_key in VEHICLES:
        topic_text = topic.get("topic", "").lower()
        scenes = VEHICLES[vehicle_key].get("scenes", [])
        hits = sum(1 for s in scenes if s.lower() in topic_text)
        if hits >= 1:
            score += 5

    return round(max(0, min(100, score)), 2)


def compute_safety_score(topic: Dict) -> float:
    """
    根据品牌安全等级、领域、情绪与叙事原型，自动计算品牌安全分。
    """
    safety_label = topic.get("品牌安全等级", "安全")
    field = topic.get("领域/主题域", "社会")
    emotion = topic.get("价值观/情绪", "共鸣")
    narrative = topic.get("叙事原型", "幽默解构")

    score = SAFETY_BASE_SCORES.get(safety_label, 70)

    field_adj = {
        "娱乐": -10,
        "国际": -10,
        "社会": -8,
        "情感": -8,
        "财经": -5,
        "职场": -5,
        "汽车": 5,
        "航天": 5,
        "科技": 3,
        "体育": 3,
        "文化": 3,
    }
    score += field_adj.get(field, 0)

    emotion_adj = {
        "争议": -15,
        "焦虑感": -5,
        "热血": -2,
        "安全感": 5,
        "治愈感": 3,
        "希望": 3,
    }
    score += emotion_adj.get(emotion, 0)

    narrative_adj = {
        "争议": -10,
        "抗争反叛": -8,
        "挑战极限": -3,
        "责任守护": 5,
        "团聚归属": 3,
    }
    score += narrative_adj.get(narrative, 0)

    return round(max(0, min(100, score)), 2)


def rank_all_topics(
    vehicle_key: str,
    topics: List[Dict],
    brand_fit_override: float = None,
    auto_external: bool = False,
) -> List[Dict]:
    """
    对单个车型，计算其与多个热点的匹配得分并排序（反向匹配：车型 → 热点）。
    """
    results = []
    for topic in topics:
        result = compute_full_score(topic, vehicle_key, brand_fit_override, auto_external)
        result["topic"] = topic.get("topic", "")
        result["platform"] = topic.get("platform", "")
        result["heat"] = topic.get("heat", 50)
        results.append(result)
    results.sort(key=lambda x: x["full_score"], reverse=True)
    return results
