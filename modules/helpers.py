'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    24.12.29.12.30
'''


# Imports

import os
import json

from time import sleep
from random import randint
from datetime import datetime, timedelta
from pyautogui import alert
from pprint import pprint

from config.settings import logs_folder_path

# Importación para manejar alertas auto
import threading
import pyautogui
import time



#### Common functions ####

#< Directories related
def make_directories(paths: list[str]) -> None:
    '''
    Function to create missing directories
    '''
    for path in paths:  
        path = path.replace("//","/")
        if '/' in path and '.' in path: path = path[:path.rfind('/')]
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            print(f'Error while creating directory "{path}": ', e)


def find_default_profile_directory() -> str | None:
    '''
    Function to search for Chrome Profiles within default locations
    '''
    default_locations = [
        r"%LOCALAPPDATA%\Google\Chrome\User Data",
        r"%USERPROFILE%\AppData\Local\Google\Chrome\User Data",
        r"%USERPROFILE%\Local Settings\Application Data\Google\Chrome\User Data"
    ]
    for location in default_locations:
        profile_dir = os.path.expandvars(location)
        if os.path.exists(profile_dir):
            return profile_dir
    return None
#>


#< Logging related
def critical_error_log(possible_reason: str, stack_trace: Exception) -> None:
    '''
    Function to log and print critical errors along with datetime stamp
    '''
    try:
        # Primero imprimir a la consola, que siempre debería funcionar
        print(f"ERROR CRÍTICO: {possible_reason}")
        print(f"Stack trace: {stack_trace}")
        print(f"Tiempo: {datetime.now()}")
        
        # Intentar registrar en un archivo alternativo sin mostrar alertas
        try:
            # No usamos print_lg para evitar bucles y alertas
            alt_log_path = f"{logs_folder_path}/critical_errors_{datetime.now().strftime('%Y%m%d')}.txt"
            try:
                with open(alt_log_path, 'a+', encoding="utf-8") as alt_file:
                    alt_file.write(f"[CRITICAL ERROR] {datetime.now()}: {possible_reason}\n")
                    alt_file.write(f"Stack trace: {str(stack_trace)}\n\n")
                print(f"Error registrado en archivo alternativo: {alt_log_path}")
            except Exception as alt_error:
                # Si también falla escribir al archivo alternativo, al menos lo mostramos en la consola
                print(f"No se pudo escribir al archivo de log alternativo: {str(alt_error)}")
        except Exception as log_error:
            # Si hay un error en el proceso de registro, simplemente mostramos en la consola
            print(f"Error al intentar registrar error crítico: {str(log_error)}")
    except Exception as e:
        # Último recurso: imprimir el error a la consola
        print(f"Error al intentar registrar un error crítico: {str(e)}")
        print(f"Error original: {possible_reason}, {stack_trace}")


def get_log_path():
    '''
    Function to replace '//' with '/' for logs path
    '''
    try:
        path = logs_folder_path+"/log.txt"
        
        # Verificamos que el directorio de logs exista y tenga permisos correctos
        verify_logs_directory()
        
        return path.replace("//","/")
    except Exception as e:
        print(f"Error al obtener la ruta del log: {str(e)}")
        critical_error_log("Failed getting log path! So assigning default logs path: './logs/log.txt'", e)
        return "logs/log.txt"


def verify_logs_directory():
    '''
    Función para verificar y reparar el directorio de logs
    '''
    try:
        # Verificar si existe el directorio logs
        logs_dir = logs_folder_path.replace("//","/")
        if not os.path.exists(logs_dir):
            print(f"Directorio de logs no encontrado. Creando: {logs_dir}")
            os.makedirs(logs_dir, exist_ok=True)
        
        # Verificar si existe el archivo de log, y si está bloqueado
        log_file = f"{logs_dir}/log.txt"
        
        # Si el archivo existe, verificar si está bloqueado
        if os.path.exists(log_file):
            try:
                # Intentamos abrir y cerrar el archivo para ver si está accesible
                with open(log_file, 'a+', encoding="utf-8") as test_file:
                    test_file.write("")
                print("Archivo de log verificado y accesible.")
            except Exception as e:
                # Si no podemos acceder, creamos uno alternativo
                print(f"Archivo de log bloqueado: {str(e)}")
                print("Creando archivo de log alternativo.")
                
                # Renombrar el archivo bloqueado como respaldo
                try:
                    backup_name = f"{logs_dir}/log_blocked_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
                    import shutil
                    shutil.copy(log_file, backup_name)
                    print(f"Respaldo creado: {backup_name}")
                except:
                    print("No se pudo crear respaldo del archivo bloqueado.")
                
                # Intentar eliminar el archivo bloqueado
                try:
                    os.remove(log_file)
                    print("Archivo de log bloqueado eliminado.")
                except:
                    print("No se pudo eliminar el archivo bloqueado.")
                
                # Crear uno nuevo
                try:
                    with open(log_file, 'w', encoding="utf-8") as new_file:
                        new_file.write(f"[NEW LOG] {datetime.now()} - Archivo de log anterior estaba bloqueado.\n")
                    print("Nuevo archivo de log creado.")
                except Exception as new_error:
                    print(f"No se pudo crear nuevo archivo de log: {str(new_error)}")
    except Exception as e:
        print(f"Error al verificar directorio de logs: {str(e)}")


__logs_file_path = get_log_path()


def print_lg(*msgs: str | dict, end: str = "\n", pretty: bool = False, flush: bool = False, from_critical: bool = False) -> None:
    '''
    Function to log and print. **Note that, `end` and `flush` parameters are ignored if `pretty = True`**
    '''
    # Primero, imprimimos en la consola (esto siempre debería funcionar)
    for message in msgs:
        pprint(message) if pretty else print(message, end=end, flush=flush)
        
    # Luego intentamos escribir al archivo de log con mejor manejo de errores
    try:
        for message in msgs:
            # Usamos un mecanismo de reintento para abrir el archivo
            max_retries = 3
            retry_delay = 0.5  # segundos
            
            for retry in range(max_retries):
                try:
                    # Intentamos abrir el archivo con un timeout
                    with open(__logs_file_path, 'a+', encoding="utf-8") as file:
                        file.write(str(message) + end)
                    break  # Si tenemos éxito, salimos del bucle de reintentos
                except Exception as e:
                    if retry < max_retries - 1:
                        # Si no es el último intento, esperamos y volvemos a intentar
                        sleep(retry_delay)
                    else:
                        # Si es el último intento y falla, sólo imprimimos un mensaje y continuamos
                        # No mostramos alertas para no interrumpir el flujo del programa
                        print(f"ERROR: No se pudo escribir en el archivo de log. El programa continuará pero los logs pueden estar incompletos.")
                        print(f"Detalles: {str(e)}")
                        
                        # Intentamos crear un archivo de registro alternativo
                        try:
                            alt_log_path = f"{logs_folder_path}/log_alt_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
                            with open(alt_log_path, 'a+', encoding="utf-8") as alt_file:
                                alt_file.write(f"[ALTERNATIVE LOG] {datetime.now()}: Problema con el archivo de log principal.\n")
                                alt_file.write(str(message) + end)
                            print(f"Se creó un archivo de log alternativo: {alt_log_path}")
                        except:
                            # Si tampoco podemos crear un archivo alternativo, simplemente continuamos
                            pass
                        
                        # Solo registramos el error crítico si no estamos ya en un error crítico
                        if not from_critical:
                            try:
                                # Usar print en lugar de critical_error_log para evitar bucle infinito
                                print(f"ERROR CRÍTICO: Log.txt está bloqueado o inaccesible.")
                                print(f"Stack trace: {e}")
                                print(f"Tiempo: {datetime.now()}")
                            except:
                                # Si incluso esto falla, simplemente continuamos
                                pass
    except Exception as e:
        # Si hay un error en el manejo del error, simplemente imprimimos y continuamos
        print(f"Error al guardar en el log: {str(e)}")
#>


def buffer(speed: int=0) -> None:
    '''
    Function to wait within a period of selected random range.
    * Will not wait if input `speed <= 0`
    * Will wait within a random range of 
      - `0.6 to 1.0 secs` if `1 <= speed < 2`
      - `1.0 to 1.8 secs` if `2 <= speed < 3`
      - `1.8 to speed secs` if `3 <= speed`
    '''
    if speed<=0:
        return
    elif speed <= 1 and speed < 2:
        return sleep(randint(6,10)*0.1)
    elif speed <= 2 and speed < 3:
        return sleep(randint(10,18)*0.1)
    else:
        return sleep(randint(18,round(speed)*10)*0.1)
    

def manual_login_retry(is_logged_in: callable, limit: int = 2) -> None:
    '''
    Function to ask and validate manual login
    '''
    count = 0
    while not is_logged_in():
        from pyautogui import alert
        print_lg("Seems like you're not logged in!")
        button = "Confirm Login"
        message = 'After you successfully Log In, please click "{}" button below.'.format(button)
        if count > limit:
            button = "Skip Confirmation"
            message = 'If you\'re seeing this message even after you logged in, Click "{}". Seems like auto login confirmation failed!'.format(button)
        count += 1
        if alert(message, "Login Required", button) and count > limit: return



def calculate_date_posted(time_string: str) -> datetime | None | ValueError:
    '''
    Function to calculate date posted from string.
    Returns datetime object | None if unable to calculate | ValueError if time_string is invalid
    Valid time string examples:
    * 10 seconds ago
    * 15 minutes ago
    * 2 hours ago
    * 1 hour ago
    * 1 day ago
    * 10 days ago
    * 1 week ago
    * 1 month ago
    * 1 year ago
    '''
    time_string = time_string.strip()
    # print_lg(f"Trying to calculate date job was posted from '{time_string}'")
    now = datetime.now()
    if "second" in time_string:
        seconds = int(time_string.split()[0])
        date_posted = now - timedelta(seconds=seconds)
    elif "minute" in time_string:
        minutes = int(time_string.split()[0])
        date_posted = now - timedelta(minutes=minutes)
    elif "hour" in time_string:
        hours = int(time_string.split()[0])
        date_posted = now - timedelta(hours=hours)
    elif "day" in time_string:
        days = int(time_string.split()[0])
        date_posted = now - timedelta(days=days)
    elif "week" in time_string:
        weeks = int(time_string.split()[0])
        date_posted = now - timedelta(weeks=weeks)
    elif "month" in time_string:
        months = int(time_string.split()[0])
        date_posted = now - timedelta(days=months * 30)
    elif "year" in time_string:
        years = int(time_string.split()[0])
        date_posted = now - timedelta(days=years * 365)
    else:
        date_posted = None
    return date_posted
    

def convert_to_lakhs(value: str) -> str:
    '''
    Converts str value to lakhs, no validations are done except for length and stripping.
    Examples:
    * "100000" -> "1.00"
    * "101,000" -> "10.1," Notice ',' is not removed 
    * "50" -> "0.00"
    * "5000" -> "0.05" 
    '''
    value = value.strip()
    l = len(value)
    if l > 0:
        if l > 5:
            value = value[:l-5] + "." + value[l-5:l-3]
        else:
            value = "0." + "0"*(5-l) + value[:2]
    return value


def convert_to_json(data) -> dict:
    '''
    Function to convert data to JSON, if unsuccessful, returns `{"error": "Unable to parse the response as JSON", "data": data}`
    '''
    try:
        result_json = json.loads(data)
        return result_json
    except json.JSONDecodeError:
        return {"error": "Unable to parse the response as JSON", "data": data}

def auto_accept_alerts(keywords=["Failed Logging"], timeout=5):
    """
    Esta función se deja como referencia pero no hace nada para evitar bloqueos.
    Ahora todos los mensajes de error se imprimen en la consola sin mostrar alertas.
    """
    print("NOTA: Los mensajes de error se mostrarán en la consola sin interrumpir el flujo del programa.")
    print("Si ves errores relacionados con el archivo de log, puedes intentar estas soluciones:")
    print("1. Cierra cualquier programa que pueda estar usando el archivo log.txt")
    print("2. Reinicia el script")
    print("3. Elimina manualmente el archivo log.txt y vuelve a ejecutar el script")