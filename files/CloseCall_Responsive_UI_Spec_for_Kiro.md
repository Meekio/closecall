# CloseCall Responsive UI Specification for Kiro

## Purpose

Redesign the CloseCall UI so it feels like a real wardrobe/fashion product rather than a narrow Gradio prototype.

**Critical requirement:** The website must NOT remain permanently mobile-width on desktop. It must use responsive layouts that adapt to desktop, tablet, and mobile viewports.

---

# 1. Visual Direction

CloseCall — Your Personal Stylist

Use a clean editorial/fashion-app aesthetic:

- Warm off-white / cream background
- White cards
- Deep charcoal primary text
- Muted grey secondary text
- Restrained lavender/violet accent
- Subtle borders and shadows
- Strong clothing imagery
- Clear typography hierarchy
- Generous but controlled spacing

Do not make the whole UI purple. Use lavender mainly for active navigation, AI states, selected controls, and small highlights.

Avoid excessive emoji icons, giant pill buttons, huge empty spaces, and generic dashboard styling.

---

# 2. Responsive Layout — CRITICAL

The current UI appears as a narrow phone-sized page even when opened in a desktop browser. **Fix this completely.**

## Desktop

Use the available viewport width naturally.

- Do NOT constrain the entire app to 400–500px.
- Use a responsive max-width for the content, approximately 1100–1400px depending on viewport.
- Use multi-column layouts.
- Wardrobe uses a responsive grid.
- Outfit recommendation cards can appear side-by-side.
- Navigation uses available horizontal space.

Concept:

```text
Desktop
┌─────────────────────────────────────────────────────────────┐
│ CloseCall       Home   Wardrobe   Outfits   Profile         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                     RESPONSIVE CONTENT                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Do NOT do this:

```text
Desktop
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              ┌───────────────────┐                          │
│              │ mobile-width app  │                          │
│              │                   │                          │
│              └───────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Tablet

- 2-column grids where useful
- Reduced horizontal padding
- Responsive cards
- Horizontal navigation when space permits

## Mobile

- Single-column page sections
- 2-column wardrobe grid
- Stacked detailed cards
- Full-width primary actions
- Compact mobile navigation
- Touch-friendly controls
- No horizontal scrolling

Suggested breakpoints:

- `< 640px` Mobile
- `640–1024px` Tablet
- `> 1024px` Desktop

Use CSS Grid/Flexbox, fluid widths, responsive max-widths, and media queries. Avoid fixed widths for major containers.

---

# 3. Global App Shell

Desktop:

```text
┌─────────────────────────────────────────────────────────────┐
│ CloseCall        Home   Wardrobe   Outfits   Profile         │
├─────────────────────────────────────────────────────────────┤
│                     PAGE CONTENT                             │
└─────────────────────────────────────────────────────────────┘
```

Mobile can use a compact top navigation or bottom navigation.

Do not force desktop navigation into an overcrowded mobile row.

---

# 4. Home

The natural-language request is the main interaction.

## Desktop

```text
CloseCall                              Home  Wardrobe  Profile

Your wardrobe.
Your plans.
One outfit that works.

┌───────────────────────────────────────────────────────────┐
│ What are you dressing for?                                │
│                                                           │
│ "Casual office outfit for a rainy day..."             →  │
└───────────────────────────────────────────────────────────┘

Try asking
[ Work ] [ Casual ] [ Date ] [ College ] [ Travel ]

┌──────────────────────────┐ ┌────────────────────────────┐
│ TODAY                    │ │ YOUR WARDROBE              │
│ Delhi · 36°C · Clear     │ │ 24 items · 18 clean        │
└──────────────────────────┘ └────────────────────────────┘

[ + Add clothes ]                         [ View wardrobe ]
```

## Mobile

Stack the sections vertically.

The request box should remain the visual focus.

Quick prompts are secondary, not giant primary buttons.

---

# 5. Wardrobe

Make this feel like a real digital wardrobe.

