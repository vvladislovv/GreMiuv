import axios from 'axios'

const API_URL = '/api'

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
})

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
}
