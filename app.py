"""
广本车型 × 热点话题匹配 Demo
运行：streamlit run app.py
"""
import io
import os
import urllib.request

import jieba
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from wordcloud import WordCloud

from data import (
    PLATFORM_TOPICS,
    PLATFORMS,
    SAMPLE_TOPICS,
    TOPIC_DIMENSIONS,
    VEHICLES,
)
from matcher import (
    compute_emotion_score,
    compute_feasibility_score,
    compute_full_score,
    compute_safety_score,
    determine_tier,
    rank_all_topics,
    rank_all_vehicles,
)
from auto_label import auto_label_topic
from angles import generate_content_angles
from content_playbook import generate_topic_playbook

st.set_page_config(
    page_title="广本车型 × 热点话题匹配 Demo",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 广本车型 × 热点话题匹配 Demo")
st.caption("输入任意热点，自动打标签、全车型匹配、生成内容角度")

# ---------- 侧边栏：全局参数 ----------
with st.sidebar:
    st.header("⚙️ 评分参数")
    st.markdown(
        """
        **热度分**默认来自平台热榜或人工假设；**情绪共鸣分、传播可行性分、安全分**
        可由 AI 根据话题 B库标签自动计算，也可关闭后手动调节。
        """
    )

    heat_override = st.slider(
        "热度分",
        0,
        100,
        80,
        help="话题在平台上的热度。接入真实热榜后可自动填充； demo 中用手动假设值。",
    )

    st.divider()
    auto_external = st.checkbox(
        "🤖 自动计算情绪/可行性/安全分",
        value=True,
        help="开启后，模型会根据话题的 B库标签（价值观/情绪、领域/主题域、叙事原型、品牌安全等级等）自动计算这三项分数。",
    )

    if auto_external:
        st.info(
            "情绪共鸣分、传播可行性分、安全分将由 AI 根据话题标签自动计算。"
        )
        emotion_override = None
        feasibility_override = None
        safety_override = None
    else:
        emotion_override = st.slider(
            "情绪共鸣分",
            0,
            100,
            75,
            help="这个话题能否引发目标车型人群的情感共鸣？高=很戳目标人群，低=没什么感觉。",
        )
        feasibility_override = st.slider(
            "传播可行性分",
            0,
            100,
            75,
            help="内容好不好做、植入点是否自然。高=容易出好内容，低=强行蹭容易翻车。",
        )
        safety_override = st.slider(
            "安全分",
            0,
            100,
            95,
            help="品牌安全风险。也可通过 B库『品牌安全等级』自动映射：安全=95、谨慎=70、风险=30。",
        )

    st.divider()
    st.markdown(
        "**品牌契合分默认由车型-话题自动匹配计算。** 若想让公式左侧与其他项一样可手动调节，可勾选下方开关。"
    )
    use_brand_fit_override = st.checkbox(
        "手动覆盖品牌契合分",
        value=False,
        help="默认关闭时，品牌契合分由 A库×B库 自动匹配得出；开启后可手动指定固定值。",
    )
    if use_brand_fit_override:
        brand_fit_override = st.slider(
            "品牌契合分",
            0,
            100,
            75,
            help="手动设定品牌契合分。将覆盖自动计算结果，用于演示『如果品牌契合度更高/更低会怎样』。",
        )
    else:
        brand_fit_override = None

    st.divider()
    brand_fit_display = brand_fit_override if use_brand_fit_override else "自动计算"
    emotion_display = "AI自动" if auto_external else emotion_override
    feasibility_display = "AI自动" if auto_external else feasibility_override
    safety_display = "AI自动" if auto_external else safety_override
    st.markdown(
        f"""
        **当前完整契合分公式：**
        ```
        = 热度({heat_override})×25%
        + 品牌契合({brand_fit_display})×35%
        + 情绪共鸣({emotion_display})×20%
        + 可行性({feasibility_display})×10%
        + 安全({safety_display})×10%
        ```
        """
    )


def draw_radar(sub_scores_map: dict, title: str):
    """用 Plotly 画雷达图"""
    categories = ["直接功能", "价值观/叙事", "人群兴趣", "竞品/品类", "文化时刻"]
    fig = go.Figure()
    for vehicle, scores in sub_scores_map.items():
        values = [
            scores["直接功能匹配"],
            scores["价值观/叙事匹配"],
            scores["人群兴趣匹配"],
            scores["竞品/品类关联"],
            scores["文化时刻适配"],
        ]
        # 闭合雷达图
        values.append(values[0])
        cat_closed = categories + [categories[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=cat_closed,
                fill="toself",
                name=vehicle,
                opacity=0.35,
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title=title,
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def draw_tag_radar(tag_counts: dict, title: str, max_value: int = None):
    """画标签分布雷达图（用于平台热点池）"""
    categories = list(tag_counts.keys())
    values = list(tag_counts.values())
    values.append(values[0])
    categories_closed = categories + [categories[0]]

    if max_value is None:
        max_value = max(values) if values else 1

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories_closed,
            fill="toself",
            name="分布",
            line_color="#FF4B4B",
            fillcolor="rgba(255, 75, 75, 0.25)",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max_value])),
        showlegend=False,
        title=title,
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def draw_topic_radar(topic: dict):
    """画单条话题的 B库六维标签雷达图"""
    dimensions = list(TOPIC_DIMENSIONS.keys())
    values = []
    hover_texts = []
    for dim in dimensions:
        options = TOPIC_DIMENSIONS[dim]
        label = topic.get(dim, options[0])
        idx = options.index(label) if label in options else 0
        # 归一化到 0-100，使不同维度的选项数量差异不影响图形形状的可比性
        normalized = idx / max(len(options) - 1, 1) * 100
        values.append(normalized)
        hover_texts.append(f"{dim}<br>{label}")

    # 闭合雷达图
    values.append(values[0])
    dimensions_closed = dimensions + [dimensions[0]]
    hover_texts.append(hover_texts[0])

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=dimensions_closed,
            fill="toself",
            text=hover_texts,
            hoverinfo="text",
            line_color="#FF4B4B",
            fillcolor="rgba(255, 75, 75, 0.25)",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
        ),
        showlegend=False,
        height=350,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    return fig


