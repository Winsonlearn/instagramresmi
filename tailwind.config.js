/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        neon: {
          cyan: '#00f0ff',
          pink: '#ff006e',
          purple: '#b300ff',
          lime: '#39ff14',
        },
        dark: {
          bg: '#0a0a0a',
          'bg-lighter': '#1a1a1a',
          'bg-lightest': '#2a2a2a',
        },
        text: {
          primary: '#ffffff',
          secondary: '#b0b0b0',
          muted: '#707070',
        },
      },
      boxShadow: {
        'glow-cyan': '0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.3), 0 0 30px rgba(0, 240, 255, 0.2)',
        'glow-pink': '0 0 10px rgba(255, 0, 110, 0.5), 0 0 20px rgba(255, 0, 110, 0.3), 0 0 30px rgba(255, 0, 110, 0.2)',
        'glow-purple': '0 0 10px rgba(179, 0, 255, 0.5), 0 0 20px rgba(179, 0, 255, 0.3), 0 0 30px rgba(179, 0, 255, 0.2)',
        'glow-lime': '0 0 10px rgba(57, 255, 20, 0.5), 0 0 20px rgba(57, 255, 20, 0.3), 0 0 30px rgba(57, 255, 20, 0.2)',
        'glow-cyan-sm': '0 0 5px rgba(0, 240, 255, 0.5)',
        'glow-pink-sm': '0 0 5px rgba(255, 0, 110, 0.5)',
        'glow-purple-sm': '0 0 5px rgba(179, 0, 255, 0.5)',
        'glow-lime-sm': '0 0 5px rgba(57, 255, 20, 0.5)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-glow-cyan': 'pulseGlowCyan 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-glow-pink': 'pulseGlowPink 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'pulse-glow-purple': 'pulseGlowPurple 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-out-right': 'slideOutRight 0.3s ease-out',
        'slide-in-up': 'slideInUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
        'shimmer': 'shimmer 2s infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        pulseGlowCyan: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(0, 240, 255, 0.8), 0 0 40px rgba(0, 240, 255, 0.5)' },
        },
        pulseGlowPink: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(255, 0, 110, 0.5), 0 0 20px rgba(255, 0, 110, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(255, 0, 110, 0.8), 0 0 40px rgba(255, 0, 110, 0.5)' },
        },
        pulseGlowPurple: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(179, 0, 255, 0.5), 0 0 20px rgba(179, 0, 255, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(179, 0, 255, 0.8), 0 0 40px rgba(179, 0, 255, 0.5)' },
        },
        glow: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0.7' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideOutRight: {
          '0%': { transform: 'translateX(0)', opacity: '1' },
          '100%': { transform: 'translateX(100%)', opacity: '0' },
        },
        slideInUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      transitionDuration: {
        '300': '300ms',
      },
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [],
}


