import { useEffect, useState } from 'react'
import { studentApi } from '../services/api'
import './SubjectRatings.css'

export const SubjectRatings = ({ student }) => {
  const [subjectsRatings, setSubjectsRatings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchRatings = async () => {
      if (!student?.fio) {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)
        const data = await studentApi.getSubjectsRatings(student.fio)
        console.log('📊 Рейтинги по предметам:', data)
        setSubjectsRatings(data || [])
      } catch (err) {
        console.error('❌ Ошибка загрузки рейтингов по предметам:', err)
        setError(err.message || 'Ошибка загрузки данных')
      } finally {
        setLoading(false)
      }
    }

    fetchRatings()
  }, [student?.fio])

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

  if (loading) {
    return (
      <div className="subject-ratings-container">
        <div className="loading-spinner-small"></div>
        <p className="loading-text">Загрузка рейтингов...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="subject-ratings-container">
        <div className="error-message">
          <p>❌ {error}</p>
        </div>
      </div>
    )
  }

  if (subjectsRatings.length === 0) {
    return (
      <div className="subject-ratings-container">
        <div className="ratings-empty">
          <p>Нет данных для отображения рейтингов</p>
        </div>
      </div>
    )
  }

  // Подсчитываем общую статистику
  const totalSubjects = subjectsRatings.length
  const totalLessons = subjectsRatings.reduce((sum, subject) => {
    return sum + (subject.ratings?.by_grades?.total_students || 0)
  }, 0)

  return (
    <div className="subject-ratings-container">
      <div className="ratings-header">
        <h2 className="ratings-title">Рейтинг по предметам</h2>
        {student?.group_name && (
          <p className="ratings-group">Группа: {student.group_name}</p>
        )}
        <div className="ratings-stats-badges">
          <div className="stat-badge">
            <span className="stat-badge-value">{totalSubjects}</span>
            <span className="stat-badge-label">Предметов</span>
          </div>
          <div className="stat-badge">
            <span className="stat-badge-value">{totalLessons}</span>
            <span className="stat-badge-label">Занятий</span>
          </div>
        </div>
      </div>

      <div className="ratings-list">
        {subjectsRatings.map((subject, index) => {
          const gradesRating = subject.ratings?.by_grades
          const attendanceRating = subject.ratings?.by_attendance
          const overallRating = subject.ratings?.overall

          // Проверяем, является ли предмет пустым
          const isEmpty = (
            (!gradesRating || (gradesRating.average_grade === 0 && gradesRating.total_students === 0)) &&
            (!attendanceRating || (attendanceRating.attendance === 0 && attendanceRating.total_students === 0))
          )

          const gradesMedal = gradesRating?.position ? getMedal(gradesRating.position) : null
          const attendanceMedal = attendanceRating?.position ? getMedal(attendanceRating.position) : null
          const overallMedal = overallRating?.position ? getMedal(overallRating.position) : null

          const gradesColor = gradesRating?.position ? getPositionColor(gradesRating.position) : '#666'
          const attendanceColor = attendanceRating?.position ? getPositionColor(attendanceRating.position) : '#666'
          const overallColor = overallRating?.position ? getPositionColor(overallRating.position) : '#666'

          return (
            <div
              key={subject.id}
              className={`subject-rating-card ${overallRating?.position <= 3 ? 'top-three' : ''} ${isEmpty ? 'disabled' : ''}`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="subject-rating-header">
                <h3 className="subject-rating-title">{subject.name}</h3>
              </div>

              <div className="subject-rating-content">
                {/* Рейтинг по оценкам */}
                <div className="rating-item rating-item-grades">
                  <div className="rating-item-header">
                    <div className="rating-item-label-wrapper">
                      <span className="rating-item-icon">📊</span>
                      <span className="rating-item-label">По оценкам</span>
                    </div>
                    {gradesRating?.position && (
                      <div className="rating-position" style={{ color: gradesColor }}>
                        {gradesMedal && <span className="position-medal">{gradesMedal}</span>}
                        <span className="position-number">{gradesRating.position}</span>
                        <span className="position-label">МЕСТО</span>
                      </div>
                    )}
                  </div>
                  {gradesRating && (
                    <div className="rating-item-details">
                      <div className="rating-detail">
                        <span className="detail-label">Средний балл:</span>
                        <span className="detail-value highlight">{gradesRating.average_grade.toFixed(2)}</span>
                      </div>
                      <div className="rating-detail">
                        <span className="detail-label">Студентов в группе:</span>
                        <span className="detail-value">{gradesRating.total_students}</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Рейтинг по посещаемости */}
                <div className="rating-item rating-item-attendance">
                  <div className="rating-item-header">
                    <div className="rating-item-label-wrapper">
                      <span className="rating-item-icon">📈</span>
                      <span className="rating-item-label">По посещаемости</span>
                    </div>
                    {attendanceRating?.position && (
                      <div className="rating-position" style={{ color: attendanceColor }}>
                        {attendanceMedal && <span className="position-medal">{attendanceMedal}</span>}
                        <span className="position-number">{attendanceRating.position}</span>
                        <span className="position-label">МЕСТО</span>
                      </div>
                    )}
                  </div>
                  {attendanceRating && (
                    <div className="rating-item-details">
                      <div className="rating-detail">
                        <span className="detail-label">Посещаемость:</span>
                        <span className="detail-value highlight">{attendanceRating.attendance.toFixed(1)}%</span>
                      </div>
                      <div className="rating-detail">
                        <span className="detail-label">Студентов в группе:</span>
                        <span className="detail-value">{attendanceRating.total_students}</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Общий рейтинг среди всех предметов */}
                <div className="rating-item overall">
                  <div className="rating-item-header">
                    <div className="rating-item-label-wrapper">
                      <span className="rating-item-icon">⭐</span>
                      <span className="rating-item-label">Общий рейтинг</span>
                    </div>
                    {overallRating?.position && (
                      <div className="rating-position" style={{ color: overallColor }}>
                        {overallMedal && <span className="position-medal">{overallMedal}</span>}
                        <span className="position-number">{overallRating.position}</span>
                        <span className="position-label">МЕСТО</span>
                      </div>
                    )}
                  </div>
                  {overallRating && (
                    <div className="rating-item-details">
                      <div className="rating-detail">
                        <span className="detail-label">Средняя позиция:</span>
                        <span className="detail-value highlight">{overallRating.average_position.toFixed(1)}</span>
                      </div>
                      <div className="rating-detail">
                        <span className="detail-label">Всего предметов:</span>
                        <span className="detail-value">{overallRating.total_subjects}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}





