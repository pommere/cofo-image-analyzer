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
    layout="centered"  # Reverted to centered for mobile screens
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
    # This places the logo right next to the title
    st.image("cofo-logo.jpg", width=128) 

with col2:
    st.markdown(f"""
        <h1 style='color: #000000; margin-bottom: 0; padding-top: 10px; '>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.5em; margin-top: 0;'>
        College of the Ozarks | "Hard Work U"
        </p>
    """, unsafe_allow_html=True)

# Updated to be applicable to Image Analysis/Phosphorescence Lab
st.markdown(r"""
Welcome to the Physics Lab! Students deduce the physical properties of geological 
specimens by modeling **UV-excited phosphorescence** and pixel-level kinetics. 
The validity of these observations is explored by examining the **Intensity** ($I$) 
decay constraints and signal-to-noise ratios found in digital imagery.

1. **Upload your Sample Image** (and optional Dark Frame) below.
2. The app will extract **RGB values** and coordinates to estimate physical data.
""")

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("1. Laboratory Module")
module = st.sidebar.selectbox("Select Experiment", 
    ["Mars Rock Phosphorescence", "Polarization & Birefringence", "Chromomagnetic Ferrofluids", "General Analysis"])

st.sidebar.header("2. Calibration")
px_to_mm = st.sidebar.number_input("Scale (pixels per mm)", value=1.0, min_value=0.001)

# --- 4. IMAGE LOADING & BACKGROUND SUBTRACTION ---
st.subheader("📁 Data Input")

# Stacked vertically for mobile rather than side-by-side columns
sample_file = st.file_uploader("Upload Sample Image", type=["jpg", "jpeg", "png"])
with st.expander("Advanced: Upload Dark Frame (Background Subtraction)"):
    dark_file = st.file_uploader("Upload Dark/Reference Frame", type=["jpg", "jpeg", "png"])

if sample_file:
    sample_img = Image.open(sample_file).convert("RGB")
    sample_arr = np.array(sample_img)

    if dark_file:
        dark_img = Image.open(dark_file).convert("RGB")
        dark_arr = np.array(dark_img)
        
        if sample_arr.shape == dark_arr.shape:
            processed_arr = cv2.subtract(sample_arr, dark_arr)
            st.success("✅ Background Subtraction Applied")
        else:
            st.error("❌ Error: Image dimensions must match for subtraction.")
            processed_arr = sample_arr
    else:
        processed_arr = sample_arr

    # --- 5. INTERACTIVE ANALYSIS (Vertical Layout) ---
    st.divider()
    st.subheader("Analysis View")
    st.info("Tap on the image below to extract RGB values.")
    
    # Image takes up full width of the centered container
    value = streamlit_image_coordinates(Image.fromarray(processed_arr), use_column_width=True)

    if value:
        st.markdown("---")
        st.subheader("Pixel Data")
        
        real_height, real_width, _ = processed_arr.shape
        display_width = value['width']
        display_height = value['height']
        
        width_scale = real_width / display_width
        height_scale = real_height / display_height
        
        x = int(value['x'] * width_scale)
        y = int(value['y'] * height_scale)
        
        x = min(x, real_width - 1)
        y = min(y, real_height - 1)
        
        r, g, b = processed_arr[y, x]
        
        # Metrics stack nicely on small screens natively
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Red", r)
        m2.metric("Green", g)
        m3.metric("Blue", b)
        
        intensity = 0.299*r + 0.587*g + 0.114*b
        m4.metric("Luminance", f"{intensity:.1f}")
        
        st.write(f"**True Pixel Coordinates:** ({x}, {y})")
        st.caption(f"Physical Location: ({x/px_to_mm:.2f}, {y/px_to_mm:.2f}) mm")

    else:
        st.markdown("---")
        st.warning("Awaiting interaction. Tap a point on the image above.")

    # --- 6. HISTOGRAM ---
    with st.expander("📊 RGB Color Distribution"):
        import plotly.graph_objects as go
        fig = go.Figure()
        for i, color in enumerate(['red', 'green', 'blue']):
            hist, bins = np.histogram(processed_arr[:, :, i], bins=256, range=(0, 256))
            fig.add_trace(go.Scatter(x=bins[:-1], y=hist, name=color.capitalize(), line=dict(color=color)))
        fig.update_layout(title="Full Image Intensity Histogram", xaxis_title="Bit Value (0-255)", yaxis_title="Pixel Count")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload a sample image to begin analysis.")