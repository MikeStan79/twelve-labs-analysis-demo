import streamlit as st
import json
from twelvelabs_client import analyze_video

st.title("Video Analysis Demo")

video_id = st.text_input("Enter Video ID")

if st.button("Run Analysis"):
    result = analyze_video("YOUR_PROMPT", video_id)
    parsed = json.loads(result.data)

    st.json(parsed)
