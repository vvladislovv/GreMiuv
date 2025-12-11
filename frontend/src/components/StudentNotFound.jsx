import './StudentNotFound.css'

export const StudentNotFound = ({ error, onRetry = null }) => {
  return (
    <div className="student-not-found-container">
      <div className="student-not-found-content">
        <div className="student-not-found-icon">👤</div>
        <h1 className="student-not-found-title">Студент не найден</h1>
        <p className="student-not-found-description">
          Не удалось найти данные студента в системе.
        </p>
        
        {error && (
          <div className="student-not-found-error">
            <p className="error-text">{error}</p>
          </div>
        )}
        
        <div className="student-not-found-help">
          <h3>Что можно сделать:</h3>
          <ul>
            <li>Проверьте правильность введённого ФИО</li>
            <li>Убедитесь, что вы зарегистрированы в системе</li>
            <li>Попробуйте обновить страницу</li>
            {onRetry && (
              <li>
                <button className="retry-button" onClick={onRetry}>
                  Попробовать снова
                </button>
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}
