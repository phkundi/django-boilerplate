# Django Boilerplate

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/django-boilerplate.git
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Create a postgres database for the project and add the credentials to the `.env` file.

```bash
createdb -U postgres database_name
```

Make sure you have PostgresSQL installed on your system for this to work.

6. Create `.env` file and add copy the content from `.env.example`. Replace the database credentials with the ones you created in the previous step.

7. Create migrations and migrate:

```bash
python manage.py makemigrations
python manage.py migrate
```

8. Create a superuser:

```bash
python manage.py createsuperuser
```

9. Run the development server:

```bash
python manage.py runserver
```

10. You can now access the admin panel at `http://127.0.0.1:8000/admin/` and the API at `http://127.0.0.1:8000/api/`.

## Adding new Apps

To create a new app, run the following command:

```bash
python manage.py startapp app_name
```

I like to organize my apps in the following structure:

```bash
django_backend/
    apps/
        app_name/
            __init__.py
            models/
                __init__.py
                models_1.py
                models_2.py
                ...
            api/
                __init__.py
                routes_1.py
                routes_2.py
                ...
            serializers/
                __init__.py
                serializers_1.py
                serializers_2.py
                ...
            services/
                __init__.py
                services_1.py
                services_2.py
                ...
            admin.py
            apps.py
            urls.py
            ... other files you may need
```

To quickly create the structure above, copy paste this into your terminal (replace `app_name` with your app name):

```bash
mkdir app_name/{models,serializers,api,services}
rm -rf app_name/{models.py,views.py}
touch app_name/urls.py app_name/{models,serializers,api,services}/__init__.py
```

Don't forget to add your app to the `INSTALLED_APPS` in `django_backend/settings.py`.

```python
INSTALLED_APPS = [
    ...
    'app_name',
    ...
]
```
