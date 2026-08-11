import {defineStore} from 'pinia'

export const usePermissionStore = defineStore(
'permission',
{
state:()=>({
    menu:[
        {
            name:'首页',
            path:'/dashboard',
        },
        {
            name:'课程管理',
            path:'/course'
        }
    ]
})
})