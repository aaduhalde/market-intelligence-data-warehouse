-- -----------------------------------------------------------------------------
-- 1. VISTA: Demanda General de Skills en el Mercado (BR-029)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('analytics.vw_market_skill_demand', 'V') IS NOT NULL
    DROP VIEW analytics.vw_market_skill_demand;
GO

CREATE VIEW analytics.vw_market_skill_demand AS
WITH TotalJobs AS (
    SELECT COUNT(DISTINCT observacion_oferta_id) AS total_ofertas
    FROM warehouse.fact_observacion_oferta
)
SELECT 
    sk.skill_id,
    sk.nombre_skill,
    sk.categoria_skill,
    COUNT(DISTINCT ros.observacion_oferta_id) AS total_menciones,
    tj.total_ofertas,
    ROUND(
        (CAST(COUNT(DISTINCT ros.observacion_oferta_id) AS FLOAT) / NULLIF(tj.total_ofertas, 0)) * 100.0, 
        2
    ) AS market_skill_demand_pct
FROM warehouse.dim_skill sk
INNER JOIN warehouse.rel_oferta_skill ros ON sk.skill_id = ros.skill_id
CROSS JOIN TotalJobs tj
GROUP BY sk.skill_id, sk.nombre_skill, sk.categoria_skill, tj.total_ofertas;
GO

-- -----------------------------------------------------------------------------
-- 2. VISTA: Consolidado de Inteligencia de Mercado (BRD-04, BR-007, BR-022)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('analytics.vw_market_intelligence_summary', 'V') IS NOT NULL
    DROP VIEW analytics.vw_market_intelligence_summary;
GO

CREATE VIEW analytics.vw_market_intelligence_summary AS
SELECT 
    f.observacion_oferta_id,
    f.proveedor_ingesta,
    f.source_job_id,
    f.titulo_puesto,
    r.nombre_rol,
    r.familia_rol,
    e.nombre_empresa,
    u.ubicacion_raw,
    u.market_tier,
    m.modalidad_trabajo,
    f.seniority,
    f.requisito_ingles,
    f.fecha_captura_id
FROM warehouse.fact_observacion_oferta f
LEFT JOIN warehouse.dim_rol r ON f.rol_id = r.rol_id
LEFT JOIN warehouse.dim_empresa e ON f.empresa_id = e.empresa_id
LEFT JOIN warehouse.dim_ubicacion u ON f.ubicacion_id = u.ubicacion_id
LEFT JOIN warehouse.dim_modalidad m ON f.modalidad_id = m.modalidad_id;
GO