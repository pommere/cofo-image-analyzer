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

# Sidebar Logo & Department Info
if os.path.exists(logo_path):
    st.sidebar.image(Image.open(logo_path), use_container_width=True)
st.sidebar.markdown("### **College of the Ozarks**\nDepartment of Mathematics and Physics")
st.sidebar.divider()

# --- 2. MAIN HEADER ---
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

# --- 3. SIDEBAR: SELECTION TOOLS ---
st.sidebar.header("1. Analysis Tools")
tool_mode = st.sidebar.selectbox(
    "Selection Tool",
    ("Rectangle", "Circle", "Point", "Freehand"),
    index=0
)

drawing_mode = {
    "Point": "point",
    "Rectangle": "rect",
    "Circle": "circle",
    "Freehand": "freedraw"
}[tool_mode]

stroke_width = st.sidebar.slider("Stroke Width", 1, 10, 3)

st.sidebar.header("2. Calibration")
px_to_mm = st.sidebar.number_input("Scale (pixels per mm)", value=1.0, min_value=0.001, format="%.4f")

# --- 4. STABLE IMAGE LOADING (Prevents Session Crashes) ---
@st.cache_data(show_spinner=False)
def get_processed_image(file_bytes, dark_bytes=None):
    # Process in a cached function so the Array memory address never changes
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    arr = np.array(img)
    if dark_bytes:
        d_img = Image.open(BytesIO(dark_bytes)).convert("RGB")
        d_arr = np.array(d_img)
        if arr.shape == d_arr.shape:
            arr = cv2.subtract(arr, d_arr)
    return arr

st.subheader("📁 Data Input")
sample_file = st.file_uploader("Upload Sample Image", type=["jpg", "jpeg", "png"])
with st.expander("Advanced: Background Subtraction"):
    dark_file = st.file_uploader("Upload Dark/Reference Frame", type=["jpg", "jpeg", "png"])

if sample_file:
    # Read bytes to pass to the cached processor
    s_bytes = sample_file.getvalue()
    d_bytes = dark_file.getvalue() if dark_file else None
    
    processed_arr = get_processed_image(s_bytes, d_bytes)
    real_h, real_w, _ = processed_arr.shape

    # --- 5. INTERACTIVE CANVAS ---
    st.divider()
    
    # Standardize dimensions for mobile stability
    canvas_width = 350 
    scale_factor = real_w / canvas_width
    canvas_height = int(real_h / scale_factor)

    # Convert to PIL for the canvas component
    display_pil = Image.fromarray(processed_arr.astype(np.uint8))
    
    # CRITICAL: A stable hardcoded key prevents "SessionInfo" desync errors
    canvas_result = st_canvas(
        fill_color="rgba(141, 32, 60, 0.3)", 
        stroke_width=stroke_width,
        stroke_color="#8D203C",
        background_image=display_pil,
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key="stable_lab_canvas",
    )

    # --- 6. DATA EXTRACTION ---
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        if objects:
            st.markdown("---")
            st.subheader("Region Statistics")
            
            # Target the most recent shape drawn
            obj = objects[-1]
            
            # Map display coords to real array indices
            left = int(obj["left"] * scale_factor)
            top = int(obj["top"] * scale_factor)
            
            if obj["type"] in ["rect", "circle", "path"]:
                if obj["type"] == "rect":
                    w, h = int(obj["width"] * scale_factor), int(obj["height"] * scale_factor)
                elif obj["type"] == "circle":
                    r = int(obj["radius"] * scale_factor)
                    w, h = 2*r, 2*r
                    left = int((obj["left"] - obj["radius"]) * scale_factor)
                    top = int((obj["top"] - obj["radius"]) * scale_factor)
                elif obj["type"] == "path": # Freehand bounding box
                    w, h = int(obj["width"] * scale_factor), int(obj["height"] * scale_factor)

                # Boundary safety check for slicing
                y1, y2 = max(0, top), min(real_h, top + h)
                x1, x2 = max(0, left), min(real_w, left + w)
                
                roi = processed_arr[y1:y2, x1:x2]
                
                if roi.size > 0:
                    avg_rgb = np.mean(roi, axis=(0, 1))
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Avg Red", f"{avg_rgb[0]:.1f}")
                    m2.metric("Avg Green", f"{avg_rgb[1]:.1f}")
                    m3.metric("Avg Blue", f"{avg_rgb[2]:.1f}")
                    
                    area_mm = ( (x2-x1) * (y2-y1) ) / (px_to_mm**2)
                    st.write(f"**Physical Area:** {area_mm:.2f} mm²")
                    st.caption(f"Peak Intensity in ROI: {np.max(roi)}")
                else:
                    st.warning("Selection is outside the image frame.")

            elif obj["type"] == "point":
                x, y = left, top
                roi = processed_arr[max(0, y-1):y+2, max(0, x-1):x+2]
                avg_rgb = np.mean(roi, axis=(0, 1))
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Red", f"{avg_rgb[0]:.0f}")
                m2.metric("Green", f"{avg_rgb[1]:.0f}")
                m3.metric("Blue", f"{avg_rgb[2]:.0f}")
                st.caption(f"Coordinates: ({x}, {y}) px")

    # --- 7. HISTOGRAM ---
    with st.expander("📊 RGB Color Distribution"):
        import plotly.graph_objects as go
        fig = go.Figure()
        for i, color in enumerate(['red', 'green', 'blue']):
            hist, bins = np.histogram(processed_arr[:, :, i], bins=256, range=(0, 256))
            fig.add_trace(go.Scatter(x=bins[:-1], y=hist, name=color.capitalize(), line=dict(color=color)))
        fig.update_layout(title="Intensity Histogram", xaxis_title="Bit Value", yaxis_title="Pixel Count")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload a sample image to begin analysis.")