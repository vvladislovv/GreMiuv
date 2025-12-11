import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Инициализация Eruda для отладки на мобильных устройствах
if (import.meta.env.DEV || window.location.search.includes('eruda=true')) {
  import('eruda').then((eruda) => {
    eruda.default.init()
    console.log('🐛 Eruda инициализирован для отладки')
  }).catch((err) => {
    console.warn('⚠️ Не удалось загрузить Eruda:', err)
  })
}

// Инициализация Telegram WebApp
if (window.Telegram?.WebApp) {
  const tg = window.Telegram.WebApp
  
  // Проверяем версию WebApp
  const version = parseFloat(tg.version || '6.0')
  
  console.log('Telegram WebApp инициализирован, версия:', version)
  
  // Базовые настройки
  tg.ready()
  tg.expand()
  
  // Настраиваем цвета только для версий, которые поддерживают это
  // Версия 6.0+ не поддерживает setHeaderColor и setBackgroundColor
  if (version < 6.0) {
    try {
      tg.setHeaderColor('#ff6b35')
      tg.setBackgroundColor('#f5f5f5')
    } catch (e) {
      console.warn('Не удалось установить цвета:', e)
    }
  } else {
    // Для версии 6.0+ используем новые методы
    try {
      // Используем setHeaderColor только если метод доступен
      if (typeof tg.setHeaderColor === 'function') {
        tg.setHeaderColor('#ff6b35')
      }
      if (typeof tg.setBackgroundColor === 'function') {
        tg.setBackgroundColor('#f5f5f5')
      }
    } catch (e) {
      // Игнорируем ошибки для версий, которые не поддерживают эти методы
      console.log('Цвета не поддерживаются в этой версии WebApp')
    }
  }
  
  // Включаем вибрацию при необходимости
  try {
    tg.enableClosingConfirmation()
  } catch (e) {
    // Игнорируем ошибки для версий, которые не поддерживают этот метод
    console.log('Closing confirmation не поддерживается в этой версии WebApp')
  }
  
  // Логируем startParam для отладки
  console.log('🔍 Полная информация о Telegram WebApp:')
  console.log('  - startParam:', tg.startParam, '(тип:', typeof tg.startParam, ')')
  console.log('  - initData:', tg.initData ? 'доступен' : 'не доступен')
  console.log('  - initDataUnsafe:', tg.initDataUnsafe)
  console.log('  - version:', tg.version)
  
  if (tg.startParam) {
    try {
      const decoded = decodeURIComponent(tg.startParam)
      console.log('✅ startParam (декодирован):', decoded)
    } catch (e) {
      console.warn('⚠️ Ошибка декодирования startParam:', e)
      console.log('📋 startParam (как есть):', tg.startParam)
    }
  } else {
    console.log('⚠️ startParam не найден или пустой')
  }
  
  // Очищаем старые тестовые данные из localStorage
  try {
    const oldTestFio = localStorage.getItem('test_fio')
    const oldStudentFio = localStorage.getItem('student_fio')
    if (oldTestFio === 'Ельченинов В.А.' || oldStudentFio === 'Ельченинов В.А.') {
      localStorage.removeItem('test_fio')
      localStorage.removeItem('student_fio')
      console.log('🧹 Удалены тестовые данные из localStorage')
    }
  } catch (e) {
    // Игнорируем ошибки
  }
  
  console.log('✅ Telegram WebApp готов к работе')
} else {
  console.log('⚠️ Telegram WebApp не обнаружен - режим разработки')
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