```text
MY WARDROBE                                  + Add clothes

24 ITEMS

┌───────────────────────────────────────────────────────────┐
│ Search your wardrobe...                                   │
└───────────────────────────────────────────────────────────┘

[ All ] [ Tops ] [ Bottoms ] [ Shoes ] [ One-pieces ] [ Outerwear ]

TOPS · 8

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  IMAGE   │ │  IMAGE   │ │  IMAGE   │ │  IMAGE   │
├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤
│ Grey     │ │ White    │ │ Blue     │ │ Black    │
│ Shirt    │ │ T-shirt  │ │ Kurti    │ │ Top      │
│ Clean ●  │ │ Clean ●  │ │ Dirty ●  │ │ Clean ●  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

Grid behavior:

- Desktop: 4–5 cards per row
- Tablet: 3 cards per row
- Mobile: 2 cards per row

Never force a narrow single-column layout on desktop.

---

# 6. Clothing Item Detail

```text
← Wardrobe

┌────────────────────────────────────┐
│                                    │
│             ITEM IMAGE             │
│                                    │
└────────────────────────────────────┘

Grey Shirt

Smart Casual
● Clean

Category       Top
Type           Shirt
Colour         Grey
Formality      3 / 5
Season         All-season
Rain           Suitable

AI confidence
█████████░ 91%

[ Edit tags ]
```

The AI confidence makes the vision-tagging feature visible.

---

# 7. Add Clothes

## Upload

```text
ADD TO WARDROBE

Upload a photo of one clothing item.

┌────────────────────────────────────┐
│                 +                  │
│                                    │
│        Drop photo here             │
│        or choose a file            │
│                                    │
└────────────────────────────────────┘

[ Analyze item ]
```

## AI processing

```text
ANALYZING YOUR ITEM

        [ clothing image ]

✓ Category detected
✓ Type detected
✓ Colour detected
✓ Formality estimated
✓ Season assessed

Generating wardrobe tags...
```

## Review

```text
LOOKS GOOD?

Grey Shirt

Category       Top
Subtype        Shirt
Colour         Grey
Formality      3 / 5
Season         All-season
Rain           Suitable
Status         Clean

Confidence: 91%

[ Save to wardrobe ]
[ Edit tags ]
```

---

# 8. Outfit Request

Keep this simple and natural-language-first.

```text
NEW OUTFIT

What do you need?

┌──────────────────────────────────────────────┐
│ I need a semi-formal office outfit for       │
│ today. It's raining and I want something     │
│ comfortable.                                 │
└──────────────────────────────────────────────┘

[ Get outfits ]
```

Do not overload users with manual filters. The agent should infer the request.

---

# 9. Agent Processing State

This is important because it demonstrates the agentic architecture.

```text
CREATING YOUR OUTFIT

Understanding your request                 ✓
Checking today's weather                   ✓
Searching your wardrobe                    ✓
Finding suitable combinations              ✓
Checking outfit validity                   ✓
Finding the best match                     ✓
```

Show only high-level actions/status. Do NOT expose hidden chain-of-thought or private reasoning.

---

# 10. Outfit Recommendations

This should be one of the strongest screens.

Desktop can show 2–3 outfit cards side-by-side.

```text
YOUR OUTFITS

Semi-formal · Office · Rainy

┌──────────────────────────────────────────────────────────┐
│ BEST MATCH                                                │
│                                                          │
│ ┌────────┐ ┌────────┐ ┌────────┐                        │
│ │ SHIRT  │ │ BOTTOM │ │ SHOES  │                        │
│ │ IMAGE  │ │ IMAGE  │ │ IMAGE  │                        │
│ └────────┘ └────────┘ └────────┘                        │
│                                                          │
│ Grey Shirt · Beige Palazzo · White Sneakers              │
│                                                          │
│ ✓ Clean   ✓ Rain suitable   ✓ Office appropriate         │
│                                                          │
│ 92% match                                                │
│                                                          │
│ WHY THIS WORKS                                           │
│ The grey and beige combination keeps the look            │
│ understated and professional while the footwear          │
│ provides comfort for a rainy day.                        │
│                                                          │
│ Styling guidance                                         │
│ Grey and beige form a balanced neutral pairing.          │
│                                                          │
│ [ Wear this ]       [ Try another ]                      │
└──────────────────────────────────────────────────────────┘
```

Mobile should stack the outfit details cleanly.

---

# 11. Styling Guidance / RAG

The system includes `retrieve_styling_guidance`.

Reflect this in the UI without exposing technical details such as TF-IDF.

Example:

```text
WHY THIS WORKS

