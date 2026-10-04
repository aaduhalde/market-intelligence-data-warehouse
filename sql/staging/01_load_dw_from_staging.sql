-- =============================================================================
-- MARKET INTELLIGENCE DATA PLATFORM
-- File: sql/staging/01_load_dw_from_staging.sql
-- Description: ETL/ELT - Carga Set-Based de Staging al Modelo Estrella
-- =============================================================================
-- 1. Cargar Dimensión Empresa
INSERT INTO warehouse.dim_empresa (nombre_empresa, nombre_empresa_raw)
SELECT DISTINCT 
    ISNULL(stg.nombre_empresa, 'No especificado'), 
    ISNULL(stg.nombre_empresa_raw, 'No especificado')
FROM staging.stg_observacion_oferta stg
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.dim_empresa e 
    WHERE e.nombre_empresa = ISNULL(stg.nombre_empresa, 'No especificado')
);
GO

-- 2. Cargar Dimensión Ubicación
INSERT INTO warehouse.dim_ubicacion (ubicacion_raw, ciudad, pais, market_tier)
SELECT DISTINCT 
    stg.ubicacion_raw, 
    ISNULL(stg.ciudad, 'No especificado'), 
    ISNULL(stg.pais, 'No especificado'), 
    ISNULL(stg.market_tier, 'Unclassified')
FROM staging.stg_observacion_oferta stg
WHERE stg.ubicacion_raw IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM warehouse.dim_ubicacion u 
    WHERE u.ubicacion_raw = stg.ubicacion_raw
);
GO

-- 3. Cargar Dimensión Rol
INSERT INTO warehouse.dim_rol (nombre_rol, familia_rol, nivel_prioridad)
SELECT DISTINCT 
    ISNULL(stg.nombre_rol, 'Other / Unclassified'), 
    ISNULL(stg.familia_rol, 'Unclassified'), 
    CASE 
        WHEN stg.familia_rol = 'primary' THEN 1
        WHEN stg.familia_rol = 'secondary' THEN 2
        ELSE 3
    END AS nivel_prioridad
FROM staging.stg_observacion_oferta stg
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.dim_rol r 
    WHERE r.nombre_rol = ISNULL(stg.nombre_rol, 'Other / Unclassified')
      AND r.familia_rol = ISNULL(stg.familia_rol, 'Unclassified')
);
GO

-- 4. Cargar Dimensión Modalidad
INSERT INTO warehouse.dim_modalidad (modalidad_trabajo)
SELECT DISTINCT ISNULL(stg.modalidad_trabajo, 'No especificado')
FROM staging.stg_observacion_oferta stg
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.dim_modalidad m 
    WHERE m.modalidad_trabajo = ISNULL(stg.modalidad_trabajo, 'No especificado')
);
GO

-- 5. Cargar Dimensión Skill (Enriquecida dinámicamente desde staging.stg_skill_taxonomy)
INSERT INTO warehouse.dim_skill (nombre_skill, categoria_skill)
SELECT DISTINCT 
    TRIM(s.value) AS nombre_skill,
    ISNULL(NULLIF(TRIM(tax.categoria_skill), ''), 'Unassigned') AS categoria_skill
FROM staging.stg_observacion_oferta stg
CROSS APPLY OPENJSON(stg.skills_array) s
LEFT JOIN staging.stg_skill_taxonomy tax
    ON LOWER(TRIM(tax.nombre_skill)) = LOWER(TRIM(s.value))
WHERE stg.skills_array IS NOT NULL
  AND ISJSON(stg.skills_array) = 1
  AND TRIM(s.value) <> ''
  AND NOT EXISTS (
    SELECT 1 FROM warehouse.dim_skill sk 
    WHERE sk.nombre_skill = TRIM(s.value)
);

