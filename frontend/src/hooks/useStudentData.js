import { useEffect, useState } from 'react'
import { studentApi } from '../services/api'

export const useStudentData = (fio, initData) => {
  const [student, setStudent] = useState(null)
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [telegramData, setTelegramData] = useState(null)

  useEffect(() => {
    console.log('🔄 useStudentData: ФИО =', fio, 'тип:', typeof fio, 'initData:', !!initData)
    
    const fetchData = async () => {
      let telegramFio = fio
      let finalFio = fio
      
      try {
        setLoading(true)
        setError(null)

        // Если есть initData, сначала получаем данные из Telegram
        if (initData && initData.trim() !== '') {
          try {
            console.log('📡 Получаем данные из Telegram...')
            const telegramResponse = await studentApi.getByTelegram(initData)
            console.log('✅ Данные из Telegram получены:', telegramResponse)
            
            setTelegramData(telegramResponse.telegram)
            
            // Используем ФИО из Telegram, если оно есть (приоритет над переданным fio)
            if (telegramResponse.fio) {
              telegramFio = telegramResponse.fio
              finalFio = telegramResponse.fio
              console.log('✅ Используем ФИО из Telegram:', finalFio)
              
              // Если студент найден в БД, загружаем его данные
              if (telegramResponse.student) {
                const [subjectsData, statsData] = await Promise.all([
                  studentApi.getSubjects(finalFio),
                  studentApi.getStats(finalFio)
                ])
                
                setStudent({
                  ...telegramResponse.student,
                  stats: statsData.stats,
                  telegram: telegramResponse.telegram
                })
                setSubjects(subjectsData)
                setLoading(false)
                return
              }
            }
          } catch (tgErr) {
            console.warn('⚠️ Ошибка при получении данных из Telegram:', tgErr)
            // Продолжаем работу без данных Telegram
          }
        }
        
        // Если ФИО не указано (ни из параметра, ни из Telegram), ждем
        if (!finalFio) {
          console.log('⚠️ useStudentData: ФИО не указано, ожидаем загрузку из Telegram...')
          setLoading(true)
          setError(null)
          setStudent(null)
          setSubjects([])
          return
        }
        
        // Если ФИО есть, но это пустая строка, показываем ошибку
        if (finalFio.trim() === '') {
          console.log('⚠️ useStudentData: ФИО пустое')
          setError('ФИО не указано')
          setLoading(false)
          return
        }

        // Получаем данные студента и предметы параллельно
        console.log('📡 Отправляем запросы на бэкенд для ФИО:', finalFio)
        const [studentData, subjectsData, statsData] = await Promise.all([
          studentApi.getByFio(finalFio),
          studentApi.getSubjects(finalFio),
          studentApi.getStats(finalFio)
        ])
        
        console.log('✅ useStudentData: Данные получены:', {
          student: studentData,
          subjectsCount: subjectsData?.length,
          stats: statsData
        })

        // Объединяем данные студента со статистикой и данными Telegram
        setStudent({
          ...studentData,
          stats: statsData.stats,
          telegram: telegramData
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
          fio: finalFio || telegramFio || fio,
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
  }, [fio, initData])

  return { student, subjects, loading, error }
}
