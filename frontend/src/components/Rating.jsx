import { memo, useCallback, useEffect, useMemo, useState } from 'react'
import { statsApi } from '../services/api'
import './Rating.css'

// Кэш для рейтингов (глобальный, чтобы сохранялся между переключениями вкладок)
const ratingCache = new Map()
// Флаги для отслеживания загрузки
const loadingFlags = new Map()

// Предзагрузка рейтинга (можно вызвать заранее)
export const preloadRating = async (groupId) => {
  if (!groupId) return
  
  const cacheKey = `group_${groupId}`
  
  // Если уже в кэше, не загружаем
  if (ratingCache.has(cacheKey)) {
    return ratingCache.get(cacheKey)
  }
  
  // Если уже загружается, не дублируем запрос
  if (loadingFlags.get(cacheKey)) {
    return new Promise((resolve) => {
      const checkCache = setInterval(() => {
        if (ratingCache.has(cacheKey)) {
          clearInterval(checkCache)
          resolve(ratingCache.get(cacheKey))
        }
      }, 100)
      
      // Таймаут на случай ошибки
      setTimeout(() => {
        clearInterval(checkCache)
        resolve(null)
      }, 10000)
    })
  }
  
  try {
    loadingFlags.set(cacheKey, true)
    
    // Загружаем оба рейтинга параллельно
    const [grades, absences] = await Promise.all([
      statsApi.getGradesRating(groupId),
      statsApi.getAbsencesRating(groupId)
    ])
    
    const ratingsData = {
      grades: grades || [],
      absences: absences || [],
      timestamp: Date.now()
    }
    
    ratingCache.set(cacheKey, ratingsData)
    loadingFlags.delete(cacheKey)
    
    // Очищаем кэш через 10 минут (увеличено для лучшей производительности)
    setTimeout(() => {
      ratingCache.delete(cacheKey)
    }, 10 * 60 * 1000)
    
    return ratingsData
  } catch (error) {
    console.error('❌ Ошибка предзагрузки рейтинга:', error)
    loadingFlags.delete(cacheKey)
    return null
  }
}

export const Rating = memo(({ student }) => {
  const [activeTab, setActiveTab] = useState('grades') // 'grades' или 'absences'
  const [gradesRating, setGradesRating] = useState([])
  const [absencesRating, setAbsencesRating] = useState([])
  const [loading, setLoading] = useState(true)

  // Мемоизируем текущий рейтинг для оптимизации
  const currentRating = useMemo(() => {
    return activeTab === 'grades' ? gradesRating : absencesRating
  }, [activeTab, gradesRating, absencesRating])

  const fetchRatings = useCallback(async () => {
    if (!student?.group_id) {
      setLoading(false)
      return
    }

    const cacheKey = `group_${student.group_id}`
    const cached = ratingCache.get(cacheKey)
    
    if (cached) {
      console.log('📦 Используем кэшированные данные рейтинга')
      setGradesRating(cached.grades || [])
      setAbsencesRating(cached.absences || [])
      setLoading(false)
      
      // Проверяем, не устарел ли кэш (больше 10 минут)
      const cacheAge = Date.now() - (cached.timestamp || 0)
      if (cacheAge > 10 * 60 * 1000) {
        // Обновляем в фоне
        preloadRating(student.group_id)
      }
      return
    }

    try {
      setLoading(true)
      
      // Используем функцию предзагрузки
      const ratingsData = await preloadRating(student.group_id)
      
      if (ratingsData) {
        setGradesRating(ratingsData.grades || [])
        setAbsencesRating(ratingsData.absences || [])
      } else {
        setGradesRating([])
        setAbsencesRating([])
      }
    } catch (error) {
      console.error('❌ Ошибка загрузки рейтинга:', error)
      console.error('Детали:', error.response?.data || error.message)
      setGradesRating([])
      setAbsencesRating([])
    } finally {
      setLoading(false)
    }
  }, [student?.group_id])

  useEffect(() => {
    fetchRatings()
  }, [fetchRatings])

  if (loading) {
    return (
      <div className="rating-container">
        <div className="loading-spinner-small"></div>
        <p className="loading-text">Загрузка рейтинга...</p>
      </div>
    )
  }

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

  if (currentRating.length === 0 && !loading) {
    return (
      <div className="rating-container">
        <div className="rating-empty">
          <div className="empty-icon">📊</div>
          <h3 className="empty-title">Нет данных</h3>
          <p className="empty-description">
            {activeTab === 'grades' 
              ? 'Нет данных для отображения рейтинга по оценкам'
              : 'Нет данных для отображения рейтинга по пропускам'}
          </p>
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

      {/* Табы для переключения между рейтингами */}
      <div className="rating-tabs">
        <button
          className={`rating-tab ${activeTab === 'grades' ? 'active' : ''}`}
          onClick={() => setActiveTab('grades')}
        >
          По оценкам
        </button>
        <button
          className={`rating-tab ${activeTab === 'absences' ? 'active' : ''}`}
          onClick={() => setActiveTab('absences')}
        >
          По пропускам
        </button>
      </div>

      <div className="rating-list">
        {currentRating.map((item, index) => {
          const isCurrentStudent = item.id === student?.id
          const medal = getMedal(item.position)
          const positionColor = getPositionColor(item.position)
          
          return (
            <div
              key={item.id || `rating-${index}`}
              className={`rating-item ${isCurrentStudent ? 'current' : ''} ${item.position <= 3 ? 'top-three' : ''}`}
              style={{ animationDelay: `${index * 0.03}s` }}
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
                    {activeTab === 'grades' ? (
                      <>
                        <div className="stat-detail">
                          <span className="stat-icon">⭐</span>
                          <span className="stat-text">
                            <span className="stat-label">Средний балл:</span> <strong>{item.average_grade?.toFixed(2) || 'Н/Д'}</strong>
                          </span>
                        </div>
                        <div className="stat-detail">
                          <span className="stat-icon">📝</span>
                          <span className="stat-text">
                            <span className="stat-label">Оценок:</span> <strong>{item.total_grades || 0}</strong>
                          </span>
                        </div>
                        {item.average_grade >= 4.5 && item.position <= 3 && (
                          <div className="excellent-badge">Отличник! 🎓</div>
                        )}
                      </>
                    ) : (
                      <div className="stat-detail">
                        <span className="stat-icon">❌</span>
                        <span className="stat-text">
                          <span className="stat-label">Пропусков:</span> <strong>{item.absences || 0}</strong>
                        </span>
                      </div>
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
})

Rating.displayName = 'Rating'
