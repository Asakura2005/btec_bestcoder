// main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

// Import Styles
import 'vuetify/styles'
import './assets/main.css'
import './assets/css/globals.css'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#6366f1', // Indigo 500
          secondary: '#4f46e5', // Indigo 600
          accent: '#818cf8', // Indigo 400
          error: '#ef4444',
          info: '#3b82f6',
          success: '#22c55e',
          warning: '#f59e0b',
          background: '#f8fafc',
          surface: '#ffffff',
          'on-surface': '#1e293b',
          'on-background': '#1e293b',
        },
      },
    },
  },
  icons: {
    defaultSet: 'mdi',
  },
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

app.use(router)

app.use(vuetify)

app.mount('#app')