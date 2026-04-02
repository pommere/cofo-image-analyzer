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
    
    # Force the array to uint8 to prevent 'blank' rendering issues
    display_img = Image.fromarray(processed_arr.astype(np.uint8))
    
    # Standardize width for mobile-friendly use
    canvas_width = 350 
    real_h, real_w, _ = processed_arr.shape
    scale_factor = real_w / canvas_width
    canvas_height = int(real_h / scale_factor)

    # Key includes 'dark_file' status so it resets when subtraction is toggled
    bg_status = "dark" if dark_file else "sample"
    canvas_key = f"canvas_{sample_file.name}_{bg_status}"

    canvas_result = st_canvas(
        fill_color="rgba(141, 32, 60, 0.3)", 
        stroke_width=stroke_width,
        stroke_color="#8D203C",
        background_image=display_img, # Explicitly processed PIL image
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode=drawing_mode,
        key=canvas_key,
    )

    # --- 6. DATA EXTRACTION ---
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        if objects:
            st.markdown("---")
            st.subheader("Region Statistics")
            
            obj = objects[-1]
            
            # Extract standard coordinates
            left = int(obj["left"] * scale_factor)
            top = int(obj["top"] * scale_factor)
            
            # Handle Shapes (Rect, Circle, and now Path/Freehand)
            if obj["type"] in ["rect", "circle", "path"]:
                if obj["type"] == "rect":
                    w = int(obj["width"] * scale_factor)
                    h = int(obj["height"] * scale_factor)
                elif obj["type"] == "circle":
                    r = int(obj["radius"] * scale_factor)
                    w, h = 2*r, 2*r
                    left = int((obj["left"] - obj["radius"]) * scale_factor)
                    top = int((obj["top"] - obj["radius"]) * scale_factor)
                elif obj["type"] == "path":
                    # Freehand bounding box
                    w = int(obj["width"] * scale_factor)
                    h = int(obj["height"] * scale_factor)

                # Boundary safety check
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
                    st.write(f"**Physical Area (Bounding Box):** {area_mm:.2f} mm²")
                    
                    # Add a quick peak intensity check (useful for phosphorescence)
                    st.caption(f"Peak Intensity in ROI: {np.max(roi):.0f}")
                else:
                    st.warning("Selection is outside image boundaries.")

            elif obj["type"] == "point":
                # Robust 3x3 average for single points
                x, y = left, top
                roi = processed_arr[max(0, y-1):y+2, max(0, x-1):x+2]
                avg_rgb = np.mean(roi, axis=(0, 1))
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Red", f"{avg_rgb[0]:.0f}")
                m2.metric("Green", f"{avg_rgb[1]:.0f}")
                m3.metric("Blue", f"{avg_rgb[2]:.0f}")

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