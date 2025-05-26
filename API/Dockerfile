# Указываем базовый образ
FROM node:18

# Устанавливаем nodemon глобально
RUN npm install -g nodemon

# Рабочая директория
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json .

# Устанавливаем зависимости
RUN npm install

# Копируем остальные файлы проекта
COPY . .

# Команда для запуска приложения с nodemon
CMD ["nodemon", "/app/index.js"]

