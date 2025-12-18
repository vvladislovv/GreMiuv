import './NotFound.css'

export const NotFound = ({ message = 'Страница не найдена', onBack = null }) => {
  return (
    <div className="not-found-container">
      <div className="not-found-content">
        <div className="not-found-icon">🔍</div>
        <h1 className="not-found-title">404</h1>
        <h2 className="not-found-subtitle">{message}</h2>
        <p className="not-found-description">
          К сожалению, запрашиваемая страница не существует или была перемещена.
        </p>
        {onBack && (
          <button className="not-found-button" onClick={onBack}>
            Вернуться назад
          </button>
        )}
      </div>
    </div>
  )
}



