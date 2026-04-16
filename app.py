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
        <h1 style='color: #000000; margin-bottom: 0; padding-top: 10px; '>Image Analysis Lab</h1>
        <p style='color: #8D203C; font-style: italic; font-size: 1.5em; margin-top: 0;'>
        College of the Ozarks | "Hard Work U"
        </p>
    """, unsafe_allow_html=True)

st.markdown(r"""
Welcome to the Physics Lab! Students deduce the physical properties of geological 
specimens by modeling **UV-excited phosphorescence** and pixel-level kinetics. 
The validity of these observations is explored by examining the **Intensity** ($I$) 
decay constraints and signal-to-noise ratios found in digital imagery.

1. **Upload your Sample Image** (and optional Dark Frame) below.
2. The app will extract average **RGB values** from your circular selection to estimate physical data.
""")

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("1. Selection Tool")
radius_px = st.sidebar.number_input("Selection Radius (pixels)", value=10, min_value=1, max_value=500)

st.sidebar.header("2. Calibration")
px_to_mm = st.sidebar.number_input("Scale (pixels per mm)", value=1.0, min_value=0.001)

# --- 4. IMAGE LOADING & BACKGROUND SUBTRACTION ---
st.subheader("📁 Data Input")

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

    # --- 5. INTERACTIVE ANALYSIS ---
    st.divider()
    st.subheader("Analysis View")
    st.info("Tap on the image below to extract data within your radius.")
    
    # Create a working copy for drawing the circle
    display_arr = processed_arr.copy()
    
    # Retrieve the last click from session state BEFORE rendering the image
    click_data = st.session_state.get("image_analyzer", None)
    
    x, y = None, None
    if click_data and click_data.get('x') is not None:
        real_height, real_width, _ = processed_arr.shape
        display_width = click_data['width']
        display_height = click_data['height']
        
        width_scale = real_width / display_width
        height_scale = real_height / display_height
        
        x = int(click_data['x'] * width_scale)
        y = int(click_data['y'] * height_scale)
        
        # Keep coordinates within image bounds
        x = max(0, min(x, real_width - 1))
        y = max(0, min(y, real_height - 1))
        
        # Draw the visual boundary on the display copy (Cyan for high contrast)
        cv2.circle(display_arr, (x, y), int(radius_px), (60, 32, 141), 2)

    # Render the interactive image with the circle drawn on it
    value = streamlit_image_coordinates(Image.fromarray(display_arr), key="image_analyzer", use_column_width=True)

    if x is not None and y is not None:
        st.markdown("---")
        st.subheader("Selection Data")
        
        # Create a filled mask to calculate the mathematical average of the selection
        mask = np.zeros(processed_arr.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), int(radius_px), 255, -1) 
        
        # Extract mean values inside the mask
        mean_color = cv2.mean(processed_arr, mask=mask)
        r, g, b = mean_color[0], mean_color[1], mean_color[2]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg Red", f"{r:.1f}")
        m2.metric("Avg Green", f"{g:.1f}")
        m3.metric("Avg Blue", f"{b:.1f}")
        
        intensity = 0.299*r + 0.587*g + 0.114*b
        m4.metric("Avg Luminance", f"{intensity:.1f}")
        
        st.write(f"**Center Pixel Coordinates:** ({x}, {y})")
        
        # Calculate physical dimensions based on calibration
        physical_x = x / px_to_mm
        physical_y = y / px_to_mm
        physical_area = np.pi * (radius_px / px_to_mm)**2
        st.caption(f"Physical Center: ({physical_x:.2f}, {physical_y:.2f}) mm | Sample Area: {physical_area:.2f} mm²")

    else:
        st.markdown("---")
        st.warning("Awaiting interaction. Tap a point on the image above.")

    # --- 6. HISTOGRAM ---
    # with st.expander("📊 Full Image RGB Distribution"):
    #     import plotly.graph_objects as go
    #     fig = go.Figure()
    #     for i, color in enumerate(['red', 'green', 'blue']):
    #         hist, bins = np.histogram(processed_arr[:, :, i], bins=256, range=(0, 256))
    #         fig.add_trace(go.Scatter(x=bins[:-1], y=hist, name=color.capitalize(), line=dict(color=color)))
    #     fig.update_layout(title="Full Image Intensity Histogram", xaxis_title="Bit Value (0-255)", yaxis_title="Pixel Count")
    #     st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload a sample image to begin analysis.")