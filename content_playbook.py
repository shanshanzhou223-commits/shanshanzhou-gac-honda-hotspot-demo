"""
热点内容演绎 playbook：根据热点 B库标签生成可直接落地的内容方案
"""
from typing import Dict, List

from data import VEHICLES, NARRATIVE_VEHICLE_MAP, AUDIENCE_VEHICLE_MAP


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


def _topic_keyword(topic_text: str, max_len: int = 12) -> str:
    """提取话题关键词"""
    t = topic_text.strip()
    if len(t) > max_len:
        return t[:max_len] + "…"
    return t


def generate_video_script(topic: Dict, vehicle_key: str = None) -> List[Dict]:
    """生成 15s / 30s / 60s 视频分镜脚本"""
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

    # 根据叙事原型选择 hook 模板
    hook_templates = {
        "探索突破": f"当所有人都在仰望{keyword}，{vehicle}想带你去更远的地方。",
        "挑战极限": f"{keyword}在挑战极限，{vehicle}也在挑战每一次出发。",
        "创新颠覆": f"{keyword}重新定义了未来，{vehicle}重新定义了出行。",
        "成长蜕变": f"{keyword}背后，是一个成年人咬牙向上的样子。{vehicle}懂。",
        "责任守护": f"{keyword}让人想守住重要的人。{vehicle}，装得下这份责任。",
        "自由逃离": f"当{keyword}刷屏，你是不是也想逃向远方？{vehicle}可以。",
        "团聚归属": f"{keyword}最好的结局，是和家人一起出发。{vehicle}刚好。",
        "抗争反叛": f"{keyword}是在说：我不服。{vehicle}也是。",
        "怀旧回归": f"{keyword}带我们回到过去，{vehicle}带我们去更好的未来。",
        "幽默解构": f"{keyword}火了。{vehicle}车主：这我熟。",
    }
    hook = hook_templates.get(narrative, f"{keyword}刷屏了，{vehicle}怎么接？")

    scripts = [
        {
            "时长": "15秒",
            "镜号": 1,
            "画面": f"{keyword}相关画面快速切入，转场至{vehicle}行驶镜头",
            "台词/字幕": hook,
            "音效": "节奏鼓点 + 引擎启动声",
        },
        {
            "时长": "15秒",
            "镜号": 2,
            "画面": f"{vehicle} {scene0}特写，突出{image0}",
            "台词/字幕": f"{vehicle} · {image0}，和{keyword}一样值得被看见",
            "音效": "音乐渐强，落版音效",
        },
        {
            "时长": "30秒",
            "镜号": 1,
            "画面": f"热点画面/网络素材混剪：{keyword}",
            "台词/字幕": f"最近，{keyword}火了。",
            "音效": "社交媒体通知音效叠加",
        },
        {
            "时长": "30秒",
            "镜号": 2,
            "画面": f"车主日常场景：{scene0}",
            "台词/字幕": hook,
            "音效": "背景音乐进入主歌",
        },
        {
            "时长": "30秒",
            "镜号": 3,
            "画面": f"{vehicle}外观 + 内饰细节混剪",
            "台词/字幕": f"{vehicle}，{image0}，不蹭热度，只讲好故事。",
            "音效": "节奏鼓点",
        },
        {
            "时长": "60秒",
            "镜号": 1,
            "画面": f"开场钩子：{keyword}刷屏瞬间",
            "台词/字幕": f"你有没有发现，{keyword}正在改变我们的情绪？",
            "音效": "悬念音效",
        },
        {
            "时长": "60秒",
            "镜号": 2,
            "画面": "路人采访/网友评论快速闪现",
            "台词/字幕": f"有人说{emotion}，有人说这就是生活。",
            "音效": "键盘敲击、消息提示",
        },
        {
            "时长": "60秒",
            "镜号": 3,
            "画面": f"{vehicle}车主故事：{scene0}场景",
            "台词/字幕": hook,
            "音效": "情绪音乐起",
        },
        {
            "时长": "60秒",
            "镜号": 4,
            "画面": f"{vehicle}产品点展示：{image0}",
            "台词/字幕": f"{vehicle}用{image0}，接住这份{emotion}。",
            "音效": "音乐推向高潮",
        },
        {
            "时长": "60秒",
            "镜号": 5,
            "画面": "车尾/车标落版，slogan",
            "台词/字幕": f"{vehicle} × {keyword}｜不止于车，更是一种态度",
            "音效": "落版音效",
        },
    ]
    return scripts


def generate_platform_copies(topic: Dict, vehicle_key: str = None) -> List[Dict]:
    """生成抖音、微博、小红书三平台发布文案"""
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
            "文案": f"当{keyword}刷屏，{vehicle}车主的{scene0}有了新的故事。#广本{vehicle_key} #{keyword} #{emotion}出行",
            "话题标签": f"#{vehicle_key} #{keyword.replace(' ', '')} #{narrative} #广本",
            "配图/视频建议": f"15-30秒短视频，前3秒用{keyword}热点画面抓眼，中段切{vehicle} {scene0}",
        },
        {
            "平台": "微博",
            "文案": f"【{vehicle} × {keyword}】{narrative}的另一种表达，也许就是{image0}。你怎么看？",
            "话题标签": f"#{keyword}# #{vehicle_key}# #广本车型热点匹配#",
            "配图/视频建议": f"九宫格：热点现场图2张 + {vehicle} {scene0}场景图5张 + 车型特写2张",
        },
        {
            "平台": "小红书",
            "文案": f"姐妹们/兄弟们，{keyword}真的{emotion}了！{vehicle}的{scene0}让我瞬间get到{image0}，这波联名我悟了✨",
            "话题标签": f"#{vehicle_key} #{keyword.replace(' ', '')} #汽车生活 #{emotion}出行",
            "配图/视频建议": f"封面：{vehicle}与{keyword}元素拼贴；内页：{scene0}氛围图+细节特写",
        },
    ]
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
            "避免直接蹭争议人物/事件肖像，使用符号化表达",
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


def generate_topic_playbook(topic: Dict, vehicle_key: str = None) -> Dict:
    """生成完整的内容演绎方案"""
    if vehicle_key is None:
        vehicle_key = _best_vehicle_for_topic(topic)
    return {
        "推荐车型": vehicle_key,
        "视频脚本": generate_video_script(topic, vehicle_key),
        "平台文案": generate_platform_copies(topic, vehicle_key),
        "视觉建议": generate_visual_guide(topic, vehicle_key),
    }