-- Actualizar categorías de skills existentes si antes estaban como 'Unassigned' o NULL
UPDATE sk
SET sk.categoria_skill = ISNULL(NULLIF(TRIM(tax.categoria_skill), ''), 'Unassigned')
FROM warehouse.dim_skill sk
INNER JOIN staging.stg_skill_taxonomy tax
    ON LOWER(TRIM(tax.nombre_skill)) = LOWER(TRIM(sk.nombre_skill))
WHERE sk.categoria_skill = 'Unassigned' OR sk.categoria_skill IS NULL OR TRIM(sk.categoria_skill) = '';
GO

-- 6. Cargar Tabla de Hechos (fact_observacion_oferta)
INSERT INTO warehouse.fact_observacion_oferta (
    proveedor_ingesta,
    source_job_id,
    titulo_puesto,
    rol_id,
    empresa_id,
    ubicacion_id,
    modalidad_id,
    fecha_captura_id,
    fecha_publicacion_id,
    plataforma_origen,
    seniority,
    requisito_ingles,
    search_query,
    descripcion_oferta,
    url_oferta,
    ingestion_timestamp_utc
)
SELECT 
    stg.proveedor_ingesta,
    stg.source_job_id,
    stg.titulo_puesto,
    ISNULL(r.rol_id, -1) AS rol_id,
    ISNULL(e.empresa_id, -1) AS empresa_id,
    ISNULL(u.ubicacion_id, -1) AS ubicacion_id,
    ISNULL(m.modalidad_id, -1) AS modalidad_id,
    ISNULL(stg.fecha_captura_id, 19000101) AS fecha_captura_id,
    ISNULL(stg.fecha_publicacion_id, 19000101) AS fecha_publicacion_id,
    stg.plataforma_origen,
    ISNULL(stg.seniority, 'No data') AS seniority,
    ISNULL(stg.requisito_ingles, 'No data') AS requisito_ingles,
    stg.search_query,
    stg.descripcion_oferta,
    stg.url_oferta,
    stg.ingestion_timestamp_utc
FROM staging.stg_observacion_oferta stg
LEFT JOIN warehouse.dim_empresa e 
    ON e.nombre_empresa = ISNULL(stg.nombre_empresa, 'No especificado')
LEFT JOIN warehouse.dim_ubicacion u 
    ON u.ubicacion_raw = stg.ubicacion_raw
LEFT JOIN warehouse.dim_modalidad m 
    ON m.modalidad_trabajo = ISNULL(stg.modalidad_trabajo, 'No especificado')
LEFT JOIN warehouse.dim_rol r 
    ON r.nombre_rol = ISNULL(stg.nombre_rol, 'Other / Unclassified')
   AND r.familia_rol = ISNULL(stg.familia_rol, 'Unclassified')
WHERE NOT EXISTS (
    SELECT 1 FROM warehouse.fact_observacion_oferta f
    WHERE f.proveedor_ingesta = stg.proveedor_ingesta
      AND f.source_job_id = stg.source_job_id
      AND f.fecha_captura_id = stg.fecha_captura_id
);
GO

-- 7. Cargar Tabla Puente (rel_oferta_skill)
INSERT INTO warehouse.rel_oferta_skill (observacion_oferta_id, skill_id)
SELECT DISTINCT
    f.observacion_oferta_id,
    sk.skill_id
FROM staging.stg_observacion_oferta stg
INNER JOIN warehouse.fact_observacion_oferta f
    ON f.proveedor_ingesta = stg.proveedor_ingesta
   AND f.source_job_id = stg.source_job_id
   AND f.fecha_captura_id = stg.fecha_captura_id
CROSS APPLY OPENJSON(stg.skills_array) s
INNER JOIN warehouse.dim_skill sk
    ON LOWER(TRIM(sk.nombre_skill)) = LOWER(TRIM(s.value))
WHERE stg.skills_array IS NOT NULL
  AND ISJSON(stg.skills_array) = 1
  AND NOT EXISTS (
    SELECT 1 FROM warehouse.rel_oferta_skill ros
    WHERE ros.observacion_oferta_id = f.observacion_oferta_id
      AND ros.skill_id = sk.skill_id
);
GO