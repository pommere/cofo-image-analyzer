import streamlit as st
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import os
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
        st.image(logo_path, width=128)

with col2:
    st.markdown(f"""
        <h1 style='color: #8D203C; margin-bottom: 0; padding-top: 10px; '>Image Analysis Lab</h1>
        <p style='color: #002147; font-style: italic; font-size: 1.5em; margin-top: 0;'>
        College of the Ozarks | "Hard Work U"
        </p>
    """, unsafe_allow_html=True)

st.markdown(r"""
Welcome to the Digital Image Analysis Lab! This tool allows you to convert qualitative 
visual observations into quantitative physical data. 

1. **Upload your Sample Image** (and optional Dark Frame).
2. **Calibrate your scale** and select a **Selection Tool** in the sidebar.
3. **Analyze regions** to extract mean intensities ($I$) and calculate physical areas ($mm^2$).
""")

# --- 3. SIDEBAR: SELECTION TOOLS ---
st.sidebar.header("1. Analysis Tools")
tool_mode = st.sidebar.selectbox(
    "Selection Tool",
    ("Point", "Rectangle", "Circle", "Freehand"),
    index=1
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

# --- 4. IMAGE LOADING & PROCESSING ---
st.subheader("📁 Data Input")
sample_file = st.file_uploader("Upload Sample Image", type=["jpg", "jpeg", "png"])
with st.expander("Advanced: Background Subtraction"):
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
            st.error("❌ Dimension Mismatch")
            processed_arr = sample_arr
    else:
        processed_arr = sample_arr

    # --- 5. INTERACTIVE CANVAS ---
    st.divider()
    st.subheader(f"Tool: {tool_mode}")
    
    # Calculate responsive height to maintain aspect ratio on canvas
    real_h, real_w, _ = processed_arr.shape
    display_width = 700 # Standard centered width
    scale_factor = real_w / display_width
    display_height = int(real_h / scale_factor)

    canvas_result = st_canvas(
        fill_color="rgba(141, 32, 60, 0.3)", 
        stroke_width=stroke_width,
        stroke_color="#8D203C",
        background_image=Image.fromarray(processed_arr),
        update_streamlit=True,
        height=display_height,
        width=display_width,
        drawing_mode=drawing_mode,
        key="canvas",
    )

    # --- 6. DATA EXTRACTION ---
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        if objects:
            st.markdown("---")
            st.subheader("Region Statistics")
            
            # Target the most recent shape
            obj = objects[-1]
            
            # Map display coords back to real array indices
            left = int(obj["left"] * scale_factor)
            top = int(obj["top"] * scale_factor)
            
            if obj["type"] == "rect":
                w = int(obj["width"] * scale_factor)
                h = int(obj["height"] * scale_factor)
                
                # Slice array to get ROI
                roi = processed_arr[top:top+h, left:left+w]
                
                if roi.size > 0:
                    r_avg, g_avg, b_avg = np.mean(roi, axis=(0, 1))
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Avg Red", f"{r_avg:.1f}")
                    c2.metric("Avg Green", f"{g_avg:.1f}")
                    c3.metric("Avg Blue", f"{b_avg:.1f}")
                    
                    area_mm = (w * h) / (px_to_mm**2)
                    c4.metric("Area", f"{area_mm:.2f} mm²")
                    st.caption(f"Bounding Box: {w}x{h} px")

            elif obj["type"] == "point":
                # Points in st_canvas have small offsets, center them
                x, y = left, top
                r, g, b = processed_arr[y, x]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Red", r)
                c2.metric("Green", g)
                c3.metric("Blue", b)
                st.write(f"**Coordinates:** ({x}, {y}) px")

            elif obj["type"] == "circle":
                radius = obj["radius"] * scale_factor
                area_mm = (np.pi * radius**2) / (px_to_mm**2)
                st.metric("Circular Area", f"{area_mm:.2f} mm²")
                st.write(f"**Radius:** {radius:.1f} px")

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