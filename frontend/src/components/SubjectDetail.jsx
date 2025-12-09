import { useState, useEffect } from 'react'
import './SubjectDetail.css'
import { studentApi } from '../services/api'

export const SubjectDetail = ({ subject, student, onBack }) => {
  const [grades, setGrades] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchGrades = async () => {
      try {
        setLoading(true)
        const data = await studentApi.getGrades(student.fio, subject.id)
        setGrades(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchGrades()
  }, [student.fio, subject.id])

  if (loading) {
    return (
      <div className="subject-detail">
        <div className="loading">Загрузка...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="subject-detail">
        <div className="error">Ошибка: {error}</div>
      </div>
    )
  }

  return (
    <div className="subject-detail">
      <div className="subject-detail-header">
        <div className="subject-header-badge">
          <span className="subject-icon">📚</span>
          <h2 className="subject-name">{subject.name}</h2>
        </div>
        <div className="subject-stats-summary">
          <div className="summary-card">
            <div className="summary-icon">📊</div>
            <div className="summary-content">
              <span className="summary-label">Всего занятий</span>
              <span className="summary-value">{subject.stats?.total || 0}</span>
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-icon">✅</div>
            <div className="summary-content">
              <span className="summary-label">Оценок</span>
              <span className="summary-value">{subject.stats?.grades || 0}</span>
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-icon">❌</div>
            <div className="summary-content">
              <span className="summary-label">Пропусков</span>
              <span className="summary-value absence-value">{subject.stats?.absences || 0}</span>
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-icon">📈</div>
            <div className="summary-content">
              <span className="summary-label">Посещаемость</span>
              <span className="summary-value attendance-value">{subject.stats?.attendance || 0}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grades-list">
        <div className="grades-header">
          <h3 className="grades-title">📋 Оценки по датам</h3>
          <span className="grades-count">{grades?.grades?.length || 0} записей</span>
        </div>
        {grades && grades.grades && grades.grades.length > 0 ? (
          <div className="grades-items">
            {grades.grades.map((grade, index) => (
              <div key={index} className={`grade-item ${getGradeClass(grade.value)}`}>
                <div className="grade-item-left">
                  <span className="grade-date-icon">📅</span>
                  <span className="grade-date">{grade.date}</span>
                </div>
                <span className={`grade-value ${getGradeClass(grade.value)}`}>
                  {grade.value || '—'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-grades">
            <div className="no-grades-icon">📝</div>
            <p>Нет оценок по этому предмету</p>
          </div>
        )}
      </div>
    </div>
  )
}

function getGradeClass(value) {
  if (!value) return 'empty'
  const val = value.toString().toLowerCase()
  if (val.includes('пропуск') || val === 'н' || val === 'н/я') return 'absence'
  const num = parseFloat(val)
  if (num >= 4.5) return 'excellent'
  if (num >= 3.5) return 'good'
  if (num >= 2.5) return 'satisfactory'
  return 'bad'
}