def generate_wordcloud(platform: str, topics: list) -> io.BytesIO:
    """根据平台热点生成词云：热点句子与关键词沿云形紧密排列，整体呈一朵云"""

    # 常见中文停用词
    stopwords = set(
        [
            "的", "了", "和", "是", "在", "有", "我", "你", "他", "它", "们", "与", "或", "等",
            "这", "那", "之", "为", "以", "及", "而", "但", "也", "都", "要", "会", "能", "可以",
            "上", "下", "来", "去", "到", "从", "把", "被", "让", "给", "对", "向", "跟", "同", "比",
            "很", "非常", "已经", "正在", "将", "就", "又", "再", "因为", "所以", "如果", "虽然",
            "但是", "然而", "而且", "还是", "不是", "没有", "不能", "不要", "不会", "应该", "需要",
            "进行", "通过", "根据", "关于", "由于", "随着", "作为", "为了", "除了", "有关", "相关",
            "以及", "及其", "其中", "其他", "其余", "部分", "一些", "一下", "一种", "一个", "这些",
            "那些", "每个", "各种", "今年", "去年", "今天", "明天", "现在", "目前", "近日", "近期",
            "当时", "当年", "以前", "以后", "之后", "以来", "期间", "时候", "时间", "年来", "年度",
            "一天", "一年", "一次", "一直", "一切", "一样", "一般", "特别", "十分", "相当", "比较",
            "更加", "越来越", "有所", "有着", "具有", "具备", "拥有", "含有", "包含", "包括", "涉及",
            "面临", "面对", "针对", "对于", "至于", "即使", "即便", "哪怕", "尽管", "不管", "无论",
            "不论", "不可", "不得", "不必", "不用", "应当", "应", "须", "必须", "必要", "须要",
            "得", "该", "当", "不", "也", "还", "太", "更", "最", "已", "正", "并", "且", "因",
            "所", "如", "果", "虽", "然", "但", "或", "若", "即", "使", "哪", "怕", "尽", "无",
            "否", "莫", "毋", "则", "却", "只", "仅", "惟", "唯", "不过", "只是", "只能", "倒是",
            "罢了", "而已", "似地", "似的", "般", "发生", "表示", "认为", "出现", "成为", "开始",
            "结束", "完成", "达到", "实现", "提出", "指出", "看到", "做到", "拿到", "想到", "说到",
            "走到", "跑到", "来到", "听到", "感到", "觉得", "知道", "明白", "懂得",
        ]
    )

    frequencies = {}
    for t in topics:
        topic = t["topic"]
        heat = t["heat"]

        # 完整话题作为词云中的核心词，权重适中
        frequencies[topic] = frequencies.get(topic, 0) + heat * 0.40

        # 分词后的关键词作为填充，让词云更密
        words = jieba.lcut(topic)
        for w in words:
            w = w.strip()
            if len(w) >= 2 and w not in stopwords:
                frequencies[w] = frequencies.get(w, 0) + heat * 0.55
            elif w.isalnum() and len(w) >= 2:
                frequencies[w] = frequencies.get(w, 0) + heat * 0.55

        # B库标签也作为辅助填充词，提升云的密度
        for dim, weight in [
            ("领域/主题域", 0.35),
            ("叙事原型", 0.30),
            ("价值观/情绪", 0.25),
            ("目标人群重合度", 0.20),
            ("热度生命周期", 0.15),
        ]:
            label = t.get(dim)
            if label:
                frequencies[label] = frequencies.get(label, 0) + heat * weight

    # 查找可用中文字体：优先系统字体，其次项目内缓存，最后从网络下载
    font_path = None
    for path in [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "NotoSansCJKsc-Regular.otf",
        "wqy-microhei.ttc",
    ]:
        if os.path.exists(path):
            font_path = path
            break

    # 如果都没有，下载一个开源中文字体到项目目录
    if font_path is None:
        local_font = "NotoSansCJKsc-Regular.otf"
        if not os.path.exists(local_font):
            try:
                font_url = (
                    "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/"
                    "SimplifiedChinese/NotoSansCJKsc-Regular.otf"
                )
                urllib.request.urlretrieve(font_url, local_font)
            except Exception:
                # 备用：文泉驿微米体
                local_font = "wqy-microhei.ttc"
                if not os.path.exists(local_font):
                    try:
                        font_url = (
                            "https://github.com/larryli/PacificFont/raw/master/"
                            "wqy-microhei.ttc"
                        )
                        urllib.request.urlretrieve(font_url, local_font)
                    except Exception:
                        local_font = None
        if local_font and os.path.exists(local_font):
            font_path = local_font

    if font_path is None:
        st.warning("未找到中文字体，词云可能显示为方框。")
        font_path = None

    # 不用 mask，让 WordCloud 在整个正方形画布上自由、均匀、紧密填充。
    # 通过更大的画布、更多的词、更小的字号来缩短词与词之间的距离。
    wc = WordCloud(
        font_path=font_path,
        width=1000,
        height=1000,
        background_color="white",
        colormap="Oranges",
        max_words=2000,
        prefer_horizontal=0.90,
        relative_scaling=0.04,
        min_font_size=1,
        max_font_size=11,
        margin=0,
        random_state=42,
    ).generate_from_frequencies(frequencies)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    buf.seek(0)
    plt.close(fig)

    # 裁剪掉四周空白，让词云更紧凑地呈现
    img = Image.open(buf).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    buf_crop = io.BytesIO()
    img.save(buf_crop, format="png")
    buf_crop.seek(0)
    return buf_crop


