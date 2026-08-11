import request from "@/uitls/request"

export function getDashboardData(){
    return request({
        url:'/dashboard',
        method:'get'
    })
}