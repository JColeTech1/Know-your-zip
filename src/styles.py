"""
CSS styles for the Miami-Dade County Explorer app.

Kept in one place so app.py stays thin. Import with:
    from src.styles import APP_CSS
    st.markdown(APP_CSS, unsafe_allow_html=True)
"""

APP_CSS = """
<style>
    /* Global text color adjustments for dark mode */
    [data-theme="dark"] { color: #FFFFFF; }

    [data-theme="dark"] .stButton > button {
        color: #1C2B30;
        background-color: #F5F0E8;
    }
    [data-theme="dark"] .stButton > button:hover {
        color: white;
        background-color: #0E7C86;
    }
    [data-theme="dark"] div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        background-color: rgba(255, 255, 255, 0.1);
    }
    [data-theme="dark"] .title-text  { color: #FFFFFF; }
    [data-theme="dark"] .stMarkdown  { color: #FFFFFF; }
    [data-theme="dark"] .stTextInput input {
        color: #000000 !important;
        background-color: #FFFFFF;
    }
    [data-theme="dark"] .stTextInput label { color: #FFFFFF; }

    /* Keep input text black in both modes */
    .stTextInput input,
    .stSelectbox select,
    .stMultiSelect select,
    .stTextArea textarea {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    .stSelectbox option, .stMultiSelect option {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    input[type="number"] {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    .stSlider [data-baseweb="slider"] { color: #000000 !important; }
    .stRadio label, .stCheckbox label { color: inherit !important; }
    [data-theme="dark"] .stRadio label span,
    [data-theme="dark"] .stCheckbox label span { color: #FFFFFF !important; }
    [data-theme="dark"] .stWidgetLabel { color: #FFFFFF; }
    [data-theme="dark"] .stWidget {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }

    /* Layout */
    .stApp { background-color: transparent; }
    .main .block-container {
        background-color: transparent;
        padding: 1rem;
    }
    .css-1d391kg { background-color: transparent; }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #F5F0E8;
        margin: 0.2rem 0;
        padding: 0.5rem;
        white-space: normal;
        word-wrap: break-word;
        border: 1px solid #D9D0C4;
        font-weight: 500;
        color: #1C2B30;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    .stButton > button:hover,
    .stButton > button[data-selected="true"] {
        background-color: #0E7C86;
        color: white;
        border-color: #0E7C86;
    }
    div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        background-color: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }

    /* Title */
    .title-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        margin: 0.5rem 0;
        padding: 0.5rem;
    }
    .title-text {
        margin: 0;
        font-family: "Source Sans Pro", sans-serif;
        font-size: calc(2rem + 2vw);
        font-weight: bold;
        line-height: 1.2;
        text-align: center;
        color: #0E7C86;
    }
    .title-text-line { display: block; }
    [data-theme="light"] .title-text { color: #0E7C86; }

    /* Logo */
    .logo-container {
        background: white;
        padding: 0.8rem;
        border-radius: 12px;
        width: min(200px, 80%);
        margin: 0 auto;
        display: flex;
        justify-content: center;
    }
    [data-theme="dark"] .logo-container { background: white; }

    /* Responsive */
    div[data-testid="column"] { padding: 0.5rem !important; }
    .stTextInput input { width: 100%; }

    @media (max-width: 640px) {
        .main .block-container { padding: 0.5rem; }
        .title-text { font-size: calc(1.5rem + 1.5vw); }
        .logo-container { width: 60%; padding: 0.5rem; }
        div[data-testid="column"] { padding: 0.3rem !important; }
        .stButton > button { height: auto; min-height: 3em; font-size: 0.9rem; }
    }
</style>
"""
