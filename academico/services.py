import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import TasaCambio

def obtener_tasa_bcv_api():
    """Línea A: Obtiene la tasa oficial desde DolarApi"""
    try:
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return Decimal(str(data.get("promedio")))
    except Exception:
        return None

def obtener_tasa_bcv_scraping():
    """Línea B (Respaldo): Extrae la tasa raspando el portal del BCV"""
    try:
        url = "https://www.bcv.org.ve/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            div_dolar = soup.find('div', id='dolar')
            if div_dolar:
                strong_val = div_dolar.find('strong')
                if strong_val:
                    val_texto = strong_val.text.strip().replace('.', '').replace(',', '.')
                    return Decimal(val_texto)
    except Exception:
        return None

def actualizar_tasa_bcv():
    """Orquestador: Intenta API, si falla va a Scraping"""
    tasa = obtener_tasa_bcv_api()
    if not tasa:
        tasa = obtener_tasa_bcv_scraping()
    return tasa

def verificar_y_actualizar_tasas():
    """
    Procedimiento principal:
    1. Verifica si la tasa de hoy ya está registrada. Si no, la busca y la guarda.
    2. Revisa una ventana de 15 días hacia atrás y rellena los días faltantes con la tasa actual.
    """
    hoy = timezone.now().date()
    
    # 1. Verificar si existe la tasa del día actual
    tasa_hoy = TasaCambio.objects.filter(moneda="USD", fecha=hoy).first()
    
    if not tasa_hoy:
        # No existe hoy: la buscamos en la API / BCV
        nuevo_precio = actualizar_tasa_bcv()
        
        if not nuevo_precio:
            # Fallback de seguridad: si la API y el BCV fallan, usamos la última registrada
            ultima = TasaCambio.objects.filter(moneda="USD").order_by('-fecha').first()
            nuevo_precio = ultima.precio if ultima else None
        
        if nuevo_precio:
            TasaCambio.objects.update_or_create(
                moneda="USD",
                fecha=hoy,
                defaults={
                    "precio": nuevo_precio,
                    "es_manual": False,
                    "es_estimado": False
                }
            )

    # 2. Obtener la tasa de referencia (hoy o la última disponible) para rellenar huecos
    tasa_referencia = TasaCambio.objects.filter(moneda="USD", fecha=hoy).first()
    if not tasa_referencia:
        tasa_referencia = TasaCambio.objects.filter(moneda="USD").order_by('-fecha').first()
    
    if tasa_referencia:
        precio_base = tasa_referencia.precio
        
        # 3. Consulta y relleno en la ventana de los últimos 15 días
        for i in range(1, 16):
            fecha_pasada = hoy - timedelta(days=i)
            
            # Si falta el registro en ese día, lo creamos como estimado
            if not TasaCambio.objects.filter(moneda="USD", fecha=fecha_pasada).exists():
                TasaCambio.objects.create(
                    moneda="USD",
                    fecha=fecha_pasada,
                    precio=precio_base,
                    es_manual=False,
                    es_estimado=True
                )

def obtener_tasa_vigente():
    """Retorna la tasa actual asegurándose de ejecutar el proceso de revisión"""
    verificar_y_actualizar_tasas()
    hoy = timezone.now().date()
    tasa_hoy = TasaCambio.objects.filter(moneda="USD", fecha=hoy).first()
    if tasa_hoy:
        return tasa_hoy.precio
    
    ultima = TasaCambio.objects.filter(moneda="USD").order_by('-fecha').first()
    return ultima.precio if ultima else None

# --- Funciones de compatibilidad para evitar errores de importación en las vistas ---
def rellenar_dias_faltantes():
    verificar_y_actualizar_tasas()

def asegurar_historico_15_dias():
    verificar_y_actualizar_tasas()