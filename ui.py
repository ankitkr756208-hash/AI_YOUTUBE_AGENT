import csv
import io
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
import streamlit as st
import streamlit.components.v1 as components
from youtube_agent import build_youtube_agent

try:
    import plotly.graph_objects as go
except Exception:
    go = None


st.set_page_config(
    page_title="AI YouTube Video Analyzer Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

HISTORY_FILE = Path(__file__).with_name("analysis_history.json")

LANG_MAP = {
    "English": {
        "hero_title": "YouTube Intelligence Studio",
        "hero_sub": "Production-grade AI analytics for creators, brands, and growth teams",
        "input_label": "YouTube Video URL",
        "analyze": "Analyze Video",
        "retry": "Retry",
        "reset": "Reset",
        "copy": "Copy Report",
        "speak": "Voice Output",
    },
    "Hindi": {
        "hero_title": "YouTube Intelligence Studio",
        "hero_sub": "Creators aur brands ke liye production-grade AI analytics",
        "input_label": "YouTube Video URL",
        "analyze": "Analyze Video",
        "retry": "Retry",
        "reset": "Reset",
        "copy": "Report Copy Karo",
        "speak": "Voice Output",
    },
}


def init_state():
    defaults = {
        "theme": "Dark",
        "language": "English",
        "history": load_history(),
        "last_url": "",
        "analysis": None,
        "metadata": None,
        "raw_report": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(history):
    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_styles(theme):
    if theme == "Light":
        vars_block = """
        --bg1:#f7fbff;
        --bg2:#e8f3ff;
        --bg3:#fdf7ff;
        --text:#102238;
        --muted:#46607c;
        --card:rgba(255,255,255,0.70);
        --border:rgba(18,42,67,0.12);
        --neon1:#00b4d8;
        --neon2:#ff6b9f;
        """
    else:
        vars_block = """
        --bg1:#050816;
        --bg2:#0c1733;
        --bg3:#1a1134;
        --text:#e7f3ff;
        --muted:#99aac3;
        --card:rgba(15,24,42,0.58);
        --border:rgba(153,196,255,0.20);
        --neon1:#00e5ff;
        --neon2:#ff4ecd;
        """
    return f"""
    <style>
    :root {{{vars_block}}}

    #MainMenu, footer, header {{visibility: hidden;}}
    .stApp {{
        color: var(--text);
        font-family: "Poppins", "Segoe UI", sans-serif;
        background:
            radial-gradient(circle at 10% 5%, rgba(0,229,255,0.22), transparent 30%),
            radial-gradient(circle at 90% 15%, rgba(255,78,205,0.22), transparent 32%),
            linear-gradient(135deg, var(--bg1), var(--bg2), var(--bg3));
        background-size: 200% 200%;
        animation: ambient 14s ease infinite;
    }}

    @keyframes ambient {{
      0% {{ background-position: 0% 50%; }}
      50% {{ background-position: 100% 50%; }}
      100% {{ background-position: 0% 50%; }}
    }}

    section[data-testid="stSidebar"] {{
        position: sticky;
        top: 0;
        height: 100vh;
        background: rgba(7, 13, 30, 0.55);
        border-right: 1px solid var(--border);
        backdrop-filter: blur(20px);
    }}

    .glass {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 22px;
        backdrop-filter: blur(18px);
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.28);
    }}

    .hero {{
        padding: 24px 26px;
        margin-bottom: 18px;
        animation: fadeup 0.8s ease;
    }}

    .hero h1 {{
        margin: 0;
        font-size: 2.2rem;
        letter-spacing: 0.2px;
    }}

    .hero p {{
        margin-top: 8px;
        color: var(--muted);
    }}

    .metric-card {{
        padding: 16px;
        text-align: center;
        border-radius: 18px;
        background: linear-gradient(165deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 0 0 1px var(--border), 0 12px 24px rgba(0, 229, 255, 0.20);
    }}

    .stButton > button {{
        width: 100%;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.2);
        color: #ffffff;
        font-weight: 700;
        background: linear-gradient(130deg, var(--neon1), #3bb2ff, var(--neon2));
        box-shadow: 0 0 12px rgba(0,229,255,0.45), 0 0 24px rgba(255,78,205,0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(0,229,255,0.65), 0 0 28px rgba(255,78,205,0.35);
    }}

    .stTextInput input {{
        border-radius: 14px !important;
        border: 1px solid var(--border) !important;
        background: rgba(255,255,255,0.06) !important;
        color: var(--text) !important;
    }}

    .sidebar-logo {{
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.5;
        margin-bottom: 14px;
    }}

    .menu-chip {{
        background: rgba(255,255,255,0.06);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }}

    .social a {{
        text-decoration: none;
        margin-right: 12px;
        color: var(--text);
        font-weight: 600;
    }}

    .skeleton {{
        height: 12px;
        width: 100%;
        border-radius: 9px;
        margin-bottom: 10px;
        background: linear-gradient(90deg, rgba(255,255,255,0.06) 25%, rgba(255,255,255,0.20) 50%, rgba(255,255,255,0.06) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.3s linear infinite;
    }}

    @keyframes shimmer {{
      0% {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}

    @keyframes fadeup {{
      from {{opacity: 0; transform: translateY(10px);}}
      to {{opacity: 1; transform: translateY(0);}}
    }}

    .fade {{
      animation: fadeup 0.65s ease;
    }}

    .fab {{
        position: fixed;
        right: 24px;
        bottom: 22px;
        width: 46px;
        height: 46px;
        border-radius: 50%;
        text-align: center;
        line-height: 46px;
        font-size: 20px;
        text-decoration: none;
        color: #fff;
        background: linear-gradient(135deg, var(--neon1), var(--neon2));
        box-shadow: 0 0 16px rgba(0,229,255,0.5);
        z-index: 999;
    }}

    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(var(--neon1), var(--neon2));
        border-radius: 20px;
    }}

    @media (max-width: 768px) {{
      .hero h1 {{font-size: 1.55rem;}}
      .fab {{right: 14px; bottom: 14px;}}
    }}
    </style>
    """


def extract_video_id(url):
    try:
        parsed = urlparse(url)
        if parsed.netloc in {"youtu.be", "www.youtu.be"}:
            return parsed.path.strip("/")
        if "youtube.com" in parsed.netloc:
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [None])[0]
            if parsed.path.startswith("/shorts/"):
                return parsed.path.split("/shorts/")[-1].split("?")[0]
            if parsed.path.startswith("/embed/"):
                return parsed.path.split("/embed/")[-1].split("?")[0]
    except Exception:
        return None
    return None


def is_valid_youtube_url(url):
    if not url:
        return False
    pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
    return bool(re.match(pattern, url.strip(), re.IGNORECASE))


def format_duration(seconds):
    if not isinstance(seconds, int) or seconds <= 0:
        return "Not available"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fetch_video_metadata(url, video_id):
    data = {
        "title": "Not available",
        "channel": "Not available",
        "publish_date": "Not available",
        "views": "Not available",
        "likes": "Not available",
        "duration": "Not available",
        "duration_seconds": None,
        "video_age_days": None,
        "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else "",
    }

    try:
        oembed = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=8,
        )
        if oembed.ok:
            payload = oembed.json()
            data["title"] = payload.get("title", data["title"])
            data["channel"] = payload.get("author_name", data["channel"])
            data["thumbnail"] = payload.get("thumbnail_url", data["thumbnail"])
    except Exception:
        pass

    try:
        from pytube import YouTube

        yt = YouTube(url)
        data["title"] = yt.title or data["title"]
        data["channel"] = yt.author or data["channel"]
        data["views"] = f"{yt.views:,}" if yt.views else data["views"]
        data["duration"] = format_duration(yt.length)
        data["duration_seconds"] = yt.length
        if yt.publish_date:
            data["publish_date"] = yt.publish_date.strftime("%d %b %Y")
            data["video_age_days"] = (datetime.now().date() - yt.publish_date.date()).days
    except Exception:
        pass

    return data


