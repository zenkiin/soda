1. Скачайте проект или инициализируйте директоририю.

2. Установите необходимые для проекта зависимости
pip install -r requirements.txt

3. Создайте базу в PostgreSQL.

4. Перейдите в настройки проекта [soda/settings.py] и в графе DATABASES установите настройки подключения: NAME, USER, PASSWORD.

5. Осуществите миграцию с помощью команды:
python manage.py migrate

6. Создайте суперпользователя.

from django.contrib.auth.models import User
user = User.objects.create_user('rsreu', 'test@example.com', 'rsreu2024')
user.save()


7. Выполните команду python manage.py shell

8. Введите следующий код:
from django.contrib.auth.models import User
superuser = User.objects.create_superuser(‘rsreu’, 'admin@example.com', ‘rsreu2024’)
superuser.save()

9. Запустите сервер с помощью команды:
python manage.py runserver

10. Авторизуйтесь по данным созданного суперпользователя:
username: rsreu
password: rsreu
