import request from '@/utils/request'

//获取课程列表
export function getCourseList(params){
    return request({
        url:'/course/list',
        method:'GET',
        params
    })
}

//获取课程详细
export function getCourseDetial(id){
    return ({
        url:`/course/${id}`,
        method:'GET',
    })
} 

//新增课程
export function createCourse(data){
    return({
        url:'/course',
        method:'POST',
        data
    })
}

//修改课程
export function updataCourse(id,data){
    return({
        url:`/course/${id}`,
        method:'PUT',
        data
    })
}

//删除课程
export function deleteCourse(id){
    return ({
        url:`/course/${id}`,
        method:'DELETE'
    })
}