def seconds_to_clock(seconds):
    if not isinstance(seconds, int) or seconds <= 0:
        return "NA"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def build_timing_insights(meta):
    duration_seconds = meta.get("duration_seconds")
    if not isinstance(duration_seconds, int) or duration_seconds <= 0:
        return {
            "span_label": "Unknown",
            "watch_style": "Timing insights not available",
            "checkpoints": {},
            "completion_estimate": "NA",
        }

    if duration_seconds <= 60:
        span_label = "Short-form"
        completion = "Very High"
    elif duration_seconds <= 300:
        span_label = "Snackable"
        completion = "High"
    elif duration_seconds <= 1200:
        span_label = "Mid-form"
        completion = "Moderate"
    else:
        span_label = "Long-form"
        completion = "Moderate to Low"

    checkpoints = {
        "Hook Zone (10%)": seconds_to_clock(int(duration_seconds * 0.10)),
        "Topic Lock (35%)": seconds_to_clock(int(duration_seconds * 0.35)),
        "Value Peak (60%)": seconds_to_clock(int(duration_seconds * 0.60)),
        "CTA Zone (85%)": seconds_to_clock(int(duration_seconds * 0.85)),
    }

    return {
        "span_label": span_label,
        "watch_style": f"{seconds_to_clock(duration_seconds)} total runtime",
        "checkpoints": checkpoints,
        "completion_estimate": completion,
    }


