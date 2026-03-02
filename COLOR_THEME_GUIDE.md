# 🎨 Raksha Ride - Complete Color Theme Guide

## Light Mode vs Dark Mode Comparison

### PRIMARY COLORS
```
Light Mode                          Dark Mode
─────────────────────────────────────────────────────
#FFB300 (Golden Yellow)      ←→    #FFB300 (Same Golden)
#FFA000 (Dark Gold)          ←→    #FFD644 (Lighter Gold)
```

### BACKGROUND COLORS
```
Light Mode                          Dark Mode
─────────────────────────────────────────────────────
#F8F9FA (Light Gray)         ←→    #0D0D0D (Very Dark)
#FFFFFF (White)              ←→    #1A1A1A (Dark Gray)
                             ←→    #262626 (Medium Dark)
```

### TEXT COLORS
```
Light Mode                          Dark Mode
─────────────────────────────────────────────────────
#1A1A1A (Dark Black)         ←→    #F0F0F0 (Light White)
#666666 (Medium Gray)        ←→    #B0B0B0 (Light Gray)
#333333 (Text Dark)          ←→    (Auto-calculated)
```

### ACCENT COLORS
```
Light Mode                          Dark Mode
─────────────────────────────────────────────────────
#00E676 (Bright Green)       ←→    #00E676 (Bright Green)
                             ←→    #69F0AE (Light Green)
#00C853 (Dark Green)         ←→    #00C853 (Dark Green)
```

### SHADOW EFFECTS
```
Light Mode                          Dark Mode
─────────────────────────────────────────────────────
0 10px 30px rgba(0,0,0,0.1) ←→    0 10px 30px rgba(0,0,0,0.5)
0 4px 12px rgba(0,0,0,0.08) ←→    0 4px 12px rgba(0,0,0,0.3)
Subtle & Professional        ←→    Deep & Rich
```

---

## Component Color Breakdown

### HEADER
**Light Mode:**
- Background: rgba(255, 255, 255, 0.92)
- Border: rgba(0, 0, 0, 0.08)
- Shadow: 0 2px 10px rgba(0, 0, 0, 0.04)

**Dark Mode:**
- Background: rgba(13, 13, 13, 0.92)
- Border: rgba(255, 255, 255, 0.1)
- Shadow: 0 2px 10px rgba(0, 0, 0, 0.3)

### FEATURE CARDS
**Light Mode:**
- Background: white
- Box Shadow: 0 8px 25px rgba(0, 0, 0, 0.08)
- Border: transparent
- Hover Effect: Golden border (rgba(255, 179, 0, 0.3))

**Dark Mode:**
- Background: Gradient from rgba(25, 25, 25, 0.95) → rgba(30, 30, 30, 0.9)
- Box Shadow: 0 8px 25px rgba(0, 0, 0, 0.3)
- Border: 2px solid rgba(255, 179, 0, 0.2)
- Hover: Border becomes rgba(255, 179, 0, 0.5)

### BUTTONS

#### Primary Button
**Light Mode:**
- Background: #FFB300
- Color: #212121
- Shadow: 0 10px 25px rgba(255, 179, 0, 0.25)
- Hover Shadow: 0 20px 50px rgba(255, 179, 0, 0.4)

**Dark Mode:**
- Background: #FFB300 (Same for visibility)
- Color: #212121
- Shadow: 0 10px 30px rgba(255, 179, 0, 0.3)
- Hover Shadow: 0 20px 60px rgba(255, 179, 0, 0.5)

#### Secondary Button
**Light Mode:**
- Background: transparent
- Border: 2.5px solid #FFB300
- Color: #FFB300

**Dark Mode:**
- Background: transparent
- Border: 2.5px solid #FFD644 (Lighter gold)
- Color: #FFD644
- Hover: Background becomes #FFD644

### SECURITY BADGE
**Light Mode:**
- Background: Gradient rgba(0, 230, 118, 0.12) → rgba(0, 188, 212, 0.08)
- Border: 1.5px solid rgba(0, 230, 118, 0.3)
- Shadow: 0 4px 15px rgba(0, 230, 118, 0.1)

**Dark Mode:**
- Background: Gradient rgba(0, 230, 118, 0.15) → rgba(0, 188, 212, 0.1)
- Border: 1.5px solid rgba(0, 230, 118, 0.4)
- Shadow: 0 4px 20px rgba(0, 230, 118, 0.15)

### METRIC CARDS
**Light Mode:**
- Background: Gradient #FFFFFF → rgba(255, 255, 255, 0.9)
- Border: 1px solid rgba(0, 0, 0, 0.05)
- Shadow: 0 8px 25px rgba(0, 0, 0, 0.08)

