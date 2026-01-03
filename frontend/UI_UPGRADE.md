# ThreatVeil UI Upgrade Documentation

This document describes the redesigned ThreatVeil frontend, now featuring a premium enterprise SaaS UI with consistent design system, improved navigation, and polished interactions.

## Design System

### Brand Colors
- **Primary Accent**: Cyan/Teal (`#22d3ee`) - Used for CTAs, active states, and brand highlights
- **Severity Colors**:
  - High: Red (`#ef4444`)
  - Medium: Amber (`#f59e0b`)
  - Low: Emerald (`#22c55e`)
- **AI Exposure**: Purple (`#a855f7`)

### Spacing Scale
Uses a consistent 4px base unit:
- `--space-1`: 4px
- `--space-2`: 8px
- `--space-3`: 12px
- `--space-4`: 16px
- `--space-6`: 24px
- `--space-8`: 32px

### Typography Hierarchy
- **Page Title**: `text-2xl font-bold tracking-tight text-white`
- **Section Title**: `text-base font-semibold text-white/95`
- **Label**: `text-xs font-medium text-slate-400 uppercase tracking-wider`
- **Muted Text**: `text-sm text-slate-400`

### Card Styling
All cards use the premium glass morphism style:
```css
.card-glass {
  @apply rounded-2xl border border-slate-800/60 bg-[#111827]/80 backdrop-blur-sm;
}
```

---

## Layout Structure

### App Shell (`/src/components/AppShell.tsx`)
The main application layout with:
- **Collapsible Sidebar**: Toggle between full (280px) and icon-only (72px) modes
- **Responsive Design**: Sidebar collapses on smaller screens, mobile uses sheet drawer
- **Content Area**: Max-width 7xl container with consistent padding

### Navigation Items
Located in `/src/components/SidebarNav.tsx`:
1. Dashboard (`/app`) - Main overview
2. Scans (`/app/scans`) - Risk assessments list
3. Horizon (`/app/horizon`) - Weekly security brief
4. Decisions (`/app/decisions`) - Coming soon
5. Assets (`/app/assets`) - Coming soon
6. Settings (`/app/settings`) - Preferences

### Top Bar (`/src/components/TopBar.tsx`)
- Organization selector placeholder
- Global search input
- "New Scan" button (opens modal)
- Notifications indicator
- User menu

---

## UI Kit Components

Located in `/src/components/ui-kit/`:

### StatCard
Metric display card with trend indicator.
```tsx
<StatCard
  label="Current Risk"
  value={75}
  icon={Shield}
  variant="danger" // 'default' | 'accent' | 'warning' | 'danger' | 'success'
  trend={{ value: -5, direction: 'down', label: 'pts' }}
/>
```

### SectionHeader
Consistent section headers with icon and action slot.
```tsx
<SectionHeader
  title="Key Findings"
  icon={ShieldAlert}
  subtitle="12 signals detected"
  action={<Button>Export</Button>}
/>
```

### RiskBadge / SeverityBadge / StatusBadge
Unified badge system with variants.
```tsx
<SeverityBadge severity="high" size="sm" showIcon />
<StatusBadge status="in-progress" />
<AIExposureBadge level="high" />
```

### EmptyState
Premium empty state with abstract SVG background.
```tsx
<EmptyState
  icon="shield"
  title="No assessments yet"
  description="Start by running your first scan."
  action={{ label: 'Run Scan', href: '/app' }}
/>
```

### LoadingSkeleton
Shimmer loading states for various elements.
```tsx
<LoadingSkeleton variant="card" />
<SkeletonTable rows={5} columns={4} />
<SkeletonStats count={4} />
```

---

## Page-Specific Features

### Dashboard (`/app/app/page.tsx`)
- Quick stats grid (domains scanned, avg risk, high risk count, AI exposure)
- Scan form with domain input
- Recent assessments table with click-to-view

### Scans List (`/app/app/scans/page.tsx`)
- Risk level filters (All/High/Medium/Low)
- DataTable with columns: Domain, Risk, AI Exposure, Scanned, Actions
- Selected scan summary panel
- Export JSON button

### Scan Detail (`/app/app/scans/[id]/page.tsx`)
- 60/40 grid layout (Cyber Risk / AI Risk)
- Security Decisions Card at top
- Tabbed signals table (All/High/Medium/Low/AI/External/Vulns)
- Copy button for fix recommendations
- Export JSON button

### Horizon (`/app/app/horizon/page.tsx`)
- Executive-grade dashboard
- Top row: 4 StatCards (Risk, Trend, AI, Critical)
- Risk reduction timeline chart
- Weekly brief card
- Share Brief modal with copy/print

---

## Customization

### Changing Brand Accent Color
1. Update `--brand-accent` in `/src/app/globals.css`
2. Update `brand.accent` in `/tailwind.config.ts`
3. Search and replace `cyan-` class usages if needed

### Adding New Navigation Items
Edit the `navItems` array in `/src/components/SidebarNav.tsx`:
```tsx
{
  title: 'New Feature',
  href: '/app/new-feature',
  icon: StarIcon,
  description: 'Description for tooltip',
  disabled: false, // Set true for "coming soon"
}
```

### Creating New Stat Cards
Use the StatCard component with appropriate variant:
```tsx
<StatCard
  label="Custom Metric"
  value={100}
  icon={CustomIcon}
  variant="accent"
  trend={{ value: 10, direction: 'up' }}
/>
```

---

## Motion & Animations

Built with `framer-motion`:
- **Page transitions**: Fade in with subtle slide up
- **Card hover**: Slight Y-axis lift
- **List items**: Staggered entrance
- **Radial gauge**: Animated stroke dash

Animation utilities in globals.css:
- `.animate-fade-in`
- `.animate-slide-up`
- `.skeleton-shimmer`

---

## Print Styles

The Share Brief modal includes print-optimized styles:
- White background for printing
- `.no-print` class hides non-essential elements
- `.print-only` class shows print-specific content

---

## Dependencies Added

- **framer-motion**: Already in package.json, used throughout for animations
- **@radix-ui/react-dialog**: Added for modal dialogs

---

## File Structure

```
src/
├── app/
│   ├── globals.css       # Design tokens & utilities
│   └── app/
│       ├── page.tsx      # Dashboard
│       ├── scans/
│       │   ├── page.tsx  # Scans list
│       │   └── [id]/page.tsx  # Scan detail
│       └── horizon/
│           └── page.tsx  # Horizon dashboard
├── components/
│   ├── ui-kit/           # Design system components
│   │   ├── StatCard.tsx
│   │   ├── SectionHeader.tsx
│   │   ├── RiskBadge.tsx
│   │   ├── EmptyState.tsx
│   │   └── LoadingSkeleton.tsx
│   ├── AppShell.tsx      # Main layout
│   ├── SidebarNav.tsx    # Navigation
│   ├── TopBar.tsx        # Header bar
│   └── NewScanModal.tsx  # Scan creation modal
└── tailwind.config.ts    # Extended Tailwind config
```
