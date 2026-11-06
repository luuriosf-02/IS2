
from pathlib import Path
import os

#Para Stripe
def _read_webhook_secret():
    env_value = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if env_value:
        return env_value
    secret_file = Path("/secrets/whsec")
    if secret_file.exists():
        return secret_file.read_text().strip()
    return ""

STRIPE_WEBHOOK_SECRET = _read_webhook_secret()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


#Stripe keys
STRIPE_PUBLISHABLE_KEY = os.environ["STRIPE_PUBLISHABLE_KEY"]  # pk_test_...
STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]            # sk_test_...

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-f!l93_7%(=l8em8&(b&im5rig5nin9_r3ram@3bfd7mnn%t^6_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "web"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "mozilla_django_oidc",

    "apps.dashboard",
    "apps.users",
    'apps.clientes',
    "apps.divisas.apps.DivisasConfig",
    "apps.payments",
    "apps.transacciones",
    "apps.stripe",
    "apps.facturacion.apps.FacturacionConfig",
    "apps.cajas.apps.CajasConfig",
]

FS_TOKEN = os.environ.get("FS_TOKEN", "")
FS_API_URL = os.environ.get(
    "FS_API_URL",
    "https://apitest.facturasegura.com.py/misife00/v1/esi",
)
FS_TIMEOUT_SECONDS = int(os.environ.get("FS_TIMEOUT_SECONDS", "30"))

FS_D_RUC_EM = os.environ.get("dRucEm") or os.environ.get("FS_D_RUC_EM", "")
FS_DV_EMI = os.environ.get("dVEmi") or os.environ.get("FS_DV_EMI", "")
FS_I_TIP_CONT = os.environ.get("iTipCont") or os.environ.get("FS_I_TIP_CONT", "")
FS_D_NUM_TIM = os.environ.get("dNumTim") or os.environ.get("FS_D_NUM_TIM", "")
FS_D_FE_INI_T = os.environ.get("dFeIniT") or os.environ.get("FS_D_FE_INI_T", "")
FS_D_TEL_EMI = os.environ.get("dTelEmi") or os.environ.get("FS_D_TEL_EMI", "")
FS_C_ACT_ECO1 = os.environ.get("cActEco1") or os.environ.get("FS_C_ACT_ECO1", "")
FS_C_ACT_ECO2 = os.environ.get("cActEco2") or os.environ.get("FS_C_ACT_ECO2", "")
FS_D_DES_ACT_ECO1 = os.environ.get("dDesActEco1") or os.environ.get("FS_D_DES_ACT_ECO1", "")
FS_D_DES_ACT_ECO2 = os.environ.get("dDesActEco2") or os.environ.get("FS_D_DES_ACT_ECO2", "")

FS_D_NOM_EMI = os.environ.get("FS_D_NOM_EMI", "")
FS_D_DIR_EMI = os.environ.get("FS_D_DIR_EMI", "")
FS_D_NUM_CAS = os.environ.get("FS_D_NUM_CAS", "")
FS_C_DEP_EMI = os.environ.get("FS_C_DEP_EMI", "")
FS_D_DES_DEP_EMI = os.environ.get("FS_D_DES_DEP_EMI", "")
FS_C_CIU_EMI = os.environ.get("FS_C_CIU_EMI", "")
FS_D_DES_CIU_EMI = os.environ.get("FS_D_DES_CIU_EMI", "")
FS_D_EMAIL_E = os.environ.get("FS_D_EMAIL_E", "")
FS_D_EST = os.environ.get("FS_D_EST", "")
FS_D_PUN_EXP = os.environ.get("FS_D_PUN_EXP", "")
FS_I_T_IMP = os.environ.get("FS_I_T_IMP", "")
FS_I_IND_PRES = os.environ.get("FS_I_IND_PRES", "")
FS_I_AFEC_IVA = os.environ.get("FS_I_AFEC_IVA", "")
FS_D_PROP_IVA = os.environ.get("FS_D_PROP_IVA", "")
FS_D_TASA_IVA = os.environ.get("FS_D_TASA_IVA", "")
FS_I_FOR_PRO_PA = os.environ.get("FS_I_FOR_PRO_PA", "")
FS_I_TI_CONT_REC_FISICA = os.environ.get("FS_I_TI_CONT_REC_FISICA", "")
FS_I_TI_CONT_REC_JURIDICA = os.environ.get("FS_I_TI_CONT_REC_JURIDICA", "")
FS_I_DEN_TARJ_VISA = os.environ.get("FS_I_DEN_TARJ_VISA", "")
FS_I_DEN_TARJ_MASTERCARD = os.environ.get("FS_I_DEN_TARJ_MASTERCARD", "")
FS_I_DEN_TARJ_AMEX = os.environ.get("FS_I_DEN_TARJ_AMEX", "")
FS_I_DEN_TARJ_OTRA = os.environ.get("FS_I_DEN_TARJ_OTRA", "")

FS_I_TIP_TRA_VENTA = os.environ.get("FS_I_TIP_TRA_VENTA", "")
FS_I_TIP_TRA_COMPRA = os.environ.get("FS_I_TIP_TRA_COMPRA", "")
FS_I_TI_OPE_B2B = os.environ.get("FS_I_TI_OPE_B2B", "")
FS_I_TI_OPE_B2C = os.environ.get("FS_I_TI_OPE_B2C", "")
DS_I_TI_DE_FACTURA = os.environ.get("DS_I_TI_DE_FACTURA", "")
DS_I_TI_DE_NOTA = os.environ.get("DS_I_TI_DE_NOTA", "")
FS_I_MOT_EMI_NOTA = os.environ.get("FS_I_MOT_EMI_NOTA", "")
FS_I_NAT_REC_CONTRIBUYENTE = os.environ.get("FS_I_NAT_REC_CONTRIBUYENTE", "")
FS_I_NAT_REC_NO_CONTRIBUYENTE = os.environ.get("FS_I_NAT_REC_NO_CONTRIBUYENTE", "")

AUTHENTICATION_BACKENDS= (
    'global_exchange.auth.MyOIDCAB',
    'django.contrib.auth.backends.ModelBackend',
)


# Configuración Keycloak / OIDC
OIDC_RP_CLIENT_ID = os.environ.get('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = os.environ.get('OIDC_RP_CLIENT_SECRET')

# URLs de Keycloak (usamos localhost porque el navegador del usuario hace las redirecciones)
KEYCLOAK_PUBLIC_URL = os.environ.get('KEYCLOAK_PUBLIC_URL')
KEYCLOAK_INTERNAL_URL = os.environ.get('KEYCLOAK_INTERNAL_URL')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM')

OIDC_OP_AUTHORIZATION_ENDPOINT = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

OIDC_RP_SIGN_ALGO = 'RS256'

LOGIN_URL = "/oidc/authenticate/"
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mozilla_django_oidc.middleware.SessionRefresh',
]

ROOT_URLCONF = 'global_exchange.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.csrf',
                'apps.users.context_processors.active_client',
                "apps.cajas.context_processors.permisos_caja",
            ],
        },
    },
]

WSGI_APPLICATION = 'global_exchange.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'midb'),
        'USER': os.environ.get('POSTGRES_USER', 'miusuario'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'miclave'),
        'HOST': 'db',  # Mismo nombre del servicio definido en docker-compose.yml
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
"""
Django settings for global_exchange project.

Generated by 'django-admin startproject' using Django 5.2.17.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""
