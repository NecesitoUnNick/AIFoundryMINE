import azure.functions as func
import logging
import os
import json
from datetime import datetime
from openai import AzureOpenAI                  # SDK Azure OpenAI
from azure.storage.blob import BlobServiceClient  # SDK Blob Storage

# --- Configuración base de la Function ---
#  • AuthLevel.ANONYMOUS  -> se puede invocar sin clave (¡cámbialo en producción!)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# --- Inicialización de clientes y constantes (MEJORA DE PERFORMANCE) ---
# Se inicializan una vez globalmente para ser reutilizados en todas las invocaciones.
# Usamos bloques try/except para manejar errores si las variables de entorno no están.

# 1. Cliente de Azure OpenAI
try:
    openai_client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2025-01-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
except Exception as e:
    openai_client = None
    logging.error(f"❌ Error al inicializar el cliente de Azure OpenAI: {e}")

# 2. Cliente de Azure Blob Storage
try:
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    else:
        blob_service_client = None
        logging.warning("⚠️ Variable AZURE_STORAGE_CONNECTION_STRING no configurada.")
except Exception as e:
    blob_service_client = None
    logging.error(f"❌ Error al inicializar el cliente de Blob Storage: {e}")

# 3. Prompt del sistema para la clasificación (constante)
SYSTEM_PROMPT = (
    "You are an advanced text classification model. "
    "Your task is to receive a complaint text in Spanish and classify it "
    "into one of the following three categories. Return only the category "
    "name in Spanish, nothing else.\n"
    "Digital Platforms: Complaints related to issues with online services, "
    "applications, or websites, such as login problems, functionality errors, "
    "or user experience issues.\n"
    "In-Person Office Assistance: Complaints regarding the quality of service "
    "received at physical office locations, including long wait times, "
    "unhelpful staff, or inadequate assistance.\n"
    "Transactional Issues with Contributions or Withdrawals: Complaints "
    "concerning problems with financial transactions, such as difficulties "
    "with deposits, withdrawals, or account management.\n"
    "Analyze the provided complaint text and return the appropriate category "
    "based on its content."
)


# --------------------------------------------------------------------------------
# Ruta: /api/Clasificador   (la URL real incluye /api/ por convención Functions)
# --------------------------------------------------------------------------------
@app.route(route="Clasificador")
def Clasificador(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("➡️  Se disparó el trigger de Clasificador.")

    # -------------------------------------------------------------------------
    # 1. Validar que los clientes se hayan inicializado correctamente
    # -------------------------------------------------------------------------
    if not openai_client:
        logging.error("Cliente de OpenAI no inicializado. Revise la configuración.")
        return func.HttpResponse(
            "Error: El servicio de IA no está configurado.",
            status_code=500
        )

    # -------------------------------------------------------------------------
    # 2. Extraer parámetro 'Queja' (en URL ?Queja=... o en el cuerpo JSON)
    # -------------------------------------------------------------------------
    queja = req.params.get("Queja")
    if not queja:
        try:
            body = req.get_json()
            queja = body.get("Queja")
        except ValueError:
            pass

    if not queja:
        return func.HttpResponse(
            "⚠️  El API funciona, pero envíe el parámetro 'Queja' en URL o JSON.",
            status_code=200
        )

    # -------------------------------------------------------------------------
    # 3. Llamada al endpoint chat.completions usando el cliente global
    # -------------------------------------------------------------------------
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": queja}
            ],
            max_tokens=20,  # Suficiente para una categoría
            temperature=0.2
        )
        categoria = response.choices[0].message.content.strip()
        usage = response.usage
    except Exception as e:
        logging.error(f"❌ Error al llamar a Azure OpenAI: {e}")
        return func.HttpResponse("Error al procesar la solicitud con el modelo de IA.", status_code=500)

    # -------------------------------------------------------------------------
    # 4. Construir el resultado
    # -------------------------------------------------------------------------
    result = {
        "categoria": categoria,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens
    }
    json_result = json.dumps(result, ensure_ascii=False, indent=2)

    # -------------------------------------------------------------------------
    # 5. Guardar el resultado en Azure Blob Storage (si está configurado)
    # -------------------------------------------------------------------------
    if blob_service_client:
        try:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
            blob_path = f"LogsAzFnOpenAI/{filename}"

            blob_client = blob_service_client.get_blob_client("cr001", blob_path)
            blob_client.upload_blob(json_result, overwrite=True)

            logging.info(f"✅ Archivo '{blob_path}' guardado en Blob Storage.")
        except Exception as e:
            logging.error(f"❌ Error al guardar en Blob Storage: {e}")
    else:
        logging.warning("No se guardó en Blob Storage (cliente no configurado).")

    # -------------------------------------------------------------------------
    # 6. Devolver la respuesta al cliente
    # -------------------------------------------------------------------------
    return func.HttpResponse(
        json_result,
        mimetype="application/json",
        status_code=200
    )