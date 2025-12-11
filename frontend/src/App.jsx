import { lazy, Suspense, useEffect, useState } from 'react'
import './App.css'
import { BottomNavigation } from './components/BottomNavigation'
import { Header } from './components/Header'
import { NotFound } from './components/NotFound'
import { preloadRating } from './components/Rating'
import { StudentNotFound } from './components/StudentNotFound'
import { SubjectDetail } from './components/SubjectDetail'
import { SubjectsList } from './components/SubjectsList'
import { useStudentData } from './hooks/useStudentData'
import { studentApi } from './services/api'

// Lazy loading для оптимизации загрузки вкладок
const Rating = lazy(() => import('./components/Rating').then(module => ({ default: module.Rating })))
const Calendar = lazy(() => import('./components/Calendar'))

function App() {
  const [selectedSubject, setSelectedSubject] = useState(null)
  const [currentView, setCurrentView] = useState('subjects') // 'subjects' | 'subject' | 'calendar'
  
  // Проверяем, что приложение запущено в Telegram Mini App
  const isTelegramWebApp = window.Telegram?.WebApp !== undefined
  
  // Получаем initData от Telegram
  const getInitData = () => {
    const tg = window.Telegram?.WebApp
    if (!tg) return ''
    
    // Пробуем получить initData напрямую
    if (tg.initData && tg.initData.trim() !== '') {
      return tg.initData
    }
    
    return ''
  }
  
  const initData = getInitData()
  
  // Очищаем ВСЕ старые тестовые данные из localStorage при первом запуске
  useEffect(() => {
    try {
      // Очищаем все старые тестовые данные
      const testFio = localStorage.getItem('test_fio')
      const studentFio = localStorage.getItem('student_fio')
      
      if (testFio === 'Ельченинов В.А.') {
        localStorage.removeItem('test_fio')
        console.log('🧹 Удален test_fio из localStorage')
      }
      
      if (studentFio === 'Ельченинов В.А.') {
        localStorage.removeItem('student_fio')
        console.log('🧹 Удален student_fio из localStorage')
      }
      
      // Если есть старые данные и мы в Telegram, очищаем их
      if (isTelegramWebApp && (testFio === 'Ельченинов В.А.' || studentFio === 'Ельченинов В.А.')) {
        console.log('🧹 Очищены все тестовые данные из localStorage')
      }
    } catch (e) {
      console.warn('⚠️ Не удалось очистить localStorage:', e)
    }
  }, [isTelegramWebApp])
  
  // Инициализируем ФИО - только из Telegram (startParam или initData)
  const getInitialFio = () => {
    // 1. Проверяем startParam (если есть)
    if (isTelegramWebApp) {
      const startParam = window.Telegram?.WebApp?.startParam
      if (startParam && startParam.trim() !== '') {
        try {
          const decoded = decodeURIComponent(startParam.trim())
          console.log('✅ ФИО из startParam:', decoded)
          return decoded
        } catch (e) {
          console.log('✅ ФИО из startParam (без декодирования):', startParam.trim())
          return startParam.trim()
        }
      }
    }
    
    // 2. Если нет startParam - возвращаем null (будет загружено из initData)
    return null
  }
  
  const [fioFromUrl, setFioFromUrl] = useState(getInitialFio())
  
  // Загружаем ФИО из Telegram через initData
  useEffect(() => {
    const loadFioFromTelegram = async () => {
      // Если уже есть ФИО из startParam, не загружаем
      if (fioFromUrl) {
        return
      }
      
      // Если нет initData, не можем загрузить
      if (!isTelegramWebApp || !initData || initData.trim() === '') {
        console.log('⚠️ Нет initData, не можем загрузить данные из Telegram')
        return
      }
      
      console.log('🔍 Загружаем данные из Telegram через initData...')
      try {
        const response = await studentApi.getByTelegram(initData)
        if (response?.fio) {
          console.log('✅ ФИО получено из Telegram:', response.fio)
          setFioFromUrl(response.fio)
        } else {
          console.log('⚠️ ФИО не найдено в базе данных для этого пользователя Telegram')
        }
      } catch (e) {
        console.error('❌ Ошибка при получении данных из Telegram:', e)
      }
    }
    
    loadFioFromTelegram()
  }, [isTelegramWebApp, initData, fioFromUrl])
  
  // Логируем информацию о Telegram Mini App
  if (isTelegramWebApp) {
    console.log('✅ Запущено в Telegram Mini App')
    console.log('Telegram WebApp версия:', window.Telegram?.WebApp?.version)
    console.log('InitData доступен:', !!initData)
  } else {
    console.log('⚠️ Запущено вне Telegram Mini App (режим разработки)')
  }
  
  const { student, subjects, loading, error } = useStudentData(fioFromUrl, initData)
  
  // Предзагрузка рейтинга при получении данных студента (для оптимизации)
  useEffect(() => {
    if (student?.group_id && currentView === 'subjects') {
      // Предзагружаем рейтинг в фоне, когда студент загружен
      preloadRating(student.group_id).catch(err => {
        console.warn('⚠️ Не удалось предзагрузить рейтинг:', err)
      })
    }
  }, [student?.group_id, currentView])
  
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
    console.log('🔄 Навигация:', { from: currentView, to: view, hasStudent: !!student, hasSubjects: !!subjects })
    setCurrentView(view)
    if (view === 'subjects') {
      setSelectedSubject(null)
    }
    // Логируем состояние после навигации
    setTimeout(() => {
      console.log('✅ Навигация завершена:', { currentView: view })
    }, 0)
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

  // Если нет initData и нет startParam - показываем ошибку
  if (isTelegramWebApp && !initData && !fioFromUrl && !loading) {
    return (
      <div className="app">
        <StudentNotFound 
          error="Не удалось получить данные из Telegram. Пожалуйста, откройте приложение через кнопку '📓 Журнал' в боте."
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  if (finalError) {
    // Разбиваем сообщение об ошибке на строки для лучшего отображения
    const errorLines = finalError.split('\n').filter(line => line.trim())
    const mainError = errorLines[0] || finalError
    
    return (
      <div className="app">
        <StudentNotFound 
          error={mainError}
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  if (!student && !loading && !fioFromUrl) {
    return (
      <div className="app">
        <StudentNotFound 
          error="Не удалось загрузить данные. Пожалуйста, убедитесь, что вы зарегистрированы в боте и открыли приложение через кнопку '📓 Журнал'."
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  if (!student && !loading && fioFromUrl) {
    return (
      <div className="app">
        <StudentNotFound 
          error="Студент не найден. Проверьте параметры доступа."
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  return (
    <div className="app">
      <Header 
        student={student} 
        onBack={currentView !== 'subjects' && currentView !== 'rating' && currentView !== 'profile' ? handleBackToSubjects : null}
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
        
        {currentView === 'subject' && !selectedSubject && (
          <NotFound 
            message="Предмет не выбран"
            onBack={handleBackToSubjects}
          />
        )}
        
        {currentView === 'calendar' && (
          <Suspense fallback={
            <div className="calendar-container">
              <div className="loading-spinner"></div>
              <p>Загрузка календаря...</p>
            </div>
          }>
            {student && subjects ? (
              <Calendar 
                student={student}
                subjects={subjects}
                onBack={handleBackToSubjects}
              />
            ) : (
              <div className="calendar-container">
                <div className="calendar-placeholder">
                  <div className="placeholder-icon">📚</div>
                  <p>Загрузка данных...</p>
                </div>
              </div>
            )}
          </Suspense>
        )}
        
        {currentView === 'rating' && (
          <Suspense fallback={
            <div className="rating-container">
              <div className="loading-spinner-small"></div>
              <p className="loading-text">Загрузка рейтинга...</p>
            </div>
          }>
            <Rating student={student} />
          </Suspense>
        )}
        
        {currentView === 'profile' && (
          <div className="profile-view">
            <div className="profile-header">
              <h2 className="profile-title">Профиль</h2>
            </div>
            {student && (
              <div className="profile-content">
                <div className="profile-avatar-section">
                  <div className="profile-avatar" style={{
                    backgroundImage: student.telegram?.photo_url ? `url(${student.telegram.photo_url})` : 'none',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}>
                    {!student.telegram?.photo_url && (
                      student.fio ? student.fio.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : '👤'
                    )}
                  </div>
                  <div className="profile-main-info">
                    <h3 className="profile-name">{student.fio}</h3>
                    {student.group_name && (
                      <p className="profile-group">Группа: {student.group_name}</p>
                    )}
                    {student.telegram?.username && (
                      <p className="profile-group" style={{ marginTop: '4px', fontSize: '14px', opacity: 0.8 }}>
                        @{student.telegram.username}
                      </p>
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
        
        {!['subjects', 'subject', 'calendar', 'rating', 'profile'].includes(currentView) && (
          <NotFound 
            message="Страница не найдена"
            onBack={handleBackToSubjects}
          />
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
