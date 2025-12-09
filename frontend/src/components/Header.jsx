import './Header.css'

export const Header = ({ student, onBack }) => {
  return (
    <div className="header">
      {onBack && (
        <button className="back-button" onClick={onBack}>
          ←
        </button>
      )}
      <div className="header-content">
        <h1 className="header-title">Мои предметы</h1>
        {student?.group_name && (
          <div className="header-group">Группа: {student.group_name}</div>
        )}
        <div className="header-stats">
          <div className="stat-badge">
            {student?.stats?.total_subjects || 0} Предметов
          </div>
          <div className="stat-badge">
            {student?.stats?.total_lessons || 0} Занятий
          </div>
        </div>
      </div>
      <div className="header-decoration">
        <div className="decoration-icon">🎓</div>
        <div className="decoration-stars">
          <span>⭐</span>
          <span>⭐</span>
          <span>⭐</span>
        </div>
      </div>
    </div>
  )
}
