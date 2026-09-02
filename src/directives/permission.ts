import type { Directive } from 'vue'
import { useUserStore } from '@/stores/user'

const permissionDirective: Directive<HTMLElement, string | string[] | undefined> =
  {
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

export default permissionDirective
