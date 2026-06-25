"""
热点内容演绎 playbook：根据热点 B库标签生成可直接落地的内容方案
"""
import hashlib
import re
import unicodedata
from itertools import combinations
from typing import Dict, List

import jieba

from angles import generate_content_angles
from data import VEHICLES, NARRATIVE_VEHICLE_MAP, AUDIENCE_VEHICLE_MAP


# ---------- 内容去重 / 重复度控制 ----------
# 常见停用词 + 无意义虚词，计算重复度时剔除
_STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也",
    "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "之",
    "与", "以", "及", "等", "中", "为", "从", "将", "向", "把", "被", "让", "给", "使", "对", "关于",
    "由", "于", "而", "但", "因为", "所以", "如果", "虽然", "然而", "因此", "或者", "还是", "以及",
    "随着", "通过", "进行", "作为", "可以", "已经", "正在", "开始", "出现", "成为", "表示", "认为",
    "需要", "能够", "可能", "应该", "方面", "问题", "时候", "情况", "部分", "一些", "一种", "一下",
    "一次", "一样", "一直", "一切", "一般", "所有", "每个", "各位", "大家", "人们", "我们", "你们",
    "他们", "它们", "它", "他", "她", "个", "来", "过", "下", "大", "小", "多", "少", "里", "外",
    "前", "后", "左", "右", "内", "间", "边", "头", "面", "部", "身", "心", "手", "眼", "口", "声",
    "地", "得", "着", "过", "呢", "吧", "啊", "哦", "嗯", "哈", "吗", "嘛", "呗", "哟", "哇", "唉",
}

# 同义/近义替换词库，用于降低画面描述的结构重复
_VARIATION_POOLS = {
    "全景": ["全景", "大全景", "远景", "航拍", "广角", "俯瞰"],
    "中景": ["中景", "近景", "半身景", "过肩镜头", "胸像"],
    "特写": ["特写", "近景特写", "细节特写", "微距", "大特写"],
    "跟拍": ["跟拍", "尾随拍摄", "动态追踪", "侧面跟拍", "运动跟随"],
    "快切": ["快切", "快剪", "快速切换", "快速组接", "跳切"],
    "叠化": ["叠化", "渐变过渡", "溶接", "画面叠化"],
    "驶过": ["驶过", "穿行", "掠过", "划过", "疾驰而过", "穿越"],
    "停在": ["停在", "静置于", "停靠在", "泊于", "伫立"],
    "画面": ["画面", "镜头", "影像", "场景", "构图"],
    "车身": ["车身", "车体", "整车轮廓", "车侧", "车体线条"],
    "车灯": ["车灯", "大灯", "贯穿灯", "尾灯", "灯组"],
    "内饰": ["内饰", "座舱", "车内", "驾驶舱", "车厢"],
    "启动": ["启动", "点火", "唤醒", "通电", "车辆启动"],
    "展现": ["展现", "呈现", "露出", "凸显", "体现"],
    "出现": ["出现", "浮现", "显现", "映入眼帘", "进入画面"],
    "背景": ["背景", "后景", "环境", "远景层", "空间氛围"],
    "快速": ["快速", "迅速", "飞快", "急速", "紧凑"],
    "缓缓": ["缓缓", "慢慢", "渐进", "徐徐"],
    "镜头": ["镜头", "机位", "视角", "视点", "取景"],
    "车主": ["车主", "驾驶者", "司机", "用户"],
    "人物": ["人物", "人物侧影", "人物背影", "人物近景"],
    "街道": ["街道", "城市道路", "街区", "路面"],
    "清晰": ["清晰", "分明", "锐利", "清楚"],
    "大字": ["大字", "大标题", "醒目文字", "主题字"],
    "热搜": ["热搜", "热榜", "热门话题", "榜单"],
    "表情": ["表情", "神情", "神态", "面部"],
    # 运动/热血主题常用词
    "运动": ["运动", "动感", "竞速", "驾驭", "操控"],
    "热血": ["热血", "激昂", "燃", "澎湃", "振奋"],
    "赛道": ["赛道", "跑道", "竞速场", "弯道", "山路"],
    "冠军": ["冠军", "胜者", "金牌", "冠军时刻", "赢家"],
    "速度": ["速度", "速率", "疾速", "飞驰", "迅猛"],
    "驾驶": ["驾驶", "驾驭", "操控", "开", "驱车"],
    "车辆": ["车辆", "座驾", "车", "它", "这台"],
    "擦汗": ["擦汗", "调整呼吸", "握拳", "目光如炬"],
    "坚定": ["坚定", "专注", "执着", "自信"],
    # 台词/字幕常用词
    "装下": ["装下", "承载", "容纳", "收下", "托起"],
    "接住": ["接住", "回应", "承接", "接住", "迎住"],
    "热血到底": ["热血到底", "燃到底", "一路热血", "热血不息"],
    "赛道基因": ["赛道基因", "运动血统", "竞速基因", "性能基因"],
    "一直都在": ["一直都在", "从未离开", "始终在线", "从未改变"],
    "不需要解释": ["不需要解释", "无需多言", "自有答案", "不言而喻"],
    "触手可及": ["触手可及", "近在眼前", "一步之遥", "垂手可得"],
}


def _tokenize(text: str) -> List[str]:
    """中文分词，返回有效词元列表。"""
    tokens = []
    for tok in jieba.cut(text):
        tok = tok.strip()
        if not tok:
            continue
        # 去掉纯标点、纯数字、纯空格的 token
        if all(
            unicodedata.category(ch).startswith("P")
            or ch.isdigit()
            or ch.isspace()
            for ch in tok
        ):
            continue
        if len(tok) == 1 and tok in _STOP_WORDS:
            continue
        tokens.append(tok)
    return tokens


def _content_tokens(text: str) -> List[str]:
    """提取用于重复度计算的内容词（去掉停用词）。"""
    tokens = _tokenize(text)
    return [t for t in tokens if t not in _STOP_WORDS]


def _strip_terms(text: str, terms: List[str]) -> str:
    """从文本中移除指定术语（用于重复度计算时排除品牌名/话题词）。"""
    if not text:
        return text
    result = text
    for term in sorted(set(terms or []), key=len, reverse=True):
        if term:
            result = result.replace(term, "")
    return result


def _containment_similarity(a: str, b: str, excluded_terms: List[str] = None) -> float:
    """
    基于内容词的包含相似度：
    similarity = |A∩B| / min(|A|,|B|)
    当 A 几乎被 B 包含时，相似度接近 1。
    excluded_terms 中的词会在分词前被剔除，避免品牌名/话题词拉高相似度。
    """
    if excluded_terms:
        a = _strip_terms(a, excluded_terms)
        b = _strip_terms(b, excluded_terms)
    tokens_a = set(_content_tokens(a))
    tokens_b = set(_content_tokens(b))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / min(len(tokens_a), len(tokens_b))


def _repetition_rate(
    texts: List[str],
    threshold: float = 0.5,
    exclude_texts: List[str] = None,
    excluded_terms: List[str] = None,
) -> float:
    """
    计算文本列表的重复度：
    重复度 = 高相似文本对数 / 总文本对数
    其中高相似定义为 containment_similarity >= threshold。
    exclude_texts 中的整句会被剔除；excluded_terms 中的词会在计算相似度时忽略。
    """
    exclude_set = set(exclude_texts or [])
    texts = [t for t in texts if t and str(t).strip() and str(t).strip() not in exclude_set]
    n = len(texts)
    if n < 2:
        return 0.0
    pairs = list(combinations(range(n), 2))
    high_sim_count = 0
    for i, j in pairs:
        if _containment_similarity(texts[i], texts[j], excluded_terms=excluded_terms) >= threshold:
            high_sim_count += 1
    return high_sim_count / len(pairs)


def _rewrite_once(text: str, seed: int = 0) -> str:
    """对单条文本做一次同义替换，seed 用于控制替换选择。"""
    new_text = text
    # 按固定顺序遍历替换词库，哈希选择候选，保证稳定
    keys = sorted(_VARIATION_POOLS.keys())
    for key in keys:
        if key not in new_text:
            continue
        pool = _VARIATION_POOLS[key]
        idx = (int(hashlib.md5(f"{new_text}|{key}|{seed}".encode()).hexdigest(), 16)) % len(pool)
        candidate = pool[idx]
        if candidate != key:
            new_text = new_text.replace(key, candidate, 1)
            return new_text
    return new_text


def _mask_terms(texts: List[str], terms: List[str]) -> tuple:
    """把 texts 中出现的 terms 替换成占位符，返回 (masked_texts, placeholders_map)。"""
    terms = sorted(set(t for t in terms if t), key=len, reverse=True)
    if not terms:
        return texts, {}

    placeholders = {}
    masked = []
    for idx, text in enumerate(texts):
        new_text = text
        for t in terms:
            if t in new_text:
                placeholder = f"__PH_{len(placeholders)}__"
                placeholders[placeholder] = t
                new_text = new_text.replace(t, placeholder)
        masked.append(new_text)
    return masked, placeholders


def _unmask_terms(texts: List[str], placeholders: dict) -> List[str]:
    """把占位符恢复成原始术语。"""
    if not placeholders:
        return texts
    restored = []
    for text in texts:
        new_text = text
        # 按占位符编号从大到小，避免短占位符覆盖长的
        for ph in sorted(
            placeholders.keys(),
            key=lambda x: int(x.replace("__PH_", "").replace("__", "")),
            reverse=True,
        ):
            new_text = new_text.replace(ph, placeholders[ph])
        restored.append(new_text)
    return restored


def _diversify_texts(
    texts: List[str],
    max_rate: float = 0.1,
    max_iter: int = 20,
    exclude_texts: List[str] = None,
    threshold: float = 0.5,
    excluded_terms: List[str] = None,
    ensure_no_identical: bool = False,
) -> List[str]:
    """
    对文本列表做迭代改写，直到重复度低于 max_rate。
    保持列表长度和顺序不变。
    exclude_texts 中的文本会被从重复度计算中剔除（如意外的 slogan/角度原文重复）。
    excluded_terms 中的词会在计算相似度时忽略，并在改写时被保护（如品牌名、话题词）。
    threshold 定义“高相似”的 containment_similarity 阈值。
    ensure_no_identical=True 时，即使整体重复度已达标，仍会继续消除完全相同的文本对。
    """
    texts = list(texts)
    exclude_set = set(exclude_texts or [])
    terms = [t for t in (excluded_terms or []) if t]

    def _filtered(items):
        return [t for t in items if t and str(t).strip() and str(t).strip() not in exclude_set]

    def _has_identical_pair(indices):
        if not ensure_no_identical:
            return False
        for i, j in combinations(indices, 2):
            if _containment_similarity(texts[i], texts[j], excluded_terms=terms) >= 0.99:
                return True
        return False

    for _ in range(max_iter):
        filtered = _filtered(texts)
        rate = _repetition_rate(filtered, threshold=threshold, excluded_terms=terms)
        valid_indices = [i for i, t in enumerate(texts) if str(t).strip() not in exclude_set]

        if rate <= max_rate and not _has_identical_pair(valid_indices):
            break

        # 只在非排除文本中找最相似的一对
        worst_pair = None
        worst_sim = -1.0
        for i, j in combinations(valid_indices, 2):
            sim = _containment_similarity(texts[i], texts[j], excluded_terms=terms)
            if sim > worst_sim:
                worst_sim = sim
                worst_pair = (i, j)

        if worst_pair is None or worst_sim < threshold:
            # ensure_no_identical 模式下，若只剩完全相同对但 threshold 不够低，仍继续处理
            if not (ensure_no_identical and worst_sim >= 0.99):
                break

        # 如果两个文本几乎完全相同，同时对两者做不同改写，避免只改一个导致高相似对数量不变
        if worst_sim >= 0.99:
            indices_to_rewrite = [worst_pair[0], worst_pair[1]]
        else:
            indices_to_rewrite = [worst_pair[1]]

        for idx in indices_to_rewrite:
            original = texts[idx]

            # 改写前先把受保护术语 mask 掉，避免被同义替换破坏
            masked_original, placeholders = _mask_terms([original], terms)
            masked_original = masked_original[0]

            rewritten = masked_original
            changed = False
            for seed in range(20):
                rewritten = _rewrite_once(masked_original, seed=seed + idx)
                if rewritten != masked_original:
                    changed = True
                    break
            if not changed:
                # 已无法通过同义替换降低重复，终止
                break

            # 恢复受保护术语
            rewritten = _unmask_terms([rewritten], placeholders)[0]
            texts[idx] = rewritten
        else:
            # 正常完成本轮改写，继续下一轮
            continue
        # 因无法继续改写而 break 时会走到这里
        break

    return texts


