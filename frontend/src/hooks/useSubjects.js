import { useEffect, useState } from 'react'
import { subjectsApi } from '../services/api'

export const useSubjects = (groupId) => {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!groupId) {
      setSubjects([])
      return
    }

    const fetchSubjects = async () => {
      try {
        setLoading(true)
        const data = await subjectsApi.getByGroup(groupId)
        setSubjects(data)
        setError(null)
      } catch (err) {
        setError(err.message)
        console.error('Ошибка загрузки предметов:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchSubjects()
  }, [groupId])

  return { subjects, loading, error }
}
