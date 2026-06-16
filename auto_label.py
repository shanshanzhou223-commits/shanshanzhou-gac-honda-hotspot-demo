"""
热点自动打标签：基于关键词规则
（未来可接入 LLM/BGE 做语义自动标注）
"""
import re
from typing import Dict

from data import KEYWORD_TO_LABELS, TOPIC_DIMENSIONS


def auto_label_topic(topic_text: str) -> Dict[str, str]:
    """
    输入热点文本，自动输出 B库六维标签建议。
    规则基于关键词匹配，演示用；实际可替换为 LLM API。
    """
    topic_text = topic_text.strip()
    labels = {}

    for dimension, mapping in KEYWORD_TO_LABELS.items():
        matched = None
        best_score = 0
        for pattern, label in mapping.items():
            # pattern 用 | 分隔多个同义词
            keywords = pattern.split("|")
            score = sum(1 for kw in keywords if kw.lower() in topic_text.lower())
            if score > best_score:
                best_score = score
                matched = label
        labels[dimension] = matched

    # 热度生命周期：默认上升期，若文本含“刷屏”“爆”等词则爆发期
    labels["热度生命周期"] = "上升期"
    if any(k in topic_text for k in ["刷屏", "爆了", "热搜第一", "全网", "突然", "刚刚"]):
        labels["热度生命周期"] = "爆发期"

    # 品牌安全等级：默认安全，若含争议词则谨慎/风险
    labels["品牌安全等级"] = "安全"
    caution_words = ["争议", "骂战", "塌房", "负面", " scandal", "丑闻", "吐槽", "翻车"]
    risk_words = [
        "离婚", "出轨", "暴力", "政治", "灾害", "事故", "起诉", "被告", "赔偿",
        "食品安全", "曝光", "黑心", "处罚", "造假", "诈骗", "犯罪", "死亡", "伤亡",
    ]
    if any(k in topic_text for k in caution_words):
        labels["品牌安全等级"] = "谨慎"
    if any(k in topic_text for k in risk_words):
        labels["品牌安全等级"] = "风险"

    # 如果是风险/谨慎话题，情绪倾向设为争议（更合理）
    if labels["品牌安全等级"] in ["风险", "谨慎"] and labels.get("价值观/情绪") in ["好奇心", "治愈感", "热血", "共鸣"]:
        labels["价值观/情绪"] = "争议"
    if labels["品牌安全等级"] == "风险" and labels.get("叙事原型") in ["幽默解构"]:
        labels["叙事原型"] = "争议"

    # 填充默认值
    for dim in TOPIC_DIMENSIONS.keys():
        if dim not in labels or labels[dim] is None:
            if dim == "领域/主题域":
                labels[dim] = "社会"
            elif dim == "叙事原型":
                labels[dim] = "幽默解构"
            elif dim == "价值观/情绪":
                labels[dim] = "共鸣"
            elif dim == "目标人群重合度":
                labels[dim] = "Z世代"
            elif dim == "热度生命周期":
                labels[dim] = "上升期"
            elif dim == "品牌安全等级":
                labels[dim] = "安全"

    return labels
