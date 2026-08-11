import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import persist from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import './styles/index.css'
import './permission'

const app = createApp(App)
const pinia = createPinia()
pinia.use(persist)

app.use(ElementPlus)
app.use(pinia)
app.use(router)
app.mount('#app')