def _global_diversify_visuals(
    visuals: List[str],
    excluded_terms: List[str] = None,
    threshold: float = 0.30,
    max_rate: float = 0.03,
    max_iter: int = 40,
) -> List[str]:
    """
    跨角度画面描述重复度控制规则。

    目标：任意热点 × 任意车型生成的多个视频角度，其所有 shots 的画面描述
    之间的重复度必须低于 max_rate，且不允许出现完全相同的画面描述。

    策略：
    1. 先由 _theme_pack 根据内容角度主题做「根上差异化」
       （如 sport 主题下再分 champion/challenge/modify/youth/track）；
    2. 再在 generate_topic_playbook 层面对全部 angles / durations / shots 的画面描述
       做全局兜底改写：每轮找出最相似的一对，对两个文本同时做多次同义替换，
       让它们从核心词到运镜都产生差异；
    3. 迭代直到整体重复度达标或无法继续改写。

    该规则对所有热点、所有车型通用生效，不依赖具体案例。
    """
    texts = list(visuals)
    terms = [t for t in (excluded_terms or []) if t]
    rewrite_counts = [0] * len(texts)  # 记录每个文本被改写次数，防止单条被过度改写

    def _current_rate() -> float:
        return _repetition_rate(texts, threshold=threshold, excluded_terms=terms)

    for _ in range(max_iter):
        rate = _current_rate()
        if rate <= max_rate:
            break

        # 找出当前最相似的一对
        worst_pair = None
        worst_sim = -1.0
        for i, j in combinations(range(len(texts)), 2):
            sim = _containment_similarity(texts[i], texts[j], excluded_terms=terms)
            if sim > worst_sim:
                worst_sim = sim
                worst_pair = (i, j)

        if worst_pair is None or worst_sim < threshold:
            break

        # 对最相似的两个文本做改写；若某个文本已改写多次，优先改写另一个
        any_changed = False
        for idx in worst_pair:
            if rewrite_counts[idx] >= 3:
                continue

            original = texts[idx]
            masked_original, placeholders = _mask_terms([original], terms)
            masked_original = masked_original[0]

            rewritten = masked_original
            changed = False
            # 单次同义替换，避免多次累积造成语法错误
            for seed_base in range(10):
                candidate = _rewrite_once(masked_original, seed=seed_base + idx)
                if candidate != masked_original:
                    rewritten = candidate
                    changed = True
                    break

            if not changed:
                continue

            rewritten = _unmask_terms([rewritten], placeholders)[0]
            texts[idx] = rewritten
            rewrite_counts[idx] += 1
            any_changed = True

        if not any_changed:
            break

    return texts


def _best_vehicle_for_topic(topic: Dict) -> str:
    """根据话题标签，快速找到最匹配的车型（用于内容演绎主角）"""
    narrative = topic.get("叙事原型", "")
    audience = topic.get("目标人群重合度", "")
    field = topic.get("领域/主题域", "")

    candidates = {}
    if narrative in NARRATIVE_VEHICLE_MAP:
        for i, v in enumerate(NARRATIVE_VEHICLE_MAP[narrative]):
            candidates[v] = candidates.get(v, 0) + (3 - i)
    if audience in AUDIENCE_VEHICLE_MAP:
        for i, v in enumerate(AUDIENCE_VEHICLE_MAP[audience]):
            candidates[v] = candidates.get(v, 0) + (3 - i)
    if field == "汽车":
        candidates["P7"] = candidates.get("P7", 0) + 2
        candidates["雅阁"] = candidates.get("雅阁", 0) + 1
    if field in ["家庭"]:
        candidates["奥德赛"] = candidates.get("奥德赛", 0) + 2
        candidates["冠道"] = candidates.get("冠道", 0) + 1
    if field in ["社会", "职场"]:
        candidates["雅阁"] = candidates.get("雅阁", 0) + 2
    if field in ["体育"]:
        candidates["型格"] = candidates.get("型格", 0) + 2
    if not candidates:
        return "雅阁"
    return max(candidates.items(), key=lambda x: x[1])[0]


def _topic_keyword(topic_text: str, max_len: int = 30) -> str:
    """提取话题关键词，默认保留完整文本避免截断"""
    t = topic_text.strip()
    if len(t) > max_len:
        return t[:max_len] + "…"
    return t


def _detect_angle_themes(angle_text: str) -> List[str]:
    """根据内容角度文本，识别画面/音效应侧重的主题标签。"""
    text = angle_text.lower()
    themes = []
    # 生活/车主故事优先于智能/科技，避免「车主的一天」被误判为 AI
    if any(k in text for k in ["车主", "一天", "生活", "故事", "日常", "回家", "通勤"]):
        themes.append("life")
    if any(k in text for k in ["星空", "太空", "火箭", "星舰", "飞船", "宇宙", "星辰", "仰望", "发射"]):
        themes.append("space")
    if any(k in text for k in ["ai", "人工智能", "懂你", "语音", "交互", "数字", "算法"]):
        themes.append("ai")
    # 单独「智能/座舱」若未命中生活，则归 AI；已命中生活则不加，避免冲突
    elif any(k in text for k in ["智能", "座舱"]):
        themes.append("ai")
    if any(k in text for k in ["未来", "科技", "进化", "答案", "突破", "创新", "颠覆"]):
        themes.append("future")
    if any(k in text for k in ["运动", "冠军", "热血", "赛道", "速度", "激情", "驾驶乐趣"]):
        themes.append("sport")
    if any(k in text for k in ["家庭", "孩子", "守护", "责任", "亲情", "爸爸", "妈妈", "家人"]):
        themes.append("family")
    if not themes:
        themes.append("default")
    return themes


def _angle_flavor(angle_text: str, themes: set) -> set:
    """
    从内容角度文本中提取更细粒度的叙事 flavor，
    让同一主题大类下的不同角度也能生成差异化的画面。
    """
    text = angle_text.lower()
    flavor = set()

    # 运动主题下的细分叙事
    if "sport" in themes or any(k in text for k in ["运动", "冠军", "赛道", "热血", "速度", "驾驶乐趣"]):
        if any(k in text for k in ["冠军", "胜者", "金牌", "领奖台", "追冠军", "冠军时刻", "赢家"]):
            flavor.add("champion")
        if any(k in text for k in ["极限", "挑战", "刷新", "突破", "不服输", "再试一次", "纪录"]):
            flavor.add("challenge")
        if any(k in text for k in ["改装", "玩车", "姿态", "低趴", "个性", "调校", "爆改"]):
            flavor.add("modify")
        if any(k in text for k in ["青年", "年轻人", "年轻", "热血青年", "态度", "青春", "新生代"]):
            flavor.add("youth")
        if any(k in text for k in ["赛道", "弯道", "操控", "驾驶乐趣", "过弯", "性能", "竞速"]):
            flavor.add("track")
        # 兜底：确保至少有一个 flavor
        if not flavor:
            flavor.add("track")

    return flavor


