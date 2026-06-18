"""
热点内容演绎 playbook：根据热点 B库标签生成可直接落地的内容方案
"""
from typing import Dict, List

from angles import generate_content_angles
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
    """
    生成 15s / 20s / 30s 视频分镜脚本。
    每版均采用三段式结构：热点解读 → 车型结合 → 产品图展示，
    并明确对应一个内容角度，分镜画面具体到景别、镜头、元素、光影。
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

    # 取前 3 个内容角度，分别作为 15s / 20s / 30s 的核心创意
    angles = generate_content_angles(
        topic_text=topic["topic"],
        vehicle_key=vehicle_key,
        topic_labels=topic,
        match_types=[],
        top_n=3,
    )
    # 兜底角度
    if len(angles) < 3:
        default_angle = f"当{keyword}刷屏，{vehicle}用{image0}回应"
        while len(angles) < 3:
            angles.append(
                {
                    "angle": default_angle,
                    "type": "短视频",
                    "platform": "抖音 / 视频号",
                    "source": "兜底",
                }
            )

    # 各时长三段式分镜模板
    durations = [
        {
            "时长": "15秒",
            "内容角度": angles[0]["angle"],
            "适合场景": "抖音/视频号信息流，前3秒抓眼，快速落版",
            "结构说明": "0-5秒 热点解读｜5-10秒 车型结合｜10-15秒 产品图展示",
            "acts": [
                {
                    "环节": "热点解读",
                    "shots": [
                        {
                            "镜号": 1,
                            "时长": "0-5秒",
                            "画面描述": (
                                f"【全景+快速推进】热点关键词「{keyword}」以大字动画从画面中心弹出，"
                                f"背景使用{field}领域的代表性画面（热搜截图/新闻现场/网络素材快闪），"
                                "色调偏冷或高饱和，制造话题感；镜头在3秒内由虚焦推至清晰。"
                            ),
                            "台词/字幕": angles[0]["angle"],
                            "音效/音乐": "强节奏鼓点入 + 社交媒体消息提示音",
                        }
                    ],
                },
                {
                    "环节": "车型结合",
                    "shots": [
                        {
                            "镜号": 2,
                            "时长": "5-10秒",
                            "画面描述": (
                                f"【中景跟拍】{vehicle}驶入与「{keyword}」情绪相符的场景（{scene0}），"
                                f"车窗或后视镜中隐约映出{field}元素；车内光线柔和，突出{image0}的氛围。"
                            ),
                            "台词/字幕": f"{vehicle} · {positioning}，和{keyword}一样值得被看见",
                            "音效/音乐": "音乐进入主歌，环境音渐弱",
                        }
                    ],
                },
                {
                    "环节": "产品图展示",
                    "shots": [
                        {
                            "镜号": 3,
                            "时长": "10-15秒",
                            "画面描述": (
                                f"【特写+环绕】{vehicle}车头/车尾/内饰特写快速切换，"
                                f"重点展示{image0}细节（如车灯、轮毂、座舱、LOGO），"
                                "最后定格在车标落版，背景干净，品牌橙点缀。"
                            ),
                            "台词/字幕": f"{vehicle}｜不止于车，更是一种态度",
                            "音效/音乐": "节奏重音 + 落版音效",
                        }
                    ],
                },
            ],
        },
        {
            "时长": "20秒",
            "内容角度": angles[1]["angle"],
            "适合场景": "抖音/视频号/微博视频，情绪递进，留足产品展示时间",
            "结构说明": "0-6秒 热点解读｜6-13秒 车型结合｜13-20秒 产品图展示",
            "acts": [
                {
                    "环节": "热点解读",
                    "shots": [
                        {
                            "镜号": 1,
                            "时长": "0-3秒",
                            "画面描述": (
                                f"【特写+快切】手机/屏幕里闪过「{keyword}」热搜、评论区、弹幕，"
                                "画面做旧或加轻微抖动，模拟真实刷手机视角。"
                            ),
                            "台词/字幕": f"最近，{keyword}火了。",
                            "音效/音乐": "消息提示音连播 + 低频底鼓",
                        },
                        {
                            "镜号": 2,
                            "时长": "3-6秒",
                            "画面描述": (
                                f"【中景】一位与{vehicle}目标人群气质相符的人物（车主/白领/家庭用户）"
                                f"看着屏幕若有所思，窗外光线为{emotion}基调；镜头缓慢推近至面部特写。"
                            ),
                            "台词/字幕": angles[1]["angle"],
                            "音效/音乐": "情绪弦乐起",
                        },
                    ],
                },
                {
                    "环节": "车型结合",
                    "shots": [
                        {
                            "镜号": 3,
                            "时长": "6-10秒",
                            "画面描述": (
                                f"【全景】{vehicle}出现在{scene0}场景，人物走向车辆；"
                                f"镜头从人物背影切换至车侧，强调{image0}与当下情绪的连接。"
                            ),
                            "台词/字幕": f"{vehicle}的{scene0}，刚好装得下这份{emotion}",
                            "音效/音乐": "主歌旋律，节奏渐强",
                        },
                        {
                            "镜号": 4,
                            "时长": "10-13秒",
                            "画面描述": (
                                f"【车内中景】人物坐进驾驶位，手部特写启动车辆，"
                                f"中控屏或仪表盘亮起，映射出{image0}相关的UI界面或环境氛围。"
                            ),
                            "台词/字幕": f"不蹭热度，只讲好故事",
                            "音效/音乐": "引擎轻启声 + 音乐推进",
                        },
                    ],
                },
                {
                    "环节": "产品图展示",
                    "shots": [
                        {
                            "镜号": 5,
                            "时长": "13-20秒",
                            "画面描述": (
                                f"【特写+环绕+落版】{vehicle}外观高光细节（前脸、轮毂、贯穿灯）"
                                "与产品卖点字幕卡交替出现，最后车标+Slogan全屏落版，背景为品牌橙渐变。"
                            ),
                            "台词/字幕": f"{vehicle} × {keyword}｜{image0}，触手可及",
                            "音效/音乐": "高潮鼓点 + 落版重音",
                        }
                    ],
                },
            ],
        },
        {
            "时长": "30秒",
            "内容角度": angles[2]["angle"],
            "适合场景": "品牌官方账号、B站、视频号，完整叙事，可投流",
            "结构说明": "0-8秒 热点解读｜8-19秒 车型结合｜19-30秒 产品图展示",
            "acts": [
                {
                    "环节": "热点解读",
                    "shots": [
                        {
                            "镜号": 1,
                            "时长": "0-4秒",
                            "画面描述": (
                                f"【全景+叠化】{field}领域相关画面蒙太奇：新闻画面、社交平台界面、"
                                f"路人反应、热搜榜单，快速叠化；中央大字「{keyword}」逐渐清晰。"
                            ),
                            "台词/字幕": f"你有没有发现，{keyword}正在改变我们的情绪？",
                            "音效/音乐": "悬念音效 + 社交媒体混音",
                        },
                        {
                            "镜号": 2,
                            "时长": "4-8秒",
                            "画面描述": (
                                f"【中景】不同人物对「{keyword}」的反应快切："
                                f"有人兴奋、有人沉思、有人转发；画面整体为{emotion}情绪色调。"
                            ),
                            "台词/字幕": f"有人说这是{emotion}，有人说这就是生活。",
                            "音效/音乐": "键盘敲击、消息提示、环境人声",
                        },
                    ],
                },
                {
                    "环节": "车型结合",
                    "shots": [
                        {
                            "镜号": 3,
                            "时长": "8-13秒",
                            "画面描述": (
                                f"【全景跟拍】{vehicle}行驶在{scene0}路线，"
                                f"镜头与车辆同向移动；背景中隐约出现{field}符号或{keyword}关键词涂鸦/路牌。"
                            ),
                            "台词/字幕": angles[2]["angle"],
                            "音效/音乐": "情绪音乐进入副歌前奏",
                        },
                        {
                            "镜号": 4,
                            "时长": "13-19秒",
                            "画面描述": (
                                f"【中景+车内】车主/乘客在{scene0}中使用{vehicle}的{image0}，"
                                f"表情自然放松；镜头从车外切换至车内，突出空间与氛围。"
                            ),
                            "台词/字幕": f"{vehicle}用{image0}，接住这份{emotion}",
                            "音效/音乐": "副歌旋律起，情绪上扬",
                        },
                    ],
                },
                {
                    "环节": "产品图展示",
                    "shots": [
                        {
                            "镜号": 5,
                            "时长": "19-24秒",
                            "画面描述": (
                                f"【特写组接】{vehicle}产品亮点蒙太奇：{image0}细节、"
                                "车身线条、车灯点亮、轮毂转动；每个镜头2-3秒，节奏紧凑。"
                            ),
                            "台词/字幕": f"{vehicle}｜{positioning}",
                            "音效/音乐": "节奏鼓点 + 电子音效",
                        },
                        {
                            "镜号": 6,
                            "时长": "24-30秒",
                            "画面描述": (
                                f"【落版全景】{vehicle}停在简洁背景前，车标正对镜头；"
                                "画面右侧出现品牌Slogan，底部出现「{vehicle} × {keyword}」联名字样。"
                            ),
                            "台词/字幕": f"{vehicle} × {keyword}｜{narrative}，一种新的表达",
                            "音效/音乐": "高潮落版音效，音乐收",
                        },
                    ],
                },
            ],
        },
    ]

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
