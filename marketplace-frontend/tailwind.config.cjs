/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class', // <-- correct key name (case-sensitive)
    content: ['./src/**/*.{html,js,svelte,ts}'],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui'],
                display: ['Poppins', 'Inter', 'ui-sans-serif']
            },
            colors: {
                brand: {
                    50: '#f4f8ff', 100: '#e9f0ff', 200: '#cfe0ff', 300: '#a8c1ff', 400: '#7ea0ff',
                    500: '#567dff', 600: '#3c5de6', 700: '#2f47b8', 800: '#25398f', 900: '#1f2c6b'
                },
                accent: {
                    50: '#fef7f1', 100: '#fde9d6', 200: '#fbd0a8', 300: '#f8b06d', 400: '#f28a2f',
                    500: '#e87010', 600: '#c95a0a', 700: '#a0470c', 800: '#7d390f', 900: '#632f10'
                }
            },
            boxShadow: { soft: '0 10px 30px rgba(2,6,23,0.08)' }
        }
    },
    plugins: []
};