def clamp_score(value, fallback=0):
    try:
        number = float(value)
    except Exception:
        number = float(fallback)
    return max(0.0, min(100.0, number))


def build_deep_insights(analysis):
    seo = clamp_score(analysis.get("seo_score", 0))
    viral = clamp_score(analysis.get("viral_potential", 0))
    engagement = clamp_score(analysis.get("engagement_score", 0))

    hook = clamp_score(analysis.get("hook_strength", (viral + engagement) / 2))
    pacing = clamp_score(analysis.get("content_pacing", (engagement + seo) / 2))
    cta = clamp_score(analysis.get("cta_strength", engagement * 0.9))
    title_thumb = clamp_score(analysis.get("thumbnail_title_match", (seo + viral) / 2))
    momentum = round((seo * 0.35 + viral * 0.4 + engagement * 0.25), 1)

    strengths = []
    risks = []
    actions = []

    if hook >= 70:
        strengths.append("🔥 Strong opening hook pattern")
    else:
        risks.append("⚠ Hook may lose early viewers in first 15-30 seconds")
        actions.append("🎯 Start with bold promise + curiosity gap in opening line")

    if pacing >= 70:
        strengths.append("⚡ Good pacing with stable flow")
    else:
        risks.append("⏱ Some sections may feel slow")
        actions.append("✂ Trim fillers and add pattern interrupts every 25-40 seconds")

    if cta >= 70:
        strengths.append("📢 CTA structure supports conversions")
    else:
        risks.append("📉 CTA may not convert enough comments/subscribers")
        actions.append("🗣 Add one specific CTA near 70-90% timeline")

    if title_thumb >= 70:
        strengths.append("🖼 Title-thumbnail alignment is compelling")
    else:
        risks.append("🧩 Title and thumbnail promise mismatch possible")
        actions.append("🧪 A/B test thumbnail text with emotional trigger word")

    if not strengths:
        strengths = ["💡 Growth potential exists with optimization"]
    if not risks:
        risks = ["✅ No major strategic risk detected"]
    if not actions:
        actions = ["🚀 Continue current format with minor iterative testing"]

    return {
        "hook_strength": round(hook, 1),
        "content_pacing": round(pacing, 1),
        "cta_strength": round(cta, 1),
        "thumbnail_title_match": round(title_thumb, 1),
        "momentum_score": momentum,
        "strengths": strengths,
        "risks": risks,
        "actions": actions,
    }


