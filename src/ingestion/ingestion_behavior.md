# Comportamiento de la Ingesta Incremental (`JobMarketIngestion`)

Este documento explica cómo opera el módulo de ingesta de ofertas laborales (`src/ingestion/...`), su impacto en el consumo de créditos de SerpAPI, la gestión de duplicados y la optimización automática de ventanas de búsqueda.

---

## 1. Consumo de Créditos en SerpAPI

* **¿Se consumen créditos en cada ejecución?** **Sí.**
* **Funcionamiento interno:** Dentro de `execute_ingestion()`, el script itera sobre la matriz de `markets × role_groups` y ejecuta una llamada real a `GoogleSearch(params).get_dict()` por cada combinación.
* **Impacto:** SerpAPI factura por cada consulta realizada, independientemente de si Google Jobs devuelve ofertas nuevas, registros duplicados o resultados vacíos. Si la configuración define 16 combinaciones (`mercados × roles`), cada ejecución completa consumirá **16 créditos**.
* **Recomendación:** Evitar ejecuciones manuales repetidas en intervalos cortos y programar el pipeline mediante tareas automatizadas (por ejemplo, una vez al día).

---

## 2. Deduplicación y Almacenamiento en `data/1_raw/`

* **¿Se guardan archivos con ofertas repetidas?** **No.**
* **Control de estado (`data/ingestion_state.json`):**
  1. Al iniciar (si `force_full_refresh=False`), `_load_state()` carga en memoria el conjunto `processed_job_ids` con todos los identificadores ingestados previamente.
  2. Para cada oferta recibida en `jobs_results`, el script evalúa su identificador único:
     ```python
     job_id = job.get("job_id") or f"{job.get('title')}_{job.get('company_name')}"
     ```
  3. Solo los registros cuyo `job_id` no exista en `self.processed_ids` se añaden a `new_jobs` y se registran en el estado.
  4. **Escritura condicional:** Si `new_jobs` contiene registros, se genera el archivo `raw_<mercado>_<rol>_<timestamp>.json` en `data/1_raw/`. Si todos los resultados ya existían, no se crea ningún archivo y se registra en el log:
     ```text
     Skipping [<grupo> - <mercado>]: Registros duplicados en el estado.
     ```

### Consideración técnica (Fallback de ID)
En caso de que una oferta en la respuesta de la API no incluya el campo `job_id`, el script construye un identificador compuesto (`title_company_name`). Si el título o el nombre de la empresa presentan variaciones mínimas en ejecuciones posteriores, la oferta podría tratarse como un registro nuevo.

---

## 3. Optimización Incremental de Ventana Temporal

* **¿El script ajusta su búsqueda en ejecuciones posteriores?** **Sí.**
* **Cálculo automático (`_determine_date_filter()`):**
  Antes de iniciar las consultas, el script lee `last_update_utc` desde `data/ingestion_state.json` y calcula los días transcurridos (`delta_days = (now_utc - last_update).days`) para asignar el filtro `date_posted`:

| Condición (`delta_days`) | Filtro asignado (`chips`) | Comportamiento en Google Jobs |
| :--- | :--- | :--- |
| Primera ejecución o `force_full_refresh=True` | `month` *(sin chip)* | Búsqueda amplia por defecto (último mes). |
| `delta_days <= 1` | `date_posted:today` | Filtra ofertas publicadas en las últimas 24 horas. |
| `delta_days <= 3` | `date_posted:3days` | Filtra ofertas de los últimos 3 días. |
| `delta_days <= 7` | `date_posted:week` | Filtra ofertas de la última semana. |
| `delta_days > 7` | `month` *(sin chip)* | Restablece la búsqueda amplia por defecto. |

### Consideraciones técnicas a tener en cuenta
1. **Cálculo en días enteros (`.days`):** En Python, `(now_utc - last_update).days` trunca las horas hacia abajo. Por ejemplo, si han pasado 22 horas desde la última ingesta, `delta_days` será `0` y el filtro aplicado será `today`.
2. **Persistencia del estado (`_save_state()`):** El archivo `ingestion_state.json` se actualiza al finalizar todo el bucle de ingesta. Si el proceso se interrumpe abruptamente a mitad de ejecución (por ejemplo, `KeyboardInterrupt` o corte de red), los archivos JSON ya escritos en `data/1_raw/` quedarán guardados, pero sus IDs no se registrarán en el estado hasta completar una corrida exitosa.