"""
Django settings for core project.
Configurado para Produção no Railway (SaaS Peixaria Duporto)
"""

from pathlib import Path
import os
import dj_database_url  # NOVO: Lê o banco de dados do Railway automaticamente

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# SEGURANÇA E AMBIENTE (RAILWAY)
# ==========================================
# Lê a chave secreta do servidor, mas se não tiver (ex: no seu PC), usa uma provisória.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-63-d0h@b*9w(uh^)n#uv%t_2cxf$yxkj65^jq3x(c&h2+i67he')

# Se estiver no Railway (com a variável DEBUG=False configurada lá), ele desativa os erros de tela. No seu PC, fica True.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Libera o acesso para o domínio do Railway e para o seu localhost
ALLOWED_HOSTS = ['*']

# Essencial para o Django 4+ aceitar formulários vindos de sites HTTPS (como o Railway)
CSRF_TRUSTED_ORIGINS = ['https://*.railway.app', 'https://*.up.railway.app']

# ==========================================
# APLICATIVOS
# ==========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'funil_vendas', # <-- Módulo principal da Peixaria
]

# ==========================================
# MIDDLEWARES (MOTORES DE INTERCEPTAÇÃO)
# ==========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # NOVO: Essencial para rodar CSS e Imagens no Railway
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # <-- Apontando para a sua pasta de HTMLs
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ==========================================
# BANCO DE DADOS INTELIGENTE
# ==========================================
# Padrão: SQLite (Seu PC)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# SE O SISTEMA ESTIVER NO RAILWAY: Ele ignora o SQLite e conecta no PostgreSQL Profissional
database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES['default'] = dj_database_url.config(default=database_url, conn_max_age=600)


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ==========================================
# IDIOMA E FUSO HORÁRIO (BRASIL)
# ==========================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ==========================================
# ARQUIVOS ESTÁTICOS (Railway / WhiteNoise)
# ==========================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Redireciona usuários não logados para a tela de login
LOGIN_URL = '/admin/login/'