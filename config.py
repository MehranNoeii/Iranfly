import os


# Telegram Bot
# ==========================

API_TOKEN = os.environ.get('API_TOKEN')



# Database
# ==========================

database_config = {
    'host': os.environ.get('database_host'),
    'user': os.environ.get('database_user'),
    'password': os.environ.get('database_password')
}

database_name = os.environ.get('database')



# Admins
# ==========================

ADMIN_ID = [
    5330477037
]