/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#FE2C55',
        'primary-light': '#FF6B81',
        'primary-dark': '#E0194A',
        'accent-cyan': '#25F4EE',
        'bg-page': '#F7F8FA',
        'bg-card': '#FFFFFF',
        'bg-elevated': '#FFFFFF',
        'bg-sunken': '#F3F4F6',
        'text-primary': '#111827',
        'text-secondary': '#6B7280',
        'text-tertiary': '#9CA3AF',
        'text-inverse': '#FFFFFF',
        'border-c': '#E5E7EB',
      },
      borderRadius: {
        lg: '14px',
        xl: '20px',
      },
      boxShadow: {
        xs: '0 1px 2px rgba(0, 0, 0, 0.04)',
        sm: '0 2px 8px rgba(0, 0, 0, 0.06)',
        base: '0 4px 16px rgba(0, 0, 0, 0.08)',
        float: '0 8px 32px rgba(0, 0, 0, 0.12)',
        input: '0 -2px 12px rgba(0, 0, 0, 0.08)',
      },
      fontFamily: {
        sans: ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'sans-serif'],
      },
    }
  },
  plugins: [],
  corePlugins: {
    preflight: false,
  }
}
