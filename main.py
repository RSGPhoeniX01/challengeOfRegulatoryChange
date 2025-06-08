import streamlit as st
import tempfile
import os
import json
from datetime import datetime
import difflib
from change_detector import detect_changes
from llm_analysis import analyze_changes

#page configuration
st.set_page_config(page_title="Text Change Analyzer", layout="wide")
st.title("Text Change Analyzer")
#instructions for the user
st.markdown("""
Upload two versions of a regulatory document to analyze:
- **Deleted**: Present in old version but missing in new.
- **Added**: Present in new version only.
- **Modified**: Similar sections with significant changes.
""")

# file upload widgets
uploaded_file_v1 = st.file_uploader("Upload OLD version of document", type=["txt"], key="v1")
uploaded_file_v2 = st.file_uploader("Upload NEW version of document", type=["txt"], key="v2")

#save uploaded files to a temporary location
def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temp file and return the path."""
    if uploaded_file is None:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name

# Remove temporary files stored
def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

# Button to trigger analysis
if st.button("Analyze Changes"):
    if not uploaded_file_v1 or not uploaded_file_v2:
        st.error("Please upload both versions of the document.")
    else:
        path_v1 = path_v2 = None
        try:
            with st.spinner("Uploading and analyzing..."):
                path_v1 = save_uploaded_file(uploaded_file_v1)
                path_v2 = save_uploaded_file(uploaded_file_v2)

                # Check if files are empty
                if os.path.getsize(path_v1) == 0 or os.path.getsize(path_v2) == 0:
                    raise ValueError("One or both files are empty.")
                
                # Detect changes between the two files
                changes = detect_changes(path_v1, path_v2)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("results", exist_ok=True)
                diff_path = f"results/differences_{timestamp}.json"
                with open(diff_path, "w", encoding="utf-8") as f:
                    json.dump(changes, f, indent=2)

                st.info("Analyzing changes with LLM. This may take a moment...")
                
                # Analyze changes using LLM
                analysis = analyze_changes(changes)

                # Save LLM Analysis results
                analysis_path = f"results/analysis_{timestamp}.json"
                with open(analysis_path, "w", encoding="utf-8") as f:
                    json.dump(analysis, f, indent=2)

                # Store in session state
                st.session_state['changes'] = changes
                st.session_state['analysis'] = analysis
                st.session_state['timestamp'] = timestamp

            st.success("Analysis Complete!")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        finally:
            cleanup_files(path_v1, path_v2)

# Show download buttons and results if available in session state
if 'changes' in st.session_state and 'analysis' in st.session_state and 'timestamp' in st.session_state:
    st.download_button(
        label="Download Changes JSON",
        data=json.dumps(st.session_state['changes'], indent=2),
        file_name=f"changes_{st.session_state['timestamp']}.json",
        mime="application/json"
    )
    st.download_button(
        label="Download Analysis JSON",
        data=json.dumps(st.session_state['analysis'], indent=2),
        file_name=f"analysis_{st.session_state['timestamp']}.json",
        mime="application/json"
    )

    # Show results in a simple way
    for idx, change in enumerate(st.session_state['analysis'], 1):
        change_type = change.get("change_type", "Unknown")
        change_summary = change.get("change_summary", "No summary available")
        original = change.get("original", "Empty")
        updated = change.get("updated", "Empty")

        with st.expander(f"{idx}. {change_type} – {change_summary}"):
            st.markdown(f"**Change Summary:** {change_summary}")
            if original.strip():
                st.markdown("**Original:**")
                st.code(original)
            if updated.strip():
                st.markdown("**Updated:**")
                st.code(updated)

