import './SubjectsList.css'

export const SubjectsList = ({ subjects, student, onSubjectSelect, onShowCalendar }) => {
  return (
    <div className="subjects-container">
      <div className="subjects-scroll">
        <div className="subjects-horizontal">
          {subjects.map((subject) => (
            <div key={subject.id} className="subject-chip">
              {subject.name}
            </div>
          ))}
        </div>
      </div>

      <div className="subjects-grid">
        {subjects.map((subject) => (
          <div
            key={subject.id}
            className="subject-card"
            onClick={() => onSubjectSelect(subject)}
          >
            <div className="subject-card-header">
              <h3 className="subject-card-title">{subject.name}</h3>
            </div>
            <div className="subject-card-stats">
              <div className="stat-item">
                <span className="stat-label">Всего:</span>
                <span className="stat-value">{subject.stats.total}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Оценок:</span>
                <span className="stat-value grade">{subject.stats.grades}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Пропусков:</span>
                <span className="stat-value absence">{subject.stats.absences}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Посещаемость:</span>
                <span className="stat-value attendance">{subject.stats.attendance}%</span>
              </div>
            </div>
            <div className="subject-card-arrow">→</div>
          </div>
        ))}
      </div>

    </div>
  )
}
