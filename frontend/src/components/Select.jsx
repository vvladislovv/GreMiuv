import './Select.css'

export const Select = ({ label, value, onChange, options = [], disabled, placeholder = 'Выберите...', loading }) => {
  return (
    <div className="select-group">
      {label && <label>{label}</label>}
      <select
        value={value || ''}
        onChange={(e) => onChange(Number(e.target.value))}
        className="select"
        disabled={disabled || loading}
      >
        <option value="">{loading ? 'Загрузка...' : placeholder}</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name || option.fio || option}
          </option>
        ))}
      </select>
    </div>
  )
}