Colour pairing
Grey + Beige → balanced neutral combination

Formality
Smart-casual pieces maintain an office-appropriate look

Weather
Rain-suitable footwear was prioritised.

▸ Styling guidance used
```

The expanded section may show the retrieved styling principle.

Do not fabricate retrieved knowledge.

---

# 12. Validation

Successful recommendation:

```text
OUTFIT CHECK

✓ All items are clean
✓ Complete outfit
✓ Appropriate for occasion
✓ Rain suitable
✓ No invalid footwear
```

The UI should communicate that recommendations are checked before being shown.

---

# 13. Failure Diagnosis and Repair

Never show only `No outfits found`.

Show the actual problem.

```text
WE COULDN'T FIND A PERFECT MATCH

We found a problem with your wardrobe.

Formal footwear
✕ No clean rain-suitable option

Trousers
✕ Available pair is marked dirty

────────────────────────────────

I can try:

Keep the formal requirement
→ You may need different footwear

Relax the formality slightly
→ I'll find the closest suitable outfit

Or tell me what you'd like to change.

[ Find closest match ]
[ Change request ]
```

After repair:

```text
CLOSEST MATCH

I relaxed the formality requirement slightly
because no fully formal rainy-day combination
was available.

Here's the closest suitable option:
```

This visually represents:

**Validate → Diagnose → Repair → Adapt**

Do not expose hidden chain-of-thought.

---

# 14. Feedback / Refinement

```text
HOW DOES THIS LOOK?

[ Looks good ]
[ Try another ]
[ Not my style ]

What should I change?

[ Less formal ]
[ More colourful ]
[ More comfortable ]
[ Different footwear ]

[ Update outfit ]
```

Refinement should use conversation memory and meaningful preferences should be persisted.

---

# 15. Profile

Keep this lightweight.

```text
PROFILE

Test User
user@example.com

WARDROBE
24 items
18 clean

PREFERENCES
3 saved preferences

────────────────────────────

Wardrobe
Saved preferences

Coming soon
Calendar integration

About CloseCall
```

Do not make Profile a large dashboard.

---

# 16. Empty States

## Empty wardrobe

```text
YOUR WARDROBE IS EMPTY

Add a few clothes and CloseCall
can start building outfits from them.

[ + Add clothes ]
```

## No valid outfit

```text
NO PERFECT MATCH

Your current wardrobe doesn't satisfy
all the requested constraints.

[ See closest alternatives ]
```

## No styling guidance

```text
No specific styling guidance was found.
The recommendation is based on wardrobe
compatibility and the requested occasion.
```

Never invent retrieval results.

---

# 17. Loading States

Avoid large generic spinners.

Use contextual messages:

- Checking weather...
- Searching wardrobe...
- Validating outfit...
- Finding a better match...

For multi-step agent activity use the checklist from Section 9.

---

# 18. Error Handling

Bad:

```text
Error 500
```

Better:

```text
WE COULDN'T COMPLETE THAT

The outfit service could not be reached.

[ Try again ]
```

Weather fallback:

```text
WEATHER UNAVAILABLE

I can still suggest an outfit using
your request and wardrobe.