def _sport_visuals(angle_text: str, flavor: set, keyword: str, vehicle: str, scene0: str, image0: str) -> Dict[str, str]:
    """
    根据运动主题的细分 flavor 与角度原文中的主导关键词，
    生成完整、差异化的视频画面描述（含景别/运镜），覆盖 15s / 20s / 30s 三版结构。
    当 angle 同时命中多个 flavor 时，按关键词信号强度选择最贴合的主导 flavor。
    """
    text = angle_text.lower()

    # 计算各 flavor 在 angle 原文中的信号强度
    flavor_weights = {
        "champion": sum(1 for k in ["冠军", "胜者", "金牌", "领奖台", "追冠军", "冠军时刻", "赢家"] if k in text),
        "challenge": sum(1 for k in ["极限", "挑战", "刷新", "突破", "不服输", "再试一次", "纪录"] if k in text),
        "modify": sum(1 for k in ["改装", "玩车", "姿态", "低趴", "个性", "调校", "爆改"] if k in text),
        "youth": sum(1 for k in ["青年", "年轻人", "年轻", "热血青年", "态度", "青春", "新生代"] if k in text),
        "track": sum(1 for k in ["赛道", "弯道", "操控", "驾驶乐趣", "过弯", "性能", "竞速"] if k in text),
    }

    # 在已检测到的 flavor 中，按信号强度选择；若强度相同，按优先级选择更具体的叙事方向。
    # 优先级：track > modify > challenge > champion > youth
    # "冠军"容易被话题关键词（如世界冠军）误触发，因此让更明确的动作词优先；
    # youth 相对宽泛，放在最后，使含"追冠军"的角度优先走 champion 路线。
    priority_order = ["track", "modify", "challenge", "champion", "youth"]
    best_flavor = "track"
    best_weight = -1
    for f in flavor:
        w = flavor_weights.get(f, 0)
        current_priority = priority_order.index(f) if f in priority_order else 99
        best_priority = priority_order.index(best_flavor) if best_flavor in priority_order else 99
        if w > best_weight or (w == best_weight and current_priority < best_priority):
            best_weight = w
            best_flavor = f
    if best_weight <= 0:
        best_flavor = "track"

    # 默认 track（赛道/操控）风格的完整画面描述
    # 在 track 内部再按 angle 关键词细分，避免多个 track 角度画面雷同
    if "弯道" in text or "攻弯" in text or "过弯" in text:
        track_scene = "山路弯道"
        track_hot = "连续S弯、路肩、弯道指示旗"
        track_veh = f"{vehicle}以精准指向连续攻弯，车身随方向盘响应，悬挂支撑有力"
        track_pro = "转向手感、悬挂支撑、车身姿态"
        track_finish = f"{vehicle}停在发卡弯顶点"
    elif "操控" in text or "指向" in text or "反馈" in text:
        track_scene = "专业赛道"
        track_hot = "桩桶、走线、赛道边界"
        track_veh = f"{vehicle}在桩桶间灵活穿梭，转向精准无虚位"
        track_pro = "方向盘、底盘反馈、轮胎抓地"
        track_finish = f"{vehicle}停在赛道维修区入口"
    elif "性能" in text or "加速" in text or "制动" in text:
        track_scene = "性能测试场"
        track_hot = "零百加速、制动距离、性能数据"
        track_veh = f"{vehicle}全力加速，轮胎紧咬地面，车身稳定推进"
        track_pro = "发动机、变速箱、刹车系统"
        track_finish = f"{vehicle}停在性能测试区"
    elif "速度" in text or "疾驰" in text or "飞驰" in text:
        track_scene = "高速直线"
        track_hot = "高速直线、风洞效果、速度线"
        track_veh = f"{vehicle}在高速直线上疾驰，气流划过车身"
        track_pro = "空气动力学、流线车身、尾翼"
        track_finish = f"{vehicle}停在高速赛道终点"
    elif "驾驶乐趣" in text or "乐趣" in text:
        track_scene = "城市山路"
        track_hot = "城市山路、连续发卡弯、驾驶席视角"
        track_veh = f"{vehicle}在城市山路上游刃有余，人车合一"
        track_pro = "换挡拨片、运动座椅、踏板反馈"
        track_finish = f"{vehicle}停在山腰观景台"
    else:
        track_scene = "赛道"
        track_hot = "赛道、计时器、挥动的黑白格旗"
        track_veh = f"{vehicle}以运动姿态切入弯道，轮胎摩擦地面，车身低伏"
        track_pro = "运动套件、方向盘、转速表、刹车卡钳"
        track_finish = f"{vehicle}停在赛道/山路尽头"

    hot_15_v = f"【全景+快切】{track_hot}与「{keyword}」热血大字交错闪现，高对比色调。"
    veh_15_v = f"【中景跟拍】{track_veh}；{scene0}变成{track_scene}场景。"
    pro_15_v = f"【特写+环绕】{track_pro}快速切换，{image0}在速度线中定格，车标落版。"
    hot20a_v = f"【特写+快切】{track_hot}与「{keyword}」大字交错，高饱和度。"
    hot20b_v = f"【中景】运动员/车主擦汗、眼神坚定；窗外光线为热血橙红。"
    veh20a_v = f"【全景】{track_veh}，轮胎带起烟雾。"
    veh20b_v = f"【车内中景】手握方向盘换挡，转速表攀升；运动座椅包裹，{image0}在驾驶激情中呈现。"
    pro20_v = f"【特写+环绕+落版】{track_pro}特写，{image0}在速度线中落版。"
    hot30a_v = f"【全景+叠化】赛事画面、{track_hot}、热搜榜单快速叠化，「{keyword}」以热血大字出现。"
    hot30b_v = f"【中景】观众/网友兴奋反应快切，画面高对比、热血色调。"
    veh30a_v = f"【全景跟拍】{track_veh}，镜头与车辆同向移动；背景有速度线和运动符号。"
    veh30b_v = f"【中景+车内】车主激情驾驶，换挡、过弯；{image0}在驾驶氛围中被强调。"
    pro30a_v = f"【特写组接】{track_pro}依次呈现，{image0}细节在速度线中。"
    pro30b_v = f"【落版全景】{track_finish}，车标正对镜头；画面右侧Slogan，底部联名字样。"

    if best_flavor == "champion":
        hot_15_v = f"【全景+快切】冠军奖杯、领奖台、金色飘带与「{keyword}」热血大字交错闪现，高对比色调。"
        veh_15_v = f"【中景跟拍】{vehicle}如冠军冲线般从画面一侧疾驰而入，车身姿态昂扬；{scene0}化作冠军时刻。"
        pro_15_v = f"【特写+环绕】冠军徽章、运动套件、方向盘、刹车卡钳快速切换，{image0}在金色光线中定格，车标落版。"
        hot20a_v = f"【特写+快切】冠军奖杯、领奖台、金色飘带与「{keyword}」大字交错，高饱和度。"
        hot20b_v = f"【中景】冠军振臂庆祝，眼神坚定；窗外洒下金色光芒。"
        veh20a_v = f"【全景】{vehicle}以胜利姿态驶过终点线，车身昂扬，彩带飞舞。"
        veh20b_v = f"【车内中景】车主握紧方向盘，目光如炬；{image0}在冠军光芒中被强调。"
        pro20_v = f"【特写+环绕+落版】冠军徽标、运动套件、尾翼、排气管特写，{image0}在金色速度线中落版。"
        hot30a_v = f"【全景+叠化】冠军时刻、领奖台、金色飘带、热搜榜单快速叠化，「{keyword}」以热血大字出现。"
        hot30b_v = f"【中景】观众欢呼、冠军庆祝快切，画面高对比、金色热血色调。"
        veh30a_v = f"【全景跟拍】{vehicle}如冠军座驾般驶过红毯/终点线，镜头与车辆同向移动；背景有彩带和冠军符号。"
        veh30b_v = f"【中景+车内】车主自信驾驶，享受胜利时刻；{image0}在荣耀氛围中被强调。"
        pro30a_v = f"【特写组接】冠军徽章、运动套件、方向盘、刹车卡钳依次呈现，{image0}细节在金色光线中。"
        pro30b_v = f"【落版全景】{vehicle}停在领奖台/冠军拱门前，车标正对镜头；画面右侧Slogan，底部联名字样。"
    elif best_flavor == "challenge":
        hot_15_v = f"【大特写+快切】计时器特写、不断刷新的纪录数字、汗水滑落与「{keyword}」热血大字交错闪现，高对比色调。"
        veh_15_v = f"【中景】{vehicle}在险峻山路/赛道挑战极限，轮胎紧贴地面，车身低伏蓄势；{scene0}化作挑战之路。"
        pro_15_v = f"【大特写+环绕】性能仪表、转速表、刹车卡钳、运动套件快速切换，{image0}在突破瞬间定格，车标落版。"
        hot20a_v = f"【大特写+快切】计时器、刷新中的纪录数字、汗水特写与「{keyword}」大字交错，高饱和度。"
        hot20b_v = f"【中景】挑战者凝视远方、目光坚毅；窗外是晨曦微光。"
        veh20a_v = f"【全景跟拍】{vehicle}在险峻山路/赛道连续攻弯，车身紧贴地面，轮胎扬起微尘。"
        veh20b_v = f"【车内近景】车主专注过弯，转速表指针攀升；{image0}在极限驾驶中被强调。"
        pro20_v = f"【特写+环绕+落版】性能仪表、刹车卡钳、运动套件、尾翼特写，{image0}在突破瞬间落版。"
        hot30a_v = f"【特写+叠化】纪录刷新、计时器特写、汗水与热搜榜单快速叠化，「{keyword}」以热血大字出现。"
        hot30b_v = f"【中景】挑战者坚毅表情、训练片段快切，画面高对比、燃色调。"
        veh30a_v = f"【全景跟拍】{vehicle}在连续弯道中疾驰，镜头与车辆同向移动；背景有计时器和纪录数字。"
        veh30b_v = f"【中景+车内】车主挑战极限，换挡、刹车、再加速；{image0}在坚持中被强调。"
        pro30a_v = f"【特写组接】性能仪表、方向盘、刹车卡钳、运动套件依次呈现，{image0}细节在速度线中。"
        pro30b_v = f"【落版全景】{vehicle}停在山巅/终点线前，车标正对镜头；画面右侧Slogan，底部联名字样。"
    elif best_flavor == "modify":
        hot_15_v = f"【中景+环绕】改装车间、个性涂装、低趴姿态与「{keyword}」热血大字交错闪现，工业灯光氛围。"
        veh_15_v = f"【中景跟拍】{vehicle}以改装姿态驶入街头，轮毂、尾翼、包围套件引人注目；{scene0}变成改装聚落。"
        pro_15_v = f"【微距+环绕】改装套件、卡钳、轮毂、方向盘快速切换，{image0}在个性光影中定格，车标落版。"
        hot20a_v = f"【中景+快切】改装车间、个性涂装、低趴姿态与「{keyword}」大字交错，高饱和度。"
        hot20b_v = f"【特写】改装玩家俯身检查细节，眼神专注；窗外是城市改装聚落。"
        veh20a_v = f"【全景】{vehicle}以低趴改装姿态停在街头，车身涂装个性鲜明。"
        veh20b_v = f"【车内中景】玩家坐进驾驶位，手握改装方向盘；{image0}在改装氛围中被强调。"
        pro20_v = f"【微距+环绕+落版】改装包围、卡钳、轮毂、排气特写，{image0}在个性光影中落版。"
        hot30a_v = f"【中景+叠化】改装案例、个性涂装、低趴姿态与热搜榜单快速叠化，「{keyword}」以热血大字出现。"
        hot30b_v = f"【中景】改装玩家交流、围观人群快切，画面高对比、街头潮流色调。"
        veh30a_v = f"【全景跟拍】{vehicle}以改装姿态穿行城市街道，镜头与车辆同向移动；背景有涂鸦和改装符号。"
        veh30b_v = f"【中景+车内】玩家驾驶{vehicle}，享受专属调校；{image0}在个性表达中被强调。"
        pro30a_v = f"【特写组接】改装套件、方向盘、轮毂、刹车卡钳依次呈现，{image0}细节在街头光线下。"
        pro30b_v = f"【落版全景】{vehicle}停在改装聚落/城市天台，车标正对镜头；画面右侧Slogan，底部联名字样。"
    elif best_flavor == "youth":
        hot_15_v = f"【全景+推拉】年轻人群欢呼、街头赛道、潮流符号与「{keyword}」热血大字交错闪现，霓虹色调。"
        veh_15_v = f"【中景跟拍】{vehicle}与年轻车主一同出现在城市街头，车身动感，气氛热烈；{scene0}变成潮流街区。"
        pro_15_v = f"【特写+环绕】潮流涂装、运动座椅、方向盘、车灯快速切换，{image0}在年轻姿态中定格，车标落版。"
        hot20a_v = f"【全景+快切】年轻人刷手机、街头潮流符号与「{keyword}」大字交错，高饱和度。"
        hot20b_v = f"【中景】年轻车主整理衣领/戴上耳机，眼神有光；窗外是霓虹城市。"
        veh20a_v = f"【全景跟拍】{vehicle}与年轻车主一起出现在城市夜景中，车身被霓虹照亮。"
        veh20b_v = f"【车内中景】年轻车主手握方向盘，随音乐点头；{image0}在年轻氛围中被强调。"
        pro20_v = f"【特写+环绕+落版】潮流配色、运动座椅、方向盘、车灯特写，{image0}在年轻光影中落版。"
        hot30a_v = f"【全景+叠化】年轻人热议、潮流符号、街头夜景与热搜榜单快速叠化，「{keyword}」以热血大字出现。"
        hot30b_v = f"【中景】年轻人群欢呼、自拍快切，画面高饱和、潮流色调。"
        veh30a_v = f"【全景跟拍】{vehicle}载着年轻车主穿行霓虹街道，镜头与车辆同向移动；背景有潮流涂鸦。"
        veh30b_v = f"【中景+车内】年轻车主驾驶{vehicle}，享受属于自己的时刻；{image0}在青春氛围中被强调。"
        pro30a_v = f"【特写组接】潮流涂装、运动座椅、方向盘、轮毂依次呈现，{image0}细节在霓虹灯光中。"
        pro30b_v = f"【落版全景】{vehicle}停在城市天台/潮流街区，车标正对镜头；画面右侧Slogan，底部联名字样。"

    return {
        "hot_15_v": hot_15_v,
        "veh_15_v": veh_15_v,
        "pro_15_v": pro_15_v,
        "hot20a_v": hot20a_v,
        "hot20b_v": hot20b_v,
        "veh20a_v": veh20a_v,
        "veh20b_v": veh20b_v,
        "pro20_v": pro20_v,
        "hot30a_v": hot30a_v,
        "hot30b_v": hot30b_v,
        "veh30a_v": veh30a_v,
        "veh30b_v": veh30b_v,
        "pro30a_v": pro30a_v,
        "pro30b_v": pro30b_v,
    }


