export const getGradeColor = (grade) => {
  if (!grade) return '#e0e0e0'
  const gradeLower = String(grade).toLowerCase()
  
  if (gradeLower.includes('пропуск') || ['н', 'н/я', 'неявка'].includes(gradeLower)) {
    return '#ff5252'
  }
  
  const num = parseInt(grade)
  if (num === 5) return '#4caf50'
  if (num === 4) return '#8bc34a'
  if (num === 3) return '#ffc107'
  if (num === 2) return '#ff9800'
  if (num === 1) return '#f44336'
  
  return '#2196f3'
}

export const formatDate = (dateString) => {
  const date = new Date(dateString)
  // Форматируем дату с названием месяца: "15 янв" или "15 января"
  const day = date.getDate()
  const month = date.toLocaleDateString('ru-RU', { month: 'short' }) // "янв", "фев", и т.д.
  return `${day} ${month}`
}

// Функция для группировки дат по месяцам (для заголовков таблицы)
export const groupDatesByMonth = (dates) => {
  const grouped = {}
  dates.forEach(dateStr => {
    const date = new Date(dateStr)
    const monthKey = date.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long' })
    if (!grouped[monthKey]) {
      grouped[monthKey] = []
    }
    grouped[monthKey].push(dateStr)
  })
  return grouped
}