[ Continue without weather ]
```

Never expose API keys, stack traces, raw exceptions, or internal prompts.

---

# 19. Responsive Component Rules

## Buttons

Desktop:
- Natural/content width where appropriate
- Do not stretch every button across the whole page

Mobile:
- Important actions can become full-width
- Maintain touch-friendly size

## Cards

Desktop:
- Responsive grid
- Multiple cards per row

Mobile:
- 2-column wardrobe cards
- 1-column detailed recommendation cards

## Images

Do not distort clothing photos.

Use responsive image sizing and appropriate object-fit/aspect-ratio behavior.

## Typography

Use responsive typography.

Avoid giant headings that consume most of the mobile viewport.

## Spacing

Use consistent spacing tokens.

Do not create large blank areas like the current prototype.

---

# 20. Desktop-Specific Layout

On desktop:

### Home
Use a wide centered content layout or two-column hero layout.

### Wardrobe
Use 4–5 columns depending on viewport.

### Outfit recommendations
Show 2–3 recommendation cards horizontally when space allows.

### Add clothes
Show upload panel and metadata side-by-side where appropriate.

### Profile
Use a compact layout.

---

# 21. Mobile-Specific Layout

On mobile:

### Home
Everything stacks vertically.

### Wardrobe
2-column clothing grid.

### Outfit
Stack outfit components and details.

### Agent status
Compact vertical checklist.

### Navigation
Use mobile-friendly navigation.

### Controls
No horizontal scrolling.

---

# 22. Accessibility

Include:

- Readable contrast
- Visible focus states
- Descriptive labels
- Clear action names
- Keyboard navigation on desktop
- Touch-friendly controls on mobile
- Meaningful image alt text where supported

Do not rely only on colour for clean/dirty or valid/invalid states. Use text/icons too.

---

# 23. Do NOT Do These Things

1. Do not make the entire website permanently 400–500px wide.
2. Do not make desktop look like a phone simulator.
3. Do not use huge empty vertical spaces.
4. Do not turn every control into a giant pill.
5. Do not use excessive emojis.
6. Do not use purple for everything.
7. Do not put every feature on the home page.
8. Do not make Profile unnecessarily large.
9. Do not hide the agentic behavior completely.
10. Do not expose chain-of-thought.
11. Do not let the LLM invent wardrobe items.
12. Do not show invalid outfits without validation.
13. Do not replace specific failure reasons with generic "No outfits found".
14. Do not replace real wardrobe images with decorative stock images.
15. Do not break the working backend/agent/tool architecture just to change the UI.

---

# 24. Architecture → UI Mapping

| System capability | UI representation |
|---|---|
| Vision tagging | Analyze item → metadata → confidence |
| Wardrobe DB | Wardrobe grid |
| Natural-language request | Main request box |
| `get_weather` | Weather status |
| `get_wardrobe_state` | Searching wardrobe status |
| Candidate generation | Creating outfit status |
| `check_outfit_validity` | Outfit check |
| `retrieve_styling_guidance` | Why this works / Styling guidance |
| `ask_user_clarification` | Targeted clarification UI |
| Guardrails | Validated recommendation |
| Failure diagnosis | Specific failure reasons |
| Repair loop | Closest match / relaxed constraint |
| Short-term memory | Try another / refine request |
| Long-term preferences | Saved preferences |
| Evaluation harness | Internal testing only |

---

# 25. Main User Journey

```text
OPEN CLOSECALL
      ↓
HOME
      ↓
"Office outfit for today.
 It's raining."
      ↓
UNDERSTAND REQUEST
      ↓
CHECK WEATHER
      ↓
SEARCH WARDROBE
      ↓
GENERATE CANDIDATES
      ↓
VALIDATE
      ↓
 ┌───────────────┐
 │ Valid outfit? │
 └───────┬───────┘
     YES │ NO
         │
         ↓
   RECOMMEND        DIAGNOSE
                       ↓
                  REPAIR / RELAX
                       ↓
                    VALIDATE
                       ↓
                  RECOMMEND
                       ↓
                  USER FEEDBACK
                       ↓
                    ADAPT
```

This is the core CloseCall experience.

---

# 26. Implementation Constraint

Redesign the UI **without replacing the current agent architecture**.

Keep:

- Single reasoning agent
- Five tools
- Wardrobe database
- Vision tagging
- Styling retrieval
- Validation
- Guardrails
- Short-term memory
- Long-term preference memory
- Evaluation harness

The redesign is primarily a presentation/responsive-layout improvement.

Do not rewrite working agent logic merely to change the UI.

---

# 27. Priority Order

## P0 — Essential

1. Responsive desktop/mobile layout
2. Home
3. Wardrobe
4. Outfit request
5. Outfit recommendation
6. Agent processing state
7. Failure diagnosis/repair

## P1

8. Add clothes / AI tagging
9. Styling guidance
10. Feedback/refinement

## P2

11. Profile
12. Empty states
13. Detailed visual polish
14. Accessibility refinements

---

# 28. Final Design Principle

CloseCall should feel like:

> A real wardrobe product powered by an autonomous styling agent.

It should NOT feel like:

> A Gradio demo squeezed into a phone-sized column.

The most important visual story is:

**My request → CloseCall understands → CloseCall checks my wardrobe → CloseCall validates the outfit → CloseCall explains the choice → CloseCall adapts when something doesn't work.**

Make that story obvious without exposing hidden chain-of-thought.
