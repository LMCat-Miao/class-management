//vue
import {createApp} from "vue"
import App from "./App.vue"

//router
import router from './router'

//pinia
import {createPinia} from 'pinia'
//引入持久化插件
import persist from 'pinia-plugin-persistedstate'

//插件
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

//全局css
import './style.css'
import './styles/index.css'

//创建应用实例
const app = createApp(App)

//创建pinia
const pinia = createPinia()
//使用持久化插件
pinia.use(persist)

//使用插件
app.use(ElementPlus)
app.use(pinia)
app.use(router)


//挂载应用实例
app.mount('#app')