
# 📦 Azure Function - Clasificador de Quejas con Azure AI Foundry y Blob Storage

Este proyecto implementa una **Azure Function HTTP Trigger** que recibe una queja en español y utiliza un modelo serverless desplegado en **Azure AI Foundry** para clasificarla automáticamente en una de tres categorías predefinidas. Además, la respuesta se **guarda como un archivo JSON en Azure Blob Storage Gen2**, en un contenedor específico, para fines de auditoría y trazabilidad.

---

## 🚀 Arquitectura General

```
Cliente → Azure Function → Azure AI Foundry con Despliegue OpenAI → Clasificación → [Respuesta + JSON en Blob Storage]
```

- **Azure Function (Python):** punto de entrada HTTP, sin autenticación (para pruebas).
- **Azure AI Foundry:** modelo GPT (nano o turbo) desplegado en Azure.
- **Blob Storage Gen2:** almacenamiento estructurado de resultados.

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

### Azure

- Una suscripción con acceso a **Azure AI Foundry**
- Recurso de **Azure Blob Storage Gen2**
- Recurso de **Azure Function App** en Python 3.10+

### Local

- Python 3.10+
- Azure Functions Core Tools
- `pip` + entorno virtual recomendado

---

## 📦 Instalación y Ejecución Local

```bash
# Clonar el repositorio
git clone https://github.com/<tu-org>/ClasificadorQuejasOpenAI.git
cd ClasificadorQuejasOpenAI

# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la Azure Function localmente
func start
```

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

⚠️ **Nota:** Nunca subas claves reales al repositorio. Usa Azure Key Vault o variables de entorno seguras.

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

Carlos Francisco Silva Ortiz
Docente Maestría en Inteligencia de Negocios
Universidad Externado de Colombia
Materia: Seminario Electivo - Herramientas para Automatización BI  
Chief Data & AI Officer @ Skandia LATAM  
[LinkedIn](https://www.linkedin.com/in/csilvao/)

---

## 📄 Licencia

MIT License
