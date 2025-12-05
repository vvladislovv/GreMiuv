import { formatDate, getGradeColor } from '../utils/gradeColors'
import './GradesTable.css'

export const GradesTable = ({ gradesData }) => {
  if (!gradesData || !gradesData.dates || gradesData.dates.length === 0) {
    return null
  }

  return (
    <div className="table-section">
      <h2 className="section-title">📋 Оценки по дням</h2>
      <div className="table-wrapper">
        <table className="grades-table">
          <thead>
            <tr>
              <th className="student-col">Студент</th>
              {gradesData.dates.map((date) => (
                <th key={date} className="date-col">
                  {formatDate(date)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {gradesData.students.map((student) => (
              <tr key={student.id}>
                <td className="student-name">{student.fio}</td>
                {gradesData.dates.map((date) => {
                  const grade = student.grades[date]
                  return (
                    <td
                      key={date}
                      className="grade-cell"
                      style={{
                        backgroundColor: getGradeColor(grade),
                        color: '#fff',
                      }}
                    >
                      {grade || '-'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
