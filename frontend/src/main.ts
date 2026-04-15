import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import { pinia } from './stores/pinia'
import { useUserStore } from './stores/user'
import { applyMarketStyle } from './styles/marketStyle'
import { applyTheme } from './styles/theme'
import './styles/global.css'

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(i18n)

const userStore = useUserStore(pinia)
applyMarketStyle(userStore.marketStyle)
applyTheme(userStore.theme)

if (import.meta.env.DEV) {
  import('./mocks/browser').then(({ worker }) => {
    worker.start({ onUnhandledRequest: 'bypass' })
  })
}

app.mount('#app')
