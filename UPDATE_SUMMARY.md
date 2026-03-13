# Update Summary: Experience Pages Standardization

## Pages Updated
1. /ja/experiences/karate/
2. /ja/experiences/kendo/
3. /ja/experiences/bonseki/
4. /ja/experiences/kado/
5. /ja/experiences/chado/
6. /ja/experiences/taiko/

## Changes Applied to Each Page

### 1. Remove "体験スケジュール" Section
- Completely removed the schedule section with time table
- This matches the kyudo/iaido approach

### 2. Remove "心の静寂" Feature Card
- Removed feature card titled "心の静寂" or "心の静けさ" if present
- Remaining cards auto-reflow in the grid

### 3. Update Introduction
- Changed section heading from "XXXの精神性" to simply "XXX" (e.g., "空手の精神性" → "空手")
- Simplified introduction text to be more concise and experience-focused

### 4. Add "料金・詳細" Section (Like Iaido)
- Add pricing section with standardized design
- Include CSS styles matching iaido page exactly
- Pricing information displayed in cards
- Horizontal layout for "所要時間" and "参加人数" (mobile stacks vertically)

### 5. Add "注意事項" Section (Like Iaido)
- Left-aligned heading and list items
- 3rem top margin for heading spacing
- Common 4 items:
  - 約3日前までのご予約をお願いします（当日予約も可能な場合があります）。
  - 初心者大歓迎です。
  - 動きやすい服装でお越しください。
  - 体験内容は天候等により変更となる場合があります。
- Equipment-specific text maintained (no generic "弓道着" references)

### 6. Responsive Design
- Mobile: Vertical stacking
- Tablet/PC: Grid layouts
- Consistent spacing across all screen sizes

## CSS Styles Added (Per Page)
```css
.pricing-section
.pricing-content
.pricing-card
.pricing-grid
.pricing-item
.pricing-details
.pricing-info-row
.info-item
.pricing-info-box
```

## Responsive Breakpoints
- Mobile: ≤768px
- Tablet: 769px-1024px
- Desktop: >1024px

