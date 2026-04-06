import streamlit as st
import json
from twelvelabs_client import (
    create_index,
    upload_video,
    run_compliance_query,
    filter_by_video,
    extract_violations,
    deduplicate_violations,
    build_compliance,
    analyze_video    
)

INDEXES = {
    "Demo Index": "69d317e09b2cb1a1df3189d7"
}

VIDEOS = {
    "69d317e09b2cb1a1df3189d7": {
        "Tattoo Coverage": "69d317e27fbe7f3d0d510056",
        "Weight Loss Drink": "69d334ae1e1c7a47bc661228",
        "Bartender": "69d334ad80a3faf42bda3cf7",
        "DIY Perfume": "69d334ae9b2cb1a1df318e59"
    }
}

# ----------------------------
# PROMPTS (your improved ones)
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

st.set_page_config(page_title="Video Analysis Demo", layout="wide")

st.title("🎥 Video Analysis Platform")
st.subheader("Compliance • Relevance • Enrichment • Description")

# Sidebar selection
st.sidebar.header("Configuration")

index_name = st.sidebar.selectbox("Select Index", list(INDEXES.keys()))
index_id = INDEXES[index_name]

video_name = st.sidebar.selectbox("Select Video", list(VIDEOS[index_id].keys()))
video_id = VIDEOS[index_id][video_name]

st.sidebar.markdown("---")
run_analysis = st.sidebar.button("🚀 Run Analysis")

# ----------------------------
# MAIN
# ----------------------------

st.markdown(f"### Selected Video: **{video_name}**")
st.markdown(f"Video ID: `{video_id}`")

if run_analysis:

    with st.spinner("Running analysis..."):

        compliance = json.loads(analyze_video(COMPLIANCE_PROMPT, video_id).data)
        relevance = json.loads(analyze_video(RELEVANCE_PROMPT, video_id).data)
        enrichment = json.loads(analyze_video(ENRICHMENT_PROMPT, video_id).data)
        description = json.loads(analyze_video(DESCRIPTION_PROMPT, video_id).data)

        final_output = {
            "video_id": video_id,
            "compliance": compliance,
            "relevance": relevance,
            "enrichment": enrichment,
            "description": description
        }

    # ----------------------------
    # TOP SUMMARY
    # ----------------------------

    st.markdown("## 🔎 Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Compliance Status",
            compliance.get("overall_status", "unknown").upper()
        )

    with col2:
        st.metric(
            "Relevance Score",
            relevance.get("overall_score", "N/A")
        )

    with col3:
        st.metric(
            "Issues Found",
            compliance.get("issue_count", 0)
        )

    st.markdown("---")

    decision = "APPROVE" if compliance["overall_status"] == "clear" else "REVIEW"

    st.metric("Decision", decision)

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
                with st.container():
                    st.markdown(f"### ⚠️ {issue['category'].replace('_',' ').title()}")
                    st.write(f"Severity: {issue['severity']}")
                    st.write(f"Timestamps: {', '.join(issue['timestamps'])}")
                    st.write(issue["explanation"])
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
