import axios from 'axios'

// Определяем базовый URL API
// В dev режиме используем прокси из vite.config.js (/api -> http://localhost:5000)
// Можно также использовать прямой URL на порт 5000 через переменную окружения
const API_URL = import.meta.env.VITE_API_URL || '/api'

// Логируем для отладки
if (import.meta.env.DEV) {
  console.log('🔧 API URL:', API_URL)
  console.log('🔧 Прокси настроен на: http://localhost:5000')
}

// Кэш для токена
let cachedToken = null

// Функция для получения токена
async function getToken() {
  if (cachedToken) {
    console.log('🔑 Используем кэшированный токен')
    return cachedToken
  }

  try {
    console.log('🔑 Запрос токена с URL:', `${API_URL}/token`)
    const response = await axios.get(`${API_URL}/token`)
    cachedToken = response.data.token
    console.log('✅ Токен получен успешно')
    return cachedToken
  } catch (error) {
    console.error('❌ Ошибка получения токена:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: `${API_URL}/token`
    })
    throw new Error('Не удалось получить токен доступа')
  }
}

// Создаем экземпляр axios с перехватчиком запросов
const api = axios.create({
  baseURL: API_URL,
  timeout: 60000, // Увеличиваем таймаут до 60 секунд для тяжелых запросов
})

// Перехватчик для добавления токена к каждому запросу
api.interceptors.request.use(
  async (config) => {
    // Пропускаем запрос токена
    if (config.url === '/token') {
      console.log('🔑 Запрос токена:', config.url)
      return config
    }

    try {
      const token = await getToken()
      config.headers.Authorization = `Bearer ${token}`
      console.log('📤 Отправка запроса:', config.method?.toUpperCase(), config.url, 'параметры:', config.params)
    } catch (error) {
      console.error('❌ Ошибка при получении токена:', error)
    }
    return config
  },
  (error) => {
    console.error('❌ Ошибка в перехватчике запроса:', error)
    return Promise.reject(error)
  }
)

// Перехватчик для обработки ошибок авторизации
api.interceptors.response.use(
  (response) => {
    console.log('📥 Получен ответ:', response.status, response.config.url, 'данные:', response.data)
    return response
  },
  async (error) => {
    console.error('❌ Ошибка ответа:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })
    
    if (error.response?.status === 401) {
      // Токен невалиден, очищаем кэш и пробуем снова
      console.log('🔄 Токен невалиден, получаем новый...')
      cachedToken = null
      try {
        const token = await getToken()
        error.config.headers.Authorization = `Bearer ${token}`
        console.log('🔄 Повторная попытка запроса...')
        return api.request(error.config)
      } catch (e) {
        console.error('❌ Не удалось получить новый токен:', e)
        return Promise.reject(e)
      }
    }
    return Promise.reject(error)
  }
)

export const groupsApi = {
  getAll: () => api.get('/groups').then(res => res.data),
}

export const subjectsApi = {
  getByGroup: (groupId) => 
    api.get('/subjects', { params: { group_id: groupId } }).then(res => res.data),
}

export const studentsApi = {
  getByGroup: (groupId) => 
    api.get('/students', { params: { group_id: groupId } }).then(res => res.data),
}

export const gradesApi = {
  getByGroupAndSubject: (groupId, subjectId) =>
    api.get('/grades', { 
      params: { group_id: groupId, subject_id: subjectId } 
    }).then(res => res.data),
}

export const statsApi = {
  getByGroupAndSubject: (groupId, subjectId) =>
    api.get('/stats', { 
      params: { group_id: groupId, subject_id: subjectId } 
    }).then(res => res.data),
  
  getAbsencesRating: (groupId) =>
    api.get('/stats/rating/absences', { 
      params: { group_id: groupId } 
    }).then(res => res.data),
  
  getGradesRating: (groupId) =>
    api.get('/stats/rating/grades', { 
      params: { group_id: groupId } 
    }).then(res => res.data),
}

export const studentApi = {
  getByFio: (fio) =>
    api.get('/student/by-fio', { params: { fio } }).then(res => res.data),
  
  getSubjects: (fio) =>
    api.get('/student/subjects', { params: { fio } }).then(res => res.data),
  
  getGrades: (fio, subjectId) =>
    api.get('/student/grades', { 
      params: { fio, subject_id: subjectId } 
    }).then(res => res.data),
  
  getStats: (fio) =>
    api.get('/student/stats', { params: { fio } }).then(res => res.data),
  
  getSubjectsRatings: (fio) =>
    api.get('/student/subjects-ratings', { params: { fio } }).then(res => res.data),
  
  getFioByTelegramId: (initData) =>
    api.get('/student/fio-by-telegram-id', {
      headers: {
        'X-Telegram-Init-Data': initData
      }
    }).then(res => res.data),
  
  getByTelegram: (initData) =>
    api.get('/student/by-telegram', {
      headers: {
        'X-Telegram-Init-Data': initData
      }
    }).then(res => res.data),
}
