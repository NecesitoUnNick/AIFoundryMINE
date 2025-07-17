# 📦 Azure Function - Clasificador de Quejas con Azure AI Foundry y Blob Storage

Este proyecto implementa una **Azure Function HTTP Trigger** que recibe una queja en español y utiliza un modelo serverless desplegado en **Azure AI Foundry** para clasificarla automáticamente en una de tres categorías predefinidas. Además, la respuesta se **guarda como un archivo JSON en Azure Blob Storage Gen2**, en un contenedor específico, para fines de auditoría y trazabilidad.

---

## 🚀 Arquitectura General

```
Cliente → Azure Function → Azure AI Foundry con Despliegue OpenAI → Clasificación → [Respuesta + JSON en Blob Storage]
```

- **Azure Function (Python):** Punto de entrada HTTP, sin autenticación (para pruebas).
- **Azure AI Foundry:** Modelo GPT (nano o turbo) desplegado en Azure.
- **Blob Storage Gen2:** Almacenamiento estructurado de resultados.

---

## 📂 Estructura del Proyecto

```
project-root/
│
├── __pycache__/                    ← Cache de Python (no subir)
├── .venv/                          ← Entorno virtual de Python (no subir)
├── .vscode/                        ← Configuración del editor VS Code (no subir)
├── .funcignore                     ← Archivos ignorados por Azure Functions
├── .gitignore                      ← Archivos ignorados por Git
│
├── function_app.py                 ← Código principal de la Azure Function ⚡
├── host.json                       ← Configuración global del host
├── local.settings.json            ← Variables de entorno (local dev)
├── requirements.txt                ← Dependencias necesarias (pip)
└── README.md                       ← Este archivo 📄
```

---

## ⚙️ Requisitos Previos

### Local

- Python 3.10+
- Azure Functions Core Tools
- `pip` y un entorno virtual (recomendado).

### Azure

- Una suscripción de Azure con acceso a **Azure AI Foundry**.
- Un recurso de **Azure Blob Storage Gen2**.
- Una **Azure Function App** configurada para Python 3.10+.

### Recursos de Azure

Antes de implementar la función, asegúrate de tener los siguientes recursos creados en tu suscripción de Azure:

1.  **Grupo de Recursos:** Un contenedor para todos los recursos relacionados.
2.  **Cuenta de Almacenamiento (Storage Account):** De tipo `StorageV2 (general purpose v2)` para Blob Storage.
    *   Dentro de la cuenta, crea un contenedor llamado `cr001` (o el que prefieras, pero recuerda actualizar el código).
3.  **Recurso de Azure AI Services:** Para acceder a los modelos de OpenAI.
    *   Anota la clave (`API Key`) y el punto de conexión (`Endpoint`).
4.  **Aplicación de Funciones (Function App):**
    *   **Runtime stack:** Python
    *   **Versión:** 3.10 (o superior)
    *   **Sistema Operativo:** Linux o Windows, según tu preferencia.

---

## 📦 Instalación y Ejecución Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-org>/ClasificadorQuejasOpenAI.git
cd ClasificadorQuejasOpenAI

# 2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la Azure Function localmente
func start
```

---

## 🚀 Despliegue en Azure

Una vez que hayas probado la función localmente, puedes implementarla en Azure.

### 1. **Inicio de Sesión en Azure CLI**

Asegúrate de tener Azure CLI instalado y autentícate en tu cuenta:

```bash
az login
```

### 2. **Publicar la Función**

Desde el directorio raíz del proyecto, ejecuta el siguiente comando. Reemplaza `<TU_FUNCTION_APP_NAME>` con el nombre de tu Function App creada en Azure.

```bash
# Publicar el código en Azure
func azure functionapp publish <TU_FUNCTION_APP_NAME>
```

Este comando empaquetará tu código y lo desplegará en la Function App especificada.

### 3. **Configurar Variables de Entorno en Azure**

Los valores de `local.settings.json` **no se publican** en Azure. Debes configurarlos manualmente en la sección de "Configuración" (Configuration) de tu Function App en el portal de Azure.

Ve a tu Function App → Configuración → "Application settings" y añade las siguientes claves con sus valores correspondientes:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_MODEL`
- `AZURE_STORAGE_CONNECTION_STRING`

**Importante:** Para mayor seguridad en entornos productivos, considera usar Azure Key Vault para gestionar estos secretos y referenciarlos desde la configuración de la Function App.

---

## 🔐 Configuración de Variables de Entorno

