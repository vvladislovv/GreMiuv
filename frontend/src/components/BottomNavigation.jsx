import './BottomNavigation.css'

export const BottomNavigation = ({ currentView, onNavigate }) => {
  const tabs = [
    { id: 'subjects', label: 'Главная', icon: '🏠', emoji: '🏠' },
    { id: 'rating', label: 'Рейтинг', icon: '📊', emoji: '📊' },
    { id: 'calendar', label: 'Календарь', icon: '📅', emoji: '📅' },
    { id: 'profile', label: 'Профиль', icon: '👤', emoji: '👤' }
  ]

  return (
    <nav className="bottom-navigation">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`nav-tab ${currentView === tab.id ? 'active' : ''}`}
          onClick={() => onNavigate(tab.id)}
        >
          <div className="nav-icon">{tab.emoji}</div>
          <span className="nav-label">{tab.label}</span>
          {currentView === tab.id && <div className="nav-indicator"></div>}
        </button>
      ))}
    </nav>
  )
}


