"""
IIBA East Tennessee Chapter — shared brand constants.

Import BRAND_CSS in any Streamlit app and call:
    st.html(BRAND_CSS)
as the first statement in main() to apply ETN typography and colors.
"""

# Palette reference:
#   #002E38  — dark teal (body text, headings)
#   #DB5D00  — orange (hero, accent, TrailBlaze)
#   #00758C  — medium teal (labels, secondary)
#   #C6D0D0  — light teal-gray (borders, dividers)
#   #F5F5F5  — near-white (card backgrounds)

BRAND_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@700&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  /* Global typography */
  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    color: #002E38;
  }
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Roboto Condensed', system-ui, sans-serif;
    font-weight: 700;
  }

  /* Hero section */
  .hero-section {
    background-color: #DB5D00;
    padding: 3.5rem 2rem 2.5rem;
    text-align: center;
    border-radius: 4px;
    margin-bottom: 2rem;
  }
  .hero-eyebrow {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    color: rgba(255,255,255,0.9);
    font-size: 0.95rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
  }
  .hero-title {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    font-size: 2.75rem;
    line-height: 1.15;
    margin: 0 0 0.75rem;
  }
  .hero-tagline {
    font-family: 'IBM Plex Sans', sans-serif;
    color: rgba(255,255,255,0.95);
    font-size: 1.15rem;
    line-height: 1.6;
    max-width: 600px;
    margin: 0 auto 1.25rem;
  }
  .hero-meta {
    font-family: 'IBM Plex Sans', sans-serif;
    color: rgba(255,255,255,0.85);
    font-size: 0.9rem;
    letter-spacing: 0.05em;
  }

  /* Section headers */
  .section-header {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #002E38;
    font-size: 1.85rem;
    padding-bottom: 0.4rem;
    border-bottom: 4px solid #DB5D00;
    margin-bottom: 1.5rem;
  }

  /* Session timeline node */
  .session-node {
    text-align: center;
    padding: 0.75rem 0.5rem;
  }
  .session-dot {
    width: 48px;
    height: 48px;
    background-color: #DB5D00;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 0.5rem;
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: white;
    font-size: 1.1rem;
  }
  .session-month {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #00758C;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .session-title-small {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #002E38;
    font-size: 0.8rem;
    margin-top: 0.25rem;
    line-height: 1.3;
  }

  /* Slide cards */
  .slide-card {
    background: #FFFFFF;
    border: 1px solid #C6D0D0;
    border-top: 4px solid #DB5D00;
    border-radius: 4px;
    padding: 1.25rem 1rem;
    min-height: 200px;
  }
  .slide-card .session-label {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #00758C;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
  }
  .slide-card h3 {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #002E38;
    font-size: 1rem;
    margin: 0 0 0.5rem;
  }
  .slide-card p {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #002E38;
    font-size: 0.875rem;
    line-height: 1.55;
    margin: 0;
  }
  .slide-empty {
    color: #888;
    font-style: italic;
    font-size: 0.875rem;
  }

  /* TrailBlaze section */
  .trailblaze-section {
    background-color: #DB5D00;
    border-radius: 4px;
    padding: 2.5rem 2rem;
    margin: 1rem 0;
  }
  .trailblaze-section h2 {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    font-size: 2rem;
    margin-bottom: 1rem;
  }
  .trailblaze-section p {
    font-family: 'IBM Plex Sans', sans-serif;
    color: rgba(255,255,255,0.97);
    font-size: 1.05rem;
    line-height: 1.75;
    margin: 0;
  }
  .trailblaze-stat {
    font-family: 'Roboto Condensed', sans-serif;
    font-weight: 700;
    color: #FFFFFF;
    font-size: 1.4rem;
    border-top: 2px solid rgba(255,255,255,0.4);
    padding-top: 1rem;
    margin-top: 1rem;
    text-align: center;
  }

  /* MCQ section */
  .mcq-container {
    background: #F5F5F5;
    border-radius: 4px;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }
  .mcq-question {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    color: #002E38;
    font-size: 1.05rem;
    margin-bottom: 1rem;
  }

  /* Section divider */
  .section-divider {
    border: none;
    border-top: 1px solid #C6D0D0;
    margin: 2.5rem 0;
  }

  /* Content Studio / authoring utilities */
  .gap-radar-gap {
    color: #C0392B;
    font-weight: 600;
  }
  .gap-radar-draft {
    color: #E67E22;
    font-weight: 600;
  }
  .gap-radar-published {
    color: #27AE60;
    font-weight: 600;
  }
</style>
"""
