import streamlit as st
from PIL import Image
import streamlit.components.v1 as html

# Page configuration
st.set_page_config(
    page_title="StreetNets | No-Code Network Analysis",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Global Reset & Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit Boilerplate */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove default top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    /* --- HERO SECTION --- */
    .hero-container {
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        padding: 4rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 1rem;
        line-height: 1.1;
    }
    
    .hero-highlight {
        background: linear-gradient(120deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        color: #64748b;
        max-width: 600px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }

    /* --- CARDS & FEATURES --- */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: #cbd5e1;
    }
    
    .icon-box {
        width: 50px;
        height: 50px;
        background: #eff6ff;
        color: #2563eb;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 1.5rem;
    }

    /* --- STEPS SECTION --- */
    .step-number {
        font-size: 4rem;
        font-weight: 900;
        color: #e2e8f0;
        line-height: 1;
        margin-bottom: -1rem;
        position: relative;
        z-index: 0;
    }
    
    .step-content {
        position: relative;
        z-index: 1;
        padding-top: 0.5rem;
    }

    /* --- BUTTONS --- */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 1rem;
        transition: all 0.2s;
    }
    
    /* Primary Button Style */
    div[data-testid="column"] > div > div > div > div > .stButton > button {
        background-color: white; 
        color: #1e293b;
        border: 1px solid #cbd5e1;
    }
    div[data-testid="column"] > div > div > div > div > .stButton > button:hover {
        border-color: #2563eb;
        color: #2563eb;
    }

    /* Footer */
    .custom-footer {
        border-top: 1px solid #e2e8f0;
        margin-top: 4rem;
        padding: 2rem 0;
        text-align: center;
        color: #94a3b8;
    }

</style>
""", unsafe_allow_html=True)

# Helper for navigation
def safe_nav(page_name):
    try:
        st.switch_page(f"pages/{page_name}.py")
    except:
        st.warning(f"Page '{page_name}' not found. Ensure files are in a 'pages/' folder.")

def main():
    # --- LOGO AREA ---
    # Centered logo using columns
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        # If you have a logo, uncomment below:
        # st.image("logo.png", width=150)
        pass 

    # --- HERO SECTION ---
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">
            Unlock Urban Insights <br>
            <span class="hero-highlight">Without Writing Code</span>
        </h1>
        <p class="hero-subtitle">
            StreetNets turns complex OpenStreetMap data into actionable graphs and visualizations. 
            Perfect for urban planners, researchers, and the curious.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- ACTION BUTTONS ---
    # Centered buttons container
    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
    
    with col2:
        if st.button("🏢 Start Analysis", use_container_width=True):
            safe_nav("Retrieve_city_data")
            
    with col3:
        if st.button("📚 Glossary", use_container_width=True):
            safe_nav("Glossary")
            
    with col4:
        if st.button("⬇️ Get Data", use_container_width=True):
            safe_nav("Download_dataframes")

    st.markdown("---")

    # --- VALUE PROPOSITION (Cards) ---
    st.markdown("<h3 style='text-align: center; margin-bottom: 2rem;'>Why StreetNets?</h3>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box">⚡</div>
            <h3>Instant Access</h3>
            <p style="color: #64748b;">Forget Python scripts and API keys. Just type a city name and get the network data instantly.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box">📊</div>
            <h3>Visual Analytics</h3>
            <p style="color: #64748b;">Understand connectivity, circuity, and street orientation through beautiful interactive graphs.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box">💾</div>
            <h3>Export Ready</h3>
            <p style="color: #64748b;">Download clean nodes and edges (CSV/Shapefile) ready for GIS software or Excel.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- DETAILED FEATURES (Zig-Zag Layout) ---
    st.markdown("<div style='margin-top: 4rem;'></div>", unsafe_allow_html=True)
    
    # Feature 1
    f1_col1, f1_col2 = st.columns([1, 1], gap="large")
    with f1_col1:
        st.image("https://placehold.co/600x400/png?text=Interactive+Map+Preview", use_container_width=True)
        # Replace above line with: st.image("your_screenshot_1.png")
    with f1_col2:
        st.subheader("Interactive Map Interface")
        st.write("""
        Don't fly blind. Our interactive map allows you to visualize the exact area you are retrieving.
        
        * **Bounding Box selection:** Define precise study areas.
        * **Polygon Drawing:** Draw custom shapes for irregular neighborhoods.
        * **Real-time Preview:** See the streets before you process them.
        """)

    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)

    # Feature 2
    f2_col1, f2_col2 = st.columns([1, 1], gap="large")
    with f2_col1:
        st.subheader("Metric Calculation")
        st.write("""
        We automatically calculate the hard math for you. 
        
        * **Circuity:** How direct are the routes?
        * **Node Density:** How "walkable" is the intersection density?
        * **Street Orientation:** Are streets aligned North-South or chaotic?
        """)
    with f2_col2:
        st.image("https://placehold.co/600x400/png?text=Polar+Charts+&+Stats", use_container_width=True)
        # Replace above line with: st.image("your_screenshot_2.png")

    st.markdown("---")

    # --- HOW IT WORKS (Steps) ---
    st.markdown("<h2 style='text-align: center; margin-bottom: 3rem;'>From Zero to Graph in 3 Steps</h2>", unsafe_allow_html=True)
    
    step1, step2, step3 = st.columns(3)
    
    with step1:
        st.markdown("""
        <div style="text-align: center;">
            <div class="step-number">01</div>
            <div class="step-content">
                <h4>Select Location</h4>
                <p style="color: #64748b; font-size: 0.9rem;">Type a city name or draw a box on the map.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with step2:
        st.markdown("""
        <div style="text-align: center;">
            <div class="step-number">02</div>
            <div class="step-content">
                <h4>Process Network</h4>
                <p style="color: #64748b; font-size: 0.9rem;">Our engine builds the graph topology in seconds.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with step3:
        st.markdown("""
        <div style="text-align: center;">
            <div class="step-number">03</div>
            <div class="step-content">
                <h4>Analyze & Download</h4>
                <p style="color: #64748b; font-size: 0.9rem;">View the stats or download the raw data.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    st.markdown("""
    <div class="custom-footer">
        Built with ❤️ using OSMnx and Streamlit <br>
        <span style="font-size: 0.8rem;">Data © OpenStreetMap contributors</span>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()