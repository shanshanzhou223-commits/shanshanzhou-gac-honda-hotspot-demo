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
        hot_15_v = f"【全景+快切】赛道、计时器、挥动的黑白格旗与「{keyword}」热血大字交错闪现，高对比色调。"
        hot_15_s = "引擎轰鸣 + 强烈鼓点 + 观众欢呼"
        veh_15_v = f"【中景跟拍】{vehicle}以运动姿态切入弯道，轮胎摩擦地面，车身低伏；{scene0}变成赛道场景。"
        veh_15_sub = f"{vehicle} · {positioning}｜和{keyword}一样，热血到底"
        veh_15_s = "引擎声 + 运动摇滚"
        pro_15_v = f"【特写+环绕】运动套件、方向盘、转速表、刹车卡钳快速切换，{image0}在速度线中定格，车标落版。"
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
        hot_15_v = f"【全景+快速推进】热点关键词「{keyword}」以大字动画从画面中心弹出，背景使用{field}领域代表性画面，色调偏冷或高饱和。"
        hot_15_s = "强节奏鼓点入 + 社交媒体消息提示音"
        veh_15_v = f"【中景跟拍】{vehicle}驶入与「{keyword}」情绪相符的场景（{scene0}），车窗或后视镜中隐约映出{field}元素。"
        veh_15_sub = f"{vehicle} · {positioning}，和{keyword}一样值得被看见"
        veh_15_s = "音乐进入主歌，环境音渐弱"
        pro_15_v = f"【特写+环绕】{vehicle}车头/车尾/内饰特写快速切换，重点展示{image0}细节，最后定格车标落版。"
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
        hot20a_v = f"【特写+快切】冠军画面、计时器、赛道弯道与「{keyword}」大字交错，高饱和度。"
        hot20a_s = "引擎轰鸣 + 强烈鼓点"
        hot20b_v = f"【中景】运动员/车主擦汗、眼神坚定；窗外光线为热血橙红。"
        hot20b_s = "运动摇滚渐入"
        veh20a_v = f"【全景】{vehicle}在山路/赛道疾驰，车身姿态低伏，轮胎带起烟雾。"
        veh20a_s = "引擎声 + 运动音乐"
        veh20b_v = f"【车内中景】手握方向盘换挡，转速表攀升；运动座椅包裹，{image0}在驾驶激情中呈现。"
        veh20b_s = "换挡声 + 音乐推进"
        pro20_v = f"【特写+环绕+落版】运动套件、卡钳、尾翼、排气管特写，{image0}在速度线中落版。"
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
        hot30a_v = f"【全景+叠化】赛事画面、冠军庆祝、计时器、热搜榜单快速叠化，「{keyword}」以热血大字出现。"
        hot30a_s = "引擎轰鸣 + 悬念音效"
        hot30b_v = f"【中景】观众/网友兴奋反应快切，画面高对比、热血色调。"
        hot30b_s = "人群欢呼 + 键盘敲击"
        veh30a_v = f"【全景跟拍】{vehicle}在山路/赛道疾驰，镜头与车辆同向移动；背景有速度线和运动符号。"
        veh30a_s = "运动摇滚进入副歌前奏"
        veh30b_v = f"【中景+车内】车主激情驾驶，换挡、过弯；{image0}在驾驶氛围中被强调。"
        veh30b_s = "副歌旋律起，情绪上扬"
        pro30a_v = f"【特写组接】运动套件、方向盘、仪表盘、刹车卡钳依次呈现，{image0}细节在速度线中。"
        pro30a_s = "节奏鼓点 + 电子音效"
        pro30b_v = f"【落版全景】{vehicle}停在赛道/山路尽头，车标正对镜头；画面右侧Slogan，底部联名字样。"
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
        "hot20b_v": hot20b_v,
        "hot20b_s": hot20b_s,
        "veh20a_v": veh20a_v,
        "veh20a_s": veh20a_s,
        "veh20b_v": veh20b_v,
        "veh20b_s": veh20b_s,
        "pro20_v": pro20_v,
        "pro20_s": pro20_s,
        "hot30a_v": hot30a_v,
        "hot30a_s": hot30a_s,
        "hot30b_v": hot30b_v,
        "hot30b_s": hot30b_s,
        "veh30a_v": veh30a_v,
        "veh30a_s": veh30a_s,
        "veh30b_v": veh30b_v,
        "veh30b_s": veh30b_s,
        "pro30a_v": pro30a_v,
        "pro30a_s": pro30a_s,
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
                            "台词/字幕": f"最近，{keyword}火了。",
                            "音效/音乐": p["hot20a_s"],
                        },
                        {
                            "镜号": 2,
                            "时长": "3-6秒",
                            "画面描述": p["hot20b_v"],
                            "台词/字幕": angle,
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
                            "台词/字幕": f"{vehicle}的{scene0}，刚好装得下这份{emotion}",
                            "音效/音乐": p["veh20a_s"],
                        },
                        {
                            "镜号": 4,
                            "时长": "10-13秒",
                            "画面描述": p["veh20b_v"],
                            "台词/字幕": f"不蹭热度，只讲好故事",
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
                            "台词/字幕": f"{vehicle} × {keyword}｜{image0}，触手可及",
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
                            "台词/字幕": f"你有没有发现，{keyword}正在改变我们的情绪？",
                            "音效/音乐": p["hot30a_s"],
                        },
                        {
                            "镜号": 2,
                            "时长": "4-8秒",
                            "画面描述": p["hot30b_v"],
                            "台词/字幕": f"有人说这是{emotion}，有人说这就是生活。",
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
                            "台词/字幕": angle,
                            "音效/音乐": p["veh30a_s"],
                        },
                        {
                            "镜号": 4,
                            "时长": "13-19秒",
                            "画面描述": p["veh30b_v"],
                            "台词/字幕": f"{vehicle}用{image0}，接住这份{emotion}",
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
                            "台词/字幕": f"{vehicle}｜{positioning}",
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
    为单个图文/长图文内容角度，生成多平台发布文案。
    覆盖：微博（短图文/thread）、知乎（讨论/回答）、微信公众号（长图文）、小红书（图文笔记）。
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

    if angle is None:
        angle = f"从{keyword}看{vehicle}：{image0}的另一种表达"

    copies = [
        {
            "平台": "微博",
            "形式": "短图文 / 九宫格 thread",
            "文案": (
                f"【{vehicle} × {keyword}】{narrative}的另一种表达，也许就是{image0}。\n\n"
                f"1️⃣ {keyword}刷屏，真正值得接住的是什么？\n"
                f"2️⃣ {vehicle}的{scene0}，恰好给了这份{emotion}一个落点。\n"
                f"3️⃣ {positioning}，不是蹭热度，是本来就这样。\n\n"
                f"你怎么看？#{keyword}# #{vehicle_key}# #广本车型热点匹配#"
            ),
            "话题标签": f"#{keyword}# #{vehicle_key}# #广本车型热点匹配#",
            "配图建议": f"九宫格：热点现场图2张 + {vehicle} {scene0}场景图5张 + 车型特写2张",
        },
        {
            "平台": "知乎",
            "形式": "回答 / 深度讨论",
            "文案": (
                f"如何评价「{keyword}」与{vehicle}的这次相遇？\n\n"
                f"我的看法是：{angle}\n\n"
                f"{keyword}本质上是一个关于{narrative}的社会情绪。{vehicle}作为{positioning}，"
                f"它的{image0}和{scene0}天然能和这个情绪产生连接。\n\n"
                f"对{audience}来说，{vehicle}不是追热点的工具，而是{emotion}的落点。\n\n"
                f"你怎么看这次{field}热点与汽车品牌的结合？"
            ),
            "话题标签": f"#{keyword}# #{vehicle_key}# #汽车营销#",
            "配图建议": f"信息长图1张：{keyword}时间线 + {vehicle}产品点对照；或3-5张场景图",
        },
        {
            "平台": "微信公众号",
            "形式": "长图文",
            "文案": (
                f"标题：{angle}\n\n"
                f"开篇：最近，{keyword}刷屏了。有人说这是{emotion}，有人说这就是生活。\n\n"
                f"第一部分：{keyword}为什么能火？\n"
                f"拆解这个{field}话题背后的{narrative}情绪，以及它为何能击中{audience}。\n\n"
                f"第二部分：{vehicle}的{image0}，如何回应这个热点？\n"
                f"从{scene0}切入，讲{vehicle}如何不蹭热度、只讲好故事。"
                f"结合产品卖点（{image0}、{positioning}）做价值锚定。\n\n"
                f"第三部分：给{audience}的一句话\n"
                f"{vehicle} × {keyword}｜{narrative}，不止于车，更是一种态度。\n\n"
                f"结尾：引导试驾/到店/留资，附车型高清图。"
            ),
            "话题标签": f"广本{vehicle_key}｜{keyword}｜{emotion}出行",
            "配图建议": f"封面：{vehicle}与{keyword}符号化拼贴；内页：{scene0}场景图+{image0}细节+情绪金句海报",
        },
        {
            "平台": "小红书",
            "形式": "图文笔记",
            "文案": (
                f"姐妹们/兄弟们，{keyword}真的{emotion}了！\n"
                f"{vehicle}的{scene0}让我瞬间get到{image0}，这波内容我悟了✨\n\n"
                f"封面：{vehicle} × {keyword}氛围感\n"
                f"内页：\n"
                f"1️⃣ 热点关键词+车型结合点\n"
                f"2️⃣ {scene0}实拍/氛围图\n"
                f"3️⃣ {image0}细节特写\n"
                f"4️⃣ 一句态度文案\n\n"
                f"#{vehicle_key} #{keyword.replace(' ', '')} #汽车生活 #{emotion}出行 #{narrative}"
            ),
            "话题标签": f"#{vehicle_key} #{keyword.replace(' ', '')} #汽车生活 #{emotion}出行",
            "配图建议": f"封面：{vehicle}与{keyword}元素拼贴；内页：{scene0}氛围图+细节特写+金句卡",
        },
    ]
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
            "配图建议": f"15-30秒短视频，前3秒用{keyword}热点画面抓眼，中段切{vehicle} {scene0}",
        },
        {
            "平台": "微博",
            "形式": "图文",
            "文案": f"【{vehicle} × {keyword}】{narrative}的另一种表达，也许就是{image0}。你怎么看？",
            "话题标签": f"#{keyword}# #{vehicle_key}# #广本车型热点匹配#",
            "配图建议": f"九宫格：热点现场图2张 + {vehicle} {scene0}场景图5张 + 车型特写2张",
        },
        {
            "平台": "小红书",
            "形式": "图文笔记",
            "文案": f"姐妹们/兄弟们，{keyword}真的{emotion}了！{vehicle}的{scene0}让我瞬间get到{image0}，这波联名我悟了✨",
            "话题标签": f"#{vehicle_key} #{keyword.replace(' ', '')} #汽车生活 #{emotion}出行",
            "配图建议": f"封面：{vehicle}与{keyword}元素拼贴；内页：{scene0}氛围图+细节特写",
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
