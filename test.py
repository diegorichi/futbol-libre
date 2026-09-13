
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. Configurar Chrome para registrar eventos de red
options = Options()
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

driver = webdriver.Chrome(options=options)

try:
    # 2. Cargar la página
    driver.get("https://hondurasplay.com/embed/stream.php?r=tntsports")

    # 3. Pausa: el script espera a que presiones ENTER en la consola
    input("\nNavegá la página, reproducí el video y presioná ENTER acá para escanear la red...")

    # 4. Extraer los logs de red acumulados
    logs = driver.get_log("performance")
    encontradas = set()

    for entry in logs:
        message = json.loads(entry["message"])["message"]
        # Filtrar llamadas de red salientes (Network.requestWillBeSent)
        if message["method"] == "Network.requestWillBeSent":
            url = message["params"]["request"]["url"]
            if ".m3u8" in url:
                encontradas.add(url)

    # 5. Imprimir resultados sin duplicados
    print("\n--- URLs .m3u8 detectadas ---")
    if encontradas:
        for url in encontradas:
            print(url)
    else:
        print("No se encontraron URLs .m3u8.")

finally:
    driver.quit()