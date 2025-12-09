import { useState, useEffect } from 'react'
import './Calendar.css'
import { studentApi } from '../services/api'

export const Calendar = ({ student, subjects, onBack }) => {
  const [selectedSubject, setSelectedSubject] = useState(null)
  const [calendarData, setCalendarData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (selectedSubject) {
      loadCalendarData()
    }
  }, [selectedSubject])

  const loadCalendarData = async () => {
    try {
      setLoading(true)
      const data = await studentApi.getGrades(student.fio, selectedSubject.id)
      setCalendarData(data)
    } catch (err) {
      console.error('Ошибка загрузки календаря:', err)
    } finally {
      setLoading(false)
    }
  }

  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate()
  }

  const getFirstDayOfMonth = (year, month) => {
    return new Date(year, month, 1).getDay()
  }

  const renderCalendar = () => {
    if (!calendarData || !calendarData.calendar) {
      return <div className="no-calendar-data">Выберите предмет для просмотра календаря</div>
    }

    const months = Object.keys(calendarData.calendar).sort()
    if (months.length === 0) {
      return <div className="no-calendar-data">Нет данных для отображения</div>
    }

    return months.map(monthKey => {
      const [year, month] = monthKey.split('-').map(Number)
      const monthData = calendarData.calendar[monthKey]
      
      // Создаем карту дат для быстрого поиска
      const dateMap = {}
      monthData.forEach(item => {
        const day = parseInt(item.date.split('-')[2])
        dateMap[day] = item.value
      })

      const daysInMonth = getDaysInMonth(year, month - 1)
      const firstDay = getFirstDayOfMonth(year, month - 1)
      const monthName = new Date(year, month - 1).toLocaleString('ru', { month: 'long', year: 'numeric' })

      const days = []
      
      // Пустые ячейки до первого дня месяца
      for (let i = 0; i < firstDay; i++) {
        days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>)
      }

      // Дни месяца
      for (let day = 1; day <= daysInMonth; day++) {
        const grade = dateMap[day]
        const hasGrade = grade !== undefined
        days.push(
          <div
            key={day}
            className={`calendar-day ${hasGrade ? 'has-grade' : ''} ${getGradeClass(grade)}`}
          >
            <span className="day-number">{day}</span>
            {hasGrade && (
              <span className="day-grade">{grade || '—'}</span>
            )}
          </div>
        )
      }

      return (
        <div key={monthKey} className="calendar-month">
          <div className="month-header">
            <h3 className="month-title">{monthName}</h3>
            <div className="month-stats">
              <span className="month-grade-count">
                {monthData.filter(item => item.value && !item.value.toString().toLowerCase().includes('пропуск') && item.value !== 'н' && item.value !== 'н/я').length} оценок
              </span>
              <span className="month-absence-count">
                {monthData.filter(item => {
                  const val = item.value?.toString().toLowerCase() || ''
                  return val.includes('пропуск') || val === 'н' || val === 'н/я'
                }).length} пропусков
              </span>
            </div>
          </div>
          <div className="calendar-weekdays">
            <div className="weekday">Пн</div>
            <div className="weekday">Вт</div>
            <div className="weekday">Ср</div>
            <div className="weekday">Чт</div>
            <div className="weekday">Пт</div>
            <div className="weekday">Сб</div>
            <div className="weekday">Вс</div>
          </div>
          <div className="calendar-grid">
            {days}
          </div>
        </div>
      )
    })
  }

  return (
    <div className="calendar-container">
      <div className="calendar-subject-selector">
        <label className="selector-label">📚 Выберите предмет:</label>
        <select
          value={selectedSubject?.id || ''}
          onChange={(e) => {
            const subject = subjects.find(s => s.id === parseInt(e.target.value))
            setSelectedSubject(subject)
          }}
          className="subject-select"
        >
          <option value="">-- Выберите предмет --</option>
          {subjects.map(subject => (
            <option key={subject.id} value={subject.id}>
              {subject.name}
            </option>
          ))}
        </select>
      </div>

      {selectedSubject && (
        <div className="selected-subject-card">
          <div className="subject-card-header">
            <h3 className="subject-card-title">{selectedSubject.name}</h3>
          </div>
          <div className="subject-card-stats">
            <div className="stat-badge">
              <span className="stat-icon">📊</span>
              <span className="stat-text">Всего: {selectedSubject.stats?.total || 0}</span>
            </div>
            <div className="stat-badge">
              <span className="stat-icon">✅</span>
              <span className="stat-text">Оценок: {selectedSubject.stats?.grades || 0}</span>
            </div>
            <div className="stat-badge">
              <span className="stat-icon">❌</span>
              <span className="stat-text">Пропусков: {selectedSubject.stats?.absences || 0}</span>
            </div>
            <div className="stat-badge">
              <span className="stat-icon">📈</span>
              <span className="stat-text">Посещаемость: {selectedSubject.stats?.attendance || 0}%</span>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="calendar-loading">
          <div className="loading-spinner"></div>
          <p>Загрузка календаря...</p>
        </div>
      ) : selectedSubject && calendarData ? (
        <div className="calendar-content">
          <div className="calendar-legend">
            <div className="legend-item">
              <div className="legend-color excellent"></div>
              <span>Отлично (5)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color good"></div>
              <span>Хорошо (4)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color satisfactory"></div>
              <span>Удовлетворительно (3)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color bad"></div>
              <span>Неудовлетворительно (2)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color absence"></div>
              <span>Пропуск</span>
            </div>
          </div>
          {renderCalendar()}
        </div>
      ) : selectedSubject ? (
        <div className="calendar-placeholder">
          <p>📅 Загрузка данных календаря...</p>
        </div>
      ) : (
        <div className="calendar-placeholder">
          <div className="placeholder-icon">📚</div>
          <p>Выберите предмет для просмотра календаря оценок</p>
          <p className="placeholder-hint">Календарь покажет все ваши оценки и пропуски по выбранному предмету</p>
        </div>
      )}
    </div>
  )
}

function getGradeClass(value) {
  if (!value) return ''
  const val = value.toString().toLowerCase()
  if (val.includes('пропуск') || val === 'н' || val === 'н/я') return 'absence'
  const num = parseFloat(val)
  if (num >= 4.5) return 'excellent'
  if (num >= 3.5) return 'good'
  if (num >= 2.5) return 'satisfactory'
  if (num >= 2) return 'bad'
  return ''
}