def _theme_pack(
    themes: List[str],
    keyword: str,
    field: str,
    emotion: str,
    vehicle: str,
    vehicle_key: str,
    image0: str,
    scene0: str,
    positioning: str,
    narrative: str,
    angle: str,
) -> Dict[str, str]:
    """为主题生成差异化的画面、台词、音效元素。"""
    t = set(themes)
    flavor = _angle_flavor(angle, t)
    sport_vis = None
    if "sport" in t:
        sport_vis = _sport_visuals(angle, flavor, keyword, vehicle, scene0, image0)

    # 15秒：优先用生活/车主故事主题，再按太空/AI/未来/运动/家庭
    if "life" in t:
        hot_15_v = f"【中景】清晨阳光照进房间，手机弹出「{keyword}」通知；咖啡杯、车钥匙、真实生活气息。"
        hot_15_s = "原声吉他 + 城市环境音 + 轻快节奏"
        veh_15_v = f"【中景跟拍】车主端着咖啡走向{vehicle}，轻松启动；{scene0}就是日常通勤/周末出游的真实画面。"
        veh_15_sub = f"{vehicle} · {positioning}｜{keyword}之后，日子照常好"
        veh_15_s = "轻快民谣 + 车门关闭声"
        pro_15_v = f"【特写】储物空间放咖啡、舒适座椅、方向盘握感、车外风景，{image0}在生活细节中落版。"
        pro_15_sub = f"{vehicle}｜好故事，从日常开始"
        pro_15_s = "温暖吉他落版"
    elif "space" in t:
        hot_15_v = f"【全景+推进】深空背景中，火箭尾焰划破夜空，热点关键词「{keyword}」以金属质感大字从星图中浮现，镜头穿过星舰舷窗推进。"
        hot_15_s = "太空环境音 + 火箭发射轰鸣 + 强节奏鼓点"
        veh_15_v = f"【中景】{vehicle}座舱被设计成飞船驾驶舱视感，中控屏显示星图/航线；窗外星河流转，{image0}在冷光中更显未来感。"
        veh_15_sub = f"{vehicle} · {positioning}｜把星舰的浪漫，装进{scene0}"
        veh_15_s = "电子合成器 + 太空感环境音"
        pro_15_v = f"【特写+环绕】{vehicle}车灯如推进器点亮，轮毂像空间站结构旋转；智能座舱特写收尾，车标在星尘中落版。"
        pro_15_sub = f"{vehicle}｜从星空到地面，探索不停"
        pro_15_s = "史诗管弦 + 电子落版音效"
    elif "ai" in t:
        hot_15_v = f"【特写+快速推进】数字界面、语音波形、AI代码流快速闪过，「{keyword}」以发光像素字出现；镜头被数据流卷入。"
        hot_15_s = "AI语音 + 电子提示音 + 科技感鼓点"
        veh_15_v = f"【中景】车主对{vehicle}说了一句话，智能座舱秒回应，HUD/中控屏同步亮起；{image0}被蓝色数据光勾勒。"
        veh_15_sub = f"{vehicle} · {positioning}｜像AI一样，懂你要去哪"
        veh_15_s = "科技感电子乐 + 语音交互音效"
        pro_15_v = f"【特写组接】中控屏、语音助手、HUD、车灯依次点亮，{image0}细节在数字光效中呈现，最后车标发光落版。"
        pro_15_sub = f"{vehicle}｜聪明的回答，不止在屏幕里"
        pro_15_s = "未来感合成器 + 落版重音"
    elif "future" in t:
        hot_15_v = f"【全景+推进】未来感城市夜景中，光线轨迹与数据粒子交织，「{keyword}」以发光立体字从城市天际线中升起。"
        hot_15_s = "未来感电子合成器 + 机械运转声 + 强节奏鼓点"
        veh_15_v = f"【中景】{vehicle}从光轨中驶出，车身被蓝色/橙色科技光勾勒；{scene0}与未来感道路融为一体。"
        veh_15_sub = f"{vehicle} · {positioning}｜{keyword}之后，未来已来"
        veh_15_s = "渐进式电子乐 + 车辆启动声"
        pro_15_v = f"【特写+环绕】{vehicle}贯穿灯如光剑点亮，车身线条在光轨中流动，{image0}细节在科技粒子中定格落版。"
        pro_15_sub = f"{vehicle}｜科技进化的下一个答案"
        pro_15_s = "未来感合成器 + 落版重音"
    elif "sport" in t:
        hot_15_v = sport_vis['hot_15_v']
        hot_15_s = "引擎轰鸣 + 强烈鼓点 + 观众欢呼"
        veh_15_v = sport_vis['veh_15_v']
        veh_15_sub = f"{vehicle} · {positioning}｜和{keyword}一样，热血到底"
        veh_15_s = "引擎声 + 运动摇滚"
        pro_15_v = sport_vis['pro_15_v']
        pro_15_sub = f"{vehicle}｜赛道基因，不需要解释"
        pro_15_s = "高潮鼓点 + 引擎收声"
    elif "family" in t:
        hot_15_v = f"【全景】夕阳下家庭聚会的剪影，孩子奔跑，关键词「{keyword}」以温暖手写字出现在画面下方。"
        hot_15_s = "温暖钢琴 + 孩子笑声 + 轻柔鼓点"
        veh_15_v = f"【中景】家人依次上车，{vehicle}电动侧滑门/大空间展现；{scene0}被金色夕阳光包围。"
        veh_15_sub = f"{vehicle} · {positioning}｜{keyword}的尽头，是家人"
        veh_15_s = "温馨弦乐 + 车门轻闭声"
        pro_15_v = f"【特写】安全座椅接口、宽敞后排、全景天窗、静音细节依次出现，{image0}在家人笑容中落版。"
        pro_15_sub = f"{vehicle}｜装得下责任，也装得下爱"
        pro_15_s = "温暖落版音效"
    else:
        # default 主题：根据 angle 关键词做三镜头差异化，降低跨角度重复度
        _angle_text_lower = angle.lower()
        if any(k in _angle_text_lower for k in ["靠谱", "成熟", "稳重", "可靠", "务实"]):
            hot_15_v = f"【全景+稳定推进】热点关键词「{keyword}」以稳重字体从画面中心升起，背景是{field}领域的稳健时刻，色调沉稳。"
            veh_15_v = f"【中景跟拍】{vehicle}以沉稳姿态驶入{field}氛围场景（{scene0}），车身线条在冷光下显得可靠。"
            pro_15_v = f"【特写+环绕】{vehicle}商务外观/内饰材质/工艺细节特写快速切换，凸显{image0}的稳重感，最后定格车标落版。"
        elif any(k in _angle_text_lower for k in ["商务", "家用", "兼顾", "多面", "人生"]):
            hot_15_v = f"【全景+分屏推进】热点关键词「{keyword}」以分屏形式出现，一边是{field}现场，一边是城市生活场景。"
            veh_15_v = f"【中景跟拍】{vehicle}在商务与家庭场景间切换（{scene0}），车身在不同光线下呈现多面气质。"
            pro_15_v = f"【特写+环绕】{vehicle}空间布局/座椅/后备箱特写快速切换，展示{image0}对多场景的兼容，最后定格车标落版。"
        elif any(k in _angle_text_lower for k in ["探索", "边界", "下一步", "未来", "突破"]):
            hot_15_v = f"【全景+推进】未来感城市夜景中，光线轨迹与数据粒子交织，「{keyword}」以发光立体字从城市天际线中升起。"
            veh_15_v = f"【中景】{vehicle}从未来感道路/光轨中驶出，车身被科技光勾勒；{scene0}与未来道路交织。"
            pro_15_v = f"【特写+环绕】{vehicle}贯穿灯/智能座舱/车身线条特写快速切换，{image0}在科技粒子中定格，最后车标落版。"
        elif any(k in _angle_text_lower for k in ["骄傲", "自豪", "荣耀", "高光"]):
            hot_15_v = f"【全景+光芒推进】热点关键词「{keyword}」在金色光芒中从画面中心升起，背景是{field}领域的高光时刻。"
            veh_15_v = f"【中景跟拍】{vehicle}在金色光芒中驶向城市，车身反射荣耀感；{scene0}被温暖光线包围。"
            pro_15_v = f"【特写+环绕】{vehicle}外观高光/品牌徽标/车身曲面特写快速切换，{image0}在金色光线下定格，最后定格车标落版。"
        else:
            hot_15_v = f"【全景+快速推进】热点关键词「{keyword}」以大字动画从画面中心弹出，背景使用{field}领域代表性画面，色调偏冷或高饱和。"
            veh_15_v = f"【中景跟拍】{vehicle}驶入与「{keyword}」情绪相符的场景（{scene0}），车窗或后视镜中隐约映出{field}元素。"
            pro_15_v = f"【特写+环绕】{vehicle}车头/车尾/内饰特写快速切换，重点展示{image0}细节，最后定格车标落版。"
        hot_15_s = "强节奏鼓点入 + 社交媒体消息提示音"
        veh_15_sub = f"{vehicle} · {positioning}，和{keyword}一样值得被看见"
        veh_15_s = "音乐进入主歌，环境音渐弱"
        pro_15_sub = f"{vehicle}｜不止于车，更是一种态度"
        pro_15_s = "节奏重音 + 落版音效"

    # 20秒：同样优先生活主题
    if "life" in t:
        hot20a_v = f"【特写】手机弹出「{keyword}」通知，旁边是咖啡和车钥匙，画面真实自然。"
        hot20a_s = "消息提示音 + 城市环境音"
        hot20b_v = f"【中景】车主伸懒腰、看窗外，晨光洒在脸上；轻松惬意。"
        hot20b_s = "原声吉他 + 轻快节奏"
        veh20a_v = f"【全景】{vehicle}出现在城市街道/咖啡店门口，车主走向车辆，生活气息浓厚。"
        veh20a_s = "轻快民谣主歌"
        veh20b_v = f"【车内中景】车主把咖啡放入杯架，调好座椅，轻松出发；{scene0}自然呈现。"
        veh20b_s = "车门关闭 + 音乐推进"
        pro20_v = f"【特写+环绕+落版】储物空间、座椅、方向盘、车漆反光依次展示，{image0}在日常光线中落版。"
        pro20_s = "温暖吉他高潮 + 落版"
    elif "space" in t:
        hot20a_v = f"【特写】手机屏幕上「{keyword}」热搜与星舰发射画面同框，画面轻微做旧。"
        hot20a_s = "消息提示音 + 火箭低频轰鸣"
        hot20b_v = f"【中景】人物仰望夜空，瞳孔中映出火箭尾焰；镜头缓缓推近，窗外是深空蓝紫色调。"
        hot20b_s = "太空环境音 + 情绪弦乐"
        veh20a_v = f"【全景】{vehicle}停在开阔高地，车灯照亮前方；远处城市灯火与星空相接，像地面上的星舰。"
        veh20a_s = "史诗电子乐渐入"
        veh20b_v = f"【车内中景】中控屏切换为星图模式，{image0}氛围灯随音乐呼吸；人物握住方向盘，像握住操纵杆。"
        veh20b_s = "电子合成器 + 车辆启动声"
        pro20_v = f"【特写+环绕+落版】{vehicle}前脸如星舰舰首，贯穿灯像推进器点亮；{image0}细节在星尘特效中落版。"
        pro20_s = "高潮管弦 + 落版重音"
    elif "ai" in t:
        hot20a_v = f"【特写+快切】AI新闻、代码流、聊天界面与「{keyword}」热搜快速切换，模拟刷屏。"
        hot20a_s = "AI语音 + 消息提示音"
        hot20b_v = f"【中景】人物对着手机说出问题，屏幕上的AI助手秒回；镜头推近至面部，光线为科技蓝。"
        hot20b_s = "科技感电子乐"
        veh20a_v = f"【全景】{vehicle}驶过未来感街区，车身反射霓虹与数据流；{scene0}与数字世界无缝衔接。"
        veh20a_s = "科技电子乐主歌"
        veh20b_v = f"【车内中景】手势控制中控屏，语音助手播报导航/音乐；{image0}在交互光效中被强调。"
        veh20b_s = "UI反馈音效 + 电子推进"
        pro20_v = f"【特写+环绕+落版】智能座舱界面、HUD、车灯、LOGO依次点亮，{image0}细节在数字粒子中落版。"
        pro20_s = "未来感合成器高潮 + 落版重音"
    elif "future" in t:
        hot20a_v = f"【特写+快切】科技新闻、未来城市概念图、光线轨迹与「{keyword}」热搜快速切换。"
        hot20a_s = "未来感电子提示音 + 消息连播"
        hot20b_v = f"【中景】人物站在落地窗前，看着未来感城市夜景；屏幕上是{keyword}，瞳孔映出科技蓝光。"
        hot20b_s = "渐进式电子乐 + 城市低频"
        veh20a_v = f"【全景】{vehicle}从未来感隧道/光轨中驶出，车身线条被流光勾勒；{scene0}与未来道路交织。"
        veh20a_s = "未来电子乐主歌"
        veh20b_v = f"【车内中景】数字仪表盘、中控屏、氛围灯随音乐律动；{image0}在科技光效中呈现。"
        veh20b_s = "车辆启动声 + 电子推进"
        pro20_v = f"【特写+环绕+落版】{vehicle}贯穿灯、车身曲面、智能座舱、LOGO依次点亮，{image0}在光粒子中落版。"
        pro20_s = "未来感合成器高潮 + 落版重音"
    elif "sport" in t:
        hot20a_v = sport_vis['hot20a_v']
        hot20a_s = "引擎轰鸣 + 强烈鼓点"
        hot20b_v = sport_vis['hot20b_v']
        hot20b_s = "运动摇滚渐入"
        veh20a_v = sport_vis['veh20a_v']
        veh20a_s = "引擎声 + 运动音乐"
        veh20b_v = sport_vis['veh20b_v']
        veh20b_s = "换挡声 + 音乐推进"
        pro20_v = sport_vis['pro20_v']
        pro20_s = "高潮鼓点 + 引擎收声"
    elif "family" in t:
        hot20a_v = f"【特写+快切】家庭相关热搜、亲子视频、评论区与「{keyword}」同框，色调暖黄。"
        hot20a_s = "消息提示音 + 轻柔钢琴"
        hot20b_v = f"【中景】父母看着手机微笑，孩子跑过来；窗外是温暖的傍晚光线。"
        hot20b_s = "温馨弦乐起"
        veh20a_v = f"【全景】{vehicle}停在住宅小区，家人拿着行李走向车辆；电动门/大空间展现。"
        veh20a_s = "温暖弦乐主歌"
        veh20b_v = f"【车内中景】孩子在后排安全座椅上笑，父母在前排放松；{image0}氛围温馨。"
        veh20b_s = "车门轻闭 + 音乐推进"
        pro20_v = f"【特写+环绕+落版】安全座椅、大空间、静音玻璃、天窗依次展示，{image0}在家庭笑容中落版。"
        pro20_s = "温暖弦乐高潮 + 落版"
    else:
        hot20a_v = f"【特写+快切】手机/屏幕里闪过「{keyword}」热搜、评论区、弹幕，画面做旧或加轻微抖动。"
        hot20a_s = "消息提示音连播 + 低频底鼓"
        hot20b_v = f"【中景】一位与{vehicle}目标人群气质相符的人物看着屏幕若有所思，窗外光线为{emotion}基调。"
        hot20b_s = "情绪弦乐起"
        veh20a_v = f"【全景】{vehicle}出现在{scene0}场景，人物走向车辆；镜头从人物背影切换至车侧。"
        veh20a_s = "主歌旋律，节奏渐强"
        veh20b_v = f"【车内中景】人物坐进驾驶位，手部特写启动车辆，中控屏或仪表盘亮起。"
        veh20b_s = "引擎轻启声 + 音乐推进"
        pro20_v = f"【特写+环绕+落版】{vehicle}外观高光细节与产品卖点字幕卡交替出现，最后车标+Slogan落版。"
        pro20_s = "高潮鼓点 + 落版重音"

    # 30秒：同样优先生活主题
    if "life" in t:
        hot30a_v = f"【全景+叠化】城市清晨、通勤人群、热搜榜单、生活场景快速叠化，「{keyword}」以自然手写大字出现。"
        hot30a_s = "原声吉他 + 悬念音效"
        hot30b_v = f"【中景】不同人过着日常：买咖啡、等电梯、看窗外；画面自然光、生活化色调。"
        hot30b_s = "城市环境音 + 轻声交谈"
        veh30a_v = f"【全景跟拍】{vehicle}行驶在城市街道/周末出游路线，镜头与车辆同向；背景是真实生活街景。"
        veh30a_s = "轻快民谣进入副歌前奏"
        veh30b_v = f"【中景+车内】车主/乘客在{scene0}中放松，喝咖啡、聊天；{image0}在日常氛围中被强调。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】储物空间、舒适座椅、方向盘、车漆反光依次呈现，{image0}细节在自然光下。"
        pro30a_s = "节奏鼓点 + 温暖音效"
        pro30b_v = f"【落版全景】{vehicle}停在咖啡店/城市街角，车标正对镜头；画面右侧Slogan，底部联名字样。"
        pro30b_s = "高潮落版音效，音乐收"
    elif "space" in t:
        hot30a_v = f"【全景+叠化】火箭发射、星舰升空、控制室欢呼、热搜榜单快速叠化，中央大字「{keyword}」在星空中清晰。"
        hot30a_s = "火箭轰鸣 + 悬念音效"
        hot30b_v = f"【中景】不同人物仰望星空、刷手机、讨论，画面整体为深蓝紫太空色调。"
        hot30b_s = "键盘敲击 + 人群低语 + 太空环境音"
        veh30a_v = f"【全景跟拍】{vehicle}行驶在空旷公路/高地，镜头与车辆同向移动；背景是星空与城市灯火交融。"
        veh30a_s = "史诗电子乐进入副歌前奏"
        veh30b_v = f"【中景+车内】车主在{scene0}中看着智能座舱的星图界面，表情放松而专注；{image0}在冷光中呈现。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】{vehicle}车灯、轮毂、智能座舱、车漆反光在星光下依次呈现，{image0}细节被星空衬托。"
        pro30a_s = "节奏鼓点 + 电子音效"
        pro30b_v = f"【落版全景】{vehicle}停在星河背景前，车标正对镜头；画面右侧出现品牌Slogan，底部「{vehicle} × {keyword}」字样。"
        pro30b_s = "高潮落版音效，音乐收"
    elif "ai" in t:
        hot30a_v = f"【全景+叠化】AI界面、数字人、代码雨、热搜榜单快速叠化，「{keyword}」以像素化方式重组清晰。"
        hot30a_s = "AI语音 + 悬念音效"
        hot30b_v = f"【中景】不同人与AI设备交互，有人惊喜、有人沉思；画面整体为科技蓝绿色调。"
        hot30b_s = "键盘敲击 + UI音效 + 环境人声"
        veh30a_v = f"【全景跟拍】{vehicle}驶过数字城市街区，车身反射霓虹与数据流；背景出现AI符号。"
        veh30a_s = "科技电子乐进入副歌前奏"
        veh30b_v = f"【中景+车内】车主用语音/手势控制{vehicle}，中控屏流畅反馈；{image0}在交互中被突出。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】智能座舱、HUD、车灯、车身线条在数字光效中依次呈现，{image0}细节科技感十足。"
        pro30a_s = "节奏鼓点 + 电子音效"
        pro30b_v = f"【落版全景】{vehicle}停在简洁科技背景前，车标正对镜头；画面右侧Slogan，底部联名字样。"
        pro30b_s = "高潮落版音效，音乐收"
    elif "future" in t:
        hot30a_v = f"【全景+叠化】未来城市概念图、光线轨迹、科技产品发布、热搜榜单快速叠化，「{keyword}」以发光立体字在城市天际线中清晰。"
        hot30a_s = "未来感电子合成器 + 悬念音效"
        hot30b_v = f"【中景】不同人看着未来感屏幕、讨论科技趋势；画面整体为蓝橙科技色调。"
        hot30b_s = "键盘敲击 + 城市低频 + 环境人声"
        veh30a_v = f"【全景跟拍】{vehicle}驶过未来感道路/光轨隧道，镜头与车辆同向移动；背景是数据流与光线轨迹。"
        veh30a_s = "未来电子乐进入副歌前奏"
        veh30b_v = f"【中景+车内】车主在{scene0}中体验{vehicle}的智能科技，数字仪表与中控屏联动；{image0}在科技光效中被突出。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】{vehicle}贯穿灯、车身曲面、智能座舱、车漆反光在光粒子中依次呈现，{image0}细节未来感十足。"
        pro30a_s = "节奏鼓点 + 电子音效"
        pro30b_v = f"【落版全景】{vehicle}停在未来感城市背景前，车标正对镜头；画面右侧Slogan，底部联名字样。"
        pro30b_s = "高潮落版音效，音乐收"
    elif "sport" in t:
        hot30a_v = sport_vis['hot30a_v']
        hot30a_s = "引擎轰鸣 + 悬念音效"
        hot30b_v = sport_vis['hot30b_v']
        hot30b_s = "人群欢呼 + 键盘敲击"
        veh30a_v = sport_vis['veh30a_v']
        veh30a_s = "运动摇滚进入副歌前奏"
        veh30b_v = sport_vis['veh30b_v']
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = sport_vis['pro30a_v']
        pro30a_s = "节奏鼓点 + 电子音效"
        pro30b_v = sport_vis['pro30b_v']
        pro30b_s = "高潮落版音效，音乐收"
    elif "family" in t:
        hot30a_v = f"【全景+叠化】家庭相关新闻、亲子视频、节日场景、热搜榜单快速叠化，「{keyword}」以温暖大字出现。"
        hot30a_s = "温暖钢琴 + 悬念音效"
        hot30b_v = f"【中景】家庭成员笑容、拥抱、准备出行；画面整体为暖黄色调。"
        hot30b_s = "孩子笑声 + 环境人声"
        veh30a_v = f"【全景跟拍】{vehicle}行驶在回家的路上，镜头与车辆同向；背景是夕阳与街道。"
        veh30a_s = "温馨弦乐进入副歌前奏"
        veh30b_v = f"【中景+车内】家人在{scene0}中放松乘坐，孩子看向窗外；{image0}在温馨氛围中被强调。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】大空间、安全座椅、静音细节、天窗依次呈现，{image0}细节在家庭光线下。"
        pro30a_s = "节奏鼓点 + 温暖音效"
        pro30b_v = f"【落版全景】{vehicle}停在小区/家门口，车标正对镜头；画面右侧Slogan，底部联名字样。"
        pro30b_s = "高潮落版音效，音乐收"
    else:
        hot30a_v = f"【全景+叠化】{field}领域相关画面蒙太奇：新闻画面、社交平台界面、路人反应、热搜榜单，中央大字「{keyword}」逐渐清晰。"
        hot30a_s = "悬念音效 + 社交媒体混音"
        hot30b_v = f"【中景】不同人物对「{keyword}」的反应快切，画面整体为{emotion}情绪色调。"
        hot30b_s = "键盘敲击、消息提示、环境人声"
        veh30a_v = f"【全景跟拍】{vehicle}行驶在{scene0}路线，镜头与车辆同向移动；背景中隐约出现{field}符号或{keyword}关键词。"
        veh30a_s = "情绪音乐进入副歌前奏"
        veh30b_v = f"【中景+车内】车主/乘客在{scene0}中使用{vehicle}的{image0}，表情自然放松。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】{vehicle}产品亮点蒙太奇：{image0}细节、车身线条、车灯点亮、轮毂转动。"
        pro30a_s = "节奏鼓点 + 电子音效"
        pro30b_v = f"【落版全景】{vehicle}停在简洁背景前，车标正对镜头；画面右侧Slogan，底部「{vehicle} × {keyword}」联名字样。"
        pro30b_s = "高潮落版音效，音乐收"

    # 中间镜头字幕：按主题差异化，避免所有角度都一样
    if "life" in t:
        hot20a_sub = f"早上刷到{keyword}，晚上它还在热搜上。"
        hot20b_sub = f"一条热搜，一杯咖啡，一个普通的早晨。"
        hot30a_sub = f"你有没有发现，{keyword}正在改变我们过日子的方式？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是普通人的日常。"
        veh20a_sub = f"{vehicle}的{scene0}，是日常里最稳的确定性。"
        veh20b_sub = f"热点会过去，但好日子的细节不会。"
        veh30a_sub = f"生活里的{emotion}，{vehicle}用{image0}稳稳接住了。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份生活里的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，过好每一天"
        pro30a_sub = f"{vehicle}｜{image0}，日子照常好"
    elif "space" in t:
        hot20a_sub = f"当{keyword}点亮夜空，有人看见了未来。"
        hot20b_sub = f"火箭升空的瞬间，有人想的是远方。"
        hot30a_sub = f"你有没有想过，{keyword}为什么会让我们抬头？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是对未知的向往。"
        veh20a_sub = f"{vehicle}的{scene0}，装得下一片星空。"
        veh20b_sub = f"我们不想上天，只想把星舰的浪漫带到地面。"
        veh30a_sub = f"从星空到地面，{vehicle}的探索没有停。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份仰望星空的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜把星空，装进{scene0}"
        pro30a_sub = f"{vehicle}｜{image0}，像星图一样指引方向"
    elif "ai" in t:
        hot20a_sub = f"{keyword}刷屏时，AI已经读完了所有评论。"
        hot20b_sub = f"AI 回答得很快，但我们真正想问的是什么？"
        hot30a_sub = f"你有没有发现，{keyword}正在让机器变得更像人？"
        hot30b_sub = f"有人说这是{emotion}，有人说这只是算法的胜利。"
        veh20a_sub = f"{vehicle}的{scene0}，AI比你更懂怎么走。"
        veh20b_sub = f"不追风口，只做一个能听懂你的座舱。"
        veh30a_sub = f"AI能读懂数据，{vehicle}能读懂你要去哪。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份被智能理解的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，懂你说的和没说的"
        pro30a_sub = f"{vehicle}｜{image0}，比想象更懂你"
    elif "future" in t:
        hot20a_sub = f"{keyword}不是终点，是下一次进化的起点。"
        hot20b_sub = f"屏幕里的未来，正在变成窗外的现实。"
        hot30a_sub = f"你有没有发现，{keyword}正在重新定义我们的出行？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是未来的样子。"
        veh20a_sub = f"{vehicle}的{scene0}，是通向未来的入口。"
        veh20b_sub = f"不模仿未来，{vehicle}正在创造它。"
        veh30a_sub = f"未来不是等来的，是{vehicle}开出来的。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份对未来的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，就是未来"
        pro30a_sub = f"{vehicle}｜{image0}，下一个时代的答案"
    elif "sport" in t:
        hot20a_sub = f"{keyword}火了，因为热血永远不过时。"
        hot20b_sub = f"冠军只有一个，但热血属于每个追它的人。"
        hot30a_sub = f"你有没有发现，{keyword}让我们的心跳都变快了？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是竞技的魅力。"
        veh20a_sub = f"{vehicle}的{scene0}，能装下这份热血。"
        veh20b_sub = f"冠军只是结果，{vehicle}的赛道基因一直都在。"
        veh30a_sub = f"赛道上的{emotion}，{vehicle}用{image0}稳稳接住了。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份赛场上的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，热血全开"
        pro30a_sub = f"{vehicle}｜{image0}，为速度而生"
    elif "family" in t:
        hot20a_sub = f"{keyword}刷屏，但家人的消息更值得置顶。"
        hot20b_sub = f"热闹是别人的，家人的消息才是置顶。"
        hot30a_sub = f"你有没有发现，{keyword}让我们更想守住重要的人？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是生活的重量。"
        veh20a_sub = f"{vehicle}的{scene0}，装得下一家人的{emotion}。"
        veh20b_sub = f"守护家人，从来不是话题，而是本能。"
        veh30a_sub = f"对家人的{emotion}，{vehicle}用{image0}稳稳接住了。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份对家人的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，守护每一程"
        pro30a_sub = f"{vehicle}｜{image0}，给家人稳稳的幸福"
    elif "life" in t:
        hot20a_sub = f"早上刷到{keyword}，晚上它还在热搜上。"
        hot20b_sub = f"一条热搜，一杯咖啡，一个普通的早晨。"
        hot30a_sub = f"你有没有发现，{keyword}正在改变我们过日子的方式？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是普通人的日常。"
        veh20a_sub = f"{vehicle}的{scene0}，是日常里最稳的确定性。"
        veh20b_sub = f"热点会过去，但好日子的细节不会。"
        veh30a_sub = f"生活里的{emotion}，{vehicle}用{image0}稳稳接住了。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份生活里的{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，过好每一天"
        pro30a_sub = f"{vehicle}｜{image0}，日子照常好"
    else:
        hot20a_sub = f"最近，{keyword}火了。"
        hot20b_sub = f"话题在刷屏，而真正重要的是你怎么看它。"
        hot30a_sub = f"你有没有发现，{keyword}正在改变我们的情绪？"
        hot30b_sub = f"有人说这是{emotion}，有人说这就是生活。"
        veh20a_sub = f"{vehicle}的{scene0}，刚好装得下这份{emotion}。"
        veh20b_sub = f"热度会过去，{vehicle}的故事一直在发生。"
        veh30a_sub = f"当{keyword}成为情绪，{vehicle}用{image0}给出了回应。"
        veh30b_sub = f"{vehicle}用{image0}，接住这份{emotion}。"
        pro20_sub = f"{vehicle} × {keyword}｜{image0}，触手可及"
        pro30a_sub = f"{vehicle}｜{positioning}"

    # 台词微调：让产品落版台词也随角度有变化
    if "space" in t:
        pro_15_sub = f"{vehicle}｜从星空到地面，探索不停"
        pro30b_sub = f"{vehicle} × {keyword}｜探索，从未止步"
    elif "ai" in t:
        pro_15_sub = f"{vehicle}｜聪明的回答，不止在屏幕里"
        pro30b_sub = f"{vehicle} × {keyword}｜AI级懂你"
    elif "future" in t:
        pro_15_sub = f"{vehicle}｜科技进化的下一个答案"
        pro30b_sub = f"{vehicle} × {keyword}｜未来，已来"
    elif "sport" in t:
        pro_15_sub = f"{vehicle}｜赛道基因，不需要解释"
        pro30b_sub = f"{vehicle} × {keyword}｜热血，是一种习惯"
    elif "family" in t:
        pro_15_sub = f"{vehicle}｜装得下责任，也装得下爱"
        pro30b_sub = f"{vehicle} × {keyword}｜守护，是最大的浪漫"
    elif "life" in t:
        pro_15_sub = f"{vehicle}｜好故事，从日常开始"
        pro30b_sub = f"{vehicle} × {keyword}｜生活，自有答案"
    else:
        pro_15_sub = f"{vehicle}｜不止于车，更是一种态度"
        pro30b_sub = f"{vehicle} × {keyword}｜{narrative}，一种新的表达"

    return {
        "hot_15_v": hot_15_v,
        "hot_15_s": hot_15_s,
        "veh_15_v": veh_15_v,
        "veh_15_sub": veh_15_sub,
        "veh_15_s": veh_15_s,
        "pro_15_v": pro_15_v,
        "pro_15_sub": pro_15_sub,
        "pro_15_s": pro_15_s,
        "hot20a_v": hot20a_v,
        "hot20a_s": hot20a_s,
        "hot20a_sub": hot20a_sub,
        "hot20b_v": hot20b_v,
        "hot20b_s": hot20b_s,
        "hot20b_sub": hot20b_sub,
        "veh20a_v": veh20a_v,
        "veh20a_s": veh20a_s,
        "veh20a_sub": veh20a_sub,
        "veh20b_v": veh20b_v,
        "veh20b_s": veh20b_s,
        "veh20b_sub": veh20b_sub,
        "pro20_v": pro20_v,
        "pro20_s": pro20_s,
        "pro20_sub": pro20_sub,
        "hot30a_v": hot30a_v,
        "hot30a_s": hot30a_s,
        "hot30a_sub": hot30a_sub,
        "hot30b_v": hot30b_v,
        "hot30b_s": hot30b_s,
        "hot30b_sub": hot30b_sub,
        "veh30a_v": veh30a_v,
        "veh30a_s": veh30a_s,
        "veh30a_sub": veh30a_sub,
        "veh30b_v": veh30b_v,
        "veh30b_s": veh30b_s,
        "veh30b_sub": veh30b_sub,
        "pro30a_v": pro30a_v,
        "pro30a_s": pro30a_s,
        "pro30a_sub": pro30a_sub,
        "pro30b_v": pro30b_v,
        "pro30b_s": pro30b_s,
        "pro30b_sub": pro30b_sub,
    }


