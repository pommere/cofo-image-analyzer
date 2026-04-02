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
    layout="wide"
)

# Custom CSS for College of the Ozarks Branding (Kept from your original)
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
col1, col2 = st.columns([1, 5]) 
with col1:
    st.image(logo_path, width=120) if os.path.exists(logo_path) else None
with col2:
    st.markdown(f"""
        <h1 style='color: #8D203C; margin-bottom: 0; padding-top: 10px;'>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.2em; margin-top: 0;'>
        Digital Image Processing for Physics & Astronomy
        </p>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("1. Laboratory Module")
module = st.sidebar.selectbox("Select Experiment", 
    ["Mars Rock Phosphorescence", "Polarization & Birefringence", "Chromomagnetic Ferrofluids", "General Analysis"])

st.sidebar.header("2. Calibration")
px_to_mm = st.sidebar.number_input("Scale (pixels per mm)", value=1.0, min_value=0.001)

# --- 4. IMAGE LOADING & BACKGROUND SUBTRACTION ---
st.subheader("📁 Data Input")
up_col1, up_col2 = st.columns(2)

with up_col1:
    sample_file = st.file_uploader("Upload Sample Image", type=["jpg", "jpeg", "png"])
with up_col2:
    dark_file = st.file_uploader("Upload Dark/Reference Frame (Optional)", type=["jpg", "jpeg", "png"])

if sample_file:
    # Convert Sample to Array
    sample_img = Image.open(sample_file).convert("RGB")
    sample_arr = np.array(sample_img)

    if dark_file:
        dark_img = Image.open(dark_file).convert("RGB")
        dark_arr = np.array(dark_img)
        
        # Ensure sizes match for subtraction
        if sample_arr.shape == dark_arr.shape:
            # Physics Logic: I_final = I_sample - I_dark
            # Use cv2.subtract to prevent negative wrap-around (it clips at 0)
            processed_arr = cv2.subtract(sample_arr, dark_arr)
            st.sidebar.success("✅ Background Subtraction Applied")
        else:
            st.sidebar.error("❌ Error: Image dimensions must match for subtraction.")
            processed_arr = sample_arr
    else:
        processed_arr = sample_arr

    # --- 5. INTERACTIVE ANALYSIS ---
    st.divider()
    display_col, data_col = st.columns([2, 1])

    with display_col:
        st.subheader("Analysis View")
        st.info("Tap/Click on the image to extract RGB values from that pixel.")
        
        # Interactive Component
        value = streamlit_image_coordinates(Image.fromarray(processed_arr), use_column_width=True)

    with data_col:
        st.subheader("Pixel Data")
        if value:
            x, y = value['x'], value['y']
            # Bound check for scaling issues
            y = min(y, processed_arr.shape[0]-1)
            x = min(x, processed_arr.shape[1]-1)
            
            r, g, b = processed_arr[y, x]
            
            # Display Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Red", r)
            m2.metric("Green", g)
            m3.metric("Blue", b)
            
            st.metric("Coordinates", f"({x}, {y}) px")
            
            # Simple Intensity Logic
            intensity = 0.299*r + 0.587*g + 0.114*b
            st.write(f"**Luminance (Y'):** {intensity:.2f}")
            
            with st.expander("📝 Lab Note"):
                st.write(f"Coordinates at ({x}, {y}) represent a physical location of roughly "
                         f"({x/px_to_mm:.2f}, {y/px_to_mm:.2f}) mm based on your current calibration.")
        else:
            st.write("Click a point on the image to see results.")

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