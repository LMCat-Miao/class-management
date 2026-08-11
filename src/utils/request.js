//axios核心封装
import axios from "axios"
import {getToken,removeToken} from "@/utils/auth.js"
//创建axios实例
const request = axios.create({
    baseURL:import.meta.env.VITE_APP_URL,
    setTimeout:5000
})
//请求拦截器
request.interceptors.request.use(
    config=>{
        const token = getToken()
        if(token){
            config.headers.Authorization =
            `Bearer ${token}`
        }
        return config
    },
    error=>{
        return Promise.reject(error)
    }
)

//响应拦截器
request.interceptors.response.use(
    response=>{
        return response.data
    },
    error=>{
        if(token === 401){
            removeToken()
            router.push('/login')
        }
        return Promise.reject(error)
    }

)
export default request