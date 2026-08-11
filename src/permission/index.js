import router from './router'
import {getToken} from "@/utils/auth.js"
import {useUserStore} from "@/store/user.js"
//路由守卫
const whiteList = ['/login'] //白名单
router.beforeEach(async(to)=>{
    //判断是否有token
    const token = getToken()
    const userStore = useUserStore()
    if(token){
        //有token
        if(to.path === '/login'){
            //如果有token,访问登录页,跳转到首页
            return '/dashboard'
        }
        if(!userStore.userInfo){
            //如果没有用户信息,获取用户信息
            await userStore.getUser()
        }
        return true
    }else{
        if(whiteList.includes(to.path)){
            //如果没有token,访问白名单,放行
            return true
        }
        //如果没有token,访问非白名单页面,跳转到登录页
        return '/login'
    }

})