def generate_video_script(topic: Dict, vehicle_key: str = None, angle: str = None) -> List[Dict]:
    """
    为单个内容角度生成 15s / 20s / 30s 视频分镜脚本。
    每版均采用三段式结构：热点解读 → 车型结合 → 产品图展示，
    并根据内容角度主题，生成差异化的画面、台词、音效。
    """
    if vehicle_key is None:
        vehicle_key = _best_vehicle_for_topic(topic)
    v = VEHICLES.get(vehicle_key, VEHICLES["雅阁"])
    keyword = _topic_keyword(topic["topic"])
    narrative = topic.get("叙事原型", "")
    emotion = topic.get("价值观/情绪", "")
    field = topic.get("领域/主题域", "")
    vehicle = v["name"]
    image0 = v["image"][0] if v["image"] else "品质"
    scene0 = v["scenes"][0] if v["scenes"] else "出行"
    positioning = v["positioning"]

    # 若未传入内容角度，自动生成一个兜底角度
    if angle is None:
        angles = generate_content_angles(
            topic_text=topic["topic"],
            vehicle_key=vehicle_key,
            topic_labels=topic,
            match_types=[],
            top_n=1,
        )
        angle = angles[0]["angle"] if angles else f"当{keyword}刷屏，{vehicle}用{image0}回应"

    themes = _detect_angle_themes(angle)
    p = _theme_pack(
        themes, keyword, field, emotion, vehicle, vehicle_key,
        image0, scene0, positioning, narrative, angle,
    )

    durations = [
        {
            "时长": "15秒",
            "内容角度": angle,
            "适合场景": "抖音/视频号信息流，前3秒抓眼，快速落版",
            "结构说明": "0-5秒 热点解读｜5-10秒 车型结合｜10-15秒 产品图展示",
            "acts": [
                {
                    "环节": "热点解读",
                    "shots": [
                        {
                            "镜号": 1,
                            "时长": "0-5秒",
                            "画面描述": p["hot_15_v"],
                            "台词/字幕": angle,
                            "音效/音乐": p["hot_15_s"],
                        }
                    ],
                },
                {
                    "环节": "车型结合",
                    "shots": [
                        {
                            "镜号": 2,
                            "时长": "5-10秒",
                            "画面描述": p["veh_15_v"],
                            "台词/字幕": p["veh_15_sub"],
                            "音效/音乐": p["veh_15_s"],
                        }
                    ],
                },
                {
                    "环节": "产品图展示",
                    "shots": [
                        {
                            "镜号": 3,
                            "时长": "10-15秒",
                            "画面描述": p["pro_15_v"],
                            "台词/字幕": p["pro_15_sub"],
                            "音效/音乐": p["pro_15_s"],
                        }
                    ],
                },
            ],
        },
        {
            "时长": "20秒",
            "内容角度": angle,
            "适合场景": "抖音/视频号/微博视频，情绪递进，留足产品展示时间",
            "结构说明": "0-6秒 热点解读｜6-13秒 车型结合｜13-20秒 产品图展示",
            "acts": [
                {
                    "环节": "热点解读",
                    "shots": [
                        {
                            "镜号": 1,
                            "时长": "0-3秒",
                            "画面描述": p["hot20a_v"],
                            "台词/字幕": p["hot20a_sub"],
                            "音效/音乐": p["hot20a_s"],
                        },
                        {
                            "镜号": 2,
                            "时长": "3-6秒",
                            "画面描述": p["hot20b_v"],
                            "台词/字幕": p["hot20b_sub"],
                            "音效/音乐": p["hot20b_s"],
                        },
                    ],
                },
                {
                    "环节": "车型结合",
                    "shots": [
                        {
                            "镜号": 3,
                            "时长": "6-10秒",
                            "画面描述": p["veh20a_v"],
                            "台词/字幕": p["veh20a_sub"],
                            "音效/音乐": p["veh20a_s"],
                        },
                        {
                            "镜号": 4,
                            "时长": "10-13秒",
                            "画面描述": p["veh20b_v"],
                            "台词/字幕": p["veh20b_sub"],
                            "音效/音乐": p["veh20b_s"],
                        },
                    ],
                },
                {
                    "环节": "产品图展示",
                    "shots": [
                        {
                            "镜号": 5,
                            "时长": "13-20秒",
                            "画面描述": p["pro20_v"],
                            "台词/字幕": p["pro20_sub"],
                            "音效/音乐": p["pro20_s"],
                        }
                    ],
                },
            ],
        },
        {
            "时长": "30秒",
            "内容角度": angle,
            "适合场景": "品牌官方账号、B站、视频号，完整叙事，可投流",
            "结构说明": "0-8秒 热点解读｜8-19秒 车型结合｜19-30秒 产品图展示",
            "acts": [
                {
                    "环节": "热点解读",
                    "shots": [
                        {
                            "镜号": 1,
                            "时长": "0-4秒",
                            "画面描述": p["hot30a_v"],
                            "台词/字幕": p["hot30a_sub"],
                            "音效/音乐": p["hot30a_s"],
                        },
                        {
                            "镜号": 2,
                            "时长": "4-8秒",
                            "画面描述": p["hot30b_v"],
                            "台词/字幕": p["hot30b_sub"],
                            "音效/音乐": p["hot30b_s"],
                        },
                    ],
                },
                {
                    "环节": "车型结合",
                    "shots": [
                        {
                            "镜号": 3,
                            "时长": "8-13秒",
                            "画面描述": p["veh30a_v"],
                            "台词/字幕": p["veh30a_sub"],
                            "音效/音乐": p["veh30a_s"],
                        },
                        {
                            "镜号": 4,
                            "时长": "13-19秒",
                            "画面描述": p["veh30b_v"],
                            "台词/字幕": p["veh30b_sub"],
                            "音效/音乐": p["veh30b_s"],
                        },
                    ],
                },
                {
                    "环节": "产品图展示",
                    "shots": [
                        {
                            "镜号": 5,
                            "时长": "19-24秒",
                            "画面描述": p["pro30a_v"],
                            "台词/字幕": p["pro30a_sub"],
                            "音效/音乐": p["pro30a_s"],
                        },
                        {
                            "镜号": 6,
                            "时长": "24-30秒",
                            "画面描述": p["pro30b_v"],
                            "台词/字幕": p["pro30b_sub"],
                            "音效/音乐": p["pro30b_s"],
                        },
                    ],
                },
            ],
        },
    ]

    # ---------- 重复度控制：画面描述 & 台词/字幕 重复度 < 10% ----------
    # 收集所有 shots 的引用和文本
    all_shots = []
    for d in durations:
        for act in d["acts"]:
            for shot in act["shots"]:
                all_shots.append(shot)

    # 去重画面描述
    visuals = [shot["画面描述"] for shot in all_shots]
    diversified_visuals = _diversify_texts(visuals, max_rate=0.1, max_iter=30)
    for shot, new_visual in zip(all_shots, diversified_visuals):
        shot["画面描述"] = new_visual

    # 去重台词/字幕；角度原文作为 intentional slogan，允许重复出现，不纳入去重
    # 同时忽略车型名与话题关键词，避免品牌一致性被误判为重复
    excluded_terms = [vehicle, keyword, vehicle_key] if vehicle_key else [vehicle, keyword]
    subs = [shot["台词/字幕"] for shot in all_shots]
    diversified_subs = _diversify_texts(
        subs, max_rate=0.1, max_iter=30, exclude_texts=[angle], excluded_terms=excluded_terms
    )
    for shot, new_sub in zip(all_shots, diversified_subs):
        if str(shot["台词/字幕"]).strip() != angle:
            shot["台词/字幕"] = new_sub

    return durations


