import os

css_path = 'static/css/themes.css'
with open(css_path, 'r', encoding='utf-8') as f:
    content = f.read()

responsive_css = """
/* =========================================================
   RESPONSIVE DESIGN (MOBILE & TABLET)
========================================================= */

/* Tablets and smaller screens */
@media (max-width: 992px) {
    /* Hero section */
    .hero {
        grid-template-columns: 1fr;
        padding: 2rem;
        gap: 2rem;
    }
    
    .hero-image {
        grid-row: 1; /* Move image to top */
    }
    
    /* Wardrobe layout */
    .wardrobe-container {
        flex-direction: column;
    }
    
    .left-panel, .right-panel {
        width: 100%;
        border-right: none;
        border-bottom: 1px solid rgba(0,0,0,0.1);
        height: auto;
    }
}

/* Mobile screens */
@media (max-width: 768px) {
    /* Navbar */
    nav {
        padding: 1rem 1.5rem !important;
        flex-wrap: wrap;
    }
    
    .nav-links {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        justify-content: center;
        width: 100%;
        margin-top: 1rem;
    }

    /* Fonts & Typography */
    h1 {
        font-size: 2.2rem !important;
    }
    
    /* Upload Grid */
    .wardrobe-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 1rem !important;
        padding: 1rem !important;
    }
    
    .filter-row {
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .filter-chip {
        padding: 0.4rem 0.8rem;
        font-size: 0.7rem;
    }

    /* Result pages grid */
    .body-result-grid, .color-grid {
        grid-template-columns: 1fr !important;
    }
    
    /* Auth Modal / Auth pages */
    .auth-card {
        padding: 2rem 1rem !important;
    }
}

/* Very small mobile */
@media (max-width: 480px) {
    .wardrobe-grid {
        grid-template-columns: 1fr !important;
    }
}
"""

if 'RESPONSIVE DESIGN (MOBILE & TABLET)' not in content:
    with open(css_path, 'a', encoding='utf-8') as f:
        f.write(responsive_css)
    print("Added responsive CSS to themes.css")
else:
    print("Responsive CSS already exists in themes.css")

