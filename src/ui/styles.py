"""
Complete mobile-first CSS for CloseCall.

Design tokens from the wireframe:
  Background   : #FDF6F0  (warm off-white)
  Surface card : #FFFFFF
  Primary      : #8B5CF6  (violet)
  Primary dark : #6D28D9
  Accent pink  : #F9A8D4
  Text primary : #1C1C1E
  Text muted   : #6B7280
  Success      : #22C55E
  Error        : #EF4444
  Border       : #E5E7EB
  Rain badge   : #BFDBFE / #1D4ED8

Fonts: system-ui → same feel as iOS/Android defaults.
"""

MOBILE_CSS = """
/* ════════════════════════════════════════════════════
   RESET & BASE
════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: #FDF6F0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #1C1C1E !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Constrain width like a phone shell */
.gradio-container {
    max-width: 480px !important;
    margin: 0 auto !important;
    min-height: 100vh !important;
    position: relative !important;
    box-shadow: 0 0 40px rgba(0,0,0,0.12) !important;
}

footer, .built-with { display: none !important; }

/* ════════════════════════════════════════════════════
   TYPOGRAPHY
════════════════════════════════════════════════════ */
.cc-title {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #1C1C1E !important;
    letter-spacing: -0.5px !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.cc-subtitle {
    font-size: 14px !important;
    color: #6B7280 !important;
    margin: 4px 0 0 0 !important;
}
.cc-section-title {
    font-size: 17px !important;
    font-weight: 600 !important;
    color: #1C1C1E !important;
    margin: 0 0 12px 0 !important;
}
.cc-label {
    font-size: 13px !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
    margin-bottom: 4px !important;
}

/* ════════════════════════════════════════════════════
   SCREEN PANELS  (each "page" is a gr.Column inside tabs)
════════════════════════════════════════════════════ */
.cc-screen {
    padding: 16px !important;
    padding-bottom: 80px !important;   /* room for bottom nav */
    min-height: calc(100vh - 56px) !important;
    background: #FDF6F0 !important;
}

/* ════════════════════════════════════════════════════
   BOTTOM NAV BAR
════════════════════════════════════════════════════ */
.cc-bottom-nav {
    display: flex !important;
    position: sticky !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    background: #FFFFFF !important;
    border-top: 1px solid #E5E7EB !important;
    z-index: 100 !important;
    padding: 0 !important;
}
/* Gradio tab buttons used as nav items */
.cc-bottom-nav .tab-nav button {
    flex: 1 !important;
    padding: 8px 4px 6px !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 2px !important;
    cursor: pointer !important;
    transition: color 0.15s !important;
}
.cc-bottom-nav .tab-nav button.selected {
    color: #8B5CF6 !important;
    border-top: 2px solid #8B5CF6 !important;
}

/* ════════════════════════════════════════════════════
   CARDS
════════════════════════════════════════════════════ */
.cc-card {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07) !important;
    border: 1px solid #F3F4F6 !important;
}
.cc-card-flat {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    padding: 12px 14px !important;
    margin-bottom: 8px !important;
    border: 1px solid #E5E7EB !important;
}

/* ════════════════════════════════════════════════════
   SPLASH / HERO
════════════════════════════════════════════════════ */
.cc-splash-bg {
    background: linear-gradient(160deg, #FDF6F0 0%, #F3E8FF 100%) !important;
    min-height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 32px 24px !important;
    text-align: center !important;
}
.cc-splash-logo {
    font-size: 36px !important;
    font-weight: 800 !important;
    color: #1C1C1E !important;
    letter-spacing: -1px !important;
}
.cc-splash-tagline {
    font-size: 15px !important;
    color: #6B7280 !important;
    margin: 8px 0 40px !important;
    line-height: 1.5 !important;
}
.cc-hanger-icon {
    font-size: 64px !important;
    margin-bottom: 24px !important;
}

/* ════════════════════════════════════════════════════
   WEATHER WIDGET
════════════════════════════════════════════════════ */
.cc-weather {
    background: #EFF6FF !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin-bottom: 16px !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    border: 1px solid #BFDBFE !important;
}
.cc-weather-city {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #1D4ED8 !important;
}
.cc-weather-desc {
    font-size: 12px !important;
    color: #3B82F6 !important;
}

/* ════════════════════════════════════════════════════
   CHIP / PILL BUTTONS  (Quick picks, filters)
════════════════════════════════════════════════════ */
.cc-chips {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    margin: 12px 0 !important;
}
/* Individual chips are gr.Button with elem_classes=["cc-chip"] */
.cc-chip button, button.cc-chip {
    background: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 20px !important;
    padding: 6px 16px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
    min-height: 36px !important;
    line-height: 1 !important;
}
.cc-chip button:hover, button.cc-chip:hover {
    background: #F3E8FF !important;
    border-color: #8B5CF6 !important;
    color: #6D28D9 !important;
}
.cc-chip-active button, button.cc-chip-active {
    background: #8B5CF6 !important;
    border-color: #8B5CF6 !important;
    color: #FFFFFF !important;
}

/* ════════════════════════════════════════════════════
   PRIMARY BUTTON
════════════════════════════════════════════════════ */
.cc-btn-primary button, button.cc-btn-primary {
    background: #1C1C1E !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 24px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 50px !important;
    cursor: pointer !important;
    transition: opacity 0.15s !important;
}
.cc-btn-primary button:hover { opacity: 0.85 !important; }

.cc-btn-secondary button, button.cc-btn-secondary {
    background: #FFFFFF !important;
    color: #1C1C1E !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 14px !important;
    padding: 13px 24px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 50px !important;
    cursor: pointer !important;
}

.cc-btn-violet button, button.cc-btn-violet {
    background: #8B5CF6 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 24px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    min-height: 50px !important;
    cursor: pointer !important;
}

/* ════════════════════════════════════════════════════
   TEXT INPUT  (NL request bar)
════════════════════════════════════════════════════ */
.cc-input textarea, .cc-input input {
    background: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    font-size: 15px !important;  /* prevents iOS zoom */
    color: #1C1C1E !important;
}
.cc-input textarea:focus, .cc-input input:focus {
    border-color: #8B5CF6 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
}

/* ════════════════════════════════════════════════════
   QUICK ACTION CARDS  (Add Clothes / My Wardrobe)
════════════════════════════════════════════════════ */
.cc-action-card button {
    background: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 16px !important;
    padding: 18px 12px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #1C1C1E !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 8px !important;
    min-height: 80px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: box-shadow 0.15s !important;
}
.cc-action-card button:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.10) !important;
}

/* ════════════════════════════════════════════════════
   UPLOAD AREA
════════════════════════════════════════════════════ */
.cc-upload-area {
    border: 2px dashed #D1D5DB !important;
    border-radius: 20px !important;
    padding: 40px 20px !important;
    text-align: center !important;
    background: #FAFAFA !important;
    margin-bottom: 16px !important;
}
.cc-upload-icon {
    font-size: 48px !important;
    margin-bottom: 12px !important;
    display: block !important;
}

/* ════════════════════════════════════════════════════
   PROCESSING / PROGRESS STEPS
════════════════════════════════════════════════════ */
.cc-step {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 8px 0 !important;
    font-size: 14px !important;
    color: #374151 !important;
}
.cc-step-done  { color: #22C55E !important; }
.cc-step-spin  { color: #8B5CF6 !important; }
.cc-step-wait  { color: #D1D5DB !important; }

/* ════════════════════════════════════════════════════
   ITEM DETAIL / TAG EDITOR
════════════════════════════════════════════════════ */
.cc-tag-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 10px 0 !important;
    border-bottom: 1px solid #F3F4F6 !important;
}
.cc-tag-label {
    font-size: 14px !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
}

/* Dropdowns match the wireframe inline style */
.cc-select select {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
    color: #1C1C1E !important;
    width: 100% !important;
}

/* Formality slider */
.cc-formality-slider input[type=range] {
    accent-color: #8B5CF6 !important;
    width: 100% !important;
    height: 4px !important;
}

/* Season chip row */
.cc-season-chip button {
    background: #F3E8FF !important;
    border: 1.5px solid #8B5CF6 !important;
    border-radius: 20px !important;
    padding: 5px 14px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #6D28D9 !important;
    cursor: pointer !important;
    min-height: 30px !important;
}
.cc-season-chip-off button {
    background: #F9FAFB !important;
    border: 1.5px solid #E5E7EB !important;
    color: #6B7280 !important;
}

/* ════════════════════════════════════════════════════
   WARDROBE GRID
════════════════════════════════════════════════════ */
.cc-wardrobe-grid {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 8px !important;
    margin-top: 12px !important;
}
.cc-item-thumb {
    aspect-ratio: 1 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    background: #F3F4F6 !important;
    position: relative !important;
}
.cc-item-thumb img {
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
}

/* ════════════════════════════════════════════════════
   OUTFIT CARDS (Recommendations)
════════════════════════════════════════════════════ */
.cc-outfit-tab {
    background: #FFFFFF !important;
    border-radius: 20px !important;
    padding: 0 !important;
    overflow: hidden !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
    margin-bottom: 16px !important;
}
.cc-outfit-header {
    padding: 16px !important;
    border-bottom: 1px solid #F3F4F6 !important;
}
.cc-outfit-why {
    background: #F0FDF4 !important;
    border-radius: 10px !important;
    padding: 12px !important;
    margin: 12px 0 !important;
    font-size: 13px !important;
    color: #166534 !important;
    line-height: 1.5 !important;
}
.cc-outfit-why ul { margin: 4px 0 0 0 !important; padding-left: 16px !important; }
.cc-outfit-why li { margin-bottom: 2px !important; }

/* Badge — e.g. "Rain Ready" */
.cc-badge {
    display: inline-block !important;
    background: #DBEAFE !important;
    color: #1D4ED8 !important;
    border-radius: 20px !important;
    padding: 3px 10px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 8px !important;
}
.cc-badge-green {
    background: #DCFCE7 !important;
    color: #166534 !important;
}
.cc-badge-amber {
    background: #FEF9C3 !important;
    color: #854D0E !important;
}

/* ════════════════════════════════════════════════════
   OUTFIT ITEM ROW  (inside outfit detail)
════════════════════════════════════════════════════ */
.cc-outfit-item-row {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 10px 0 !important;
    border-bottom: 1px solid #F9FAFB !important;
    font-size: 14px !important;
}
.cc-outfit-item-cat {
    font-size: 11px !important;
    color: #6B7280 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ════════════════════════════════════════════════════
   FEEDBACK CHIPS  (Not quite right?)
════════════════════════════════════════════════════ */
.cc-feedback-chip button {
    background: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    text-align: left !important;
    width: 100% !important;
    min-height: 44px !important;
    cursor: pointer !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.cc-feedback-chip button:hover {
    border-color: #8B5CF6 !important;
    background: #F5F3FF !important;
    color: #6D28D9 !important;
}

/* ════════════════════════════════════════════════════
   AGENT THINKING STEPS  (Outfit Request screen)
════════════════════════════════════════════════════ */
.cc-agent-steps {
    background: #FAFAFA !important;
    border-radius: 14px !important;
    padding: 14px !important;
    margin: 12px 0 !important;
    font-size: 13px !important;
    color: #374151 !important;
}
.cc-agent-step-item {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 5px 0 !important;
}

/* ════════════════════════════════════════════════════
   PROFILE PAGE
════════════════════════════════════════════════════ */
.cc-profile-avatar {
    width: 64px !important;
    height: 64px !important;
    border-radius: 50% !important;
    background: #E9D5FF !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 28px !important;
    margin-bottom: 8px !important;
}
.cc-profile-row {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 14px 0 !important;
    border-bottom: 1px solid #F3F4F6 !important;
    font-size: 15px !important;
    color: #1C1C1E !important;
    cursor: pointer !important;
}
.cc-profile-row-icon { font-size: 20px !important; margin-right: 12px !important; }
.cc-profile-chevron { color: #9CA3AF !important; font-size: 16px !important; }

/* ════════════════════════════════════════════════════
   CHAT MESSAGES  (inside outfit request)
════════════════════════════════════════════════════ */
.cc-bubble-user {
    background: #1C1C1E !important;
    color: #FFFFFF !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    max-width: 85% !important;
    margin-left: auto !important;
    margin-bottom: 8px !important;
    line-height: 1.5 !important;
}
.cc-bubble-agent {
    background: #FFFFFF !important;
    color: #1C1C1E !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    max-width: 92% !important;
    margin-right: auto !important;
    margin-bottom: 8px !important;
    line-height: 1.5 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
    border: 1px solid #F3F4F6 !important;
}

/* ════════════════════════════════════════════════════
   GRADIO OVERRIDES  (normalize Gradio's own styles)
════════════════════════════════════════════════════ */
/* Remove Gradio borders/shadows from Groups/Columns */
.gradio-group, .gr-group { box-shadow: none !important; border: none !important; }

/* Gradio Tab bar at bottom */
.tab-nav {
    background: #FFFFFF !important;
    border-top: 1px solid #E5E7EB !important;
    border-bottom: none !important;
    position: sticky !important;
    bottom: 0 !important;
    z-index: 50 !important;
    padding: 0 !important;
}
.tab-nav button {
    font-size: 11px !important;
    padding: 10px 0 8px !important;
    color: #9CA3AF !important;
    border-radius: 0 !important;
    border-bottom: none !important;
    border-top: 2px solid transparent !important;
    flex: 1 !important;
}
.tab-nav button.selected {
    color: #8B5CF6 !important;
    border-top-color: #8B5CF6 !important;
    background: transparent !important;
}

/* Remove default Gradio label styling */
.gr-form label { display: none !important; }

/* Make Gradio image upload match the wireframe */
.cc-upload-zone .image-container {
    border: 2px dashed #D1D5DB !important;
    border-radius: 20px !important;
    background: #FAFAFA !important;
}

/* Gradio accordion: flatten */
.gr-accordion { background: transparent !important; border: none !important; box-shadow: none !important; }

/* Chatbot messages */
.chatbot .message.user .bubble-wrap { justify-content: flex-end !important; }
.chatbot .message.bot .bubble-wrap { justify-content: flex-start !important; }

/* Responsive: on actual desktop don't cap at 480px */
@media (min-width: 768px) {
    .gradio-container { max-width: 480px !important; }
}

/* Prevent iOS font size inflation */
@media (max-width: 480px) {
    input, textarea, select { font-size: 16px !important; }
}
"""
