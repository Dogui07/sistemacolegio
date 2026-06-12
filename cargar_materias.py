import os
import csv
import django

# 1. Configurar el entorno de Django apuntando a tu carpeta 'config'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academico.models import Asignatura, Colegio

def importar_csv():
    ruta_archivo = 'asignaturas.csv'
    
    if not os.path.exists(ruta_archivo):
        print(f"Error: No se encuentra el archivo {ruta_archivo}")
        return

    print("Iniciando carga con auto-limpieza de formato...")
    
    # 1. Leemos el archivo y limpiamos las comillas externas deformadas
    lineas_limpias = []
    with open(ruta_archivo, mode='r', encoding='latin-1') as file:
        # La primera línea (cabecera) la dejamos igual
        cabecera = next(file, "")
        lineas_limpias.append(cabecera)
        
        for line in file:
            line = line.strip()
            if not line:
                continue
            
            # Si la línea entera está envuelta en comillas, se las quitamos
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            
            # Convertimos las dobles comillas "" en una comilla simple " para el estándar CSV
            line = line.replace('""', '"')
            lineas_limpias.append(line)

    # 2. Procesamos las líneas ya normalizadas con el lector de CSV
    reader = csv.reader(lineas_limpias, delimiter=',', quotechar='"')
    next(reader, None) # Omitir cabecera
    
    creadas = 0
    actualizadas = 0
    
    for num_linea, row in enumerate(reader, start=2):
        if not row or len(row) < 5:
            continue
            
        try:
            colegio_id         = row[0].strip()
            codigo             = row[1].strip()
            nombre             = row[2].strip()
            descripcion        = row[3].strip()
            nivel              = row[4].strip()
            grado              = row[5].strip()
            horas_semanales    = int(row[6].strip() or 0)
            es_area_desarrollo = row[7].strip() == '1'
            es_especialidad    = row[8].strip() == '1'
            es_tecnica         = row[9].strip() == '1'
            mencion            = row[10].strip() if row[10].strip() else None
            activo             = row[11].strip() == '1'

            # Buscamos el colegio asignado (usualmente ID 1)
            colegio_obj = Colegio.objects.get(id=colegio_id)
            
            # Guardamos o actualizamos en la Base de Datos
            asignatura, created = Asignatura.objects.update_or_create(
                codigo=codigo,
                colegio=colegio_obj,
                defaults={
                    'nombre': nombre,
                    'descripcion': descripcion if descripcion else None,
                    'nivel': nivel,
                    'grado': grado,
                    'horas_semanales': horas_semanales,
                    'es_area_desarrollo': es_area_desarrollo,
                    'es_especialidad': es_especialidad,
                    'es_tecnica': es_tecnica,
                    'mencion': mencion,
                    'activo': activo,
                }
            )
            
            if created:
                creadas += 1
            else:
                actualizadas += 1
                
        except Colegio.DoesNotExist:
            print(f"⚠️ Línea {num_linea}: El Colegio con ID {colegio_id} no existe en tu Base de Datos.")
        except Exception as e:
            print(f"❌ Error en la línea {num_linea}: {e}. Fila: {row}")

    print(f"\n¡Proceso Terminado!")
    print(f"-> Asignaturas nuevas creadas: {creadas}")
    print(f"-> Asignaturas verificadas/actualizadas: {actualizadas}")

if __name__ == '__main__':
    importar_csv()