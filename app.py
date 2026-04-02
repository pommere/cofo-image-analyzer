import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import os
from streamlit_image_coordinates import streamlit_image_coordinates

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

# Sidebar Logo & Department Info
if os.path.exists(logo_path):
    st.sidebar.image(Image.open(logo_path), use_container_width=True)
st.sidebar.markdown("### **College of the Ozarks**\nDepartment of Mathematics and Physics")
st.sidebar.divider()

# --- 2. MAIN HEADER ---
col1, col2 = st.columns([1, 4]) 
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=128)
with col2:
    st.markdown(f"""
        <h1 style='color: #8D203C; margin-bottom: 0; padding-top: 10px; '>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.5em; margin-top: 0;'>
        College of the Ozarks | "Hard Work U"
        </p>
    """, unsafe_allow_html=True)

st.markdown(r"""
Welcome to the Digital Image Analysis Lab! Convert qualitative visual observations into quantitative physical data.

1. **Upload your Sample Image** (and optional Dark Frame).
2. **Calibrate your scale** in the sidebar.
3. **Tap the image** to extract mean intensities ($I$) and calculate physical coordinates.
""")

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("1. Laboratory Module")
module = st.sidebar.selectbox("Select Experiment", 
    ["Mars Rock Phosphorescence", "Polarization & Birefringence", "Chromomagnetic Ferrofluids", "General Analysis"])

st.sidebar.header("2. Calibration")
px_to_mm = st.sidebar.number_input("Scale (pixels per mm)", value=1.0, min_value=0.001, format="%.4f")

# --- 4. DATA INPUT ---
st.subheader("📁 Data Input")
sample_file = st.file_uploader("Upload Sample Image", type=["jpg", "jpeg", "png"])
with st.expander("Advanced: Upload Dark Frame (Background Subtraction)"):
    dark_file = st.file_uploader("Upload Dark/Reference Frame", type=["jpg", "jpeg", "png"])

if sample_file:
    # Stable processing
    sample_img = Image.open(sample_file).convert("RGB")
    sample_arr = np.array(sample_img)

    if dark_file:
        dark_img = Image.open(dark_file).convert("RGB")
        dark_arr = np.array(dark_img)
        if sample_arr.shape == dark_arr.shape:
            processed_arr = cv2.subtract(sample_arr, dark_arr)
            st.success("✅ Background Subtraction Applied")
        else:
            st.error("❌ Dimension mismatch. Subtraction disabled.")
            processed_arr = sample_arr
    else:
        processed_arr = sample_arr

    # --- 5. INTERACTIVE ANALYSIS ---
    st.divider()
    st.subheader("Analysis View")
    st.info("Tap the image to sample a point:")
    
    # Using the coordinates component for better mobile stability
    value = streamlit_image_coordinates(Image.fromarray(processed_arr), use_column_width=True)

    if value:
        st.markdown("---")
        st.subheader("Pixel Analysis (3x3 Mean)")
        
        real_h, real_w, _ = processed_arr.shape
        # Scale tap to true array dimensions
        x = int(value['x'] * (real_w / value['width']))
        y = int(value['y'] * (real_h / value['height']))
        
        # Guard against edge-taps
        x = np.clip(x, 1, real_w - 2)
        y = np.clip(y, 1, real_h - 2)
        
        # Sample 3x3 ROI for noise reduction
        roi = processed_arr[y-1:y+2, x-1:x+2]
        r, g, b = np.mean(roi, axis=(0, 1))
        
        # Display Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Red", f"{r:.1f}")
        m2.metric("Green", f"{g:.1f}")
        m3.metric("Blue", f"{b:.1f}")
        
        luminance = 0.299*r + 0.587*g + 0.114*b
        m4.metric("Luminance", f"{luminance:.1f}")
        
        st.write(f"**Coordinates:** ({x}, {y}) px")
        st.caption(f"Physical Location: ({x/px_to_mm:.2f}, {y/px_to_mm:.2f}) mm")

    # --- 6. HISTOGRAM ---
    with st.expander("📊 Full Image RGB Distribution"):
        import plotly.graph_objects as go
        fig = go.Figure()
        for i, color in enumerate(['red', 'green', 'blue']):
            hist, bins = np.histogram(processed_arr[:, :, i], bins=256, range=(0, 256))
            fig.add_trace(go.Scatter(x=bins[:-1], y=hist, name=color.capitalize(), line=dict(color=color)))
        fig.update_layout(xaxis_title="Intensity (0-255)", yaxis_title="Pixel Count")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload a sample image to begin analysis.")