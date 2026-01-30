import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import './styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Toast, { timeout: 3000 })
app.use(i18n)

if (import.meta.env.DEV) {
  import('./mocks/browser').then(({ worker }) => {
    worker.start({ onUnhandledRequest: 'bypass' })
  })
}

app.mount('#app')
