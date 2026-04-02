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
    # Use a clean IF block. This avoids the "DeltaGenerator" text dump.
    if os.path.exists(logo_path):
        st.image(logo_path, width=120)

with col2:
    st.markdown(f"""
        <h1 style='color: #8D203C; margin-bottom: 0; padding-top: 10px;'>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.2em; margin-top: 0;'>
        College of the Ozarks | Department of Physics
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
            # 1. Get the 'real' dimensions of the uploaded image
            real_height, real_width, _ = processed_arr.shape
        
            # 2. Get the dimensions of the image as displayed in the browser
            display_width = value['width']
            display_height = value['height']
        
            # 3. Calculate scaling factors
            width_scale = real_width / display_width
            height_scale = real_height / display_height
        
            # 4. Map 'click' coordinates to 'real' array indices
            x = int(value['x'] * width_scale)
            y = int(value['y'] * height_scale)
        
            # 5. Bound check (preventing index errors at the very edge)
            x = min(x, real_width - 1)
            y = min(y, real_height - 1)
        
            # 6. Extract the actual RGB
            r, g, b = processed_arr[y, x]
        
            # Display the corrected metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Red", r)
            m2.metric("Green", g)
            m3.metric("Blue", b)
        
            st.write(f"**True Pixel Coordinates:** ({x}, {y})")
        else:
            st.write("Click a point on the image to see results.")

else:
    st.info("Please upload a sample image to begin analysis.")