def _flatten_video_script(scripts: List[Dict]) -> List[Dict]:
    """
    将结构化视频脚本拍平成旧版 DataFrame 格式，便于兼容展示。
    """
    flat = []
    for d in scripts:
        flat.append(
            {
                "时长": d["时长"],
                "内容角度": d["内容角度"],
                "适合场景": d["适合场景"],
                "结构说明": d["结构说明"],
                "镜号": "—",
                "环节": "—",
                "画面": "—",
                "台词/字幕": "—",
                "音效/音乐": "—",
            }
        )
        for act in d["acts"]:
            for shot in act["shots"]:
                flat.append(
                    {
                        "时长": d["时长"],
                        "内容角度": "",
                        "适合场景": "",
                        "结构说明": "",
                        "镜号": shot["镜号"],
                        "环节": act["环节"],
                        "画面": shot["画面描述"],
                        "台词/字幕": shot["台词/字幕"],
                        "音效/音乐": shot["音效/音乐"],
                    }
                )
    return flat


def generate_graphic_copies(topic: Dict, vehicle_key: str = None, angle: str = None) -> List[Dict]:
    """
    为单个图文/长图文内容角度，生成可直接发布的完整多平台文案。
    覆盖：微博、知乎、微信公众号、小红书。
    每个角度有独立的文案逻辑，避免同主题重复；文案中不出现「蹭热点」等负面表述。
    """
    if vehicle_key is None:
        vehicle_key = _best_vehicle_for_topic(topic)
    v = VEHICLES.get(vehicle_key, VEHICLES["雅阁"])
    keyword = _topic_keyword(topic["topic"])
    narrative = topic.get("叙事原型", "")
    emotion = topic.get("价值观/情绪", "")
    field = topic.get("领域/主题域", "")
    audience = topic.get("目标人群重合度", "")
    vehicle = v["name"]
    image0 = v["image"][0] if v["image"] else "品质"
    scene0 = v["scenes"][0] if v["scenes"] else "出行"
    positioning = v["positioning"]
    selling_points = v.get("image", ["品质"])
    selling_text = "、".join(selling_points[:3]) if len(selling_points) >= 3 else "、".join(selling_points)
    safe_keyword = keyword.replace(" ", "")

    if angle is None:
        angle = f"从{keyword}看{vehicle}：{image0}的另一种表达"

    # 角度类型判定（按特异性从高到低，避免“为什么……刚刚好”被误判为 why）
    angle_type = "default"
    if "守住" in angle or "别人" in angle or "不追" in angle:
        angle_type = "guard"
    elif "刚刚" in angle or "刚好" in angle or "正好" in angle or "恰逢" in angle:
        angle_type = "fit"
    elif "氛围" in angle or "氛围感" in angle or "情绪" in angle:
        angle_type = "atmosphere"
    elif "一天" in angle or "日常" in angle or "车主" in angle or "生活" in angle:
        angle_type = "life"
    elif "答案" in angle or "回应" in angle or "未来" in angle:
        angle_type = "answer"
    elif "为什么" in angle or "怎么" in angle or "如何" in angle:
        angle_type = "why"

    # 主题词库（只用于配图/标签/氛围，不主导文案结构）
    themes = _detect_angle_themes(angle)
    t = set(themes)
    if "space" in t:
        theme_tag_line = "航天探索"
        theme_visual = "星空、火箭尾焰、轿跑车身、智能座舱"
        base_tags = "#航天 #探索 #未来出行"
    elif "ai" in t:
        theme_tag_line = "智能科技"
        theme_visual = "数字界面、语音助手、HUD、车灯细节"
        base_tags = "#AI #智能座舱 #科技出行"
    elif "sport" in t:
        theme_tag_line = "运动驾趣"
        theme_visual = "过弯姿态、运动套件、仪表盘、方向盘"
        base_tags = "#驾驶乐趣 #运动基因 #热血"
    elif "family" in t:
        theme_tag_line = "家庭守护"
        theme_visual = "家人、大空间、安全配置、夕阳街道"
        base_tags = "#家庭出行 #守护 #责任"
    elif "life" in t:
        theme_tag_line = "生活方式"
        theme_visual = "城市街角、咖啡、通勤、真实日常"
        base_tags = "#日常 #生活方式 #稳稳的幸福"
    else:
        theme_tag_line = narrative if narrative else "车型热点"
        theme_visual = f"{field}氛围、{scene0}、{image0}细节"
        base_tags = f"#{field} #{narrative} #汽车品牌"

    # 卖点强调句（按角度类型 + 平台差异化，避免跨平台重复）
    if angle_type == "why":
        selling_claims = [
            f"{vehicle}的{selling_text}，恰好能回应{keyword}背后的{narrative}。",
            f"从{selling_text}来看，{vehicle}和{keyword}指向的是同一种{narrative}。",
            f"{vehicle}没有解释自己为什么出现，它只是用{selling_text}给出了回应。",
            f"当{keyword}点燃好奇，{vehicle}的{selling_text}正好承接了这份追问。",
        ]
    elif angle_type == "guard":
        selling_claims = [
            f"当外界被{keyword}吸引，{vehicle}选择用{selling_text}守住自己的节奏——不喧哗，自有声。",
            f"{vehicle}没有跟进{keyword}的喧嚣，而是回到{scene0}，用{selling_text}稳住自己的表达。",
            f"热闹是别人的，{vehicle}只负责用{selling_text}把{scene0}做好。",
            f"在{keyword}的讨论里，{vehicle}选择用{selling_text}守好自己的位置。",
        ]
    elif angle_type == "fit":
        selling_claims = [
            f"{keyword}的火，和{vehicle}的{selling_text}相遇，不早不晚，刚刚好。",
            f"{keyword}需要的不是追逐，而是一个刚好能装下它的产品——比如{vehicle}的{selling_text}。",
            f"{vehicle}的{selling_text}，让{keyword}的{emotion}有了一个具体的落点。",
            f"不是{vehicle}蹭上了{keyword}，而是{selling_text}刚好接住了这份情绪。",
        ]
    elif angle_type == "atmosphere":
        selling_claims = [
            f"{keyword}的{emotion}，被{vehicle}的{selling_text}转化成可触摸的{scene0}氛围。",
            f"坐进{vehicle}，{keyword}带来的{emotion}就落在了{selling_text}的细节里。",
            f"{vehicle}用{selling_text}，把{keyword}的{emotion}铺进了{scene0}的每一寸空间。",
            f"{keyword}是情绪的入口，{vehicle}的{selling_text}是氛围的落点。",
        ]
    elif angle_type == "life":
        selling_claims = [
            f"{keyword}是当下的热闹，{vehicle}的{selling_text}是日子里的确定感。",
            f"一周后{keyword}可能淡出，但{vehicle}的{selling_text}会继续陪在{scene0}里。",
            f"对日常来说，{vehicle}的{selling_text}比{keyword}更持久。",
            f"{keyword}会过去，{vehicle}用{selling_text}把日子拉回它本来的样子。",
        ]
    elif angle_type == "answer":
        selling_claims = [
            f"{keyword}提出了问题，{vehicle}用{selling_text}给出了自己的回答。",
            f"关于{narrative}，{vehicle}的{selling_text}就是它的答案。",
            f"{vehicle}没有停留在概念，而是用{selling_text}把回答写进了{scene0}。",
            f"{keyword}问的是趋势，{vehicle}用{selling_text}答的是体验。",
        ]
    else:
        selling_claims = [
            f"{vehicle}的{selling_text}，让它和{keyword}之间产生了一种自然的连接。",
            f"{keyword}和{vehicle}的{selling_text}之间，有一种不需要解释的契合。",
            f"当{keyword}成为情绪，{vehicle}用{selling_text}给出了自己的表达。",
            f"{vehicle}没有追逐{keyword}，它的{selling_text}本就在回应同一种情绪。",
        ]

    # ---------------- 微博 ----------------
    if angle_type == "why":
        weibo_body = (
            f"为什么{keyword}会让{vehicle}被重新看见？\n\n"
            f"因为{vehicle}的{selling_text}，"
            f"本就和{keyword}背后的{narrative}同频。\n\n"
            f"{selling_claims[0]}\n\n"
            f"这不是强行关联，而是产品力本身就在回应同一种情绪。"
        )
    elif angle_type == "guard":
        weibo_body = (
            f"别人都在聊{keyword}，{vehicle}在做什么？\n\n"
            f"它没有跟着喧哗，而是回到自己最熟悉的{scene0}，"
            f"用{selling_text}守住一份稳定。\n\n"
            f"{selling_claims[0]}\n\n"
            f"真正的品牌表达，从来不需要大声。"
        )
    elif angle_type == "fit":
        weibo_body = (
            f"{keyword}火了，{vehicle}为什么刚刚好？\n\n"
            f"因为{vehicle}的{selling_text}，恰好能装下这份{emotion}。\n\n"
            f"{selling_claims[0]}\n\n"
            f"热闹会过去，但好的产品力不会。"
        )
    elif angle_type == "atmosphere":
        weibo_body = (
            f"{keyword}的{emotion}，{vehicle}怎么呈现？\n\n"
            f"不是简单同框，而是把{emotion}融进{scene0}的每一处细节。\n\n"
            f"{selling_claims[0]}\n\n"
            f"坐进车里，氛围就对了。"
        )
    elif angle_type == "life":
        weibo_body = (
            f"{keyword}之后，{vehicle}的一天怎么过？\n\n"
            f"照常好。{selling_text}，让它在喧嚣之外依然值得被选择。\n\n"
            f"{selling_claims[0]}\n\n"
            f"日子不是话题堆出来的，是一辆好车陪出来的。"
        )
    elif angle_type == "answer":
        weibo_body = (
            f"{keyword}之后，{vehicle}的{image0}是什么答案？\n\n"
            f"是{selling_text}的集合，是{positioning}对{narrative}的回应。\n\n"
            f"{selling_claims[0]}\n\n"
            f"答案不在口号里，在每一次出发里。"
        )
    else:
        weibo_body = (
            f"{keyword}刷屏，{vehicle}给出了一个自己的表达。\n\n"
            f"{selling_claims[0]}\n\n"
            f"好的表达，不是追逐，而是自然发生。"
        )

    weibo_copy = (
        f"【{vehicle} × {keyword}｜{theme_tag_line}】\n\n"
        f"{weibo_body}\n\n"
        f"配图建议：{theme_visual}画面3张 + {vehicle} {scene0}场景图4张 + 外观/内饰特写2张\n\n"
        f"#{safe_keyword}# #{vehicle_key}# #广本车型热点匹配# {base_tags}"
    )

    # ---------------- 知乎 ----------------
    if angle_type == "why":
        zhihu_body = (
            f"{keyword}火了，{vehicle}为什么会被提到？\n\n"
            f"表面上看是一次话题与车型的相遇，本质上是因为{vehicle}的{selling_text}，"
            f"和{keyword}所代表的{narrative}高度契合。对{audience}来说，"
            f"{vehicle}不是突然出现的选择，而是当{emotion}被激发时，自然浮现在脑海里的答案。\n\n"
            f"{selling_claims[1]}\n\n"
            f"所以，{vehicle}回应的不是{keyword}本身，而是{keyword}背后那群人和那种情绪。"
        )
    elif angle_type == "guard":
        zhihu_body = (
            f"当{keyword}成为公共话题，品牌该不该跟？\n\n"
            f"{vehicle}给了一个不一样的示范：它选择守住自己的{scene0}，"
            f"用{selling_text}去回应，而不是被讨论牵着走。对{audience}来说，"
            f"这种稳定感本身就是一种价值。\n\n"
            f"{selling_claims[1]}\n\n"
            f"真正打动人的品牌表达，往往发生在喧嚣之外。"
        )
    elif angle_type == "fit":
        zhihu_body = (
            f"为什么说{keyword}和{vehicle}刚刚好？\n\n"
            f"因为{keyword}唤起的{emotion}，需要一个具体的产品来承接。"
            f"{vehicle}作为{positioning}，它的{selling_text}正好提供了这个落点。\n\n"
            f"{selling_claims[1]}\n\n"
            f"好的品牌沟通，不是硬要把两个东西绑在一起，而是让观众自己觉得：这就是它。"
        )
    elif angle_type == "atmosphere":
        zhihu_body = (
            f"氛围感这件事，怎么才能落到实处？\n\n"
            f"{keyword}给了我们一个{emotion}的入口，而{vehicle}用{selling_text}，"
            f"把这种情绪延伸到了{scene0}的每一个细节里。\n\n"
            f"{selling_claims[1]}\n\n"
            f"对{audience}来说，坐进{vehicle}的那一刻，{keyword}就不再只是屏幕上的话题，"
            f"而是一种可以被体验的氛围。"
        )
    elif angle_type == "life":
        zhihu_body = (
            f"热闹之外，{vehicle}的日常价值是什么？\n\n"
            f"{keyword}可能会在一周后淡出讨论，但{audience}对{scene0}的需求不会变。"
            f"{vehicle}的{selling_text}，正是在这些日常里建立信任的地方。\n\n"
            f"{selling_claims[1]}\n\n"
            f"一辆好车不会只活在热闹里，它活在每一次平顺的起步、每一次安心的抵达里。"
        )
    elif angle_type == "answer":
        zhihu_body = (
            f"{keyword}提出了一个关于{narrative}的问题，{vehicle}的回答是什么？\n\n"
            f"它的回答是{selling_text}。作为{positioning}，"
            f"{vehicle}没有停留在口号，而是把这些产品力放进了{scene0}的真实体验中。\n\n"
            f"{selling_claims[1]}\n\n"
            f"所以，当{audience}在思考「这个时代需要一辆什么样的车」时，"
            f"{vehicle}已经用行动给出了答案。"
        )
    else:
        zhihu_body = (
            f"如何评价{keyword}与{vehicle}的关联？\n\n"
            f"{keyword}是一个关于{narrative}的社会情绪，而{vehicle}的{selling_text}，"
            f"恰好能和这个情绪产生真实的对话。对{audience}来说，"
            f"{vehicle}不是追逐潮流的工具，而是{emotion}的落点。\n\n"
            f"{selling_claims[1]}"
        )

    zhihu_copy = (
        f"{angle}\n\n"
        f"{zhihu_body}\n\n"
        f"#{safe_keyword}# #{vehicle_key}# #汽车营销#"
    )

    # ---------------- 微信公众号 ----------------
    if angle_type == "why":
        section1 = f"{keyword}刷屏，很多人都在问：这和{vehicle}有什么关系？答案是：{vehicle}的{selling_text}，本就和{keyword}背后的{narrative}同频。"
        section2 = f"对{audience}来说，{vehicle}不是 suddenly 出现的选择。当{emotion}被激发，他们会自然地想到一辆{positioning}。"
        section3 = f"{selling_claims[2]}"
        section4 = f"所以{vehicle}回应的不是{keyword}本身，而是{keyword}背后的那群人，以及他们对{narrative}的真实渴望。"
    elif angle_type == "guard":
        section1 = f"{keyword}很热闹，但{vehicle}选择不慌不忙。它回到自己最熟悉的{scene0}，用{selling_text}守住自己的节奏。"
        section2 = f"对{audience}来说，热闹之外，更重要的是稳定。{vehicle}作为{positioning}，它的价值从来不靠喧哗证明。"
        section3 = f"{selling_claims[2]}"
        section4 = f"真正的品牌表达，不需要追逐每一次讨论。{vehicle}相信，产品力本身就是最好的回应。"
    elif angle_type == "fit":
        section1 = f"{keyword}火了，{vehicle}刚刚好。不是刻意，而是{vehicle}的{selling_text}，恰好能装下这份{emotion}。"
        section2 = f"对{audience}而言，{positioning}的出现，让{keyword}从一个屏幕上的话题，变成了一种可以被体验的感觉。"
        section3 = f"{selling_claims[2]}"
        section4 = f"热闹会过去，但{vehicle}的{selling_text}会继续陪着你，从讨论走回日常。"
    elif angle_type == "atmosphere":
        section1 = f"{keyword}给了我们一种{emotion}的氛围，而{vehicle}把这种氛围延伸到了{scene0}里。"
        section2 = f"对{audience}来说，坐进{vehicle}的那一刻，{keyword}不再是遥远的屏幕内容，而是触手可及的空间感受。"
        section3 = f"{selling_claims[2]}"
        section4 = f"好的氛围，不只是视觉，更是产品力带来的安心与愉悦。"
    elif angle_type == "life":
        section1 = f"{keyword}刷屏的时候，{vehicle}的车主可能正在{scene0}。讨论会过去，但日子照常好。"
        section2 = f"对{audience}来说，{vehicle}的{selling_text}，是生活里不需要解释的确定性。"
        section3 = f"{selling_claims[2]}"
        section4 = f"一辆好车的价值，从不取决于它是否被热议，而取决于它是否出现在你需要它的每一次出发里。"
    elif angle_type == "answer":
        section1 = f"{keyword}让很多人开始思考{narrative}。{vehicle}用{selling_text}，给出了自己的回答。"
        section2 = f"作为{positioning}，{vehicle}没有停留在概念，而是把产品力放进了{scene0}的真实体验中。"
        section3 = f"{selling_claims[2]}"
        section4 = f"答案不在口号里，在每一次踩下电门、每一次智能交互、每一次安全抵达里。"
    else:
        section1 = f"{keyword}刷屏，{vehicle}用自己的方式回应了它。"
        section2 = f"对{audience}来说，{vehicle}的{selling_text}，让{keyword}的{emotion}有了具体的落点。"
        section3 = f"{selling_claims[2]}"
        section4 = f"从产品到体验，{vehicle}都在做同一件事：让好的出行，自然发生。"

    wechat_copy = (
        f"{angle}\n\n"
        f"文／广汽本田\n\n"
        f"{keyword}刷屏。\n\n"
        f"01 ｜ {keyword}与{vehicle}\n"
        f"{section1}\n\n"
        f"02 ｜ 关于{audience}\n"
        f"{section2}\n\n"
        f"03 ｜ 产品力，是底气\n"
        f"{section3}\n\n"
        f"04 ｜ 写在最后\n"
        f"{section4}\n\n"
        f"——\n"
        f"【互动话题】你怎么看{keyword}与{vehicle}的关联？欢迎在评论区留言。\n\n"
        f"预约试驾{vehicle}，到店感受{selling_text}。\n"
        f"（文末插入{vehicle}高清外观图 / 智能座舱细节 / 核心配置表 / 试驾预约二维码）"
    )

    # ---------------- 小红书 ----------------
    if angle_type == "why":
        xhs_body = (
            f"🌟 为什么{keyword}会让{vehicle}被看见？\n"
            f"因为{vehicle}的{selling_text}，本就和{keyword}背后的{narrative}同频。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}\n\n"
            f"💡 它回应的不是话题本身，是{emotion}。"
        )
    elif angle_type == "guard":
        xhs_body = (
            f"🌟 别人聊{keyword}，{vehicle}在做什么？\n"
            f"守住自己的{scene0}，用{selling_text}稳稳回应。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}\n\n"
            f"💡 不喧哗，自有声。"
        )
    elif angle_type == "fit":
        xhs_body = (
            f"🌟 {keyword}火了，{vehicle}为什么刚刚好？\n"
            f"因为{selling_text}，恰好能装下这份{emotion}。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}\n\n"
            f"💡 不早不晚，就是这种感觉。"
        )
    elif angle_type == "atmosphere":
        xhs_body = (
            f"🌟 {keyword}的{emotion}，{vehicle}怎么呈现？\n"
            f"把它融进{scene0}的每一处细节里。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}\n\n"
            f"💡 坐进车里，氛围就对了。"
        )
    elif angle_type == "life":
        xhs_body = (
            f"🌟 {keyword}之后，{vehicle}的一天怎么过？\n"
            f"照常好。{selling_text}，让日子稳稳地继续。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}\n\n"
            f"💡 讨论会过去，好车不会。"
        )
    elif angle_type == "answer":
        xhs_body = (
            f"🌟 {keyword}之后，{vehicle}的答案是什么？\n"
            f"{selling_text}，全写进{scene0}的体验里。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}\n\n"
            f"💡 答案不在口号里，在每一次出发里。"
        )
    else:
        xhs_body = (
            f"🌟 {keyword}刷屏，{vehicle}怎么回应？\n"
            f"用{selling_text}，给出自己的表达。\n\n"
            f"🚗 {vehicle}的底气\n"
            f"{selling_claims[3]}"
        )

    xhs_copy = (
        f"{keyword}刷屏，但{vehicle}这波让我悟了✨\n\n"
        f"姐妹们/兄弟们，{keyword}真的{emotion}了！\n"
        f"但最让我惊喜的是，{vehicle}的{scene0}和这个话题居然这么搭。\n\n"
        f"{xhs_body}\n\n"
        f"📸 拍摄 tips\n"
        f"1️⃣ 封面：{vehicle}轿跑外观与{keyword}元素拼贴\n"
        f"2️⃣ 内页：{scene0}氛围图 + 智能座舱/驾控细节特写\n"
        f"3️⃣ 文案卡：预约试驾，感受{selling_text}\n\n"
        f"#{vehicle_key} #{safe_keyword} #汽车生活 #{emotion}出行 #{narrative} {base_tags} #广本"
    )

    copies = [
        {
            "平台": "微博",
            "形式": "短图文 / 九宫格 thread",
            "文案": weibo_copy,
            "话题标签": f"#{safe_keyword}# #{vehicle_key}# #广本车型热点匹配# {base_tags}",
            "配图建议": f"九宫格：{theme_visual}画面3张 + {vehicle} {scene0}场景图4张 + 外观/内饰特写2张",
        },
        {
            "平台": "知乎",
            "形式": "回答 / 深度讨论",
            "文案": zhihu_copy,
            "话题标签": f"#{safe_keyword}# #{vehicle_key}# #汽车营销#",
            "配图建议": f"信息长图1张：{keyword}与{vehicle}核心卖点（{selling_text}）对照；或3-5张{scene0}场景图",
        },
        {
            "平台": "微信公众号",
            "形式": "长图文",
            "文案": wechat_copy,
            "话题标签": f"广本{vehicle_key}｜{keyword}｜{emotion}出行",
            "配图建议": f"封面：{vehicle}轿跑外观与{keyword}符号化拼贴；内页：外观全景+智能座舱+{scene0}场景+核心卖点（{selling_text}）图解",
        },
        {
            "平台": "小红书",
            "形式": "图文笔记",
            "文案": xhs_copy,
            "话题标签": f"#{vehicle_key} #{safe_keyword} #汽车生活 #{emotion}出行 {base_tags}",
            "配图建议": f"封面：{vehicle}轿跑外观与{keyword}元素拼贴；内页：{scene0}氛围图+外观/智能/驾控细节特写+金句卡",
        },
    ]

    # ---------- 重复度控制：各平台文案重复度 < 10% ----------
    # 角度原文作为标题/Slogan 允许重复出现，不纳入去重
    copy_texts = [c["文案"] for c in copies]
    excluded_terms = [vehicle, keyword, vehicle_key]
    diversified_copy_texts = _diversify_texts(
        copy_texts,
        max_rate=0.1,
        max_iter=30,
        exclude_texts=[angle],
        threshold=0.7,
        excluded_terms=excluded_terms,
    )
    for c, new_text in zip(copies, diversified_copy_texts):
        c["文案"] = new_text

    return copies


