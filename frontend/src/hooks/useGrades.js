import { useEffect, useState } from 'react'
import { gradesApi, statsApi } from '../services/api'

export const useGrades = (groupId, subjectId) => {
  const [gradesData, setGradesData] = useState(null)
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!groupId || !subjectId) {
      setGradesData(null)
      setStats([])
      return
    }

    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const [grades, statsData] = await Promise.all([
          gradesApi.getByGroupAndSubject(groupId, subjectId),
          statsApi.getByGroupAndSubject(groupId, subjectId),
        ])
        
        setGradesData(grades)
        setStats(statsData)
      } catch (err) {
        setError(err.message)
        console.error('Ошибка загрузки данных:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [groupId, subjectId])

  return { gradesData, stats, loading, error }
}
