import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import { useUserStore } from './stores/user'
import { applyMarketStyle } from './styles/marketStyle'
import './styles/global.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(Toast, { timeout: 3000 })
app.use(i18n)

const userStore = useUserStore(pinia)
applyMarketStyle(userStore.marketStyle)

if (import.meta.env.DEV) {
  import('./mocks/browser').then(({ worker }) => {
    worker.start({ onUnhandledRequest: 'bypass' })
  })
}

app.mount('#app')
