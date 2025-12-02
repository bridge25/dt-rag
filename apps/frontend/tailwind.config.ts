/**
 * Tailwind CSS configuration
 *
 * @CODE:FRONTEND-001
 */

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ['class', 'class'],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #8b5cf6 0%, #1e293b 100%)',
        'gradient-shimmer': 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        xl: '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem'
      },
      boxShadow: {
        soft: '0 8px 32px rgba(0, 0, 0, 0.12)',
        card: '0 4px 24px rgba(0, 0, 0, 0.08)',
        'soft-lg': '0 12px 48px rgba(0, 0, 0, 0.15)',
        'elevation-1': '0 1px 2px rgba(0,0,0,0.05)',
        'elevation-2': '0 4px 6px rgba(0,0,0,0.07)',
        'elevation-3': '0 10px 15px rgba(0,0,0,0.1)',
        'elevation-4': '0 20px 25px rgba(0,0,0,0.15)',
        'elevation-5': '0 25px 50px rgba(0,0,0,0.25)',
        'lift': '0 10px 30px rgba(139, 92, 246, 0.15)',
        'lift-hover': '0 20px 40px rgba(139, 92, 246, 0.25)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glass-hover': '0 8px 32px 0 rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,255,255,0.1)',
        'glow-blue': '0 0 20px rgba(0, 243, 255, 0.15)',
        'glow-purple': '0 0 20px rgba(188, 19, 254, 0.15)',
        'neon-blue': '0 0 10px rgba(0, 243, 255, 0.5), 0 0 20px rgba(0, 243, 255, 0.3)',
        'neon-purple': '0 0 10px rgba(188, 19, 254, 0.5), 0 0 20px rgba(188, 19, 254, 0.3)',
        // Ethereal Glass shadows
        'ethereal-sm': '0 0 10px rgba(0, 247, 255, 0.15)',
        'ethereal-md': '0 0 20px rgba(0, 247, 255, 0.25)',
        'ethereal-lg': '0 0 40px rgba(0, 247, 255, 0.35)',
        'ethereal-gold': '0 0 30px rgba(255, 215, 0, 0.4)',
        'ethereal-purple': '0 0 25px rgba(188, 19, 254, 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 250ms ease-in-out',
        'slide-in': 'slideIn 300ms ease-out',
        'shine': 'shine 2s infinite',
        'lift': 'lift 200ms ease-out',
        'confetti': 'confetti 500ms ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'energy-beam': 'energyBeam 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        shine: {
          '0%': { left: '-100%' },
          '50%, 100%': { left: '100%' },
        },
        lift: {
          '0%': { transform: 'translateY(0) scale(1)' },
          '100%': { transform: 'translateY(-2px) scale(1.02)' },
        },
        confetti: {
          '0%': { transform: 'translateY(0) rotate(0deg)', opacity: '1' },
          '100%': { transform: 'translateY(-100px) rotate(360deg)', opacity: '0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.6', boxShadow: '0 0 20px rgba(0, 247, 255, 0.3)' },
          '50%': { opacity: '1', boxShadow: '0 0 40px rgba(0, 247, 255, 0.6)' },
        },
        energyBeam: {
          '0%': { opacity: '0.4', strokeDashoffset: '1000' },
          '50%': { opacity: '1' },
          '100%': { opacity: '0.4', strokeDashoffset: '0' },
        },
      },
      transitionDuration: {
        'fast': '200ms',
        'normal': '300ms',
        'slow': '400ms',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      colors: {
        'dark-navy': 'hsl(var(--dark-navy))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        },
        // Ethereal Glass Color Palette
        space: {
          DEFAULT: '#0b1121',
          light: '#0f172a',
        },
        ethereal: {
          cyan: '#00f7ff',
          blue: '#00f3ff',
          purple: '#bc13fe',
          gold: '#ffd700',
          green: '#0aff0a',
        },
        // Cyberpunk Glass Custom Colors (legacy)
        neon: {
          blue: '#00f3ff',
          purple: '#bc13fe',
          green: '#0aff0a',
          pink: '#ff00ff',
        },
        glass: {
          border: 'rgba(255, 255, 255, 0.1)',
          surface: 'rgba(255, 255, 255, 0.05)',
          highlight: 'rgba(255, 255, 255, 0.15)',
        }
      }
    }
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
