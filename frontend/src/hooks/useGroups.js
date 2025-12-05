import { useEffect, useState } from 'react'
import { groupsApi } from '../services/api'

export const useGroups = () => {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        const data = await groupsApi.getAll()
        setGroups(data)
        setError(null)
      } catch (err) {
        setError(err.message)
        console.error('Ошибка загрузки групп:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchGroups()
  }, [])

  return { groups, loading, error }
}