def generate_platform_copies(topic: Dict, vehicle_key: str = None) -> List[Dict]:
    """生成抖音、微博、小红书三平台发布文案（默认角度，保持兼容）"""
    if vehicle_key is None:
        vehicle_key = _best_vehicle_for_topic(topic)
    v = VEHICLES.get(vehicle_key, VEHICLES["雅阁"])
    keyword = _topic_keyword(topic["topic"])
    narrative = topic.get("叙事原型", "")
    emotion = topic.get("价值观/情绪", "")
    vehicle = v["name"]
    image0 = v["image"][0] if v["image"] else "品质"
    scene0 = v["scenes"][0] if v["scenes"] else "出行"

    copies = [
        {
            "平台": "抖音",
            "形式": "短视频",
            "文案": f"当{keyword}刷屏，{vehicle}车主的{scene0}有了新的故事。#广本{vehicle_key} #{keyword} #{emotion}出行",
            "话题标签": f"#{vehicle_key} #{keyword.replace(' ', '')} #{narrative} #广本",
            "配图建议": f"15-30秒短视频，前3秒用{keyword}讨论画面抓眼，中段切{vehicle} {scene0}",
        },
        {
            "平台": "微博",
            "形式": "图文",
            "文案": f"【{vehicle} × {keyword}】{narrative}的另一种表达，也许就是{image0}。你怎么看？",
            "话题标签": f"#{keyword}# #{vehicle_key}# #广本车型热点匹配#",
            "配图建议": f"九宫格：话题现场图2张 + {vehicle} {scene0}场景图5张 + 车型特写2张",
        },
        {
            "平台": "小红书",
            "形式": "图文笔记",
            "文案": f"姐妹们/兄弟们，{keyword}真的{emotion}了！{vehicle}的{scene0}让我瞬间get到{image0}，这种关联我悟了✨",
            "话题标签": f"#{vehicle_key} #{keyword.replace(' ', '')} #汽车生活 #{emotion}出行",
            "配图建议": f"封面：{vehicle}与{keyword}元素拼贴；内页：{scene0}氛围图+细节特写",
        },
    ]

    # ---------- 重复度控制：各平台文案重复度 < 10% ----------
    copy_texts = [c["文案"] for c in copies]
    excluded_terms = [vehicle, keyword, vehicle_key]
    diversified_copy_texts = _diversify_texts(
        copy_texts,
        max_rate=0.1,
        max_iter=30,
        threshold=0.7,
        excluded_terms=excluded_terms,
    )
    for c, new_text in zip(copies, diversified_copy_texts):
        c["文案"] = new_text

    return copies


