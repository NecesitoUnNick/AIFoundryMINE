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

# --------------------------------------------------------------------------------
# Ruta: /api/Clasificador   (la URL real incluye /api/ por convención Functions)
# --------------------------------------------------------------------------------
@app.route(route="Clasificador")
def Clasificador(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("➡️  Se disparó el trigger de Clasificador.")

    # -------------------------------------------------------------------------
    # 1. Extraer parámetro 'Queja' (en URL ?Queja=... o en el cuerpo JSON)
    # -------------------------------------------------------------------------
    queja = req.params.get("Queja")
    if not queja:
        try:
            body = req.get_json()              # Intenta leer JSON del cuerpo
            queja = body.get("Queja")
        except ValueError:
            pass                               # No era JSON válido; queja seguirá en None

    # -------------------------------------------------------------------------
    # 2. Si recibimos la queja, lanzamos el modelo; si no, devolvemos mensaje.
    # -------------------------------------------------------------------------
    if not queja:
        return func.HttpResponse(
            "⚠️  El API funciona, pero envíe el parámetro 'Queja' en URL o JSON.",
            status_code=200
        )

    # -------------------------------------------------------------------------
    # 3. Instanciar el cliente AzureOpenAI (usa variables de entorno seguras)
    # -------------------------------------------------------------------------
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2025-01-01-preview",                # Versión de API
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    # Prompt del sistema con las instrucciones de clasificación
    system_prompt = (
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

    # -------------------------------------------------------------------------
    # 4. Llamada al endpoint chat.completions
    #    • model  : nombre del deployment configurado en Azure OpenAI
    #    • temperature: 1.0 (más creatividad); ajústalo si quieres respuestas
    #                   más consistentes (p.ej., 0.2)
    # -------------------------------------------------------------------------
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL"),  # p.ej. "gpt-4o-nano"
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": queja}
        ],
        max_completion_tokens=50, #OJO, ACÁ evitamos sorpresas para la salida, pocos tokens de salida
        temperature=0.25
    )

    # -------------------------------------------------------------------------
    # 5. Construir el resultado con la categoría y uso de tokens
    # -------------------------------------------------------------------------
    result = {
        "categoria": response.choices[0].message.content.strip(),
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens
    }

    # Conviértelo a string JSON bonito (acentos OK con ensure_ascii=False)
    json_result = json.dumps(result, ensure_ascii=False, indent=2)

    # -------------------------------------------------------------------------
    # 6. Guardar el resultado en Azure Blob Storage
    # -------------------------------------------------------------------------
    try:
        # Nombre archivo : YYYYMMDD_HHMMSS.json
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
        blob_path = f"LogsAzFnOpenAI/{filename}"

        # Cadena de conexión en variable de entorno AZURE_STORAGE_CONNECTION_STRING
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        blob_service = BlobServiceClient.from_connection_string(conn_str)

        # Subir al contenedor cr001
        blob_client = blob_service.get_blob_client("cr001", blob_path)
        blob_client.upload_blob(json_result, overwrite=True)

        logging.info(f"✅ Archivo '{blob_path}' guardado en Blob Storage.")
    except Exception as e:
        logging.error(f"❌ Error al guardar en Blob Storage: {e}")

    # -------------------------------------------------------------------------
    # 7. Devolver la respuesta al cliente
    # -------------------------------------------------------------------------
    return func.HttpResponse(
        json_result,
        mimetype="application/json",
        status_code=200
    )