def generate_compact_tag_cloud(platform: str, topics: list) -> str:
    """用 HTML+CSS 生成一个紧凑的方形标签云，词与词之间只留极小间隙"""
    # 按热度降序，让大词排在前面
    sorted_topics = sorted(topics, key=lambda x: x["heat"], reverse=True)

    def _heat_to_size(heat: int) -> int:
        """热度映射到字号：热度 60-100 对应 13-32px"""
        return int(13 + (heat - 60) / 40 * 19) if heat >= 60 else 12

    def _heat_to_color(heat: int) -> str:
        """热度映射到橙色深浅：热度越高颜色越深"""
        if heat >= 90:
            return "#D35400"  # 深橙
        elif heat >= 80:
            return "#E67E22"
        elif heat >= 70:
            return "#F39C12"
        elif heat >= 60:
            return "#F5B041"
        else:
            return "#F8C471"  # 浅橙

    tags = []
    for t in sorted_topics:
        topic = t["topic"]
        heat = t["heat"]
        size = _heat_to_size(heat)
        color = _heat_to_color(heat)
        # 对话题做 HTML 转义，避免特殊字符破坏页面
        safe_topic = topic.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tags.append(
            f'<span class="tag" style="font-size:{size}px;background-color:{color};" '
            f'title="热度 {heat}">{safe_topic}</span>'
        )

    # 加入一些分词关键词和 B库标签作为填充，让云更饱满
    fillers = []
    for t in sorted_topics:
        heat = t["heat"]
        # 分词
        words = jieba.lcut(t["topic"])
        for w in words:
            w = w.strip()
            if len(w) >= 2:
                fillers.append((w, heat * 0.5))
        # B库标签
        for dim in ["领域/主题域", "叙事原型", "价值观/情绪", "目标人群重合度"]:
            label = t.get(dim)
            if label:
                fillers.append((label, heat * 0.35))

    # 去重并按热度排序，只保留部分填充词避免过多
    filler_dict = {}
    for text, h in fillers:
        filler_dict[text] = max(filler_dict.get(text, 0), h)
    sorted_fillers = sorted(filler_dict.items(), key=lambda x: x[1], reverse=True)

    for text, h in sorted_fillers[:40]:
        size = int(11 + (h - 30) / 70 * 8) if h > 30 else 10
        color = "#FAD7A0"  # 填充词用更浅的橙色
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tags.append(
            f'<span class="tag filler" style="font-size:{size}px;background-color:{color};color:#D35400;" '
            f'title="热度 {int(h)}">{safe_text}</span>'
        )

    html = f"""
    <style>
    .compact-tag-cloud {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-content: center;
        gap: 2px;
        padding: 16px;
        line-height: 1.3;
        max-width: 100%;
        border-radius: 12px;
        background: #fff;
    }}
    .compact-tag-cloud .tag {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        color: #fff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
        font-weight: 500;
        white-space: nowrap;
        transition: transform 0.15s ease;
    }}
    .compact-tag-cloud .tag:hover {{
        transform: scale(1.08);
        z-index: 10;
        box-shadow: 0 2px 8px rgba(211, 84, 0, 0.25);
    }}
    .compact-tag-cloud .filler {{
        font-weight: 400;
    }}
    </style>
    <div class="compact-tag-cloud">
        {''.join(tags)}
    </div>
    """
    return html


def render_content_playbook(topic: dict, vehicle_key: str, title: str = "内容演绎方案"):
    """渲染完整的内容演绎模块：视频脚本 + 平台文案 + 视觉建议"""
    playbook = generate_topic_playbook(topic, vehicle_key)
    v = VEHICLES[vehicle_key]

    st.markdown(f"**{title}** — 承接车型：`{v['name']}`")

    with st.expander("🎬 查看视频分镜脚本"):
        script_df = pd.DataFrame(playbook["视频脚本"])
        st.dataframe(
            script_df,
            use_container_width=True,
            hide_index=True,
            column_order=["时长", "镜号", "画面", "台词/字幕", "音效"],
        )

    with st.expander("📝 查看三平台发布文案"):
        copy_df = pd.DataFrame(playbook["平台文案"])
        st.dataframe(
            copy_df,
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("🎨 查看配图 / 视觉建议"):
        visual = playbook["视觉建议"]
        st.markdown(f"- **主视觉风格**：{visual['主视觉风格']}")
        st.markdown(f"- **推荐配色**：{visual['推荐配色']}")
        st.markdown("- **画面元素**：")
        for elem in visual["画面元素"]:
            st.markdown(f"  - {elem}")
        st.markdown("- **拍摄/设计建议**：")
        for tip in visual["拍摄/设计建议"]:
            st.markdown(f"  - {tip}")
        st.info("💡 图片生成能力后续可接入 AI 绘图工具；当前先以文字版视觉方案呈现。")


tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 车型标签库", "🔥 平台热点池", "🎯 单热点全车型匹配", "📐 评分逻辑"]
)

# ---------- Tab 1: 车型标签库 ----------
with tab1:
    st.subheader("A库：车型形象标签")

    # 车型图片目录：优先使用 processed/ 下的处理图，否则用原图
    BASE_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
    IMAGE_DIR = os.path.join(BASE_IMAGE_DIR, "processed")

    cols = st.columns(2)
    for idx, (key, v) in enumerate(VEHICLES.items()):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{v['name']}** — {v['positioning']}")

                # 尝试加载车型图片（优先 processed/ 目录）
                img_path = None
                for folder in [IMAGE_DIR, BASE_IMAGE_DIR]:
                    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                        candidate = os.path.join(folder, f"{key}{ext}")
                        if os.path.exists(candidate):
                            img_path = candidate
                            break
                    if img_path:
                        break

                img_cols = st.columns([1, 2])
                with img_cols[0]:
                    if img_path:
                        st.image(img_path, use_container_width=True)
                    else:
                        st.info("📷 暂无图片\n请把车型图放入 `images/` 文件夹，命名为 `{车型名}.png`")
                with img_cols[1]:
                    st.markdown(f"**形象维度**：{', '.join(v['image'])}")
                    st.markdown(f"**利益点/场景**：{', '.join(v['scenes'])}")
                    st.markdown(f"**目标人群**：{', '.join(v['audience'])}")
                    st.markdown(f"**应避免调性**：{', '.join(v['avoid'])}")

# ---------- Tab 2: 平台热点池 ----------
with tab2:
    st.subheader("🔥 各平台热点追踪与自动标签")

    # 板块一：热榜词条词云
    st.markdown("### 1️⃣ 热榜词条词云")
    st.markdown("选择平台，查看该平台 Top10 热点的词云示意（词越大代表热度越高）。")

    wordcloud_col, legend_col = st.columns([3, 1])
    with wordcloud_col:
        selected_platform = st.selectbox(
            "选择平台",
            PLATFORMS,
            key="wordcloud_platform",
        )
        wc_topics = PLATFORM_TOPICS[selected_platform]
        tag_cloud_html = generate_compact_tag_cloud(selected_platform, wc_topics)
        components.html(tag_cloud_html, height=420, scrolling=True)

    with legend_col:
        st.markdown("**🏆 热度排行 Top5**")
        for i, t in enumerate(wc_topics[:5]):
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"{i + 1}.")
            st.markdown(f"{rank_emoji} `{t['topic']}` · 🔥{t['heat']}")

    st.divider()

    # 板块二：每条话题的 B库六维雷达图拆解
    st.markdown("### 2️⃣ 各平台热点 B库六维标签拆解")
    st.markdown("下方按平台直接展示每条热点的 B库六维标签与雷达图，无需点击展开。")

    platform_tabs = st.tabs(PLATFORMS)
    for platform, ptab in zip(PLATFORMS, platform_tabs):
        with ptab:
            topics = PLATFORM_TOPICS[platform]
            safety_emoji = {"安全": "🟢", "谨慎": "🟡", "风险": "🔴"}

            for idx, t in enumerate(topics):
                rank = idx + 1
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
                safety_icon = safety_emoji.get(t["品牌安全等级"], "⚪")

                with st.container(border=True):
                    st.markdown(f"### {medal} {t['topic']}")
                    st.caption(
                        f"🔥 热度 {t['heat']}  ·  {safety_icon} 品牌安全：{t['品牌安全等级']}"
                    )

                    label_col, radar_col = st.columns([1, 1.2])
                    with label_col:
                        st.markdown("**B库六维标签**")
                        tag_cols = st.columns(3)
                        for i, dim in enumerate(TOPIC_DIMENSIONS.keys()):
                            with tag_cols[i % 3]:
                                st.caption(f"**{dim}**")
                                st.markdown(f"`{t.get(dim, '-')}`")
                    with radar_col:
                        st.plotly_chart(
                            draw_topic_radar(t),
                            use_container_width=True,
                            key=f"topic_radar_{platform}_{idx}",
                        )

    with st.expander("B库六维标签说明"):
        dim_df = pd.DataFrame(
            [(k, ", ".join(v)) for k, v in TOPIC_DIMENSIONS.items()],
            columns=["维度", "可选标签"],
        )
        st.dataframe(dim_df, use_container_width=True)

