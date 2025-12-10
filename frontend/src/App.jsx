import { useEffect, useState } from 'react'
import './App.css'
import { BottomNavigation } from './components/BottomNavigation'
import { Calendar } from './components/Calendar'
import { Header } from './components/Header'
import { Rating } from './components/Rating'
import { SubjectDetail } from './components/SubjectDetail'
import { SubjectRatings } from './components/SubjectRatings'
import { SubjectsList } from './components/SubjectsList'
import { useStudentData } from './hooks/useStudentData'
import { studentApi } from './services/api'

function App() {
  const [selectedSubject, setSelectedSubject] = useState(null)
  const [currentView, setCurrentView] = useState('subjects') // 'subjects' | 'subject' | 'calendar'
  
  // Проверяем, что приложение запущено в Telegram Mini App
  const isTelegramWebApp = window.Telegram?.WebApp !== undefined
  
  // Инициализируем ФИО сразу с тестовым значением для быстрого старта
  const getInitialFio = () => {
    // 1. Проверяем startParam
    if (isTelegramWebApp) {
      const startParam = window.Telegram?.WebApp?.startParam
      if (startParam && startParam.trim() !== '') {
        try {
          return decodeURIComponent(startParam.trim())
        } catch (e) {
          return startParam.trim()
        }
      }
    }
    
    // 2. Проверяем URL параметры
    const urlParams = new URLSearchParams(window.location.search)
    const fioFromUrl = urlParams.get('fio')
    if (fioFromUrl) return fioFromUrl
    
    // 3. Проверяем localStorage
    try {
      const fioFromStorage = localStorage.getItem('student_fio')
      if (fioFromStorage) return fioFromStorage
    } catch (e) {
      // Игнорируем ошибки localStorage
    }
    
    // 4. Используем тестовое ФИО по умолчанию
    return localStorage.getItem('test_fio') || 'Ельченинов В.А.'
  }
  
  const [fioFromUrl, setFioFromUrl] = useState(getInitialFio())
  
  // Обновляем ФИО из initData асинхронно (если нужно)
  useEffect(() => {
    const updateFioFromInitData = async () => {
      // Если уже есть ФИО из startParam или URL, не обновляем
      if (fioFromUrl && fioFromUrl !== 'Ельченинов В.А.') {
        return
      }
      
      const initData = window.Telegram?.WebApp?.initData || ''
      
      // Если есть initData, пробуем получить ФИО из базы данных
      if (isTelegramWebApp && initData && initData.trim() !== '') {
        console.log('🔍 Пробуем получить ФИО из базы данных через initData...')
        try {
          const response = await studentApi.getFioByTelegramId(initData)
          if (response?.fio) {
            console.log('✅ ФИО получено из базы данных:', response.fio)
            setFioFromUrl(response.fio)
            try {
              localStorage.setItem('student_fio', response.fio)
            } catch (e) {
              console.warn('⚠️ Не удалось сохранить ФИО:', e)
            }
          }
        } catch (e) {
          console.warn('⚠️ Ошибка при получении ФИО из базы данных:', e)
        }
      }
    }
    
    updateFioFromInitData()
  }, [isTelegramWebApp, fioFromUrl])
  
  // Сохраняем текущее ФИО в localStorage
  useEffect(() => {
    if (fioFromUrl) {
      try {
        localStorage.setItem('student_fio', fioFromUrl)
        localStorage.setItem('test_fio', fioFromUrl)
      } catch (e) {
        console.warn('⚠️ Не удалось сохранить ФИО:', e)
      }
    }
  }, [fioFromUrl])
  
  // Получаем initData от Telegram
  const initData = window.Telegram?.WebApp?.initData || ''
  
  // Логируем информацию о Telegram Mini App
  if (isTelegramWebApp) {
    console.log('✅ Запущено в Telegram Mini App')
    console.log('Telegram WebApp версия:', window.Telegram?.WebApp?.version)
    console.log('InitData доступен:', !!initData)
  } else {
    console.log('⚠️ Запущено вне Telegram Mini App (режим разработки)')
  }
  
  const { student, subjects, loading, error } = useStudentData(fioFromUrl, initData)
  
  // Логируем состояние для отладки
  useEffect(() => {
    console.log('📊 App состояние:', {
      fioFromUrl,
      loading,
      hasStudent: !!student,
      subjectsCount: subjects?.length,
      error
    })
  }, [fioFromUrl, loading, student, subjects, error])
  
  // Используем loading напрямую, без дополнительных проверок
  const isLoading = loading
  
  // Используем error напрямую
  const finalError = error

  const handleSubjectSelect = (subject) => {
    setSelectedSubject(subject)
    setCurrentView('subject')
  }

  const handleBackToSubjects = () => {
    setSelectedSubject(null)
    setCurrentView('subjects')
  }

  const handleShowCalendar = () => {
    setCurrentView('calendar')
  }

  const handleNavigate = (view) => {
    setCurrentView(view)
    if (view === 'subjects') {
      setSelectedSubject(null)
    }
  }

  // Не показываем спиннер загрузки - сразу показываем контент
  // if (isLoading && !fioFromUrl) {
  //   return (
  //     <div className="app">
  //       <div className="loading-container">
  //         <div className="loading-spinner"></div>
  //         <p>Загрузка данных...</p>
  //       </div>
  //     </div>
  //   )
  // }

  if (finalError) {
    // Разбиваем сообщение об ошибке на строки для лучшего отображения
    const errorLines = finalError.split('\n').filter(line => line.trim())
    const mainError = errorLines[0] || finalError
    const additionalInfo = errorLines.slice(1)
    
    // Специальное сообщение для случая, когда ФИО не указано
    const isMissingFio = !fioFromUrl || finalError === 'ФИО не указано'
    
    return (
      <div className="app">
        <div className="error-container">
          <div className="error-content">
            <h2>❌ Ошибка</h2>
            {isMissingFio ? (
              <div className="error-message">
                <p className="error-main">
                  ФИО не указано в параметрах URL
                </p>
                <div className="error-details">
                  <div className="error-line">
                    Для работы приложения необходимо открыть его через кнопку бота после регистрации.
                  </div>
                  <div className="error-line">
                    Убедитесь, что вы:
                  </div>
                  <div className="error-line">  • Зарегистрированы в боте командой /start</div>
                  <div className="error-line">  • Указали правильное ФИО при регистрации</div>
                  <div className="error-line">  • Открыли приложение через кнопку "📓 Журнал" в боте</div>
                </div>
              </div>
            ) : (
              <>
                <div className="error-message">
                  <p className="error-main">{mainError}</p>
                  {additionalInfo.length > 0 && (
                    <div className="error-details">
                      {additionalInfo.map((line, index) => (
                        <div key={index} className="error-line">
                          {line.trim().startsWith('•') ? (
                            <span className="error-bullet">{line}</span>
                          ) : (
                            <span>{line}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="error-help">
                  <p>Возможные причины:</p>
                  <ul>
                    <li>Студент с таким ФИО не найден в базе данных</li>
                    <li>ФИО указано неверно (проверьте написание)</li>
                    <li>Данные еще не загружены в систему</li>
                  </ul>
                  <p className="error-note">
                    {isTelegramWebApp 
                      ? 'Если вы используете Telegram бота, убедитесь, что вы зарегистрированы с правильным ФИО и открыли приложение через кнопку бота.'
                      : 'Если вы используете Telegram бота, убедитесь, что вы зарегистрированы с правильным ФИО.'}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!student) {
    return (
      <div className="app">
        <div className="error-container">
          <p>❌ Студент не найден. Проверьте параметры доступа.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <Header 
        student={student} 
        onBack={currentView !== 'subjects' && currentView !== 'rating' && currentView !== 'subject-ratings' && currentView !== 'profile' ? handleBackToSubjects : null}
      />
      
      <div className="app-content" style={{ paddingBottom: '80px' }}>
        {currentView === 'subjects' && (
          <SubjectsList 
            subjects={subjects}
            student={student}
            onSubjectSelect={handleSubjectSelect}
            onShowCalendar={handleShowCalendar}
          />
        )}
        
        {currentView === 'subject' && selectedSubject && (
          <SubjectDetail 
            subject={selectedSubject}
            student={student}
            onBack={handleBackToSubjects}
          />
        )}
        
        {currentView === 'calendar' && (
          <Calendar 
            student={student}
            subjects={subjects}
            onBack={handleBackToSubjects}
          />
        )}
        
        {currentView === 'rating' && (
          <Rating student={student} />
        )}
        
        {currentView === 'subject-ratings' && (
          <SubjectRatings student={student} />
        )}
        
        {currentView === 'profile' && (
          <div className="profile-view">
            <div className="profile-header">
              <h2 className="profile-title">Профиль</h2>
            </div>
            {student && (
              <div className="profile-content">
                <div className="profile-avatar-section">
                  <div className="profile-avatar">
                    {student.fio ? student.fio.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : '👤'}
                  </div>
                  <div className="profile-main-info">
                    <h3 className="profile-name">{student.fio}</h3>
                    {student.group_name && (
                      <p className="profile-group">Группа: {student.group_name}</p>
                    )}
                  </div>
                </div>
                {student.stats && (
                  <div className="profile-stats-grid">
                    <div className="profile-stat-card">
                      <div className="stat-card-icon">📚</div>
                      <div className="stat-card-content">
                        <div className="stat-card-value">{student.stats.total_subjects}</div>
                        <div className="stat-card-label">Предметов</div>
                      </div>
                    </div>
                    <div className="profile-stat-card">
                      <div className="stat-card-icon">📝</div>
                      <div className="stat-card-content">
                        <div className="stat-card-value">{student.stats.total_lessons}</div>
                        <div className="stat-card-label">Занятий</div>
                      </div>
                    </div>
                    <div className="profile-stat-card">
                      <div className="stat-card-icon">⭐</div>
                      <div className="stat-card-content">
                        <div className="stat-card-value">{student.stats.average_grade ? student.stats.average_grade.toFixed(2) : 'Н/Д'}</div>
                        <div className="stat-card-label">Средний балл</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
      
      <BottomNavigation 
        currentView={currentView === 'subject' ? 'subjects' : currentView}
        onNavigate={handleNavigate}
      />
    </div>
  )
}

export default App
