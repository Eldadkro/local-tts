import os

import httpx
import streamlit as st

from app.ui.api_client import build_synthesize_payload, clone_voice, get_voices, synthesize

MAX_TEXT_LENGTH = int(os.getenv("LOCAL_TTS_MAX_TEXT_LENGTH", "20000"))


def main() -> None:
    st.set_page_config(page_title="Local TTS", layout="centered")
    st.title("Local TTS")

    text = st.text_area(
        "Text to synthesize",
        height=160,
        max_chars=MAX_TEXT_LENGTH,
        help=f"Maximum {MAX_TEXT_LENGTH} characters.",
    )
    voice_mode = st.radio("Voice source", options=["preset", "clone"], horizontal=True)

    try:
        voices = get_voices()
    except httpx.HTTPError as exc:
        st.error(f"Unable to fetch voices from API: {exc}")
        return

    selected_preset = None
    cloned_voice_id = st.session_state.get("cloned_voice_id")

    if voice_mode == "preset":
        presets = voices.get("presets", [])
        if not presets:
            st.error("No preset voices available.")
            return
        selected_preset = st.selectbox("Preset voice", options=presets)
    else:
        uploaded = st.file_uploader("Reference audio", type=["wav", "mp3"])
        if uploaded is not None and st.button("Upload clone"):
            try:
                cloned_voice_id = clone_voice(uploaded.name, uploaded.getvalue(), uploaded.type)
                st.session_state["cloned_voice_id"] = cloned_voice_id
                st.success(f"Clone voice ready: {cloned_voice_id}")
            except httpx.HTTPError as exc:
                st.error(f"Failed to upload clone reference audio: {exc}")

        if cloned_voice_id:
            st.caption(f"Using cloned voice: {cloned_voice_id}")

    if st.button("Synthesize", type="primary"):
        if not text.strip():
            st.warning("Enter text before synthesis.")
            return

        if len(text) > MAX_TEXT_LENGTH:
            st.warning(f"Text exceeds the {MAX_TEXT_LENGTH}-character limit.")
            return

        if voice_mode == "clone" and not cloned_voice_id:
            st.warning("Upload reference audio and create a cloned voice first.")
            return

        payload = build_synthesize_payload(
            text=text,
            voice_mode=voice_mode,
            voice_id=selected_preset,
            cloned_voice_id=cloned_voice_id,
        )
        try:
            audio = synthesize(payload)
        except httpx.HTTPError as exc:
            st.error(f"Synthesis failed: {exc}")
            return

        st.audio(audio, format="audio/wav")


if __name__ == "__main__":
    main()
