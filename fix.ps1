# Создаем __init__.py если нет

New-Item -ItemType File -Force -Path ".\apps\__init__.py"
New-Item -ItemType File -Force -Path ".\apps\users\__init__.py"

# Перезаписываем apps.py

@"
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    label = 'users'
"@ | Set-Content ".\apps\users\apps.py"

# Чистим migrations users кроме __init__.py

if (Test-Path ".\apps\users\migrations") {
    Get-ChildItem ".\apps\users\migrations" -Exclude "__init__.py" | Remove-Item -Recurse -Force
}

# Создаем migrations/__init__.py если нет

New-Item -ItemType Directory -Force -Path ".\apps\users\migrations"
New-Item -ItemType File -Force -Path ".\apps\users\migrations\__init__.py"

# Удаляем sqlite базу

if (Test-Path ".\db.sqlite3") {
    Remove-Item ".\db.sqlite3" -Force
}

Write-Host ""
Write-Host "====================================="
Write-Host "DigitalChair FIX APPLIED"
Write-Host "====================================="
Write-Host ""
Write-Host "Теперь выполни:"
Write-Host ""
Write-Host "python manage.py makemigrations"
Write-Host "python manage.py migrate"
Write-Host ""