En `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",

    "AZURE_OPENAI_API_KEY": "<TU_API_KEY>",
    "AZURE_OPENAI_ENDPOINT": "https://<tu-recurso>.cognitiveservices.azure.com/",
    "AZURE_OPENAI_MODEL": "gpt-4.1-nano",

    "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=...;AccountName=...;AccountKey=...;"
  }
}
```

⚠️ **Importante:** El archivo `local.settings.json` es **solo para desarrollo local** y no debe ser subido al repositorio de Git. Contiene secretos que no deben ser expuestos. Asegúrate de que la línea `local.settings.json` esté en tu archivo `.gitignore`.

**Nota:** Nunca subas claves reales al repositorio. Usa Azure Key Vault o variables de entorno seguras en producción.

---

## 🧠 Lógica del Clasificador

El sistema recibe un texto en español y lo clasifica en una de estas categorías:

1. **Problemas con plataformas digitales** (portal web o app móvil)
2. **Problemas con atención física en oficinas**
3. **Problemas con transacciones de aportes o retiros**

El modelo retorna únicamente el nombre de la categoría en español. Luego, se registra lo siguiente:

- Categoría clasificada
- Tokens de entrada y salida
- Total de tokens usados

---

## 📤 Ejemplo de Request

### 1. **Por parámetro GET:**

```
GET /api/Clasificador?Queja=No puedo ingresar a la app, se cierra sola
```

### 2. **Por JSON POST:**

```json
{
  "Queja": "El retiro aún no llega a mi cuenta bancaria"
}
```

---

## 🧪 Pruebas (Testing)

### Pruebas Locales

Mientras `func start` se está ejecutando, puedes usar una herramienta como `curl` o Postman para probar la función.

**Prueba con cURL (GET):**

```bash
curl "http://localhost:7071/api/Clasificador?Queja=No%20puedo%20ingresar%20a%20la%20app,%20se%20cierra%20sola"
```

**Prueba con cURL (POST):**

```bash
curl -X POST \
  http://localhost:7071/api/Clasificador \
  -H 'Content-Type: application/json' \
  -d '{"Queja": "El retiro aún no llega a mi cuenta bancaria"}'
```

### Pruebas en Azure

Una vez desplegada la función, puedes probarla de la misma manera, pero usando la URL de la función en Azure.

1.  **Obtener la URL de la Función:**
    *   Ve al Portal de Azure → Tu Function App → Funciones → Clasificador.
    *   Haz clic en **"Get Function Url"** y copia la URL.

2.  **Probar con cURL:**

    Reemplaza `<URL_DE_TU_FUNCION>` con la URL que copiaste.

    ```bash
    # Ejemplo GET
    curl "<URL_DE_TU_FUNCION>&Queja=Mi%20tarjeta%20fue%20rechazada%20sin%20motivo"

    # Ejemplo POST
    curl -X POST \
      "<URL_DE_TU_FUNCION>" \
      -H 'Content-Type: application/json' \
      -d '{"Queja": "No entiendo el último cobro en mi factura"}'
    ```

---

## 📥 Ejemplo de Respuesta

```json
{
  "categoria": "Problemas con transacciones de aportes o retiros",
  "prompt_tokens": 160,
  "completion_tokens": 7,
  "total_tokens": 167
}
```

---

## 📁 Almacenamiento de Respuesta

- Cada resultado se guarda como un `.json` en:
  ```
  Contenedor: cr001
  Ruta: LogsAzFnOpenAI/20240705_134855.json
  ```

- Esto permite trazabilidad, análisis posterior y auditoría de uso.

---

## 🛡️ Seguridad

- Como vimos en la clase, actualmente el consumo del azure function tiene  `http_auth_level` como **ANONYMOUS**. Cambiar a `FUNCTION` o `ADMIN` para entornos productivos.
- En caso de mayor seguridad, se recomienda usar Azure Key Vault y Azure Managed Identity para proteger secretos.

---

## 📚 Recursos y Referencias

- [Azure AI Foundry](https://learn.microsoft.com/es-es/azure/ai-foundry/what-is-azure-ai-foundry)
- [Azure Functions Python Developer Guide](https://learn.microsoft.com/es-es/azure/azure-functions/functions-reference-python)
- [Azure Blob Storage SDK for Python](https://pypi.org/project/azure-storage-blob/)

---

## 🧑‍💻 Autor

Carlos Francisco Silva Ortiz <br>
Docente Maestría en Inteligencia de Negocios <br>
Universidad Externado de Colombia <br>
Materia: Seminario Electivo - Herramientas para Automatización BI <br>
Chief Data & AI Officer @ Skandia LATAM  
[LinkedIn](https://www.linkedin.com/in/csilvao/)

---

## 📄 Licencia

MIT License