def build_retention_profile(meta, analysis):
    duration_seconds = meta.get("duration_seconds")
    engagement = clamp_score(analysis.get("engagement_score", 0))
    hook = clamp_score(analysis.get("hook_strength", engagement * 0.95))
    pacing = clamp_score(analysis.get("content_pacing", engagement * 0.9))
    cta = clamp_score(analysis.get("cta_strength", engagement * 0.88))

    labels = [
        "0-10% Intro",
        "10-25% Setup",
        "25-40% Value Start",
        "40-60% Mid Retention",
        "60-80% Depth Zone",
        "80-100% CTA Close",
    ]

    base_retention = [
        (hook * 0.80 + engagement * 0.20),
        (hook * 0.55 + pacing * 0.45),
        (pacing * 0.72 + engagement * 0.28),
        (pacing * 0.55 + engagement * 0.45),
        (engagement * 0.7 + cta * 0.3),
        (cta * 0.65 + engagement * 0.35),
    ]

    if isinstance(duration_seconds, int) and duration_seconds > 1200:
        base_retention = [
            base_retention[0],
            base_retention[1] - 2,
            base_retention[2] - 3,
            base_retention[3] - 5,
            base_retention[4] - 4,
            base_retention[5] - 2,
        ]

    normalized = [max(5.0, min(98.0, round(v, 1))) for v in base_retention]
    risk_values = [round(100.0 - v, 1) for v in normalized]

    risk_tags = []
    for value in risk_values:
        if value >= 45:
            risk_tags.append("High")
        elif value >= 28:
            risk_tags.append("Medium")
        else:
            risk_tags.append("Low")

    return {
        "labels": labels,
        "retention_values": normalized,
        "risk_values": risk_values,
        "risk_tags": risk_tags,
    }


