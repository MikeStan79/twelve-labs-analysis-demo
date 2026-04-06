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


VIDEO_PATH = r"I:\Media\Videos\4K Video Downloader\12L\Worlds_Most_Full_Coverage_Foundation.mp4"

import os
import json

USE_CACHE = False

def main():
    import json

    video_id = "69d334ad80a3faf42bda3cf7"

    print("Running full video analysis...\n")

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

    print("\nFINAL OUTPUT:\n")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

    