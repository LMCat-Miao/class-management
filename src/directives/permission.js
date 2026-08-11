import { useUserStore } from '@/stores/user'

export default {
  mounted(el, binding) {
    const value = binding.value
    if (!value) return

    const userStore = useUserStore()
    const codes = Array.isArray(value) ? value : [value]
    if (!userStore.hasPermission(codes)) {
      el.parentNode?.removeChild(el)
    }
  }
}
