import './SubjectsList.css'

export const SubjectsList = ({ subjects, student, onSubjectSelect, onShowCalendar }) => {
  // Проверяем, является ли предмет пустым (нет данных вообще)
  const isSubjectEmpty = (subject) => {
    const stats = subject.stats || {}
    return (
      (stats.total === 0 || !stats.total) &&
      (stats.grades === 0 || !stats.grades) &&
      (stats.absences === 0 || !stats.absences) &&
      (stats.attendance === 0 || !stats.attendance)
    )
  }

  // Получаем цвет и смайл для предмета в зависимости от названия
  const getSubjectStyle = (subjectName) => {
    const name = subjectName.toLowerCase()
    
    // Определяем цвет на основе названия предмета
    let gradient = 'linear-gradient(135deg, #2c2c2c 0%, #3a3a3a 100%)'
    let emoji = '📚'
    
    if (name.includes('математик') || name.includes('алгебр') || name.includes('геометр')) {
      gradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      emoji = '🔢'
    } else if (name.includes('физик') || name.includes('хими')) {
      gradient = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
      emoji = '⚗️'
    } else if (name.includes('информатик') || name.includes('программир') || name.includes('технология разработки')) {
      gradient = 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
      emoji = '💻'
    } else if (name.includes('иностранн') || name.includes('английск') || name.includes('немецк')) {
      gradient = 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
      emoji = '🌍'
    } else if (name.includes('истори') || name.includes('обществ')) {
      gradient = 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
      emoji = '📜'
    } else if (name.includes('литератур') || name.includes('русск')) {
      gradient = 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
      emoji = '📖'
    } else if (name.includes('экономик') || name.includes('менеджмент')) {
      gradient = 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)'
      emoji = '💰'
    } else if (name.includes('философи') || name.includes('огсэ')) {
      gradient = 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)'
      emoji = '🤔'
    } else if (name.includes('мдк') || name.includes('инструментальн')) {
      gradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      emoji = '🔧'
    } else if (name.includes('численн') || name.includes('метод')) {
      gradient = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
      emoji = '📊'
    } else {
      // Для остальных - чередуем цвета
      const colors = [
        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
      ]
      const index = subjectName.length % colors.length
      gradient = colors[index]
    }
    
    return { gradient, emoji }
  }

  return (
    <div className="subjects-container">
      <div className="subjects-grid">
        {subjects.map((subject, index) => {
          const isEmpty = isSubjectEmpty(subject)
          const { gradient, emoji } = getSubjectStyle(subject.name)
          
          // Определяем цвет фона на основе итоговой оценки (если есть)
          let cardBackground = gradient
          if (subject.final_grade && !isEmpty) {
            const grade = subject.final_grade
            if (grade >= 4.5) {
              cardBackground = 'linear-gradient(135deg, #4caf50 0%, #66bb6a 100%)' // Зеленый - отлично
            } else if (grade >= 3.5) {
              cardBackground = 'linear-gradient(135deg, #2196f3 0%, #42a5f5 100%)' // Синий - хорошо
            } else if (grade >= 2.5) {
              cardBackground = 'linear-gradient(135deg, #ffc107 0%, #ffca28 100%)' // Желтый - удовлетворительно
            } else {
              cardBackground = 'linear-gradient(135deg, #f44336 0%, #ef5350 100%)' // Красный - неудовлетворительно
            }
          }
          
          return (
            <div
              key={subject.id}
              className={`subject-card ${isEmpty ? 'disabled' : ''} ${subject.final_grade ? 'has-final-grade' : ''}`}
              onClick={isEmpty ? undefined : () => onSubjectSelect(subject)}
              style={!isEmpty ? { background: cardBackground } : {}}
            >
              <div className="subject-card-header">
                <h3 className="subject-card-title">
                  <span className="subject-emoji">{emoji}</span>
                  {subject.name}
                </h3>
              </div>
              <div className="subject-card-stats">
                <div className="stat-item">
                  <span className="stat-label">Всего:</span>
                  <span className="stat-value">{subject.stats?.total || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Оценок:</span>
                  <span className="stat-value grade">{subject.stats?.grades || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Пропусков:</span>
                  <span className="stat-value absence">{subject.stats?.absences || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Посещаемость:</span>
                  <span className="stat-value attendance">{subject.stats?.attendance || 0}%</span>
                </div>
              </div>
              {!isEmpty && <div className="subject-card-arrow">→</div>}
              {isEmpty && <div className="subject-card-locked">🔒</div>}
            </div>
          )
        })}
      </div>

    </div>
  )
}
