//创建pinia仓库
import {defineStore} from 'pinia'
import {getUserInfo} from '@/api/user.js'
//创建用户仓库
export const useUserStore = defineStore(
'user',
{

state:()=>({

userInfo:null

}),

actions:{

setUserInfo(info){

this.userInfo=info

},
//获取用户信息
async getUser(){
    const res = await getUserInfo()
    this.userInfo = res.data
},

clearUserInfo(){

this.userInfo=null


}

}

}

)