# ---------- Tab 3: 单热点全车型匹配 + 车型反向匹配热点 ----------
with tab3:
    st.subheader("双向匹配：热点 ↔ 车型")
    st.caption("既可以从一个热点看全部车型谁最匹配，也可以从一辆车型看全部热点哪个最适合承接。")

    direction_tabs = st.tabs(["🔥 热点 → 全部车型", "🚗 车型 → 全部热点"])

    # ========== 子tab 1：热点 → 全部车型（原有功能） ==========
    with direction_tabs[0]:
        st.markdown("**输入一个新热点，看全部车型谁最匹配**")

        col_input, col_example = st.columns([3, 1])
        with col_input:
            topic_text = st.text_input(
                "热点文本",
                value="马斯克发射SpaceX星舰",
                placeholder="输入任意热点，如：国产AI大模型DeepSeek爆火",
                key="topic_to_vehicle_input",
            )
        with col_example:
            example = st.selectbox(
                "或选择一个示例热点",
                ["— 自定义 —"] + [t["topic"] for t in SAMPLE_TOPICS],
                key="topic_to_vehicle_example",
            )
            if example != "— 自定义 —":
                topic_text = example

        # 自动打标签
        auto_labels = auto_label_topic(topic_text)

        # 如果是示例，用示例标签覆盖自动标签
        selected_sample = next((t for t in SAMPLE_TOPICS if t["topic"] == topic_text), None)
        if selected_sample:
            for k in TOPIC_DIMENSIONS.keys():
                if k in selected_sample:
                    auto_labels[k] = selected_sample[k]
            heat_override = selected_sample.get("heat", heat_override)

        st.divider()
        st.markdown("**📝 自动识别 / 手动校准 B库标签**")

        labels = {}
        cols = st.columns(3)
        # 用 topic_text 参与 key，切换热点时自动重置为自动标签
        for idx, (dim, options) in enumerate(TOPIC_DIMENSIONS.items()):
            with cols[idx % 3]:
                default_idx = (
                    options.index(auto_labels.get(dim, options[0]))
                    if auto_labels.get(dim) in options
                    else 0
                )
                labels[dim] = st.selectbox(
                    dim,
                    options,
                    index=default_idx,
                    key=f"single_{dim}_{topic_text}",
                )

        labels["heat"] = heat_override
        if not auto_external:
            labels["emotion_score"] = emotion_override
            labels["feasibility_score"] = feasibility_override
            labels["safety_override"] = safety_override
        labels["brand_fit_override"] = brand_fit_override

        # 显示标签对应的安全分参考
        safety_label = labels.get("品牌安全等级", "安全")
        safety_map_display = {"安全": 95, "谨慎": 70, "风险": 30}
        computed_safety = safety_map_display.get(safety_label, 70)
        if auto_external:
            st.caption(
                f"当前『{safety_label}』标签对应安全分参考值：{computed_safety}；"
                f"已开启 AI 自动计算，最终安全分将根据标签组合自动得出。"
            )
        else:
            st.caption(
                f"当前『{safety_label}』标签对应安全分参考值：{computed_safety}；"
                f"左侧滑块已设为：{safety_override}，最终匹配将使用 {safety_override}。"
            )

        # 开始匹配按钮
        match_clicked = st.button(
            "🚀 开始匹配（热点 → 车型）", type="primary", use_container_width=True
        )

        if match_clicked:
            if auto_external:
                st.info(
                    "本次匹配中，**热度分**使用左侧设定值，**情绪共鸣分 / 传播可行性分 / 安全分** 由 AI 根据 B库标签自动计算。"
                )
            else:
                st.info(
                    "本次匹配使用左侧手动设定的『热度/情绪/可行性/安全分』。实际落地时，热度可接入平台热榜 API。"
                )

            # 安全风险提示（置顶）
            if labels.get("品牌安全等级") == "风险":
                st.error(
                    "⚠️ 该热点已被识别为**高风险**，不建议品牌借势。以下为模型演算结果，仅作参考，不生成内容角度。"
                )
            elif labels.get("品牌安全等级") == "谨慎":
                st.warning(
                    "⚠️ 该热点为**谨慎级**，可生成内容角度，但需人工复核品牌安全风险后再决策。"
                )

            # 计算全车型匹配
            rankings = rank_all_vehicles(
                labels,
                labels.get("brand_fit_override"),
                auto_external=auto_external,
            )

            # 1. 全车型得分表
            st.subheader("📊 全部车型匹配得分")
            rank_df = pd.DataFrame(
                [
                    {
                        "排名": i + 1,
                        "车型": r["vehicle"],
                        "完整契合分": r["full_score"],
                        "品牌契合分": r["brand_fit"],
                        "推荐等级": r["tier"],
                        "主要匹配类型": " + ".join(r["match_types"]),
                    }
                    for i, r in enumerate(rankings)
                ]
            )
            st.dataframe(rank_df, use_container_width=True)

            # 2. 雷达图：TOP4 车型五维对比
            st.subheader("🕸️ 品牌契合分雷达对比（TOP4）")
            top4 = rankings[:4]
            radar_data = {r["vehicle"]: r["sub_scores"] for r in top4}
            fig = draw_radar(radar_data, title=f"『{topic_text}』与 TOP4 车型契合度对比")
            st.plotly_chart(fig, use_container_width=True)

            # 3. TOP1 详情
            top1 = rankings[0]
            st.divider()
            st.subheader(f"🏆 最匹配车型：{top1['vehicle']}（{top1['tier']}，{top1['full_score']}分）")

            c1, c2, c3 = st.columns(3)
            c1.metric("完整契合分", top1["full_score"])
            c2.metric("品牌契合分", top1["brand_fit"])
            c3.metric("主要匹配类型", " + ".join(top1["match_types"]))

            # 计算过程展示
            with st.expander("📐 查看评分计算过程"):
                s = top1["sub_scores"]
                brand_fit_source = "手动覆盖" if use_brand_fit_override else "自动计算"
                external_source = "AI自动" if auto_external else "手动设定"
                st.markdown(
                    f"""
                    **第一步：计算品牌契合分（5个维度加权）**

                    | 维度 | 得分 | 权重 | 加权得分 |
                    |---|---|---|---|
                    | 直接功能匹配 | {s['直接功能匹配']} | 30% | {round(s['直接功能匹配'] * 0.30, 2)} |
                    | 价值观/叙事匹配 | {s['价值观/叙事匹配']} | 25% | {round(s['价值观/叙事匹配'] * 0.25, 2)} |
                    | 人群兴趣匹配 | {s['人群兴趣匹配']} | 25% | {round(s['人群兴趣匹配'] * 0.25, 2)} |
                    | 竞品/品类关联 | {s['竞品/品类关联']} | 15% | {round(s['竞品/品类关联'] * 0.15, 2)} |
                    | 文化时刻适配 | {s['文化时刻适配']} | 5% | {round(s['文化时刻适配'] * 0.05, 2)} |

                    **品牌契合分 = {top1['brand_fit']}**（{brand_fit_source}）
                    """
                )

                if auto_external:
                    st.markdown(
                        f"""
                        > 🤖 **外部维度为 AI 自动计算（{external_source}）**
                        > - **情绪共鸣分 {top1['emotion']}**：基于「{labels.get('价值观/情绪', '-')}」情绪标签 + 「{labels.get('热度生命周期', '-')}」生命周期，并参考车型特征自动推导。
                        > - **传播可行性分 {top1['feasibility']}**：基于「{labels.get('领域/主题域', '-')}」领域 + 「{labels.get('叙事原型', '-')}」叙事原型 + 「{labels.get('品牌安全等级', '-')}」安全等级自动推导。
                        > - **安全分 {top1['safety']}**：基于「{labels.get('品牌安全等级', '-')}」安全等级，叠加领域、情绪、叙事原型风险加权自动推导。
                        """
                    )

                st.markdown(
                    f"""
                    **第二步：计算完整契合分（热度 + 品牌契合 + 情绪 + 可行性 + 安全）**

                    | 因子 | 得分 | 来源 | 权重 | 加权得分 |
                    |---|---|---|---|---|
                    | 热度 | {top1['heat']} | 手动设定 | 25% | {round(top1['heat'] * 0.25, 2)} |
                    | 品牌契合 | {top1['brand_fit']} | {brand_fit_source} | 35% | {round(top1['brand_fit'] * 0.35, 2)} |
                    | 情绪共鸣 | {top1['emotion']} | {external_source} | 20% | {round(top1['emotion'] * 0.20, 2)} |
                    | 传播可行性 | {top1['feasibility']} | {external_source} | 10% | {round(top1['feasibility'] * 0.10, 2)} |
                    | 安全分 | {top1['safety']} | {external_source} | 10% | {round(top1['safety'] * 0.10, 2)} |

                    **完整契合分 = {top1['full_score']} → {top1['tier']}**
                    """
                )
                st.markdown(
                    """
                    **推荐等级标准**：S级（≥85）、A级（70-84）、B级（55-69）、C级（<55）
                    """
                )

            # TOP1 子分明细
            sub_df = pd.DataFrame(
                [{"维度": k, "得分": v} for k, v in top1["sub_scores"].items()]
            )
            st.bar_chart(sub_df.set_index("维度"))

            # 4. 内容角度 + 深度演绎（仅非风险热点才生成）
            if labels.get("品牌安全等级") != "风险":
                st.markdown("**💡 建议内容角度**")
                angles = generate_content_angles(
                    topic_text, top1["vehicle"], labels, top1["match_types"], top_n=8
                )
                angle_df = pd.DataFrame(
                    [
                        {
                            "序号": i + 1,
                            "内容角度": a["angle"],
                            "形式": a["type"],
                            "推荐平台": a["platform"],
                        }
                        for i, a in enumerate(angles)
                    ]
                )
                st.dataframe(angle_df, use_container_width=True, hide_index=True)

                # 深度内容演绎：视频脚本 + 平台文案 + 视觉建议
                topic_for_playbook = {"topic": topic_text, **labels}
                render_content_playbook(
                    topic_for_playbook,
                    top1["vehicle"],
                    title="🎬 深度内容演绎方案（视频脚本 / 平台文案 / 配图建议）",
                )

                # 再给出 TOP2 的角度（如果与 TOP1 同 tier 或分数接近）
                if len(rankings) >= 2 and rankings[1]["full_score"] >= top1["full_score"] - 8:
                    top2 = rankings[1]
                    with st.expander(f"查看次优车型 {top2['vehicle']} 的内容角度"):
                        angles2 = generate_content_angles(
                            topic_text, top2["vehicle"], labels, top2["match_types"], top_n=5
                        )
                        for a in angles2:
                            st.markdown(
                                f"- **{a['type']}（{a['platform']}）**：{a['angle']}"
                            )
            else:
                st.info("由于热点安全等级为「风险」，系统已停止生成内容角度。建议放弃该热点。")

            # 5. 各车型明细（可选展开）
            st.divider()
            with st.expander("查看全部车型明细"):
                for r in rankings:
                    st.markdown(
                        f"**{r['vehicle']}**：完整分 {r['full_score']}，品牌契合 {r['brand_fit']}，"
                        f"等级 {r['tier']}，匹配类型：{' + '.join(r['match_types'])}"
                    )

    # ========== 子tab 2：车型 → 全部热点（新增反向匹配） ==========
    with direction_tabs[1]:
        st.markdown("**选择一辆车型，看全部热点中哪个最适合它承接**")

        vehicle_cols, platform_cols = st.columns([1, 1])
        with vehicle_cols:
            selected_vehicle = st.selectbox(
                "选择车型",
                list(VEHICLES.keys()),
                key="vehicle_to_topics_vehicle",
            )
        with platform_cols:
            platform_options = ["全部平台"] + PLATFORMS
            selected_platform_for_vehicle = st.selectbox(
                "选择热点来源",
                platform_options,
                key="vehicle_to_topics_platform",
            )

        # 组装热点池
        if selected_platform_for_vehicle == "全部平台":
            all_topics = []
            for platform, topics in PLATFORM_TOPICS.items():
                for t in topics:
                    topic_copy = dict(t)
                    topic_copy["platform"] = platform
                    all_topics.append(topic_copy)
        else:
            all_topics = [
                {**t, "platform": selected_platform_for_vehicle}
                for t in PLATFORM_TOPICS[selected_platform_for_vehicle]
            ]

        reverse_match_clicked = st.button(
            "🚀 开始匹配（车型 → 热点）", type="primary", use_container_width=True
        )

        if reverse_match_clicked:
            v = VEHICLES[selected_vehicle]
            st.info(
                f"正在为 **{v['name']}** 计算与 **{len(all_topics)}** 条热点的匹配度，"
                f"情绪/可行性/安全分由 AI 自动计算。"
            )

            topic_rankings = rank_all_topics(
                selected_vehicle,
                all_topics,
                brand_fit_override,
                auto_external=auto_external,
            )

            # TOP10 热点排行
            st.subheader(f"📊 {v['name']} 最匹配的热点 Top10")
            topic_rank_df = pd.DataFrame(
                [
                    {
                        "排名": i + 1,
                        "热点": r["topic"],
                        "来源平台": r["platform"],
                        "完整契合分": r["full_score"],
                        "品牌契合分": r["brand_fit"],
                        "热度": r["heat"],
                        "推荐等级": r["tier"],
                        "主要匹配类型": " + ".join(r["match_types"]),
                    }
                    for i, r in enumerate(topic_rankings[:10])
                ]
            )
            st.dataframe(topic_rank_df, use_container_width=True, hide_index=True)

            # TOP1 热点详情 + 内容演绎
            top_topic = topic_rankings[0]
            st.divider()
            st.subheader(
                f"🏆 最匹配热点：{top_topic['topic']}（{top_topic['tier']}，{top_topic['full_score']}分）"
            )

            t1, t2, t3 = st.columns(3)
            t1.metric("完整契合分", top_topic["full_score"])
            t2.metric("品牌契合分", top_topic["brand_fit"])
            t3.metric("主要匹配类型", " + ".join(top_topic["match_types"]))

            # 雷达图：该车型对 TOP5 热点的品牌契合五维对比
            st.subheader("🕸️ 该车型与 TOP5 热点的品牌契合对比")
            top5_topics = topic_rankings[:5]
            radar_data = {r["topic"]: r["sub_scores"] for r in top5_topics}
            fig = draw_radar(
                radar_data,
                title=f"『{selected_vehicle}』与 TOP5 热点的品牌契合五维对比",
            )
            st.plotly_chart(fig, use_container_width=True)

            # 内容角度 + 深度演绎
            if top_topic["safety"] >= 30:
                st.markdown("**💡 建议内容角度**")
                # 构造 labels
                top_topic_labels = next(
                    t for t in all_topics if t["topic"] == top_topic["topic"]
                )
                angles = generate_content_angles(
                    top_topic["topic"],
                    selected_vehicle,
                    top_topic_labels,
                    top_topic["match_types"],
                    top_n=5,
                )
                for i, a in enumerate(angles):
                    st.markdown(f"{i + 1}. **{a['type']}（{a['platform']}）**：{a['angle']}")

                # 深度内容演绎：视频脚本 + 平台文案 + 视觉建议
                render_content_playbook(
                    top_topic_labels,
                    selected_vehicle,
                    title="🎬 深度内容演绎方案（视频脚本 / 平台文案 / 配图建议）",
                )

            # 全部热点明细（展开）
            st.divider()
            with st.expander("查看全部热点匹配明细"):
                for r in topic_rankings:
                    st.markdown(
                        f"**{r['topic']}**（{r['platform']}）："
                        f"完整分 {r['full_score']}，品牌契合 {r['brand_fit']}，"
                        f"等级 {r['tier']}，匹配类型：{' + '.join(r['match_types'])}"
                    )

