import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    menu?: boolean
    menuTitle?: Record<string, string>
    roles?: string[]
    public?: boolean
  }
}

export {}
