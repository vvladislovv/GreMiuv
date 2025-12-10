import { useEffect, useState } from 'react'
import { statsApi } from '../services/api'
import './Rating.css'

export const Rating = ({ student }) => {
  const [gradesRating, setGradesRating] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRating = async () => {
      if (!student?.group_id) {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        const grades = await statsApi.getGradesRating(student.group_id)
        console.log('📊 Рейтинг по оценкам:', grades)
        
        if (grades && grades.length > 0) {
          console.log('📊 Пример данных по оценкам:', grades[0])
          console.log('📊 Все позиции по оценкам:', grades.map(r => `${r.fio}: ${r.position} место, средний ${r.average_grade}`))
        }
        
        setGradesRating(grades || [])
      } catch (error) {
        console.error('❌ Ошибка загрузки рейтинга:', error)
        console.error('Детали:', error.response?.data || error.message)
      } finally {
        setLoading(false)
      }
    }

    fetchRating()
  }, [student?.group_id])

  if (loading) {
    return (
      <div className="rating-container">
        <div className="loading-spinner-small"></div>
        <p className="loading-text">Загрузка рейтинга...</p>
      </div>
    )
  }

  const currentRating = gradesRating
  const currentStudentIndex = currentRating.findIndex(r => r.id === student?.id)

  // Получаем медаль для первых трех мест
  const getMedal = (position) => {
    if (position === 1) return '🥇'
    if (position === 2) return '🥈'
    if (position === 3) return '🥉'
    return null
  }

  // Получаем цвет для позиции
  const getPositionColor = (position) => {
    if (position === 1) return '#ffd700' // Золотой
    if (position === 2) return '#c0c0c0' // Серебряный
    if (position === 3) return '#cd7f32' // Бронзовый
    return '#ff6b35'
  }

  if (currentRating.length === 0) {
    return (
      <div className="rating-container">
        <div className="rating-empty">
          <p>Нет данных для отображения рейтинга</p>
        </div>
      </div>
    )
  }

  return (
    <div className="rating-container">
      <div className="rating-header">
        <h2 className="rating-title">Рейтинг группы</h2>
        {student?.group_name && (
          <p className="rating-group">Группа: {student.group_name}</p>
        )}
      </div>

      <div className="rating-list">
        {currentRating.map((item, index) => {
          const isCurrentStudent = item.id === student?.id
          const medal = getMedal(item.position)
          const positionColor = getPositionColor(item.position)
          
          // Логируем для отладки
          if (index < 5) {
            console.log(`📊 Студент ${index + 1}: ${item.fio}, позиция: ${item.position}, пропуски: ${item.absences || 'N/A'}, средний: ${item.average_grade || 'N/A'}`)
          }
          
          return (
            <div
              key={item.id || `rating-${index}`}
              className={`rating-item ${isCurrentStudent ? 'current' : ''} ${item.position <= 3 ? 'top-three' : ''}`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="rating-position" style={{ color: positionColor }}>
                {medal && <span className="position-medal">{medal}</span>}
                <span className="position-number" style={{ color: positionColor }}>
                  {item.position}
                </span>
                <span className="position-label">место</span>
              </div>
              <div className="rating-info">
                <div className="rating-name">
                  {item.fio}
                  {isCurrentStudent && <span className="you-indicator"> (Вы)</span>}
                </div>
                <div className="rating-details">
                  <div className="rating-stats">
                    <div className="stat-detail">
                      <span className="stat-icon">⭐</span>
                      <span className="stat-text">
                        <span className="stat-label">Средний балл:</span> <strong>{item.average_grade.toFixed(2)}</strong>
                      </span>
                    </div>
                    <div className="stat-detail">
                      <span className="stat-icon">📝</span>
                      <span className="stat-text">
                        <span className="stat-label">Оценок:</span> <strong>{item.total_grades}</strong>
                      </span>
                    </div>
                    {item.average_grade >= 4.5 && (
                      <div className="excellent-badge">Отличник! 🎓</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
