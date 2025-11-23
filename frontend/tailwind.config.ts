import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#0F172A',
          accent: '#22d3ee',
        },
      },
      boxShadow: {
        card: '0 25px 50px -12px rgba(15, 23, 42, 0.25)',
      },
    },
  },
  plugins: [],
};

export default config;
