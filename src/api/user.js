//封装登录接口
import request from "@/utils/request.js"
//获取用户信息接口
export function getUserInfo(){
    return request({
        url:'/user/info',
        method:'get'
    })
}

export function login(data){
    return request({
        url:'/login',
        method:'post',
        data
    })
}
    