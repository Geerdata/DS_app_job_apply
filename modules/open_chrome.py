'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    24.12.29.12.30
'''

from modules.helpers import make_directories
from config.settings import run_in_background, stealth_mode, disable_extensions, safe_mode, file_name, failed_file_name, logs_folder_path, generated_resume_path
from config.questions import default_resume_path
if stealth_mode:
    import undetected_chromedriver as uc
else: 
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from modules.helpers import find_default_profile_directory, critical_error_log, print_lg
from datetime import datetime

try:
    make_directories([file_name,failed_file_name,logs_folder_path+"/screenshots",default_resume_path,generated_resume_path+"/temp"])

    # Set up WebDriver with Chrome Profile
    options = uc.ChromeOptions() if stealth_mode else Options()
    if run_in_background:   options.add_argument("--headless")
    if disable_extensions:  options.add_argument("--disable-extensions")
    
    # Opciones adicionales para evitar bloqueos y problemas de estabilidad
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-in-process-stack-traces")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")
    
    # Ignorar errores de certificados
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    
    # Detección automática de descargas
    options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    print_lg("IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!")
    if safe_mode: 
        print_lg("SAFE MODE: Will login with a guest profile, browsing history will not be saved in the browser!")
    else:
        profile_dir = find_default_profile_directory()
        if profile_dir: options.add_argument(f"--user-data-dir={profile_dir}")
        else: print_lg("Default profile directory not found. Logging in with a guest profile, Web history will not be saved!")
    if stealth_mode:
        # try: 
        #     driver = uc.Chrome(driver_executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe", options=options)
        # except (FileNotFoundError, PermissionError) as e: 
        #     print_lg("(Undetected Mode) Got '{}' when using pre-installed ChromeDriver.".format(type(e).__name__)) 
            print_lg("Downloading Chrome Driver... This may take some time. Undetected mode requires download every run!")
            try:
                # Intento limpiar procesos previos de Chrome antes de iniciar uno nuevo
                import psutil
                import subprocess
                
                # Intenta matar procesos de chrome y chromedriver
                print_lg("Limpiando procesos de Chrome previos...")
                try:
                    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
                    subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True)
                except Exception as e:
                    print_lg(f"No se pudieron matar procesos previos: {str(e)}")
                
                # Espera un momento para asegurar que los procesos se cierren
                import time
                time.sleep(2)
                
                # Ahora inicia Chrome con las opciones optimizadas
                driver = uc.Chrome(options=options)
            except Exception as e:
                print_lg(f"Error al iniciar Chrome en modo no detectable: {str(e)}")
                print_lg("Intentando iniciar en modo normal...")
                options = Options()  # Reiniciar las opciones para modo normal
                # Aplicar de nuevo las opciones de estabilidad
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(options=options)
    else: 
        # Intento limpiar procesos previos de Chrome antes de iniciar
        import psutil
        import subprocess
        
        # Intenta matar procesos de chrome y chromedriver
        print_lg("Limpiando procesos de Chrome previos...")
        try:
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True)
        except Exception as e:
            print_lg(f"No se pudieron matar procesos previos: {str(e)}")
        
        # Espera un momento para asegurar que los procesos se cierren
        import time
        time.sleep(2)
        
        driver = webdriver.Chrome(options=options) #, service=Service(executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe"))
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
except Exception as e:
    msg = 'Seems like either... \n\n1. Chrome is already running. \nA. Close all Chrome windows and try again. \n\n2. Google Chrome or Chromedriver is out dated. \nA. Update browser and Chromedriver (You can run "windows-setup.bat" in /setup folder for Windows PC to update Chromedriver)! \n\n3. If error occurred when using "stealth_mode", try reinstalling undetected-chromedriver. \nA. Open a terminal and use commands "pip uninstall undetected-chromedriver" and "pip install undetected-chromedriver". \n\n\nIf issue persists, try Safe Mode. Set, safe_mode = True in config.py \n\nPlease check GitHub discussions/support for solutions https://github.com/GodsScion/Auto_job_applier_linkedIn \n                                   OR \nReach out in discord ( https://discord.gg/fFp7uUzWCY )'
    if isinstance(e,TimeoutError): msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    
    # Mostrar detalles adicionales del error para facilitar la depuración
    error_details = f"\n\nDetalle del error: {str(e)}"
    if "DevToolsActivePort file doesn't exist" in str(e):
        error_details += "\n\nEste error suele ocurrir cuando Chrome se bloquea o no se cierra correctamente. Intenta reiniciar la PC o usar las siguientes soluciones:\n"
        error_details += "1. Abrir el Administrador de tareas y terminar todos los procesos relacionados con Chrome\n"
        error_details += "2. Ejecutar el comando 'taskkill /f /im chrome.exe' en CMD\n"
        error_details += "3. Instalar la última versión de Chrome y ChromeDriver"
    
    # Solo imprimir en la consola, no mostrar alertas bloqueantes
    print(msg + error_details)
    
    # Usamos print en lugar de critical_error_log para evitar mostrar alertas
    print(f"ERROR CRÍTICO: Problema al abrir Chrome")
    print(f"Stack trace: {e}")
    print(f"Tiempo: {datetime.now()}")
    
    try:
        # Intentamos cerrar Chrome de forma limpia
        try: driver.quit()
        except NameError: pass
        
        # Intentamos matar los procesos de Chrome directamente
        try:
            import subprocess
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True)
            print("Se han terminado los procesos de Chrome manualmente")
        except:
            pass
    finally:
        # Terminar el programa con mensaje claro
        print("\nEl programa se cerrará debido a un error crítico con Chrome. Por favor reinicia el script.")
        exit()
    