# ---------- Tab 4: 评分逻辑 ----------
with tab4:
    st.subheader("📐 模型评分逻辑")
    st.markdown(
        """
        本 Demo 的核心是把「热点话题」和「车型形象」都抽象成标签，再通过加权公式算出匹配度。
        **核心原则**：不是"话题里有没有车"，而是"品牌能不能成为这个话题的一个有意义的注脚"。
        """
    )

    st.markdown("**整体计算流程**")
    st.code(
        """
A库（车型标签） + B库（热点标签）
           ↓
    计算「品牌契合分」
    （A库 × B库，五种匹配类型加权）
           ↓
    叠加热度、情绪、可行性、安全
    （4 个外部维度）
           ↓
    得出「车型话题契合分」
           ↓
    输出 S/A/B/C 推荐等级
        """,
        language=None,
    )

    st.markdown("**第一步：A库 + B库 同时打标签**")
    st.markdown(
        """
        模型需要同时理解「车型」和「热点」两端的标签，才能判断二者是否匹配：
        - **A库（车型形象标签库）**：给每款车型打上 **形象维度、利益点/场景、目标人群、应避免调性** 等标签。
        - **B库（热点话题标签库）**：给每个热点打上 **领域/主题域、叙事原型、价值观/情绪、目标人群重合度、热度生命周期、品牌安全等级** 6 维标签。
        """
    )

    with st.expander("点击查看 A库 与 B库 标签释义"):
        st.markdown("##### A库：车型形象标签")
        st.markdown(
            """
            | 标签维度 | 含义 | 示例（以雅阁为例） |
            |---|---|---|
            | 形象维度 | 车型给消费者的整体印象 | 成熟稳重、品质可靠、舒适体面、科技升级、经济省心 |
            | 利益点/场景 | 车型适合的使用场景 | 商务接待、家庭出行、长途自驾、城市通勤、职场进阶 |
            | 目标人群 | 车型核心受众 | 30-45岁家庭用户、商务人士、职场中年人 |
            | 应避免调性 | 与车型形象冲突的内容方向 | 鬼火改装、低价攀比、年轻化叛逆、浮夸 |
            """
        )

        st.markdown("##### B库：热点话题六维标签")
        st.markdown("###### 1）领域/主题域")
        st.markdown(
            """
            | 领域 | 典型热点示例 |
            |---|---|
            | 科技 | SpaceX发射、AI突破、新能源技术 |
            | 航天 | 火箭发射、空间站、探月工程 |
            | AI | DeepSeek、ChatGPT、智能驾驶 |
            | 体育 | 奥运会、世界杯、运动员故事 |
            | 娱乐 | 明星事件、综艺、电影上映 |
            | 社会 | 职场焦虑、婚恋话题、返乡潮 |
            | 职场 | 35岁危机、加班文化、升职加薪 |
            | 情感 | 分手综艺、婚恋观、独立女性 |
            | 家庭 | 亲子教育、三代同堂、年夜饭 |
            | 财经 | 股市涨跌、消费降级、房产 |
            | 文化 | 国潮、传统节日、非遗 |
            | 国际 | 国际关系、跨国企业动态 |
            | 汽车 | 新车发布、试驾测评、汽车文化 |
            | 消费 | 618、双11、性价比消费 |
            """
        )

        st.markdown("##### 2）叙事原型")
        st.markdown(
            """
            | 叙事原型 | 核心精神 | 典型话题 |
            |---|---|---|
            | 探索突破 | 未知、勇气、frontier | SpaceX发射、探月、深海 |
            | 挑战极限 | 更快更高更强 | 奥运会、极限运动 |
            | 创新颠覆 | 改变规则、重新定义 | AI革命、新能源 |
            | 成长蜕变 | 从0到1、自我超越 | 普通人逆袭、职场成长 |
            | 责任守护 | 家庭、社会、安全感 | 奶爸车、交通安全 |
            | 自由逃离 | 逃离内卷、寻找自我 | gap year、自驾旅行 |
            | 团聚归属 | 回家、团圆、亲情 | 春运、年夜饭、中秋 |
            | 抗争反叛 | 对抗权威、打破常规 | 年轻人整顿职场 |
            | 怀旧回归 | 经典重现、童年回忆 | 老歌翻红、经典车 |
            | 幽默解构 | 玩梗、自嘲、轻松 | 网络热梗、沙雕视频 |
            """
        )

        st.markdown("##### 3）价值观/情绪")
        st.markdown(
            """
            | 情绪 | 传播特点 | 适合品牌动作 |
            |---|---|---|
            | 好奇心 | 高参与、高分享 | 科普、揭秘、未来科技 |
            | 自豪感 | 民族认同强 | 国产崛起、技术突破 |
            | 焦虑感 | 高共鸣但需谨慎 | 提供解决方案、安全感 |
            | 治愈感 | 正向情感、品牌好感 | 生活方式、家庭温情 |
            | 热血 | 年轻、冲动、高互动 | 运动、挑战、极限 |
            | 共鸣 | 广泛传播基础 | 用户故事、场景代入 |
            | 幽默 | 轻松破圈 | 玩梗、轻植入 |
            | 争议 | 高风险高流量 | 一般避开 |
            | 希望 | 正向、品牌加分 | 未来、成长、创新 |
            | 安全感 | 家庭、可靠 | 产品品质、守护 |
            """
        )

        st.markdown("##### 4）目标人群重合度")
        st.markdown(
            """
            | 人群标签 | 典型画像 |
            |---|---|
            | 科技男 | 关注 AI、航天、电动车、智能产品的男性 |
            | 职场中年人 | 35 岁左右、注重稳重与家庭责任的商务/家庭用户 |
            | 年轻女性 | 关注生活方式、国潮、情感话题 |
            | 宝爸宝妈 | 30-45 岁、关注亲子/家庭出行 |
            | Z世代 | 大学生/年轻白领、追逐潮流与热点 |
            | 银发族 | 关注健康、养老、稳定出行 |
            | 汽车玩家 | 关注改装、性能、汽车文化 |
            """
        )

        st.markdown("##### 5）热度生命周期")
        st.markdown(
            """
            | 生命周期 | 含义 | 借势建议 |
            |---|---|---|
            | 萌芽期 | 话题刚出现，讨论量小 | 提前布局，搏早期红利 |
            | 上升期 | 热度快速爬升 | 最佳介入窗口，及时跟进 |
            | 爆发期 | 全民关注，流量峰值 | 可借势但成本高，需快速决策 |
            | 长尾期 | 热度下降但仍有讨论 | 适合轻量跟进或系列收尾 |
            | 回落期 | 已基本降温 | 一般不再建议投入 |
            """
        )

        st.markdown("##### 6）品牌安全等级")
        st.markdown(
            """
            | 安全等级 | 含义 | 行动建议 |
            |---|---|---|
            | 安全 | 正向或中性话题，无舆情风险 | 可正常借势 |
            | 谨慎 | 存在争议或敏感点，需把控角度 | 可借势，但需人工复核 |
            | 风险 | 负面、争议大或价值观冲突 | 不建议借势 |
            """
        )

    st.markdown("**第二步：计算品牌契合分（A库 × B库）**")
    st.markdown(
        """
        将 A库 中的车型标签与 B库 中的热点标签进行对应匹配，得到 5 个品牌契合子项得分，再加权汇总。
        """
    )
    st.markdown("**A库 × B库 标签映射表**")
    st.markdown(
        """
        | 品牌契合子项 | 权重 | A库标签 | B库标签 |
        |---|---|---|---|
        | 直接功能匹配 | 30% | 利益点/场景 | 领域/主题域 |
        | 价值观/叙事匹配 | 25% | 形象维度 | 叙事原型 |
        | 人群兴趣匹配 | 25% | 目标人群 | 目标人群重合度 |
        | 竞品/品类关联 | 15% | 车型属性 | 领域/主题域 |
        | 文化时刻适配 | 5% | 车型属性 | 热度生命周期 |
        """
    )
    st.latex(
        r"""
        \text{品牌契合分} = \underbrace{F_\text{功能} \times 30\%}_{\text{是否天然需要车/出行场景}}
        + \underbrace{V_\text{价值观} \times 25\%}_{\text{话题精神与车型形象是否同频}}
        + \underbrace{A_\text{人群} \times 25\%}_{\text{话题受众是否是车型目标人群}}
        + \underbrace{C_\text{竞品} \times 15\%}_{\text{是否涉及电动车/竞品/品类}}
        + \underbrace{M_\text{文化} \times 5\%}_{\text{是否全民大事件}}
        """
    )

    st.markdown("**五种匹配类型说明**")
    match_type_df = pd.DataFrame(
        [
            {"匹配类型": "功能场景匹配", "含义": "话题天然需要车/出行场景", "示例": "带娃自驾游 → 奥德赛"},
            {"匹配类型": "价值观/叙事匹配", "含义": "话题精神与车型形象同频", "示例": "SpaceX探索 → P7未来科技"},
            {"匹配类型": "人群兴趣匹配", "含义": "话题受众就是车型目标人群", "示例": "改装文化 → 型格/飞度"},
            {"匹配类型": "竞品/品类匹配", "含义": "话题涉及直接/间接竞品或品类", "示例": "马斯克/Tesla → P7电动车"},
            {"匹配类型": "文化时刻匹配", "含义": "全民大事件，品牌可刷存在感", "示例": "奥运会 → 型格运动精神"},
        ]
    )
    st.dataframe(match_type_df, use_container_width=True, hide_index=True)

    with st.expander("查看品牌契合分子项评分标准"):
        st.markdown(
            """
            | 子项 | 强匹配（80-100） | 中匹配（50-79） | 弱匹配（0-49） |
            |---|---|---|---|
            | 直接功能匹配分 | 话题天然涉及车型使用场景 | 可联想但不直接 | 几乎无关 |
            | 价值观叙事匹配分 | 话题精神与车型核心定位高度一致 | 部分价值观重合 | 价值观冲突或无关联 |
            | 人群兴趣匹配分 | 话题受众与车型目标人群高度重合 | 部分重合 | 几乎不重合 |
            | 竞品/品类关联分 | 直接涉及电动车/燃油车/竞品/技术路线 | 间接相关 | 完全无关 |
            | 文化时刻适配分 | 全民级超级大事件 | 垂直领域热点 | 小众话题 |
            """
        )

    st.markdown("**第三步：计算完整契合分（加入热度、情绪、可行性、安全）**")
    st.latex(
        r"""
        \text{完整契合分} = H_\text{热度} \times 25\%
        + B_\text{品牌契合} \times 35\%
        + E_\text{情绪} \times 20\%
        + X_\text{可行性} \times 10\%
        + S_\text{安全} \times 10\%
        """
    )

    with st.expander("查看完整契合分各因子说明与 AI 自动计算规则"):
        st.markdown("##### 各因子来源/说明")
        st.markdown(
            """
            | 因子 | 权重 | 来源/说明 |
            |---|---|---|
            | 品牌契合分 | 35% | 由 A库×B库 自动计算 |
            | 热度分 | 25% | 平台榜单、搜索量、讨论量，归一化到0-100 |
            | 情绪共鸣分 | 20% | 默认由 AI 根据「价值观/情绪 + 热度生命周期 + 车型特征」自动计算；也可手动输入 |
            | 传播可行性分 | 10% | 默认由 AI 根据「领域/主题域 + 叙事原型 + 品牌安全等级 + 生命周期」自动计算；也可手动输入 |
            | 安全分 | 10% | 默认由 AI 根据「品牌安全等级 + 领域 + 情绪 + 叙事原型」自动计算；也可手动输入 |
            """
        )

        st.markdown("##### AI 自动计算规则")
        st.markdown("###### 情绪共鸣分")
        st.markdown(
            """
            | 情绪标签 | 基础分 | 说明 |
            |---|---|---|
            | 共鸣 / 焦虑感 / 热血 / 治愈感 / 自豪感 / 希望 | 85-90 | 高共鸣情绪 |
            | 安全感 | 80 | 正向且与家庭/守护场景强相关 |
            | 好奇心 / 幽默 | 70-75 | 中等共鸣，需结合内容形式 |
            | 争议 | 45 | 负面或高风险情绪，共鸣但需警惕 |

            在此基础上，根据「热度生命周期」和车型关键词做 ±5 微调。
            """
        )
        st.markdown("###### 传播可行性分")
        st.markdown(
            """
            | 领域 | 基础分 | 说明 |
            |---|---|---|
            | 汽车 / 社会 / 职场 / 家庭 / 情感 / 文化 | 78-85 | 容易找到品牌植入点 |
            | 娱乐 / 体育 / 消费 | 72-75 | 植入点中等 |
            | AI / 航天 / 财经 / 国际 | 50-60 | 专业门槛高或话题遥远，需谨慎 |

            再根据叙事原型（幽默解构/自由逃离等加分，争议/抗争反叛减分）、
            品牌安全等级、生命周期做 ±5~±20 微调。
            """
        )
        st.markdown("###### 安全分")
        st.markdown(
            """
            | 品牌安全等级 | 基础分 |
            |---|---|
            | 安全 | 90 |
            | 谨慎 | 65 |
            | 风险 | 25 |

            叠加领域、情绪、叙事原型的风险加权：
            - 高风险领域/情绪/叙事（娱乐争议、国际、焦虑、争议等）减分
            - 低风险领域/情绪/叙事（汽车、航天、安全感、责任守护等）加分
            """
        )

    st.markdown("**第四步：输出推荐等级**")
    tier_df = pd.DataFrame(
        [
            {"等级": "S级", "分数区间": "85 - 100", "含义": "高度契合且高热，优先做", "行动": "优先资源配置，做系列内容"},
            {"等级": "A级", "分数区间": "70 - 84", "含义": "契合度不错，有热点价值", "行动": "做，注意植入角度"},
            {"等级": "B级", "分数区间": "55 - 69", "含义": "可蹭但需谨慎", "行动": "评估 ROI，小成本试做"},
            {"等级": "C级", "分数区间": "< 55", "含义": "不建议", "行动": "放弃或仅监测"},
        ]
    )
    st.dataframe(tier_df, use_container_width=True, hide_index=True)

    st.markdown("**附录：车型-叙事原型快速对应表**")
    narrative_map_df = pd.DataFrame(
        [
            {"叙事原型": "探索突破", "最匹配车型": "P7", "次匹配车型": "型格"},
            {"叙事原型": "挑战极限", "最匹配车型": "型格", "次匹配车型": "P7"},
            {"叙事原型": "创新颠覆", "最匹配车型": "P7", "次匹配车型": "飞度"},
            {"叙事原型": "成长蜕变", "最匹配车型": "雅阁", "次匹配车型": "飞度"},
            {"叙事原型": "责任守护", "最匹配车型": "奥德赛", "次匹配车型": "冠道"},
            {"叙事原型": "自由逃离", "最匹配车型": "飞度", "次匹配车型": "皓影"},
            {"叙事原型": "团聚归属", "最匹配车型": "奥德赛", "次匹配车型": "冠道"},
            {"叙事原型": "抗争反叛", "最匹配车型": "型格", "次匹配车型": "飞度"},
            {"叙事原型": "怀旧回归", "最匹配车型": "雅阁", "次匹配车型": "飞度"},
            {"叙事原型": "幽默解构", "最匹配车型": "飞度", "次匹配车型": "型格"},
            {"叙事原型": "成熟自洽", "最匹配车型": "雅阁", "次匹配车型": "冠道"},
            {"叙事原型": "未来科技", "最匹配车型": "P7", "次匹配车型": "型格"},
        ]
    )
    st.dataframe(narrative_map_df, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "说明：本 Demo 的自动标签基于关键词规则，便于演示；未来可接入 LLM 或 Embedding 模型做更精准的语义匹配。"
)