**Dark Mode:**
- Background: Gradient rgba(35, 35, 35, 0.9) → rgba(30, 30, 30, 0.85)
- Border: 1px solid rgba(255, 179, 0, 0.15)
- Shadow: 0 8px 25px rgba(0, 0, 0, 0.2)
- Hover Border: rgba(255, 179, 0, 0.3)

### PROFILE CARDS
**Light Mode:**
- Background: Gradient var(--card-bg-light) → rgba(255, 255, 255, 0.9)
- Shadow: 0 15px 40px rgba(0, 0, 0, 0.12)
- Border: 1px solid rgba(0, 0, 0, 0.05)

**Dark Mode:**
- Background: Gradient rgba(25, 25, 25, 0.95) → rgba(30, 30, 30, 0.9)
- Shadow: 0 15px 50px rgba(0, 0, 0, 0.4)
- Border: 1px solid rgba(255, 179, 0, 0.15)

### ALERT OVERLAY
**Light Mode:**
- Overlay: rgba(0, 0, 0, 0.85)
- Alert Background: Gradient #212121 → #1a1a1a
- Border: 3px solid #ff5252
- Shadow: 0 20px 60px rgba(255, 82, 82, 0.3)

**Dark Mode:**
- Overlay: rgba(0, 0, 0, 0.85) (Same darker)
- Alert Background: Gradient rgba(20, 20, 20, 0.95) → rgba(15, 15, 15, 0.9)
- Border: 3px solid #ff6e40 (Warmer red)
- Shadow: 0 20px 70px rgba(255, 82, 82, 0.4)

### SUMMARY MODAL
**Light Mode:**
- Background: Gradient #FFFFFF → rgba(255, 255, 255, 0.95)
- Border: 1px solid rgba(255, 179, 0, 0.1)
- Shadow: 0 25px 70px rgba(0, 0, 0, 0.35)

**Dark Mode:**
- Background: Gradient rgba(25, 25, 25, 0.95) → rgba(30, 30, 30, 0.9)
- Border: 1px solid rgba(255, 179, 0, 0.2)
- Shadow: 0 25px 70px rgba(0, 0, 0, 0.6)

### THEME TOGGLE BUTTON
**Light Mode:**
- Background: rgba(255, 179, 0, 0.15)
- Border: 2px solid rgba(255, 179, 0, 0.3)
- Color: #FFB300
- Animation: glowPulse (golden glow)

**Dark Mode:**
- Background: rgba(0, 230, 118, 0.15)
- Border: 2px solid rgba(0, 230, 118, 0.4)
- Color: #69F0AE (Light Green)
- Animation: accentPulse (green glow)

---

## Hover Effects Color Transitions

### Navigation Links
```
Light Mode: Black → Golden (#FFB300)
Dark Mode:  Light White → Golden (#FFB300)
Background: Transparent → rgba(255, 179, 0, 0.1/0.15)
```

### Feature Cards
```
Light Mode: Normal → Golden Border 0.3 opacity
Dark Mode:  Normal → Golden Border 0.5 opacity
Shadow:     Normal → Enhanced with golden tint
```

### Buttons
```
Light Mode: Golden → Darker Gold
Dark Mode:  Golden → Darker Gold (Same)
Shadow:     Expands & glows in both modes
```

### Cards (Profile, Metric)
```
Light Mode: White → Subtle highlighted
Dark Mode:  Dark → Golden border appears
Transform:  translateY(-6px) in both modes
```

---

## Color Harmony

### Primary Accent (Light Mode)
- Golden Yellow (#FFB300) pairs with:
  - Dark texts (#1A1A1A, #333333)
  - Light backgrounds (#F8F9FA)
  - Creates professional, warm feel

### Primary Accent (Dark Mode)
- Golden Yellow (#FFB300) pairs with:
  - Light texts (#F0F0F0, #B0B0B0)
  - Dark backgrounds (#0D0D0D, #1A1A1A)
  - Creates premium, sophisticated feel

### Secondary Accent (Dark Mode Only)
- Green (#00E676, #69F0AE) provides:
  - Safety/Security signals
  - Contrast against dark backgrounds
  - Success indicators

---

## Accessibility Notes

✅ **Contrast Ratios (WCAG AA)**
- Light mode text on light background: 4.5:1+
- Dark mode text on dark background: 7:1+ (better readability)
- Button colors: 7:1+ contrast in both modes

✅ **Color Blind Friendly**
- Not relying solely on color for information
- Using text labels with icon indicators
- Borders and shadows provide alternative visual cues

✅ **Reduced Motion**
- All animations use smooth easing
- Transitions are 0.3s-0.6s (respects preferences)
- No flashing or excessive movement

---

**Color Theme Version**: 2.0  
**Last Updated**: February 26, 2026  
**Website**: Raksha Ride
