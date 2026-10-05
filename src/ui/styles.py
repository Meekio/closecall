"""
CloseCall — Responsive CSS
Design tokens:
  Background   : #FAF9F7  (warm off-white / cream)
  Surface      : #FFFFFF
  Primary text : #1A1A1A  (deep charcoal)
  Muted text   : #6B7280
  Accent       : #7C5CFC  (restrained lavender/violet)
  Accent light : #EDE9FE
  Border       : #E8E5E0
  Success      : #16A34A
  Error        : #DC2626
  Warning      : #D97706
  Shadow       : rgba(0,0,0,0.06)

Breakpoints:
  Mobile  : < 640px
  Tablet  : 640–1024px
  Desktop : > 1024px
"""

APP_CSS = """
/* ═══════════════════════════════════════════════════════════
   RESET & BASE
═══════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body,
.gradio-container,
.gradio-container > .main,
.gradio-container > .main > .wrap {
    background: #FAF9F7 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif !important;
    color: #1A1A1A !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh !important;
}

/* CRITICAL: remove the narrow mobile-only cap */
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
}

footer, .built-with, .svelte-1rjryqp { display: none !important; }

/* ═══════════════════════════════════════════════════════════
   INNER PAGE WRAPPER  — fluid, max 1280px, centred
═══════════════════════════════════════════════════════════ */
.cc-page {
    width: 100% !important;
    max-width: 1280px !important;
    margin: 0 auto !important;
    padding: 0 24px 80px !important;
}

@media (max-width: 1024px) {
    .cc-page { padding: 0 20px 80px !important; }
}
@media (max-width: 640px) {
    .cc-page { padding: 0 16px 72px !important; }
}

/* ═══════════════════════════════════════════════════════════
   NAVIGATION — Gradio 6 tab bar
   Targets both .tab-nav (older) and the Gradio 6 svelte classes
═══════════════════════════════════════════════════════════ */

/* Target every possible Gradio tab container */
.tab-nav,
div[class*="tab-nav"],
.tabs > div:first-child,
.gradio-container .tabs .tab-nav,
.block.tabs > div:first-child {
    background: #FFFFFF !important;
    border-bottom: 2px solid #E8E5E0 !important;
    border-top: none !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 200 !important;
    padding: 0 32px !important;
    display: flex !important;
    align-items: stretch !important;
    gap: 0 !important;
    width: 100% !important;
    box-shadow: 0 1px 0 #E8E5E0 !important;
}

/* Every tab button — Gradio 6 renders them as <button> inside the nav */
.tab-nav button,
div[class*="tab-nav"] button,
.tabs > div:first-child button,
.block.tabs > div:first-child button {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    padding: 14px 24px !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    cursor: pointer !important;
    transition: color 0.15s, border-color 0.15s !important;
    white-space: nowrap !important;
    min-height: 48px !important;
    line-height: 1 !important;
    letter-spacing: 0.1px !important;
    margin: 0 !important;
    flex-shrink: 0 !important;
}

.tab-nav button:hover,
div[class*="tab-nav"] button:hover,
.tabs > div:first-child button:hover,
.block.tabs > div:first-child button:hover {
    color: #1A1A1A !important;
    background: #F8F7F5 !important;
}

.tab-nav button.selected,
div[class*="tab-nav"] button.selected,
.tabs > div:first-child button.selected,
.block.tabs > div:first-child button.selected {
    color: #7C5CFC !important;
    border-bottom-color: #7C5CFC !important;
    font-weight: 600 !important;
    background: transparent !important;
}

/* Mobile: bottom sticky nav */
@media (max-width: 640px) {
    .tab-nav,
    div[class*="tab-nav"],
    .tabs > div:first-child,
    .block.tabs > div:first-child {
        position: fixed !important;
        top: auto !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        border-top: 2px solid #E8E5E0 !important;
        border-bottom: none !important;
        padding: 0 !important;
        box-shadow: 0 -1px 0 #E8E5E0 !important;
    }
    .tab-nav button,
    div[class*="tab-nav"] button,
    .tabs > div:first-child button,
    .block.tabs > div:first-child button {
        flex: 1 !important;
        padding: 10px 4px 8px !important;
        font-size: 11px !important;
        border-bottom: none !important;
        border-top: 3px solid transparent !important;
        text-align: center !important;
    }
    .tab-nav button.selected,
    div[class*="tab-nav"] button.selected,
    .tabs > div:first-child button.selected,
    .block.tabs > div:first-child button.selected {
        border-bottom: none !important;
        border-top-color: #7C5CFC !important;
    }
}

/* ═══════════════════════════════════════════════════════════
   TYPOGRAPHY
═══════════════════════════════════════════════════════════ */
.cc-hero-title {
    font-size: clamp(28px, 4vw, 52px) !important;
    font-weight: 800 !important;
    color: #1A1A1A !important;
    letter-spacing: -1.5px !important;
    line-height: 1.1 !important;
}
.cc-hero-sub {
    font-size: clamp(15px, 1.5vw, 18px) !important;
    color: #6B7280 !important;
    line-height: 1.6 !important;
    margin-top: 12px !important;
}
.cc-page-title {
    font-size: clamp(20px, 2.5vw, 28px) !important;
    font-weight: 700 !important;
    color: #1A1A1A !important;
    letter-spacing: -0.5px !important;
}
.cc-section-label {
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: #9CA3AF !important;
    margin-bottom: 12px !important;
}
.cc-body {
    font-size: 15px !important;
    color: #374151 !important;
    line-height: 1.6 !important;
}
.cc-muted {
    font-size: 13px !important;
    color: #6B7280 !important;
}

/* ═══════════════════════════════════════════════════════════
   CARDS
═══════════════════════════════════════════════════════════ */
.cc-card {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    border: 1px solid #E8E5E0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    padding: 24px !important;
    transition: box-shadow 0.2s !important;
}
.cc-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important; }

.cc-card-sm {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid #E8E5E0 !important;
    padding: 16px !important;
}

.cc-stat-card {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid #E8E5E0 !important;
    padding: 20px !important;
    text-align: center !important;
}

/* ═══════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════ */

/* Primary — deep charcoal */
.cc-btn-primary button, button.cc-btn-primary {
    background: #1A1A1A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 13px 28px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: opacity 0.15s !important;
    min-height: 46px !important;
    width: 100% !important;
}
.cc-btn-primary button:hover { opacity: 0.82 !important; }

/* Accent — violet */
.cc-btn-accent button, button.cc-btn-accent {
    background: #7C5CFC !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 13px 28px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    min-height: 46px !important;
    width: 100% !important;
    transition: opacity 0.15s !important;
}
.cc-btn-accent button:hover { opacity: 0.88 !important; }

/* Secondary — outlined */
.cc-btn-secondary button, button.cc-btn-secondary {
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1.5px solid #D1CCC4 !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    min-height: 46px !important;
    width: 100% !important;
    transition: border-color 0.15s !important;
}
.cc-btn-secondary button:hover { border-color: #7C5CFC !important; color: #7C5CFC !important; }

/* Ghost — text only */
.cc-btn-ghost button, button.cc-btn-ghost {
    background: transparent !important;
    color: #6B7280 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
}
.cc-btn-ghost button:hover { color: #1A1A1A !important; background: #F5F3F0 !important; }

/* ═══════════════════════════════════════════════════════════
   CHIPS / PILLS  (Quick picks, filters)
═══════════════════════════════════════════════════════════ */
.cc-chip button, button.cc-chip {
    background: #FFFFFF !important;
    border: 1.5px solid #E8E5E0 !important;
    border-radius: 100px !important;
    padding: 7px 18px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
    min-height: 36px !important;
}
.cc-chip button:hover, button.cc-chip:hover {
    background: #EDE9FE !important;
    border-color: #7C5CFC !important;
    color: #5B3FD4 !important;
}
.cc-chip-active button, button.cc-chip-active {
    background: #7C5CFC !important;
    border-color: #7C5CFC !important;
    color: #FFFFFF !important;
}

/* ═══════════════════════════════════════════════════════════
   INPUTS
═══════════════════════════════════════════════════════════ */
.cc-input textarea, .cc-input input,
.cc-input .svelte-1pi49e2 textarea {
    background: #FFFFFF !important;
    border: 1.5px solid #E8E5E0 !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    font-size: 15px !important;
    color: #1A1A1A !important;
    line-height: 1.5 !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    width: 100% !important;
}
.cc-input textarea:focus, .cc-input input:focus {
    border-color: #7C5CFC !important;
    box-shadow: 0 0 0 3px rgba(124, 92, 252, 0.12) !important;
    outline: none !important;
}
/* Prevent iOS zoom */
@media (max-width: 640px) {
    .cc-input textarea, .cc-input input { font-size: 16px !important; }
}

/* ═══════════════════════════════════════════════════════════
   WEATHER WIDGET
═══════════════════════════════════════════════════════════ */
.cc-weather-widget {
    background: #F0F4FF !important;
    border: 1px solid #C7D7F8 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
}

/* ═══════════════════════════════════════════════════════════
   WARDROBE GRID
═══════════════════════════════════════════════════════════ */
.cc-wardrobe-grid {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 16px !important;
}
@media (max-width: 1024px) {
    .cc-wardrobe-grid { grid-template-columns: repeat(3, 1fr) !important; gap: 12px !important; }
}
@media (max-width: 640px) {
    .cc-wardrobe-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 10px !important; }
}

/* Clothing item thumbnail card */
.cc-item-card {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid #E8E5E0 !important;
    overflow: hidden !important;
    transition: box-shadow 0.2s, transform 0.2s !important;
    cursor: pointer !important;
}
.cc-item-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.10) !important;
    transform: translateY(-2px) !important;
}

/* ═══════════════════════════════════════════════════════════
   OUTFIT RECOMMENDATION CARDS
═══════════════════════════════════════════════════════════ */
.cc-outfit-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)) !important;
    gap: 20px !important;
    align-items: start !important;
}
@media (max-width: 640px) {
    .cc-outfit-grid { grid-template-columns: 1fr !important; }
}

.cc-outfit-card {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    border: 1px solid #E8E5E0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    overflow: hidden !important;
}
.cc-outfit-best {
    border-color: #7C5CFC !important;
    box-shadow: 0 4px 20px rgba(124,92,252,0.15) !important;
}

/* ═══════════════════════════════════════════════════════════
   AGENT PROCESSING STEPS
═══════════════════════════════════════════════════════════ */
.cc-agent-steps {
    background: #F8F7F5 !important;
    border-radius: 12px !important;
    border: 1px solid #E8E5E0 !important;
    padding: 20px 24px !important;
}

/* ═══════════════════════════════════════════════════════════
   BADGES / STATUS
═══════════════════════════════════════════════════════════ */
.cc-badge-clean {
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
    background: #DCFCE7 !important;
    color: #15803D !important;
    border-radius: 100px !important;
    padding: 3px 10px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
}
.cc-badge-dirty {
    background: #FEE2E2 !important;
    color: #B91C1C !important;
    border-radius: 100px !important;
    padding: 3px 10px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
}
.cc-badge-violet {
    background: #EDE9FE !important;
    color: #5B3FD4 !important;
    border-radius: 100px !important;
    padding: 3px 10px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    display: inline-block !important;
}
.cc-badge-rain {
    background: #DBEAFE !important;
    color: #1D4ED8 !important;
    border-radius: 100px !important;
    padding: 3px 10px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    display: inline-block !important;
}

/* ═══════════════════════════════════════════════════════════
   VALIDATION / WHY THIS WORKS
═══════════════════════════════════════════════════════════ */
.cc-why-box {
    background: #F0FDF4 !important;
    border-left: 3px solid #16A34A !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 14px 16px !important;
    margin-top: 14px !important;
}
.cc-fail-box {
    background: #FFF7ED !important;
    border-left: 3px solid #D97706 !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 14px 16px !important;
    margin-top: 14px !important;
}
.cc-error-box {
    background: #FEF2F2 !important;
    border-left: 3px solid #DC2626 !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 14px 16px !important;
    margin-top: 14px !important;
}

/* ═══════════════════════════════════════════════════════════
   UPLOAD AREA
═══════════════════════════════════════════════════════════ */
.cc-upload-zone .upload-container,
.cc-upload-zone .image-container,
.cc-upload-zone .svelte-xws3k2 {
    border: 2px dashed #C8C3BB !important;
    border-radius: 14px !important;
    background: #FDFCFA !important;
}

/* ═══════════════════════════════════════════════════════════
   AI CONFIDENCE BAR
═══════════════════════════════════════════════════════════ */
.cc-confidence-bar {
    height: 6px !important;
    background: #E8E5E0 !important;
    border-radius: 100px !important;
    overflow: hidden !important;
    margin-top: 6px !important;
}
.cc-confidence-fill {
    height: 100% !important;
    background: linear-gradient(90deg, #7C5CFC, #A78BFA) !important;
    border-radius: 100px !important;
    transition: width 0.4s ease !important;
}

/* ═══════════════════════════════════════════════════════════
   FEEDBACK CHIPS
═══════════════════════════════════════════════════════════ */
.cc-feedback-btn button {
    background: #FFFFFF !important;
    border: 1.5px solid #E8E5E0 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    text-align: left !important;
    width: 100% !important;
    min-height: 46px !important;
    cursor: pointer !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.cc-feedback-btn button:hover {
    border-color: #7C5CFC !important;
    background: #F5F3FF !important;
    color: #5B3FD4 !important;
}

/* ═══════════════════════════════════════════════════════════
   PROFILE
═══════════════════════════════════════════════════════════ */
.cc-profile-row {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 16px 0 !important;
    border-bottom: 1px solid #F0EDE8 !important;
    font-size: 15px !important;
    color: #1A1A1A !important;
}
.cc-profile-row:last-child { border-bottom: none !important; }

/* ═══════════════════════════════════════════════════════════
   DIVIDERS & SEPARATORS
═══════════════════════════════════════════════════════════ */
.cc-divider {
    height: 1px !important;
    background: #E8E5E0 !important;
    margin: 24px 0 !important;
    border: none !important;
}

/* ═══════════════════════════════════════════════════════════
   GRADIO OVERRIDES
═══════════════════════════════════════════════════════════ */
.gradio-group, .gr-group {
    box-shadow: none !important;
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
}

/* Remove default Gradio label styling inside our custom HTML areas */
.gr-form label, .gr-padded label { color: #6B7280 !important; font-size: 13px !important; }

/* Gradio accordion flatten */
.gr-accordion {
    background: #FFFFFF !important;
    border: 1px solid #E8E5E0 !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}

/* Chatbot bubbles */
.chatbot .message.user .bubble-wrap { justify-content: flex-end !important; }
.chatbot .message.bot  .bubble-wrap { justify-content: flex-start !important; }

/* Gradio Radio / Checkbox styling */
.gr-check-radio { accent-color: #7C5CFC !important; }

/* Slider accent */
input[type=range] { accent-color: #7C5CFC !important; }

/* Dropdown */
.cc-select select, .cc-select .wrap-inner {
    background: #FFFFFF !important;
    border: 1.5px solid #E8E5E0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    color: #1A1A1A !important;
}

/* Tab content area — no default padding/border */
.tabitem { background: transparent !important; border: none !important; padding: 0 !important; }

/* Ensure rows don't add unwanted gutters */
.gr-row { gap: 0 !important; }
"""