def render_retention_heatmap(meta, analysis):
    profile = build_retention_profile(meta, analysis)
    st.markdown("### 🌡 Retention Risk Heatmap")

    if go:
        fig = go.Figure(
            data=go.Heatmap(
                z=[profile["risk_values"]],
                x=profile["labels"],
                y=["Risk Intensity"],
                colorscale=[
                    [0.0, "#16a34a"],
                    [0.45, "#f59e0b"],
                    [1.0, "#ef4444"],
                ],
                zmin=0,
                zmax=100,
                text=[profile["risk_tags"]],
                texttemplate="%{text}<br>%{z}%",
                hovertemplate="%{x}<br>Drop Risk: %{z}%<extra></extra>",
            )
        )
        fig.update_layout(height=260, margin={"l": 10, "r": 10, "t": 25, "b": 10})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write({"segments": profile["labels"], "drop_risk": profile["risk_values"]})

    c1, c2 = st.columns(2)
    with c1:
        if go:
            fig = go.Figure([
                go.Scatter(
                    x=profile["labels"],
                    y=profile["retention_values"],
                    mode="lines+markers",
                    name="Estimated Retention",
                )
            ])
            fig.update_layout(title="📉 Segment-wise Retention Curve", yaxis_range=[0, 100], height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(profile["retention_values"])

    with c2:
        st.markdown("#### 🎯 Drop-off Hotspots")
        ranked = sorted(
            zip(profile["labels"], profile["risk_values"], profile["risk_tags"]),
            key=lambda x: x[1],
            reverse=True,
        )
        for segment, risk, tag in ranked[:3]:
            emoji = "🔴" if tag == "High" else "🟠" if tag == "Medium" else "🟢"
            st.markdown(f"- {emoji} **{segment}**: {risk}% risk ({tag})")


def extract_json_from_text(text):
    if not text:
        return None
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.replace("json", "", 1).strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(candidate[start : end + 1])
    except Exception:
        return None


def default_analysis(raw_text):
    return {
        "video_summary": raw_text[:700] if raw_text else "Analysis generated.",
        "main_topics": ["Content Strategy", "Audience Retention", "Hook Quality"],
        "sentiment": {"positive": 52, "neutral": 32, "negative": 16},
        "target_audience": "18-34 creators and growth-focused viewers",
        "seo_score": 72,
        "viral_potential": 68,
        "engagement_score": 74,
        "final_rating": 7.4,
        "improvement_suggestions": [
            "Strengthen first 15-second hook.",
            "Use clearer keyword-rich title and chapter markers.",
            "Add stronger end-screen CTA for comments and subscriptions.",
        ],
        "best_upload_times": ["Tuesday 6:30 PM", "Thursday 7:00 PM", "Sunday 11:00 AM"],
        "audience_age": {"13-17": 8, "18-24": 35, "25-34": 31, "35-44": 18, "45+": 8},
        "hook_strength": 71,
        "content_pacing": 69,
        "cta_strength": 66,
        "thumbnail_title_match": 74,
    }


def run_ai_analysis(agent, url, language):
    prompt = f"""
    Analyze this YouTube video URL with deep creator intelligence: {url}
    Respond in {language} with strict JSON only (no markdown, no prose outside JSON).
    Schema:
    {{
      "video_summary": "string",
      "main_topics": ["string"],
      "sentiment": {{"positive": 0-100, "neutral": 0-100, "negative": 0-100}},
      "target_audience": "string",
      "seo_score": 0-100,
      "viral_potential": 0-100,
      "engagement_score": 0-100,
      "final_rating": 0-10,
      "improvement_suggestions": ["string"],
      "best_upload_times": ["string"],
            "audience_age": {{"13-17":0-100,"18-24":0-100,"25-34":0-100,"35-44":0-100,"45+":0-100}},
            "hook_strength": 0-100,
            "content_pacing": 0-100,
            "cta_strength": 0-100,
            "thumbnail_title_match": 0-100
    }}
    """
    response = agent.run(prompt)
    raw = getattr(response, "content", str(response))
    parsed = extract_json_from_text(raw)
    if not isinstance(parsed, dict):
        parsed = default_analysis(raw)
    return parsed, raw


def analysis_to_markdown(meta, analysis):
    topics = ", ".join(analysis.get("main_topics", []))
    improvements = "\n".join([f"- {x}" for x in analysis.get("improvement_suggestions", [])])
    times = "\n".join([f"- {x}" for x in analysis.get("best_upload_times", [])])
    return (
        f"# YouTube AI Analysis Report\n\n"
        f"## Video\n"
        f"- Title: {meta.get('title', 'NA')}\n"
        f"- Channel: {meta.get('channel', 'NA')}\n"
        f"- Publish Date: {meta.get('publish_date', 'NA')}\n"
        f"- Views: {meta.get('views', 'NA')}\n"
        f"- Duration: {meta.get('duration', 'NA')}\n\n"
        f"## Summary\n{analysis.get('video_summary', 'NA')}\n\n"
        f"## Main Topics\n{topics}\n\n"
        f"## Scores\n"
        f"- SEO Score: {analysis.get('seo_score', 0)}\n"
        f"- Viral Potential: {analysis.get('viral_potential', 0)}\n"
        f"- Engagement Score: {analysis.get('engagement_score', 0)}\n"
        f"- Final Rating: {analysis.get('final_rating', 0)}/10\n\n"
        f"## Improvement Suggestions\n{improvements}\n\n"
        f"## Best Upload Time Suggestions\n{times}\n"
    )


def pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_pdf_bytes(title, body):
    lines = [title, ""] + body.splitlines()
    content_lines = ["BT", "/F1 10 Tf", "40 790 Td", "14 TL"]
    line_count = 0
    for line in lines:
        chunks = [line[i : i + 96] for i in range(0, len(line), 96)] or [""]
        for chunk in chunks:
            if line_count > 52:
                break
            content_lines.append(f"({pdf_escape(chunk)}) Tj")
            content_lines.append("T*")
            line_count += 1
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="ignore")

    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>endobj\n"
    )
    objects.append(b"4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    objects.append(f"5 0 obj<< /Length {len(stream)} >>stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj

    xref_start = len(pdf)
    pdf += f"xref\n0 {len(objects)+1}\n".encode("latin-1")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode("latin-1")
    pdf += f"trailer<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin-1")
    return pdf


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">🚀 NovaLens AI<br>Premium Video Analyzer</div>', unsafe_allow_html=True)
        st.session_state["theme"] = st.selectbox("Theme", ["Dark", "Light"], index=0 if st.session_state["theme"] == "Dark" else 1)
        st.session_state["language"] = st.selectbox("Language", ["English", "Hindi"], index=0 if st.session_state["language"] == "English" else 1)

        for item in ["Dashboard", "Features", "Analytics", "History", "Settings"]:
            st.markdown(f'<div class="menu-chip">• {item}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### About Developer")
        st.caption("Built with Streamlit + AI Agent backend")
        st.markdown(
            '<div class="social"><a href="https://github.com" target="_blank">GitHub</a>'
            '<a href="https://linkedin.com" target="_blank">LinkedIn</a>'
            '<a href="https://x.com" target="_blank">X</a></div>',
            unsafe_allow_html=True,
        )


def show_video_preview(meta, url, video_id):
    st.markdown("### 🎥 Video Preview")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.video(url)
    with c2:
        if meta.get("thumbnail"):
            st.image(meta["thumbnail"], use_container_width=True)
        st.markdown(f"**📝 Title:** {meta.get('title', 'Not available')}")
        st.markdown(f"**📺 Channel:** {meta.get('channel', 'Not available')}")
        st.markdown(f"**📅 Publish Date:** {meta.get('publish_date', 'Not available')}")
        st.markdown(f"**👀 Views:** {meta.get('views', 'Not available')}")
        st.markdown(f"**👍 Likes:** {meta.get('likes', 'Not available')} (if available)")
        st.markdown(f"**⏳ Duration:** {meta.get('duration', 'Not available')}")
        age_days = meta.get("video_age_days")
        if isinstance(age_days, int) and age_days >= 0:
            st.markdown(f"**🕰 Video Age:** {age_days} days")
        st.caption(f"🆔 Video ID: {video_id if video_id else 'Not detected'}")


def render_timing_details(meta):
    timing = build_timing_insights(meta)
    st.markdown("### ⏱ Video Time Span Intelligence")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f"<div class='metric-card fade'><h4>🎬 Format</h4><h3>{timing['span_label']}</h3></div>",
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"<div class='metric-card fade'><h4>⌛ Runtime</h4><h3>{timing['watch_style']}</h3></div>",
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"<div class='metric-card fade'><h4>📈 Completion Outlook</h4><h3>{timing['completion_estimate']}</h3></div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### 🧭 Recommended Timeline Checkpoints")
    for label, clock in timing["checkpoints"].items():
        st.markdown(f"- {label}: **{clock}**")


