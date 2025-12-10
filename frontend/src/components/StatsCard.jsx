import './StatsCard.css'

export const StatsCard = ({ stat }) => {
  const getAttendanceColor = (attendance) => {
    if (attendance >= 80) return '#4caf50'
    if (attendance >= 50) return '#ffc107'
    return '#f44336'
  }

  return (
    <div className="stat-card">
      <div className="stat-name">{stat.fio}</div>
      <div className="stat-details">
        <div className="stat-item">
          <span className="stat-label">Всего:</span>
          <span className="stat-value">{stat.total}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Оценок:</span>
          <span className="stat-value grade">{stat.grades}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Пропусков:</span>
          <span className="stat-value absence">{stat.absences}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Посещаемость:</span>
          <span className="stat-value attendance">
            {stat.attendance}%
          </span>
        </div>
      </div>
    </div>
  )
}
