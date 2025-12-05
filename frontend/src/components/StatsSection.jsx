import { StatsCard } from './StatsCard'
import './StatsSection.css'

export const StatsSection = ({ stats }) => {
  if (!stats || stats.length === 0) {
    return null
  }

  return (
    <div className="stats-section">
      <h2 className="section-title">📊 Статистика посещаемости</h2>
      <div className="stats-grid">
        {stats.map((stat) => (
          <StatsCard key={stat.id} stat={stat} />
        ))}
      </div>
    </div>
  )
}
