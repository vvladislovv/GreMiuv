import { useEffect, useState } from 'react'
import { studentApi } from '../services/api'

export const useStudentData = (fio, initData) => {
  const [student, setStudent] = useState(null)
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    console.log('🔄 useStudentData: ФИО =', fio, 'тип:', typeof fio)
    
    // Если ФИО не указано, устанавливаем состояние загрузки, но не ошибку
    // Ошибка будет показана только если ФИО действительно не найдено после всех попыток
    if (!fio) {
      console.log('⚠️ useStudentData: ФИО не указано, ожидаем...')
      setLoading(true)
      setError(null)
      setStudent(null)
      setSubjects([])
      return
    }
    
    // Если ФИО есть, но это пустая строка, показываем ошибку
    if (fio.trim() === '') {
      console.log('⚠️ useStudentData: ФИО пустое')
      setError('ФИО не указано')
      setLoading(false)
      return
    }

    const fetchData = async () => {
      try {
        console.log('📡 useStudentData: Начинаем загрузку данных для ФИО:', fio)
        setLoading(true)
        setError(null)

        // Получаем данные студента и предметы параллельно
        console.log('📡 Отправляем запросы на бэкенд...')
        const [studentData, subjectsData, statsData] = await Promise.all([
          studentApi.getByFio(fio),
          studentApi.getSubjects(fio),
          studentApi.getStats(fio)
        ])
        
        console.log('✅ useStudentData: Данные получены:', {
          student: studentData,
          subjectsCount: subjectsData?.length,
          stats: statsData
        })

        // Объединяем данные студента со статистикой
        setStudent({
          ...studentData,
          stats: statsData.stats
        })
        setSubjects(subjectsData)
      } catch (err) {
        // Улучшенная обработка ошибок
        let errorMessage = 'Ошибка загрузки данных'
        
        if (err.response) {
          // Ошибка от сервера
          const detail = err.response.data?.detail || err.response.data?.message
          // Если детали содержат переносы строк, сохраняем их
          errorMessage = detail || `Ошибка ${err.response.status}`
        } else if (err.request) {
          // Запрос отправлен, но ответа нет
          errorMessage = 'Сервер не отвечает. Проверьте подключение к интернету.'
        } else {
          // Другая ошибка
          errorMessage = err.message || 'Неизвестная ошибка'
        }
        
        setError(errorMessage)
        console.error('❌ useStudentData: Ошибка загрузки данных студента:', {
          error: err,
          fio: fio,
          response: err.response?.data,
          status: err.response?.status,
          message: err.message,
          request: err.request ? 'Запрос отправлен, но ответа нет' : 'Запрос не отправлен'
        })
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [fio])

  return { student, subjects, loading, error }
}
