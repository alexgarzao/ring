## Typography Standards

### Font Selection (AVOID GENERIC)

```tsx
// FORBIDDEN - Generic AI fonts
font-family: 'Inter', sans-serif;      // Too common
font-family: 'Roboto', sans-serif;     // Too common
font-family: 'Arial', sans-serif;      // System font
font-family: system-ui, sans-serif;    // System stack

// RECOMMENDED - Distinctive fonts
font-family: 'Geist', sans-serif;      // Modern, tech
font-family: 'Satoshi', sans-serif;    // Contemporary
font-family: 'Cabinet Grotesk', sans-serif; // Bold, editorial
font-family: 'Clash Display', sans-serif;   // Display headings
font-family: 'General Sans', sans-serif;    // Clean, versatile
```

### Font Pairing

```css
/* Display + Body pairing */
--font-display: 'Clash Display', sans-serif;
--font-body: 'Satoshi', sans-serif;

/* Heading uses display */
h1, h2, h3 {
    font-family: var(--font-display);
}

/* Body uses readable font */
body, p, span {
    font-family: var(--font-body);
}
```

---