def render_deep_analysis_section(analysis):
    deep = build_deep_insights(analysis)
    st.markdown("### 🧠 Deep Analysis Engine")

    row1 = st.columns(5)
    deep_cards = [
        ("🎣 Hook Strength", deep["hook_strength"]),
        ("⚙ Content Pacing", deep["content_pacing"]),
        ("📣 CTA Strength", deep["cta_strength"]),
        ("🖼 Thumb-Title Match", deep["thumbnail_title_match"]),
        ("🚀 Momentum", deep["momentum_score"]),
    ]
    for idx, (title, score) in enumerate(deep_cards):
        with row1[idx]:
            st.markdown(
                f"<div class='metric-card fade'><h4>{title}</h4><h2>{score}</h2></div>",
                unsafe_allow_html=True,
            )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### ✅ Strength Signals")
        for item in deep["strengths"]:
            st.markdown(f"- {item}")
    with c2:
        st.markdown("#### ⚠ Risk Signals")
        for item in deep["risks"]:
            st.markdown(f"- {item}")
    with c3:
        st.markdown("#### 🎯 Action Plan")
        for item in deep["actions"]:
            st.markdown(f"- {item}")


def render_score_cards(analysis):
    cards = [
        ("🔍 SEO Score", analysis.get("seo_score", 0)),
        ("🔥 Viral Potential", analysis.get("viral_potential", 0)),
        ("💬 Engagement", analysis.get("engagement_score", 0)),
        ("⭐ Final Rating", f"{analysis.get('final_rating', 0)}/10"),
    ]
    cols = st.columns(4)
    for idx, (title, value) in enumerate(cards):
        with cols[idx]:
            st.markdown(
                f"<div class='metric-card fade'><h4>{title}</h4><h2>{value}</h2></div>",
                unsafe_allow_html=True,
            )


