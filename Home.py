import streamlit as st
from PIL import Image
import base64
from io import BytesIO
from streamlit.components.v1 import html
import folium
from streamlit_folium import st_folium
import os



# Page configuration
st.set_page_config(
    page_title="StreetNets - Make Street Network Data Accessible",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom styling */
    .main-header {
        
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
    }
    
    .hero-section {
    
        text-align: center;
        padding: 4rem 0;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: bold;
        color: #111827;
        margin-bottom: 1.5rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        color: #2563eb;
        display: block;
    }
    
    .hero-description {
        font-size: 1.25rem;
        color: #7c8391;
        margin-bottom: 2rem;
        max-width: auto;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }
    
    .problem-section {
        background-color: #000000;
        padding: 5rem 0;
        margin: 3rem -1rem;
    }
    
    .problem-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #111827;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .problem-card {
        background: white;
        padding: 2rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .problem-icon {
        width: 3rem;
        height: 3rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        font-size: 1.5rem;
    }
    
    .features-section {
        padding: auto;
    }
    
    .features-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #111827;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .features-description {
        font-size: 1.25rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 4rem;
        max-width: auto;
        margin-left: auto;
        margin-right: auto;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 0.75rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .feature-card.active {
        background: #eff6ff;
        border: 2px solid #bfdbfe;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        width: 3rem;
        height: 3rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .steps-section {
        background-color: #f9fafb;
        padding: 5rem 0;
        margin: 3rem -1rem;
    }
    
    .steps-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #111827;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .steps-description {
        font-size: 1.25rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 4rem;
    }
    
    .step-number {
        width: 4rem;
        height: 4rem;
        background: #2563eb;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0 auto 1rem auto;
    }
    
    .cta-section {
        background: linear-gradient(135deg, #2563eb 0%, #4338ca 100%);
        color: white;
        padding: 3rem;
        border-radius: 1.5rem;
        text-align: center;
        margin: 3rem 0;
    }
    
    .cta-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .cta-description {
        font-size: 1.25rem;
        opacity: 0.9;
        margin-bottom: 2rem;
        max-width: auto;
        margin-left: auto;
        margin-right: auto;
    }
    
    .footer-section {
        background: #111827;
        color: white;
        padding: 3rem 0;
        margin: 3rem -1rem -1rem -1rem;
    }
    
    .badge {
        position: absolute;
        top: -1rem;
        right: -1rem;
        background: #2563eb;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .image-container {
        position: relative;
        background: white;
        border-radius: 1rem;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
        padding: 2rem;
        border: 1px solid #e5e7eb;
        margin: 2rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 1.125rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #1d4ed8;
        transform: translateY(-1px);
    }
    
    /* Navigation styling */
    .nav-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 2rem 0;
    }
    
    .nav-logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .nav-logo-icon {
        width: 2rem;
        height: 2rem;
        background: #2563eb;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }
    
    .nav-logo-text {
        font-size: 1.5rem;
        font-weight: bold;
        color: #111827;
    }
</style>
""", unsafe_allow_html=True)

def load_image(image_path):
    """Load and return an image"""
    try:
        return Image.open(image_path)
    except:
        return None


# Button to navigate to other
def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)

def main():
    # Header/Navigation
    logo_path = "logo.png"

    try:
        os.path.exists(logo_path)
        
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="data:image/png;base64,{load_image(logo_path)}" width="180">
            </div>
            """, unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning("Logo da ORBTY não encontrado.")
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">
            Make Street Network Data<br>
            <span class="hero-subtitle">Accessible to Everyone</span>
        </h1>
        <p class="hero-description">
            Unlock the power of OpenStreetMap data without coding. Visualize, analyze, and understand urban street networks with our intuitive dashboard.
        </p>
    </div>
    """, unsafe_allow_html=True)


    # Hero buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏢 Retrieve city data", key="hero_start", use_container_width=True):
            nav_page("Retrieve_city_data", timeout_secs=3,)
    with col2:
        if st.button("⬇️ Download our dataframes", key="hero_demo", use_container_width=True):
            nav_page("Download_dataframes", timeout_secs=3)
    with col3:
        if st.button("📚 Learn More", key="hero_learn", use_container_width=True):
            nav_page("Glossary", timeout_secs=3)

    # Hero Image
    # street_networks_img = load_image("backups/street-networks-grid.jpg")
    # if street_networks_img:
    #     st.markdown('<div class="image-container">', unsafe_allow_html=True)
    #     st.image(street_networks_img, caption="Street network visualizations of different cities", use_container_width=True)
    #     st.markdown('<div class="badge">No Code Required</div>', unsafe_allow_html=True)
    #     st.markdown('</div>', unsafe_allow_html=True)
    
    # Problem Statement Section
    st.markdown("""
    <div class="problem-section">
        <h2 class="problem-title">
            Street Network Analysis Shouldn't Require a PhD in Programming
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Problem cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="problem-card">
            <div class="problem-icon" style="background: #fef2f2; color: #dc2626;">
                👥
            </div>
            <h3 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">Complex Tools</h3>
            <p style="color: #6b7280;">Existing solutions require Python knowledge and complex setup processes.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="problem-card">
            <div class="problem-icon" style="background: #fffbeb; color: #d97706;">
                ⚡
            </div>
            <h3 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">Time Consuming</h3>
            <p style="color: #6b7280;">Hours spent on data processing instead of actual analysis and insights.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="problem-card">
            <div class="problem-icon" style="background: #faf5ff; color: #9333ea;">
                📊
            </div>
            <h3 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">Limited Access</h3>
            <p style="color: #6b7280;">Valuable urban data insights locked behind technical barriers.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Features Section
    st.markdown("""
    <div class="features-section">
        <h2 class="features-title">Powerful Features, Simple Interface</h2>
        <p class="features-description">
            Everything you need to explore and analyze street networks, designed for researchers, planners, and curious minds.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features with interactive selection
    features = [
        {
            "title": "Interactive Visualizations",
            "description": "Explore street networks with beautiful, interactive maps and charts without writing a single line of code.",
            "icon": "📍",
            "image": folium.Map(location= ["-23.533773", "-46.625290"], zoom_start=10)
        },
        {
            "title": "Comprehensive Analytics", 
            "description": "Get detailed statistics about street networks including connectivity, orientation patterns, and network topology.",
            "icon": "📊",
            "image": "backups/city-orientations.png"
        },
        {
            "title": "Easy Data Export",
            "description": "Download processed street network data in CSV format for further analysis or reporting.",
            "icon": "💾",
            "image": "backups/street-networks-grid.jpg"
        }
    ]
    
    # Feature selection
    if 'active_feature' not in st.session_state:
        st.session_state.active_feature = 0
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        for i, feature in enumerate(features):
            active_class = "active" if i == st.session_state.active_feature else ""
            if st.button(f"{feature['icon']} {feature['title']}", key=f"feature_{i}"):
                st.session_state.active_feature = i
            
            st.markdown(f"""
            <div class="feature-card {active_class}">
                <div class="feature-icon" style="background: {'#2563eb' if i == st.session_state.active_feature else '#f3f4f6'}; color: {'white' if i == st.session_state.active_feature else '#6b7280'};">
                    {feature['icon']}
                </div>
                <h3 style="font-size: 1.25rem; font-weight: 600; color: #111827; margin-bottom: 0.5rem;">{feature['title']}</h3>
                <p style="color: #6b7280;">{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        active_feature = features[st.session_state.active_feature]
        feature_img = active_feature['image']
    
        if isinstance(active_feature['image'], folium.Map):
            # Display Folium map
            st_folium(active_feature['image'], width = '100%', height=1000)
        else:
            st.markdown('<div class="image-container">', unsafe_allow_html=True)
            st.image(feature_img, caption=active_feature['title'], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # How it Works Section
    st.markdown("""
    <div class="steps-section">
        <h2 class="steps-title">Three Simple Steps to Insights</h2>
        <p class="steps-description">
            From city selection to data download in minutes, not hours.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Steps
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center;">
            <div class="step-number">1</div>
            <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">Select Your City</h3>
            <p style="color: #6b7280;">Choose from our predefined list or enter any city available at OSM.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <div class="step-number">2</div>
            <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">Explore & Analyze</h3>
            <p style="color: #6b7280;">View interactive visualizations and comprehensive network statistics.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center;">
            <div class="step-number">3</div>
            <h3 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">Download Data</h3>
            <p style="color: #6b7280;">Export processed data in CSV format for further analysis.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # # Call to Action Section
    # st.markdown("""
    # <div class="cta-section">
    #     <h2 class="cta-title">Ready to Explore Street Networks?</h2>
    #     <p class="cta-description">
    #         Join researchers, urban planners, and data enthusiasts who are already using StreetNets to unlock urban insights.
    #     </p>
    # </div>
    # """, unsafe_allow_html=True)
    
    # # CTA buttons
    # col1, col2, col3 = st.columns([1, 1, 1])
    # with col2:
    #     if st.button("🚀 Launch StreetNets", key="cta_launch"):
    #         st.success("Redirecting to the main StreetNets dashboard...")
    #     if st.button("📚 View Documentation", key="cta_docs"):
    #         st.info("Documentation will be available soon!")
    
    # Footer
    st.markdown("""
    <div class="footer-section">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                <div style="width: 2rem; height: 2rem; background: #2563eb; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; color: white;">🛣️</div>
                <span style="font-size: 1.5rem; font-weight: bold;">StreetNets</span>
            </div>
            <div style="text-align: right; color: #9ca3af;">
                <p>Making street network data accessible to everyone.</p>
                <p style="font-size: 0.875rem; margin-top: 0.5rem;">Built with OpenStreetMap data</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

