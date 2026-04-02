import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import os
from streamlit_image_coordinates import streamlit_image_coordinates

# --- 1. SETTINGS & BRANDING ---
# Official College of the Ozarks Branding
# Load Local Logo

# Make sure 'cofo_logo.png' is uploaded to your GitHub repo
logo_path = "cofo-logo.jpg"

# Load the image first
favicon = Image.open("cofo-logo.jpg")

# This MUST be the first Streamlit command
st.set_page_config(
    page_title="CofO | Inverted Pendulum Lab", 
    page_icon=favicon, 
    layout="centered"
)

st.markdown("""
    <style>
        /* 1. Force the Main Title and all headers to Maroon */
        h1, h2, h3, .stHeader {
            color: #8D203C !important;
        }

        /* 2. Target the Sidebar Background (The missing Maroon part) */
        [data-testid="stSidebar"] {
            background-color: #8D203C !important;
        }

        /* 3. Force Sidebar Text to White */
        [data-testid="stSidebar"] * {
            color: white !important;
        }

        /* 4. Fix Sidebar Input Boxes (Dark text on white background) */
        [data-testid="stSidebar"] input {
            color: #8D203C !important; 
        }

        /* 5. Keep the Main Body text black for readability */
        .stApp p, .stApp span, .stApp li {
            color: #000000 !important;
        }
        
        /* 6. Metric Styling */
        [data-testid="stMetricLabel"] { color: #444444 !important; }
        [data-testid="stMetricValue"] { color: #8D203C !important; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.image(logo, use_container_width=True)
else:
    # This acts as a fallback if the file isn't found
    st.sidebar.warning(f"Logo '{logo_path}' not found in repo.")

# Sidebar Branding
st.sidebar.markdown("### **College of the Ozarks**\nDepartment of Mathematics and Physics")
st.sidebar.divider()

# --- Styled Main Header with Logo ---
# Create two columns: a small one for the logo and a large one for the text
col1, col2 = st.columns([1, 4]) 

with col1:
    # This places the logo right next to the title
    st.image("cofo-logo.jpg", width=128) 

with col2:
    st.markdown(f"""
        <h1 style='color: #8D203C; margin-bottom: 0; padding-top: 10px;'>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.5em; margin-top: 0;'>
        College of the Ozarks | "Hard Work U"
        </p>
    """, unsafe_allow_html=True)

st.markdown(r"""
Welcome to the Physics Lab! Students deduce the local acceleration due to gravity ($g$)
by modeling human locomotion as an **inverted pendulum**. The validity of this model
is explored by examining the **Froude Number** ($Fr$) constraints and biological noise found
in their own gait.

1. Upload your **Phyphox CSV** file below.
2. The app will calculate the FFT to estimate $g$ from your stride period.
""")

# --- 3. SIDEBAR CONTROLS ---
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