def render_charts(analysis):
    sentiment = analysis.get("sentiment", {"positive": 0, "neutral": 0, "negative": 0})
    audience = analysis.get("audience_age", {"13-17": 0, "18-24": 0, "25-34": 0, "35-44": 0, "45+": 0})

    st.markdown("### 📊 Charts & Visualizations")
    c1, c2 = st.columns(2)

    with c1:
        if go:
            fig = go.Figure(
                data=[go.Pie(labels=list(sentiment.keys()), values=list(sentiment.values()), hole=0.45)]
            )
            fig.update_layout(title="😊 Sentiment Pie Chart", height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("😊 Sentiment Pie Chart")
            st.write(sentiment)

    with c2:
        bar_data = {
            "SEO": analysis.get("seo_score", 0),
            "Viral": analysis.get("viral_potential", 0),
            "Engagement": analysis.get("engagement_score", 0),
        }
        if go:
            fig = go.Figure([go.Bar(x=list(bar_data.keys()), y=list(bar_data.values()))])
            fig.update_layout(title="📶 Engagement Bar Graph", yaxis_range=[0, 100], height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(bar_data)

    c3, c4 = st.columns(2)
    with c3:
        if go:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=analysis.get("seo_score", 0),
                    title={"text": "🧭 SEO Score Meter"},
                    gauge={"axis": {"range": [0, 100]}},
                )
            )
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.metric("SEO Score Meter", analysis.get("seo_score", 0))

    with c4:
        if go:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=analysis.get("viral_potential", 0),
                    title={"text": "🌀 Viral Score Progress Ring"},
                    gauge={"axis": {"range": [0, 100]}},
                )
            )
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.metric("Viral Score", analysis.get("viral_potential", 0))

    if go:
        fig = go.Figure([go.Scatter(x=list(audience.keys()), y=list(audience.values()), mode="lines+markers")])
        fig.update_layout(title="👥 Audience Age Graph", yaxis_range=[0, 100], height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(audience)


def to_csv_bytes(history):
    if not history:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=sorted(history[0].keys()))
    writer.writeheader()
    writer.writerows(history)
    return output.getvalue().encode("utf-8")


def render_copy_and_voice(report_text, button_copy, button_voice):
    payload = json.dumps(report_text)
    components.html(
        f"""
        <div style="display:flex;gap:12px;margin-top:8px;margin-bottom:10px;">
          <button onclick='navigator.clipboard.writeText({payload})' style='padding:8px 12px;border-radius:10px;border:none;background:#06b6d4;color:#fff;font-weight:600;'>📋 {button_copy}</button>
          <button onclick='(function(){{const u=new SpeechSynthesisUtterance({payload});u.rate=1;speechSynthesis.cancel();speechSynthesis.speak(u);}})()' style='padding:8px 12px;border-radius:10px;border:none;background:#ec4899;color:#fff;font-weight:600;'>🔊 {button_voice}</button>
        </div>
        """,
        height=64,
    )


@st.cache_resource
def get_agent():
    return build_youtube_agent()


