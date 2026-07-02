import { computed, type Ref } from 'vue'

export interface FlatCategory {
  id: number
  name: string
  displayName: string
}

/**
 * 分类树展平 composable
 * @param treeData 分类树响应式数据
 * @param options.maxLevel 最大层级过滤（如 3 表示只展示 level<3 的分类作为父分类选项）
 */
export function useCategoryTree(treeData: Ref<any[]>, options?: { maxLevel?: number }) {
  const flatCategories = computed<FlatCategory[]>(() => {
    const result: FlatCategory[] = []
    const walk = (nodes: any[], depth = 0) => {
      nodes.forEach((n) => {
        if (!options?.maxLevel || n.level < options.maxLevel) {
          result.push({ id: n.id, name: n.name, displayName: '　'.repeat(depth) + n.name })
        }
        if (n.children?.length) walk(n.children, depth + 1)
      })
    }
    walk(treeData.value)
    return result
  })

  return { flatCategories }
}
