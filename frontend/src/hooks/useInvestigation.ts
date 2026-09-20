import { useState, useEffect, useRef } from 'react'
import type { Investigation } from '@/types/api'
import { api } from '@/services/api'

export function useInvestigation(investigationId: string) {
  const [investigation, setInvestigation] = useState<Investigation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    let isMounted = true

    const fetchInvestigation = async () => {
      try {
        const data = await api.getInvestigation(investigationId)
        if (!isMounted) return

        setInvestigation(data)
        setError(null)
        setLoading(false)
      } catch (err) {
        if (!isMounted) return
        setError(err instanceof Error ? err.message : 'Failed to fetch investigation')
        setLoading(false)
      }
    }

    // Initial fetch
    fetchInvestigation()

    return () => {
      isMounted = false
    }
  }, [investigationId])

  return { investigation, loading, error }
}
