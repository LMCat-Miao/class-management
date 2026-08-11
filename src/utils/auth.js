//封装token

//统一管理key取名token
const TOKEN_KEY = 'token'

//获取token,获取登录凭证
export function getToken(){
    return localStorage.getItem(TOKEN_KEY)
}

//保存token,保存登录凭证
export function setToken(token){
    return localStorage.setItem(TOKEN_KEY,token)
}

//删除token，删除登录凭证
export function removeToken(){
    return localStorage.removeItem(TOKEN_KEY)
}