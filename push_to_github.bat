@echo off
chcp 65001 >nul
echo ========================================================
echo    🐙 RAZGON ZONE - ОТПРАВКА В GITHUB
echo ========================================================
echo.
set /p REPO_URL="Вставьте ссылку на ваш репозиторий GitHub (например, https://github.com/Username/razgon-zone.git): "
if "%REPO_URL%"=="" (
    echo [ОШИБКА] Ссылка на репозиторий не введена.
    pause
    exit /b 1
)

echo.
echo [1/4] Инициализация Git...
git init

echo.
echo [2/4] Индексация файлов...
git add .

echo.
echo [3/4] Создание коммита...
git commit -m "feat: Razgon Zone HFT & Trading Platform"

echo.
echo [4/4] Отправка в GitHub (ветка main)...
git branch -M main
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git push -u origin main

echo.
echo ========================================================
echo    🎉 Код успешно опубликован в GitHub!
echo    Теперь привяжите этот репозиторий в Railway (New Project - GitHub Repo)
echo ========================================================
pause
