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

st.sidebar.header("1. Tool Selection")
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

st.sidebar.header("2. Calibration")
px_to_mm = st.sidebar.number_input("Scale (pixels per mm)", value=1.0, min_value=0.001, format="%.4f")

# --- 3. STABLE IMAGE PROCESSING ---
@st.cache_data(show_spinner=False)
def get_processed_image(file_bytes, dark_bytes=None):
    if not file_bytes:
        return None
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    arr = np.array(img)
    if dark_bytes:
        d_img = Image.open(BytesIO(dark_bytes)).convert("RGB")
        d_arr = np.array(d_img)
        if arr.shape == d_arr.shape:
            arr = cv2.subtract(arr, d_arr)
    return arr

# --- 4. DATA INPUT ---
st.subheader("📁 Data Input")
sample_file = st.file_uploader("Upload Sample Image", type=["jpg", "jpeg", "png"], key="uploader_s")
dark_file = st.file_uploader("Upload Dark/Reference Frame (Optional)", type=["jpg", "jpeg", "png"], key="uploader_d")

if sample_file:
    # Use cached processor to stabilize the array in memory
    processed_arr = get_processed_image(sample_file.getvalue(), dark_file.getvalue() if dark_file else None)
    
    if processed_arr is not None:
        real_h, real_w, _ = processed_arr.shape
        
        # Standardize dimensions for mobile/desktop stability
        canvas_width = 350 
        scale_factor = real_w / canvas_width
        canvas_height = int(real_h / scale_factor)

        # Convert to PIL for the canvas component
        display_pil = Image.fromarray(processed_arr.astype(np.uint8))

        # --- 5. INTERACTIVE CANVAS (Session-Safe Version) ---
        st.divider()
        
        # Using a fixed key like 'physics_canvas_v2' prevents SessionInfo desync
        canvas_result = st_canvas(
            fill_color="rgba(141, 32, 60, 0.3)", 
            stroke_width=2,
            stroke_color="#8D203C",
            background_image=display_pil,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode=drawing_mode,
            point_display_radius=5 if drawing_mode == 'point' else 0,
            key="physics_canvas_v2", 
        )

        # --- 6. DATA EXTRACTION (Override: Latest Only) ---
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if objects:
                st.markdown("---")
                st.subheader("Region Statistics")
                
                # We strictly only care about the most recent shape drawn
                obj = objects[-1]
                
                # Mapping coordinates
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
                    elif obj["type"] == "path": # Freehand
                        w, h = int(obj["width"] * scale_factor), int(obj["height"] * scale_factor)

                    # Extract ROI
                    y1, y2 = max(0, top), min(real_h, top + h)
                    x1, x2 = max(0, left), min(real_w, left + w)
                    roi = processed_arr[y1:y2, x1:x2]
                    
                    if roi.size > 0:
                        avg_rgb = np.mean(roi, axis=(0, 1))
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Red Intensity", f"{avg_rgb[0]:.1f}")
                        m2.metric("Green Intensity", f"{avg_rgb[1]:.1f}")
                        m3.metric("Blue Intensity", f"{avg_rgb[2]:.1f}")
                        
                        area_mm = ( (x2-x1) * (y2-y1) ) / (px_to_mm**2)
                        st.write(f"**Bounding Area:** {area_mm:.2f} mm²")
                    else:
                        st.warning("Selection outside image boundaries.")

                elif obj["type"] == "point":
                    # 3x3 local average for single points
                    roi = processed_arr[max(0, top-1):top+2, max(0, left-1):left+2]
                    avg_rgb = np.mean(roi, axis=(0, 1))
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Red", f"{avg_rgb[0]:.0f}")
                    m2.metric("Green", f"{avg_rgb[1]:.0f}")
                    m3.metric("Blue", f"{avg_rgb[2]:.0f}")

else:
    st.info("Awaiting image upload to begin analysis.")