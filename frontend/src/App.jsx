import { useState } from 'react'
import './App.css'
import { GradesTable } from './components/GradesTable'
import { Select } from './components/Select'
import { StatsSection } from './components/StatsSection'
import { useGrades } from './hooks/useGrades'
import { useGroups } from './hooks/useGroups'
import { useSubjects } from './hooks/useSubjects'

function App() {
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [selectedSubject, setSelectedSubject] = useState(null)

  const { groups, loading: groupsLoading } = useGroups()
  const { subjects } = useSubjects(selectedGroup)
  const { gradesData, stats, loading: gradesLoading } = useGrades(selectedGroup, selectedSubject)

  const handleGroupChange = (groupId) => {
    setSelectedGroup(groupId)
    setSelectedSubject(null)
  }

  return (
    <div className="app">
      <div className="container">
        <h1 className="title">📚 Журнал оценок</h1>

        <div className="controls">
          <Select
            label="Группа:"
            value={selectedGroup}
            onChange={handleGroupChange}
            options={groups}
            loading={groupsLoading}
            placeholder="Выберите группу"
          />

          {selectedGroup && (
            <Select
              label="Предмет:"
              value={selectedSubject}
              onChange={setSelectedSubject}
              options={subjects}
              disabled={!selectedGroup}
              placeholder="Выберите предмет"
            />
          )}
        </div>

        {gradesLoading && (
          <div className="loading">Загрузка...</div>
        )}

        <StatsSection stats={stats} />

        <GradesTable gradesData={gradesData} />

        {selectedGroup && selectedSubject && !gradesLoading && 
         (!gradesData || gradesData.dates?.length === 0) && (
          <div className="empty-state">
            <p>Нет данных для отображения</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