def generate_visual_guide(topic: Dict, vehicle_key: str = None) -> Dict:
    """生成配图/视觉风格建议"""
    if vehicle_key is None:
        vehicle_key = _best_vehicle_for_topic(topic)
    v = VEHICLES.get(vehicle_key, VEHICLES["雅阁"])
    keyword = _topic_keyword(topic["topic"])
    emotion = topic.get("价值观/情绪", "")
    field = topic.get("领域/主题域", "")
    narrative = topic.get("叙事原型", "")

    tone_map = {
        "好奇心": "科技感、未来感、星空/城市夜景",
        "自豪感": "大国重器风、红金配色、城市天际线",
        "焦虑感": "低饱和、城市灰、车窗倒影、孤独但不丧",
        "治愈感": "暖色调、自然光、家庭/露营场景",
        "热血": "高对比、运动轨迹、速度线、汗水",
        "共鸣": "生活化、真实场景、普通人面孔",
        "幽默": "高饱和、表情包式构图、反差萌",
        "争议": "慎用，建议改为安全角度的讨论图",
        "希望": "逆光、日出、道路延伸、温暖光线",
        "安全感": "稳定构图、家庭特写、大空间内饰",
    }

    return {
        "主视觉风格": tone_map.get(emotion, "简洁大气，突出车型与热点元素"),
        "推荐配色": _color_for_emotion(emotion),
        "画面元素": [
            f"{v['name']} 车型主体（占画面 40%-60%）",
            f"{keyword} 符号化元素（如文字、icon、场景剪影）",
            f"{field} 领域氛围背景",
        ],
        "拍摄/设计建议": [
            f"用 {narrative} 的叙事基调组织画面节奏",
            f"把 {v['image'][0] if v['image'] else '车型'} 作为情绪落点",
            "避免直接使用争议人物/事件肖像，使用符号化表达",
            "视频前3秒必须出现热点关键词或画面，降低跳出率",
        ],
    }


def _color_for_emotion(emotion: str) -> str:
    mapping = {
        "好奇心": "深蓝 + 橙色点缀",
        "自豪感": "中国红 + 金色",
        "焦虑感": "灰蓝 + 暖黄一束光",
        "治愈感": "米白 + 暖绿",
        "热血": "黑红 + 高对比白",
        "共鸣": "自然光肤色 + 城市灰",
        "幽默": "亮黄 + 荧光绿",
        "希望": "晨曦金 + 天空蓝",
        "安全感": "深灰 + 暖棕",
    }
    return mapping.get(emotion, "品牌橙 + 白")


def generate_topic_playbook(
    topic: Dict,
    vehicle_key: str = None,
    classified_angles: Dict[str, List[Dict]] = None,
) -> Dict:
    """
    生成完整的内容演绎方案。
    如果传入 classified_angles（含 video / graphic 两类），
    则为每个视频角度生成 15s/20s/30s 分镜，为每个图文角度生成多平台文案。
    """
    if vehicle_key is None:
        vehicle_key = _best_vehicle_for_topic(topic)

    if classified_angles is None:
        # 保持旧版行为：只生成默认的一套视频脚本 + 平台文案
        return {
            "推荐车型": vehicle_key,
            "视频脚本": { "默认": generate_video_script(topic, vehicle_key) },
            "平台文案": { "默认": generate_platform_copies(topic, vehicle_key) },
            "视觉建议": generate_visual_guide(topic, vehicle_key),
        }

    video_angles = classified_angles.get("video", [])
    graphic_angles = classified_angles.get("graphic", [])

    video_scripts = {}
    for i, va in enumerate(video_angles, start=1):
        label = f"角度{i}：{va['angle']}"
        video_scripts[label] = generate_video_script(
            topic, vehicle_key, angle=va["angle"]
        )

    # ---------- 跨角度画面描述重复度控制规则 ----------
    # 规则目标：任意热点 × 任意车型生成的多个视频角度，其所有 shots 的画面描述
    # 之间的重复度必须低于 5%，且不允许出现完全相同的画面描述。
    #
    # 实现方式：
    # 1. 先由 _theme_pack 根据内容角度主题做「根上差异化」（如 sport 主题下再分 champion/challenge/modify/youth/track）；
    # 2. 再在 generate_topic_playbook 层面对全部 angles / durations / shots 的画面描述
    #    做一次全局去重兜底（_global_diversify_visuals），强制把跨角度重复度压下去；
    # 3. 该规则对所有热点、所有车型通用生效，不依赖具体案例。
    all_visual_refs = []  # (label, duration_idx, act_idx, shot_idx)
    all_visuals = []
    for label, scripts in video_scripts.items():
        for d_idx, d in enumerate(scripts):
            for a_idx, act in enumerate(d["acts"]):
                for s_idx, shot in enumerate(act["shots"]):
                    all_visual_refs.append((label, d_idx, a_idx, s_idx))
                    all_visuals.append(shot["画面描述"])

    if len(all_visuals) >= 2:
        vehicle = VEHICLES.get(vehicle_key, VEHICLES["雅阁"])["name"]
        keyword = _topic_keyword(topic["topic"])
        diversified_visuals = _global_diversify_visuals(
            all_visuals,
            threshold=0.30,
            max_rate=0.03,
            max_iter=40,
            excluded_terms=[vehicle, keyword, vehicle_key] if vehicle_key else [vehicle, keyword],
        )
        for (label, d_idx, a_idx, s_idx), new_visual in zip(all_visual_refs, diversified_visuals):
            video_scripts[label][d_idx]["acts"][a_idx]["shots"][s_idx]["画面描述"] = new_visual

    graphic_copies = {}
    for i, ga in enumerate(graphic_angles, start=1):
        label = f"角度{i}：{ga['angle']}"
        graphic_copies[label] = generate_graphic_copies(
            topic, vehicle_key, angle=ga["angle"]
        )

    return {
        "推荐车型": vehicle_key,
        "视频脚本": video_scripts,
        "平台文案": graphic_copies,
        "视觉建议": generate_visual_guide(topic, vehicle_key),
    }
