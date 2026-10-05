"""
Static styling knowledge base for CloseCall's retrieval tool.
Each entry: id, category, and the guidance text.
"""

STYLING_KB = [
    # Color pairing
    {"id": "color_01", "category": "color", "text": "Pairing a bold or bright top with a neutral bottom (black, grey, navy, beige) balances visual weight and keeps an outfit from looking busy."},
    {"id": "color_02", "category": "color", "text": "Monochrome outfits using different shades of the same color family read as deliberate and put-together rather than mismatched."},
    {"id": "color_03", "category": "color", "text": "Cool tones like navy, grey, charcoal, and black read more formal than warm tones like orange, yellow, and bright red in most professional contexts."},
    {"id": "color_04", "category": "color", "text": "Pastels and light neutrals suit daytime and casual settings; deep, saturated colors suit evening and formal settings."},
    {"id": "color_05", "category": "color", "text": "Complementary colors that are opposite on the color wheel create a deliberate, high-contrast look best used sparingly as an accent, not across equal-sized garment areas."},
    {"id": "color_06", "category": "color", "text": "Earth tones like olive, rust, camel, and brown pair naturally with denim and are versatile across casual and smart-casual occasions."},
    {"id": "color_07", "category": "color", "text": "White or off-white pairs with nearly any color and is a safe neutral base for both tops and bottoms."},
    {"id": "color_08", "category": "color", "text": "Avoid pairing two highly saturated, competing colors of similar brightness in the same outfit, such as bright red with bright green, as it tends to visually clash."},
    # Formality and occasion
    {"id": "formality_09", "category": "formality", "text": "Structured fabrics like cotton shirting and tailored trousers read as more formal than soft, draped, or jersey fabrics."},
    {"id": "formality_10", "category": "formality", "text": "Closed-toe footwear such as formal shoes, loafers, and structured flats is appropriate for office and formal settings; open sandals and chappals generally are not."},
    {"id": "formality_11", "category": "formality", "text": "Denim is widely accepted as business casual in many modern workplaces but is typically inappropriate for formal or black-tie occasions."},
    {"id": "formality_12", "category": "formality", "text": "Layering a blazer or structured jacket over a casual top is a reliable way to elevate an otherwise casual outfit to smart-casual."},
    {"id": "formality_13", "category": "formality", "text": "T-shirts and graphic tees are best suited to casual or athleisure contexts and are generally avoided in office or formal settings."},
    {"id": "formality_14", "category": "formality", "text": "A single statement piece paired with otherwise neutral basics is a safe way to dress up for a date or party without overdoing it."},
    {"id": "formality_15", "category": "formality", "text": "For college or casual daily wear, comfort and ease of movement typically take priority over strict formality rules."},
    # Weather and fabric
    {"id": "weather_16", "category": "weather", "text": "In rain or high humidity, synthetic or quick-dry fabrics and closed, water-resistant footwear are preferable to suede, canvas, or absorbent natural fibers."},
    {"id": "weather_17", "category": "weather", "text": "Dark colors show less visible water staining than light colors, making them a practical choice for rainy-day outfits."},
    {"id": "weather_18", "category": "weather", "text": "Lightweight, breathable fabrics like cotton and linen suit hot and humid weather; heavier fabrics like wool and fleece suit cold weather."},
    {"id": "weather_19", "category": "weather", "text": "Layering a jacket or outerwear over a base outfit is the standard approach for adapting one outfit across variable or cooler weather."},
    {"id": "weather_20", "category": "weather", "text": "Open-toe and breathable footwear suit warm, dry weather; closed footwear is preferable in cold or wet conditions."},
    {"id": "weather_21", "category": "weather", "text": "Humidity and heat make heavier or stiff fabrics uncomfortable and prone to clinging; looser-fitting garments are generally preferred."},
    {"id": "weather_22", "category": "weather", "text": "In cold weather, darker and warmer tones like maroon, forest green, and charcoal are both practically and aesthetically suited to the season, alongside heavier fabrics."},
    # Silhouette and proportion
    {"id": "silhouette_23", "category": "silhouette", "text": "Balancing a loose-fitting top with fitted bottoms, or vice versa, creates a proportioned silhouette; pairing loose with loose can read as shapeless."},
    {"id": "silhouette_24", "category": "silhouette", "text": "High-waisted bottoms paired with a tucked-in top is a common technique for creating a more defined silhouette."},
    {"id": "silhouette_25", "category": "silhouette", "text": "Oversized or relaxed-fit pieces suit casual and streetwear-inspired looks more than formal or office contexts."},
    {"id": "silhouette_26", "category": "silhouette", "text": "Matching the formality level of separate pieces keeps an outfit visually coherent, so avoid pairing a very formal top with very casual bottoms."},
    # Patterns and accessorizing
    {"id": "pattern_27", "category": "pattern", "text": "Mixing more than one bold pattern in a single outfit, such as stripes with florals, is generally avoided unless the patterns share a common color palette."},
    {"id": "pattern_28", "category": "pattern", "text": "A patterned item is best paired with solid, neutral-colored separates to avoid visual competition."},
    {"id": "pattern_29", "category": "pattern", "text": "Accessories like belts, scarves, and simple jewelry can bridge the formality gap between a casual top and a more formal bottom, or vice versa."},
    {"id": "pattern_30", "category": "pattern", "text": "Footwear color is often chosen to match either the bottom or a neutral tone already present in the outfit, to visually anchor the look."},
]