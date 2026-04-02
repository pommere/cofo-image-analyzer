import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import os
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# --- 1. SETTINGS & BRANDING ---
logo_path = "cofo-logo.jpg"
favicon = Image.open(logo_path) if os.path.exists(logo_path) else None

st.set_page_config(
    page_title="CofO | Image Analysis Lab", 
    page_icon=favicon, 
    layout="centered" 
)

# Custom CSS for College of the Ozarks Branding
st.markdown("""
    <style>
        section[data-testid="stSidebar"] * { color: white !important; }
        section[data-testid="stSidebar"] input { color: #8D203C !important; }
        .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span { color: #000000; }
        [data-testid="stMetricLabel"] { color: #444444 !important; }
        [data-testid="stMetricValue"] { color: #000000 !important; }
        section[data-testid="stSidebar"] hr { border-top: 1px solid #ffffff44 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
if os.path.exists(logo_path):
    st.sidebar.image(Image.open(logo_path), use_container_width=True)
st.sidebar.markdown("### **Physics Department**\nCollege of the Ozarks")

st.sidebar.header("1. Lab Settings")
stroke_width = st.sidebar.slider("Point Marker Size", 1, 10, 3)

# --- 3. MAIN HEADER & WELCOME ---
col1, col2 = st.columns([1, 4]) 
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=120)
with col2:
    st.markdown(f"""
        <h1 style='color: #8D203C; margin-bottom: 0; padding-top: 10px; '>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.3em; margin-top: 0;'>
        College of the Ozarks | "Hard Work U"
        </p>
    """, unsafe_allow_html=True)

st.markdown("""
**Objective:** Use the Point tool to sample specific coordinates on your specimen.
1. Upload your image.
2. Click directly on the sample to extract **Red, Green, and Blue** intensity values.
""")

# --- 4. STABLE IMAGE PROCESSING ---
@st.cache_data(show_spinner=False)
def get_processed_image(file_bytes):
    if not file_bytes: return None
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    return np.array(img)

# --- 5. DATA INPUT ---
sample_file = st.file_uploader("Upload Specimen Image", type=["jpg", "jpeg", "png"], key="uploader_s")

if sample_file:
    processed_arr = get_processed_image(sample_file.getvalue())
    
    if processed_arr is not None:
        real_h, real_w, _ = processed_arr.shape
        canvas_width = 350 
        scale_factor = real_w / canvas_width
        canvas_height = int(real_h / scale_factor)
        display_pil = Image.fromarray(processed_arr.astype(np.uint8))

        # --- 6. POINT CLICK CANVAS ---
        st.divider()
        st.caption("Click the image to sample data:")
        
        canvas_result = st_canvas(
            fill_color="rgba(141, 32, 60, 0.3)", 
            stroke_width=stroke_width,
            stroke_color="#8D203C",
            background_image=display_pil,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="point",
            key="physics_point_lab_v1", 
        )

        # --- 7. DATA EXTRACTION ---
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if objects:
                st.markdown("---")
                st.subheader("Point Analysis")
                
                # Analyze the most recent click
                obj = objects[-1]
                left = int(obj["left"] * scale_factor)
                top = int(obj["top"] * scale_factor)
                
                # Sample a small 3x3 window around the click for stability
                y1, y2 = max(0, top-1), min(real_h, top+2)
                x1, x2 = max(0, left-1), min(real_w, left+2)
                roi = processed_arr[y1:y2, x1:x2]
                
                if roi.size > 0:
                    avg_rgb = np.mean(roi, axis=(0, 1))
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Red Intensity", f"{avg_rgb[0]:.0f}")
                    c2.metric("Green Intensity", f"{avg_rgb[1]:.0f}")
                    c3.metric("Blue Intensity", f"{avg_rgb[2]:.0f}")
                    st.write(f"**Coordinates:** x={left}, y={top} (pixels)")
                else:
                    st.warning("Click detected outside image bounds.")

        # --- 8. GLOBAL INTENSITY ---
        with st.expander("📊 Full Image Statistics"):
            avg_all = np.mean(processed_arr, axis=(0, 1))
            st.write(f"**Global Mean RGB:** ({avg_all[0]:.1f}, {avg_all[1]:.1f}, {avg_all[2]:.1f})")

else:
    st.info("Awaiting specimen image...")