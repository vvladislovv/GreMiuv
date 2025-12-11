import { useEffect, useRef, useState } from 'react'
import './Debugger.css'

export const Debugger = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [logs, setLogs] = useState([])
  const [filter, setFilter] = useState('')
  const logsEndRef = useRef(null)

  // Перехватываем console.log, console.error, console.warn
  useEffect(() => {
    const originalLog = console.log
    const originalError = console.error
    const originalWarn = console.warn

    const addLog = (type, args) => {
      const message = args.map(arg => {
        if (typeof arg === 'object') {
          try {
            return JSON.stringify(arg, null, 2)
          } catch {
            return String(arg)
          }
        }
        return String(arg)
      }).join(' ')

      setLogs(prev => [...prev, {
        id: Date.now() + Math.random(),
        type,
        message,
        timestamp: new Date().toLocaleTimeString()
      }])
    }

    console.log = (...args) => {
      originalLog(...args)
      addLog('log', args)
    }

    console.error = (...args) => {
      originalError(...args)
      addLog('error', args)
    }

    console.warn = (...args) => {
      originalWarn(...args)
      addLog('warn', args)
    }

    return () => {
      console.log = originalLog
      console.error = originalError
      console.warn = originalWarn
    }
  }, [])

  // Автопрокрутка к последнему логу
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const filteredLogs = logs.filter(log => 
    log.message.toLowerCase().includes(filter.toLowerCase()) ||
    log.type.toLowerCase().includes(filter.toLowerCase())
  )

  const clearLogs = () => {
    setLogs([])
  }

  if (!isOpen) {
    return (
      <button
        className="debugger-toggle"
        onClick={() => setIsOpen(true)}
        title="Открыть консоль отладки"
      >
        🐛
      </button>
    )
  }

  return (
    <div className="debugger-panel">
      <div className="debugger-header">
        <h3>🐛 Консоль отладки</h3>
        <div className="debugger-controls">
          <input
            type="text"
            placeholder="Фильтр..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="debugger-filter"
          />
          <button onClick={clearLogs} className="debugger-clear">
            Очистить
          </button>
          <button onClick={() => setIsOpen(false)} className="debugger-close">
            ✕
          </button>
        </div>
      </div>
      <div className="debugger-content">
        {filteredLogs.length === 0 ? (
          <div className="debugger-empty">Нет логов</div>
        ) : (
          <div className="debugger-logs">
            {filteredLogs.map(log => (
              <div key={log.id} className={`debugger-log debugger-log-${log.type}`}>
                <span className="debugger-timestamp">{log.timestamp}</span>
                <span className="debugger-type">{log.type.toUpperCase()}</span>
                <pre className="debugger-message">{log.message}</pre>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
      <div className="debugger-footer">
        <span>Всего логов: {logs.length}</span>
        {filter && <span>Отфильтровано: {filteredLogs.length}</span>}
      </div>
    </div>
  )
}
