## Animation Standards

### CSS Transitions (Simple Effects)

```css
/* Standard transition */
.button {
    transition: all 150ms ease;
}

/* Specific properties for performance */
.card {
    transition: transform 200ms ease, box-shadow 200ms ease;
}

/* Hover states */
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
```

### Framer Motion (Complex Animations)

```tsx
import { motion, AnimatePresence } from 'framer-motion';

// Page transitions
function PageWrapper({ children }: { children: React.ReactNode }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
        >
            {children}
        </motion.div>
    );
}

// Staggered list animation
function ItemList({ items }: { items: Item[] }) {
    return (
        <motion.ul>
            {items.map((item, i) => (
                <motion.li
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                >
                    {item.name}
                </motion.li>
            ))}
        </motion.ul>
    );
}
```

### Animation Guidelines

1. **Focus on high-impact moments** - Page loads, modal opens, state changes
2. **One orchestrated animation > scattered micro-interactions**
3. **Keep durations short** - 150-300ms for UI, 300-500ms for page transitions
4. **Use easing** - `ease`, `ease-out` for exits, `ease-in-out` for continuous

---

