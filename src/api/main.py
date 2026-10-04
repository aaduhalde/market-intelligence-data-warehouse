import os
import pyodbc
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader

app = FastAPI(title="Market Intelligence Data Warehouse API")

# --- SEGURIDAD ---
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
API_SECRET_KEY = os.getenv("MY_API_SECRET_KEY")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Acceso Denegado: Credenciales inválidas"
        )
    return api_key

# --- BASE DE DATOS ---
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DB = os.getenv("SQL_DB")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

disponibles = pyodbc.drivers()
driver_elegido = next(
    (d for d in disponibles if "ODBC Driver 18" in d),
    next((d for d in disponibles if "ODBC Driver 17" in d), 
         next((d for d in disponibles if "SQL Server" in d), "ODBC Driver 17 for SQL Server"))
)

CONNECTION_STRING = (
    f"Driver={{{driver_elegido}}};Server={SQL_SERVER},1433;Database={SQL_DB};"
    f"Uid={SQL_USER};Pwd={SQL_PASSWORD};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
)

# --- RUTAS ---
@app.get("/")
def read_root():
    return {"status": "market-intel-api en ejecución"}

@app.get("/db/test-conexion", dependencies=[Depends(verify_api_key)])
def test_conexion():
    if not all([SQL_SERVER, SQL_DB, SQL_USER, SQL_PASSWORD]):
        raise HTTPException(status_code=500, detail="Faltan variables de entorno.")
    
    try:
        with pyodbc.connect(CONNECTION_STRING) as conn:
            return {
                "status": "Conexión exitosa",
                "database": SQL_DB,
                "server": SQL_SERVER
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar: {str(e)}")