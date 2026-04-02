# 🔬 CofO Image Analysis Lab
### Digital Image Processing for Physics & Astronomy

This application provides a web-based, mobile-friendly alternative to **ImageJ/Fiji**. It is designed for students at the **College of the Ozarks** to perform quantitative image analysis directly from their devices, bypassing the need for local software installations.

---

## 🌟 Core Functionality

### 1. Interactive RGB Extraction
* **Coordinate Mapping:** Click or tap any pixel to retrieve real-time **Red, Green, and Blue** intensity values (0–255).
* **Point Selection:** Precise $(x, y)$ coordinate tracking for mapping features across multiple experimental frames.

### 2. Background Subtraction
To isolate true signals (such as mineral fluorescence or photonic crystal reflections), the app allows for digital background subtraction:
$$I_{final} = I_{sample} - I_{dark}$$
This process removes consistent sensor noise and ambient light contamination, ensuring that the measured RGB values represent the physical phenomena rather than environmental interference.

### 3. Region of Interest (ROI) & Area Analysis
* **Scale Calibration:** Define a "pixels-per-mm" constant using a reference object in the frame.
* **Area Measurement:** Calculate the surface area of irregular shapes, essential for biomechanics or material science labs.
* **Mean Intensity:** Automatically average the brightness across a selected region to reduce the impact of local fluctuations.

---

## 📂 Laboratory Applications

This tool is optimized for several key modules in the **PHY 1004** and **PHY 1014** curricula at the College of the Ozarks:

* **Mars Rock Phosphorescence:** Quantifying the UV-excited "afterglow" of Gale Crater simulants. By using background subtraction to remove the initial UV flash, students can isolate the phosphorescent decay and analyze the specific RGB signatures of different mineral compositions.
* **Polarization and Birefringence:** Analyzing the interference colors produced by stress-induced birefringence in thin films and plastics. Students can use the RGB extractor to map phase retardation values and quantify the optical properties of anisotropic materials.
* **Chromomagnetic Ferrofluids:** Investigating the "structural color" of ferrofluids under varying magnetic fields. The app allows for precise intensity profiling of laser diffraction patterns and Bragg-like reflections to determine nanoparticle spacing and alignment.
---

## 🚀 Getting Started

### Local Development
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/pommere/cofo-image-analyzer.git](https://github.com/pommere/cofo-image-analyzer.git)