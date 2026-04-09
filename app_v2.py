import streamlit as st
import json
from twelvelabs_client import analyze_video

# ----------------------------
# SESSION CACHE
# ----------------------------

if "results_cache" not in st.session_state:
    st.session_state.results_cache = {}

# ----------------------------
# CONFIG
# ----------------------------

VIDEOS = {
    "Worlds Most Full Coverage Foundation": "69d317e27fbe7f3d0d510056",
    "I Lost 50 Pounds Drinking THIS": "69d334ae1e1c7a47bc661228",
    "Shots Time": "69d334ad80a3faf42bda3cf7",
    "Easiest way to make Dior Sauvage for men": "69d334ae9b2cb1a1df318e59",
    "An Effortlessly Chic Makeup Tutorial by Bobbi": "69d3529e80a3faf42bda411a",
    "Baked Balance Brighten Color Correcting Foundation": "69d334ae80a3faf42bda3cfb",
    "Bronzing Powder Makeup Tutorial": "69d3529d1e1c7a47bc6615bd",
    "Alicias 10 Minute Makeup Routine": "69d7ccbe4f56f5868588c8bb",
    "Makeup Transformation": "69d3529a80a3faf42bda4118"
}

# ----------------------------
# HELPERS
# ----------------------------

ID_TO_NAME = {v: k for k, v in VIDEOS.items()}


# ----------------------------
# PROMPTS
# ----------------------------

COMPLIANCE_PROMPT = """
You are an advertising compliance reviewer for creator-led beauty ads.

Assess this video against the following compliance rules.

Required policy categories:
1. hate_harassment
   - Hate speech, harassment, insulting or discriminatory language, gestures, or imagery
2. profanity_explicit
   - Profanity, explicit language, or sexualized language inappropriate for a paid ad
3. drugs_illegal_behavior
   - Drug use, drug references, illegal behavior, or promotion of unlawful acts
4. unsafe_or_misleading_product_usage
   - Unsafe use of a beauty product
   - Misleading demonstration of product performance
   - Unrealistic or inappropriate application
   - Harmful use near sensitive areas such as eyes
5. medical_or_cosmetic_claims
   - Unsupported efficacy claims
   - Medical-style claims
   - Before/after or transformational claims that imply guaranteed results

Additional advertiser-sensitive category:
6. alcohol_presence
   - Alcohol consumption, alcohol service, or alcohol-centric context

Instructions:
- Evaluate visual content, spoken audio, on-screen text, and overall context.
- Use multimodal reasoning. Do not rely only on transcript.
- Flag subtle or implied violations where appropriate.
- If uncertain, prefer REVIEW-style flagging rather than ignoring the issue.
- Group timestamps into ranges where possible.
- Use format "mm:ss-mm:ss" for ranges.
- Do not output second-by-second timestamp lists unless an issue is truly isolated.

Return JSON only:
{
  "overall_status": "clear | flagged",
  "issue_count": 0,
  "issues": [
    {
      "category": "hate_harassment | profanity_explicit | drugs_illegal_behavior | unsafe_or_misleading_product_usage | medical_or_cosmetic_claims | alcohol_presence",
      "severity": "low | medium | high",
      "timestamps": ["mm:ss-mm:ss"],
      "explanation": "Clear explanation of the risk and why it matters for paid advertising"
    }
  ],
  "confidence": "low | medium | high"
}
"""

RELEVANCE_PROMPT = """
You are evaluating whether this video is suitable for use in a paid beauty campaign.

Assess:

1. Product relevance:
   - Is a beauty product clearly shown or demonstrated?

2. Demonstration quality:
   - Is the product application clear and credible?

3. Audience suitability:
   - Is the content appropriate for a broad consumer audience?

4. Brand alignment:
   - Is the tone, style, and message appropriate for a premium beauty brand?

Return JSON:
{
  "product_relevance": "LOW | MEDIUM | HIGH",
  "demonstration_quality": "LOW | MEDIUM | HIGH",
  "audience_suitability": "LOW | MEDIUM | HIGH",
  "brand_alignment": "LOW | MEDIUM | HIGH",
  "overall_score": "LOW | MEDIUM | HIGH",
  "reasons": ["..."]
}

Be critical — do not assume content is suitable by default.
"""

ENRICHMENT_PROMPT = """
Extract structured metadata from this video for marketing analysis.

Production quality guidelines:

LOW:
- Poor lighting, shaky camera, low resolution
- Amateur or unedited content

MEDIUM:
- Decent lighting and framing
- Some editing but not professional

HIGH:
- Professional lighting and composition
- Clear focus, stable shots
- High production value or polished editing

Be decisive — do not default to medium unless clearly appropriate.

Video orientation guidelines:

VERTICAL:
- Portrait format (height > width)
- Typical of TikTok, Instagram Reels, YouTube Shorts
- Subject centered vertically, narrow frame

HORIZONTAL:
- Landscape format (width > height)
- Typical of YouTube, TV, cinematic content

Determine orientation based on framing and composition, not assumptions.

If the video appears formatted for mobile-first platforms, classify as VERTICAL.

Do not default to horizontal — choose based on visible layout.

Return JSON:
{
  "topics": [],
  "product_mentions": [],
  "brands_detected": [],
  "visual_elements": [],
  "creator_style": "tutorial | review | transformation | other",
  "demographics": {
    "age_group": "...",
    "gender": "..."
  },
  "video_properties": {
    "orientation": "horizontal | vertical",
    "production_quality": "low | medium | high"
  }
}
"""