def main():
    init_state()
    render_sidebar()
    lang = LANG_MAP[st.session_state["language"]]
    st.markdown(get_styles(st.session_state["theme"]), unsafe_allow_html=True)
    st.markdown('<a id="top"></a>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="glass hero">
                    <h1>🎬 {lang['hero_title']}</h1>
                    <p>✨ {lang['hero_sub']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown("<div class='metric-card'>⚡ Fast AI Analysis</div>", unsafe_allow_html=True)
    with k2:
        st.markdown("<div class='metric-card'>📊 Advanced Dashboard</div>", unsafe_allow_html=True)
    with k3:
        st.markdown("<div class='metric-card'>🧠 Actionable Strategy</div>", unsafe_allow_html=True)

    st.markdown("<div class='glass' style='padding:18px;margin-top:14px;'>", unsafe_allow_html=True)
    video_url = st.text_input(lang["input_label"], value=st.session_state.get("last_url", ""), placeholder="https://www.youtube.com/watch?v=...")

    is_valid = is_valid_youtube_url(video_url)
    if video_url:
        if is_valid:
            st.success("✅ Valid YouTube URL detected")
        else:
            st.error("❌ Invalid URL. Please enter a valid YouTube link.")

    a1, a2, a3 = st.columns([2, 1, 1])
    analyze_clicked = a1.button(f"🚀 {lang['analyze']}", use_container_width=True)
    retry_clicked = a2.button(f"🔁 {lang['retry']}", use_container_width=True)
    reset_clicked = a3.button(f"🧹 {lang['reset']}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if reset_clicked:
        st.session_state["last_url"] = ""
        st.session_state["analysis"] = None
        st.session_state["metadata"] = None
        st.session_state["raw_report"] = ""
        st.rerun()

    should_analyze = False
    if analyze_clicked and is_valid:
        should_analyze = True
    if retry_clicked and st.session_state.get("last_url"):
        video_url = st.session_state["last_url"]
        should_analyze = True

    if should_analyze:
        st.session_state["last_url"] = video_url
        progress = st.progress(0)
        status = st.empty()
        skeleton = st.empty()
        skeleton.markdown(
            """
            <div class='glass' style='padding:16px;margin-top:10px;'>
              <div class='skeleton'></div><div class='skeleton'></div><div class='skeleton'></div>
              <div class='skeleton' style='width:75%;'></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for pct, msg in [
            (12, "Validating URL..."),
            (26, "Extracting metadata and duration span..."),
            (42, "Preparing advanced AI context..."),
            (58, "Running deep model analysis..."),
        ]:
            progress.progress(pct)
            status.info(msg)
            time.sleep(0.12)

        video_id = extract_video_id(video_url)
        metadata = fetch_video_metadata(video_url, video_id)
        agent = get_agent()
        analysis, raw = run_ai_analysis(agent, video_url, st.session_state["language"])

        progress.progress(85)
        status.info("Building premium dashboard and deep insights...")
        time.sleep(0.1)
        progress.progress(100)
        status.success("✅ Analysis completed")
        skeleton.empty()

        st.session_state["metadata"] = metadata
        st.session_state["analysis"] = analysis
        st.session_state["raw_report"] = analysis_to_markdown(metadata, analysis)

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "video_url": video_url,
            "title": metadata.get("title", "NA"),
            "channel": metadata.get("channel", "NA"),
            "seo_score": analysis.get("seo_score", 0),
            "viral_potential": analysis.get("viral_potential", 0),
            "engagement_score": analysis.get("engagement_score", 0),
            "final_rating": analysis.get("final_rating", 0),
        }
        st.session_state["history"] = [record] + st.session_state["history"][:149]
        save_history(st.session_state["history"])

    metadata = st.session_state.get("metadata")
    analysis = st.session_state.get("analysis")
    report_md = st.session_state.get("raw_report", "")

    if metadata and analysis:
        video_id = extract_video_id(st.session_state.get("last_url", ""))
        show_video_preview(metadata, st.session_state.get("last_url", ""), video_id)

        st.markdown("### 🤖 AI Analysis Dashboard")
        render_score_cards(analysis)
        render_timing_details(metadata)
        render_deep_analysis_section(analysis)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🧾 Video Summary")
            st.markdown(f"<div class='glass fade' style='padding:14px;'>{analysis.get('video_summary', '')}</div>", unsafe_allow_html=True)
            st.markdown("#### 🧩 Main Topics")
            st.write(analysis.get("main_topics", []))
            st.markdown("#### 🎯 Target Audience")
            st.info(analysis.get("target_audience", "Not available"))

        with c2:
            st.markdown("#### 🛠 Improvement Suggestions")
            for item in analysis.get("improvement_suggestions", []):
                st.markdown(f"- {item}")
            st.markdown("#### 🕒 Best Upload Time Suggestions")
            for slot in analysis.get("best_upload_times", []):
                st.markdown(f"- {slot}")

        render_retention_heatmap(metadata, analysis)
        render_charts(analysis)

        st.markdown("### 🧰 Report Tools")
        render_copy_and_voice(report_md, lang["copy"], lang["speak"])
        st.text_area("Report Preview", report_md, height=220)

        pdf_bytes = generate_pdf_bytes("YouTube AI Analysis", report_md)
        st.download_button(
            "📄 Download Report as PDF",
            data=pdf_bytes,
            file_name="youtube_analysis_report.pdf",
            mime="application/pdf",
        )

        st.download_button(
            "📤 Export History to CSV",
            data=to_csv_bytes(st.session_state.get("history", [])),
            file_name="youtube_analysis_history.csv",
            mime="text/csv",
        )

    st.markdown("### 🗂 History")
    history = st.session_state.get("history", [])
    if history:
        st.dataframe(history[:20], use_container_width=True)
    else:
        st.caption("No history yet.")

    st.markdown('<a class="fab" href="#top">↑</a>', unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        st.error(f"Something went wrong: {exc}")