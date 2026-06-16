#services.py
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
                    # Limpiamos posibles espacios y formateamos el decimal anglosajón
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

def obtener_tasa_vigente():
    """Lazy Check: Retorna la tasa de hoy o la actualiza si pasaron 4 horas"""
    hoy = timezone.now().date()
    ahora = timezone.now()

    # Buscar si ya existe la tasa asentada para hoy
    tasa_hoy = TasaCambio.objects.filter(moneda="USD", fecha=hoy).first()
    if tasa_hoy:
        return tasa_hoy.precio

    # Si no hay tasa de hoy, buscamos el último registro histórico que exista
    ultima_tasa = TasaCambio.objects.filter(moneda="USD").first()

    # Si el sistema nunca ha tenido tasas o si la última revisión tiene más de 4 horas
    if not ultima_tasa or (ahora - ultima_tasa.fecha_actualizacion) > timedelta(hours=4):
        nuevo_precio = actualizar_tasa_bcv()
        if nuevo_precio:
            tasa_hoy, _ = TasaCambio.objects.update_or_create(
                moneda="USD",
                fecha=hoy,
                defaults={"precio": nuevo_precio}
            )
            return tasa_hoy.precio

    # Si todo falla (BCV caído y API caída), usamos la última registrada como salvavidas
    return ultima_tasa.precio if ultima_tasa else None

def rellenar_dias_faltantes():
    ultima_tasa = TasaCambio.objects.filter(moneda="USD").order_by('-fecha').first()
    if not ultima_tasa: return

    hoy = timezone.now().date()
    if ultima_tasa.fecha >= hoy: return

    precio_a_propagar = ultima_tasa.precio
    fecha_cursor = ultima_tasa.fecha + timedelta(days=1)
    
    while fecha_cursor < hoy:
        # Aquí marcamos es_manual=False porque el sistema lo está generando
        TasaCambio.objects.get_or_create(
            moneda="USD",
            fecha=fecha_cursor,
            defaults={"precio": precio_a_propagar, "es_manual": False}
        )
        fecha_cursor += timedelta(days=1)

def asegurar_historico_15_dias():
    hoy = timezone.now().date()
    # Obtenemos el último precio conocido real
    ultimo_registro = TasaCambio.objects.order_by('-fecha').first()

    if not ultimo_registro:
        return
    
    precio_base = ultimo_registro.precio if ultimo_registro else 0

    for i in range(15):
        fecha_a_verificar = hoy - timedelta(days=i)

        if not TasaCambio.objects.filter(fecha=fecha_a_verificar).exists():
            TasaCambio.objects.create(
                fecha=fecha_a_verificar,
                precio=precio_base,
                moneda="USD", # Asegúrate de especificar la moneda
                es_manual=False,
                es_estimado=True  # Marcado en rojo
            )   