DESCRIPTION_PROMPT = """
Provide a marketing-ready description of this video.

Return JSON:
{
  "short_description": "2–3 sentences",
  "detailed_description": "4–6 sentences including product, usage, and outcome",
  "YouTube ready title",
  "YouTube ready description"
}
"""


# ----------------------------
# UI
# ----------------------------

st.set_page_config(page_title="Video Analysis v2", layout="wide")

st.title("🎥 Video Analysis Platform (v2)")
st.caption("Includes caching + rerun control")

# Sidebar
video_name = st.sidebar.selectbox("Select Video", list(VIDEOS.keys()))
video_id = VIDEOS[video_name]

use_cache = st.sidebar.checkbox("Use cached results", value=True)
run_analysis = st.sidebar.button("🚀 Run Analysis")

st.markdown(f"### Selected Video: **{video_name}**")

# ----------------------------
# ANALYSIS LOGIC
# ----------------------------

cache_key = video_id

if run_analysis:

    if use_cache and cache_key in st.session_state.results_cache:
        st.info("Using cached results")

        final_output = st.session_state.results_cache[cache_key]

    else:
        with st.spinner("Running analysis..."):

            compliance = json.loads(analyze_video(COMPLIANCE_PROMPT, video_id).data)
            relevance = json.loads(analyze_video(RELEVANCE_PROMPT, video_id).data)
            enrichment = json.loads(analyze_video(ENRICHMENT_PROMPT, video_id).data)
            description = json.loads(analyze_video(DESCRIPTION_PROMPT, video_id).data)

            final_output = {
                "compliance": compliance,
                "relevance": relevance,
                "enrichment": enrichment,
                "description": description
            }

            st.session_state.results_cache[cache_key] = final_output

    compliance = final_output["compliance"]
    relevance = final_output["relevance"]
    enrichment = final_output["enrichment"]
    description = final_output["description"]

    # ----------------------------
    # SUMMARY
    # ----------------------------

    st.markdown("## 🔎 Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Compliance", compliance.get("overall_status", "unknown").upper())
    col2.metric("Relevance", relevance.get("overall_score", "N/A"))
    col3.metric("Issues", compliance.get("issue_count", 0))

    decision = "APPROVE" if compliance["overall_status"] == "clear" else "REVIEW"
    st.metric("Decision", decision)

    st.markdown("---")

    # ----------------------------
    # TABS
    # ----------------------------

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Compliance", "Relevance", "Enrichment", "Description", "Raw JSON"]
    )


    # ----------------------------
    # COMPLIANCE TAB
    # ----------------------------

    with tab1:
        st.subheader("Compliance Analysis")
    
        if compliance.get("issues"):
            for issue in compliance["issues"]:
                st.markdown(f"### ⚠️ {issue['category'].replace('_',' ').title()}")
    
                # ✅ Clean timestamp display
                st.write(f"Timestamps: {', '.join(issue['timestamps'])}")
    
                st.write(issue["explanation"])
                st.markdown("---")
        else:
            st.success("No compliance issues detected")

    # ----------------------------
    # RELEVANCE TAB
    # ----------------------------

    with tab2:
        st.subheader("Relevance Analysis")

        st.metric("Overall Score", relevance.get("overall_score", "N/A"))

        st.markdown("### Breakdown")
        st.write(f"Product Relevance: {relevance.get('product_relevance', 'N/A')}")
        st.write(f"Demonstration Quality: {relevance.get('demonstration_quality', 'N/A')}")
        st.write(f"Audience Suitability: {relevance.get('audience_suitability', 'N/A')}")
        st.write(f"Brand Alignment: {relevance.get('brand_alignment', 'N/A')}")

        if relevance.get("reasons"):
            st.markdown("### Reasons")
            for r in relevance["reasons"]:
                st.write(f"- {r}")

    # ----------------------------
    # ENRICHMENT TAB
    # ----------------------------

    with tab3:
        st.subheader("Enrichment")

        st.markdown("### Topics")
        st.write(", ".join(enrichment.get("topics", [])) or "None")
            
        st.markdown("### Products")
        st.write(", ".join(enrichment.get("product_mentions", [])) or "None")
        
        st.markdown("### Brands")
        st.write(", ".join(enrichment.get("brands_detected", [])) or "None")
        
        st.markdown("### Visual Elements")
        st.write(", ".join(enrichment.get("visual_elements", [])) or "None")
        
        st.markdown("### Creator Style")
        st.write(enrichment.get("creator_style", "N/A"))
        
        st.markdown("### Demographics")
        demo = enrichment.get("demographics", {})
        st.write(f"Age Group: {demo.get('age_group', 'N/A')}")
        st.write(f"Gender: {demo.get('gender', 'N/A')}")
        
        st.markdown("### Video Properties")
        props = enrichment.get("video_properties", {})
        st.write(f"Orientation: {props.get('orientation', 'N/A')}")
        st.write(f"Production Quality: {props.get('production_quality', 'N/A')}")
    # ----------------------------
    # DESCRIPTION TAB
    # ----------------------------

    with tab4:
        st.subheader("Description")
        
        st.markdown("### Short Description")
        st.write(description.get("short_description", ""))
        
        st.markdown("### Detailed Description")
        st.write(description.get("detailed_description", ""))

    # ----------------------------
    # RAW OUTPUT
    # ----------------------------

    with tab5:
        st.subheader("Full Output")
        st.json(final_output)

# ----------------------------
# CACHE VIEW
# ----------------------------

if st.session_state.results_cache:
    st.sidebar.markdown("### Cached Videos")
    for k in st.session_state.results_cache:
        name = ID_TO_NAME.get(k, k)
        st.sidebar.write(name)
