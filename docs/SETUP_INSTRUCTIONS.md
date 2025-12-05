# Инструкция по настройке Google Drive API

## Быстрая настройка (Service Account - рекомендуется)

Этот способ полностью автоматический, браузер не открывается.

### Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на https://console.cloud.google.com/
2. Войдите в свой Google аккаунт
3. Нажмите на выпадающий список проектов вверху
4. Нажмите "Новый проект"
5. Введите название проекта (например, "Excel Parser")
6. Нажмите "Создать"

### Шаг 2: Включение Google Drive API

1. В меню слева выберите "APIs & Services" > "Library"
2. В поиске введите "Google Drive API"
3. Нажмите на "Google Drive API"
4. Нажмите кнопку "Enable" (Включить)

### Шаг 3: Создание Service Account

1. В меню слева выберите "IAM & Admin" > "Service Accounts"
2. Нажмите "Create Service Account" (Создать сервисный аккаунт)
3. Заполните:
   - Service account name: `excel-parser` (или любое другое имя)
   - Service account ID: автоматически заполнится
4. Нажмите "Create and Continue"
5. В разделе "Grant this service account access to project" выберите роль "Editor" (или "Viewer" если нужен только просмотр)
6. Нажмите "Continue", затем "Done"

### Шаг 4: Создание ключа

1. Найдите созданный Service Account в списке
2. Нажмите на email адрес Service Account
3. Перейдите на вкладку "Keys"
4. Нажмите "Add Key" > "Create new key"
5. Выберите "JSON"
6. Нажмите "Create"
7. Файл автоматически скачается

### Шаг 5: Сохранение ключа

1. Переименуйте скачанный JSON файл в `service_account.json`
2. Переместите его в папку проекта `/Users/evochka/Documents/GreMuiv/`

### Шаг 6: Предоставление доступа к папке Google Drive

1. Откройте скачанный `service_account.json`
2. Найдите поле `"client_email"` - это email адрес Service Account (например, `excel-parser@project-id.iam.gserviceaccount.com`)
3. Откройте папку Google Drive: https://drive.google.com/drive/folders/1Vte1-RAsucB6WLRiQRAUN1Yq37k7GpQb
4. Нажмите правой кнопкой мыши на папку > "Поделиться" (Share)
5. Вставьте email адрес из `client_email`
6. Дайте права "Читатель" (Viewer)
7. Нажмите "Отправить"

### Готово!

Теперь приложение будет работать автоматически без открытия браузера.

---

## Альтернативный способ (OAuth 2.0)

Если по какой-то причине не хотите использовать Service Account:

### Шаг 1-2: То же самое (создание проекта и включение API)

### Шаг 3: Создание OAuth 2.0 credentials

1. В меню слева выберите "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "OAuth client ID"
3. Если появится запрос на настройку экрана согласия:
   - User Type: External
   - App name: Excel Parser
   - User support email: ваш email
   - Developer contact: ваш email
   - Нажмите "Save and Continue"
   - Scopes: оставьте по умолчанию, нажмите "Save and Continue"
   - Test users: добавьте свой email, нажмите "Save and Continue"
4. Application type: выберите "Desktop app"
5. Name: Excel Parser (или любое другое)
6. Нажмите "Create"
7. Нажмите "Download JSON"
8. Переименуйте файл в `credentials.json` и поместите в папку проекта

### Шаг 4: Первый запуск

1. Запустите приложение: `python main.py`
2. Откроется браузер для авторизации
3. Войдите в свой Google аккаунт
4. Разрешите доступ приложению
5. После этого будет создан файл `token.json` для последующих запусков

---

## Проверка настройки

После настройки запустите приложение:

```bash
cd /Users/evochka/Documents/GreMuiv
source venv/bin/activate
python main.py
```

Если все настроено правильно, вы увидите:
- "Используется Service Account (автоматический режим)" (для Service Account)
- или процесс авторизации (для OAuth)

