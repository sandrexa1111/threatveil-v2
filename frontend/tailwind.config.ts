import type { Config } from 'tailwindcss';

const config: Config = {
	darkMode: ['class'],
	content: ['./src/**/*.{ts,tsx}'],
	theme: {
		extend: {
			// Spacing utilities mapped to design tokens
			spacing: {
				'4.5': '1.125rem',  // 18px
				'13': '3.25rem',    // 52px
				'15': '3.75rem',    // 60px
				'18': '4.5rem',     // 72px
				'22': '5.5rem',     // 88px
			},
			colors: {
				brand: {
					DEFAULT: '#0F172A',
					accent: '#22d3ee',
					'accent-light': '#67e8f9',
					'accent-dark': '#0891b2',
				},
				// Semantic severity colors
				severity: {
					high: '#ef4444',
					medium: '#f59e0b',
					low: '#22c55e',
					critical: '#dc2626',
				},
				// AI exposure colors
				ai: {
					high: '#a855f7',
					medium: '#8b5cf6',
					low: '#6366f1',
				},
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))',
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))',
				},
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))',
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))',
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))',
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))',
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))',
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))',
				},
			},
			boxShadow: {
				card: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
				'card-hover': '0 8px 25px -5px rgba(0, 0, 0, 0.3), 0 4px 10px -5px rgba(34, 211, 238, 0.1)',
				'glow-accent': '0 0 20px rgba(34, 211, 238, 0.15)',
				'glow-accent-lg': '0 0 30px rgba(34, 211, 238, 0.2)',
			},
			borderRadius: {
				'2xl': '1rem',
				'3xl': '1.5rem',
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)',
			},
			fontSize: {
				'2xs': ['0.625rem', { lineHeight: '0.75rem' }],
			},
			keyframes: {
				fadeIn: {
					'0%': { opacity: '0' },
					'100%': { opacity: '1' },
				},
				slideUp: {
					'0%': { opacity: '0', transform: 'translateY(10px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' },
				},
				slideInLeft: {
					'0%': { opacity: '0', transform: 'translateX(-10px)' },
					'100%': { opacity: '1', transform: 'translateX(0)' },
				},
				shimmer: {
					'0%': { backgroundPosition: '200% 0' },
					'100%': { backgroundPosition: '-200% 0' },
				},
				// New animations for High-Fidelity UI
				float: {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-10px)' },
				},
				'pulse-glow': {
					'0%, 100%': { opacity: '0.5', transform: 'scale(1)' },
					'50%': { opacity: '1', transform: 'scale(1.1)' },
				},
				'draw-path': {
					'0%': { strokeDashoffset: '1' },
					'100%': { strokeDashoffset: '0' },
				}
			},
			animation: {
				'fade-in': 'fadeIn 0.3s ease-out',
				'slide-up': 'slideUp 0.3s ease-out',
				'slide-in-left': 'slideInLeft 0.2s ease-out',
				'shimmer': 'shimmer 1.5s ease-in-out infinite',
				'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				// New animations
				'float': 'float 6s ease-in-out infinite',
				'pulse-glow': 'pulse-glow 4s ease-in-out infinite',
				'draw': 'draw-path 1s ease-out forwards',
			},
			transitionDuration: {
				'250': '250ms',
				'350': '350ms',
			},
			backdropBlur: {
				xs: '2px',
			},
		},
	},
	plugins: [require('tailwindcss-animate')],
};

export default config;
