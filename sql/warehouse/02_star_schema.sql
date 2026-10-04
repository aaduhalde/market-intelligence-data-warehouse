-- =============================================================================
-- MARKET INTELLIGENCE DATA PLATFORM
-- File: 02_star_schema.sql
-- Description: Observation Fact Model for Job Market Snapshots
-- Target Engine: SQL Server 2019+ / Azure SQL Database
-- =============================================================================
-- -----------------------------------------------------------------------------
-- 1. TABLAS DE DIMENSIÓN (ESQUEMA WAREHOUSE)
-- -----------------------------------------------------------------------------

-- BR-005: Normalización de Empresa
IF OBJECT_ID('warehouse.dim_empresa', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.dim_empresa (
        empresa_id INT IDENTITY(1,1) PRIMARY KEY,
        nombre_empresa VARCHAR(255) NOT NULL,
        nombre_empresa_raw VARCHAR(255) NOT NULL,
        CONSTRAINT UQ_dim_empresa_nombre UNIQUE (nombre_empresa)
    );
END
GO

-- BR-006 & BR-007: Ubicación y Clasificación de Mercado
IF OBJECT_ID('warehouse.dim_ubicacion', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.dim_ubicacion (
        ubicacion_id INT IDENTITY(1,1) PRIMARY KEY,
        ubicacion_raw VARCHAR(255) NOT NULL,
        ciudad VARCHAR(100) NULL,
        pais VARCHAR(100) NULL,
        market_tier VARCHAR(50) NOT NULL DEFAULT 'Unclassified'
    );
END
GO

-- BR-008: Modalidad de Trabajo
IF OBJECT_ID('warehouse.dim_modalidad', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.dim_modalidad (
        modalidad_id INT IDENTITY(1,1) PRIMARY KEY,
        modalidad_trabajo VARCHAR(50) NOT NULL UNIQUE
    );
END
GO

-- BR-004: Taxonomía de Roles Normalizados
IF OBJECT_ID('warehouse.dim_rol', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.dim_rol (
        rol_id INT IDENTITY(1,1) PRIMARY KEY,
        nombre_rol VARCHAR(150) NOT NULL UNIQUE,
        familia_rol VARCHAR(50) NOT NULL,
        nivel_prioridad TINYINT NOT NULL DEFAULT 3
    );
END
GO

-- BR-015 & BR-017: Habilidades y Categorías Técnicas
IF OBJECT_ID('warehouse.dim_skill', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.dim_skill (
        skill_id INT IDENTITY(1,1) PRIMARY KEY,
        nombre_skill VARCHAR(100) NOT NULL UNIQUE,
        categoria_skill VARCHAR(100) NOT NULL DEFAULT 'Unknown'
    );
END
GO

-- BR-010 & BR-011: Dimensión Calendario Única (Role-Playing Dimension)
IF OBJECT_ID('warehouse.dim_fecha', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.dim_fecha (
        fecha_id INT PRIMARY KEY,                  -- Formato YYYYMMDD
        fecha DATE NOT NULL,
        anio INT NOT NULL,
        mes INT NOT NULL,
        nombre_mes VARCHAR(20) NOT NULL,
        trimestre INT NOT NULL,
        dia_semana VARCHAR(20) NOT NULL
    );
END
GO

-- -----------------------------------------------------------------------------
-- 2. TABLA PRINCIPAL DE HECHOS (OBSERVATION FACT TABLE)
-- -----------------------------------------------------------------------------

IF OBJECT_ID('warehouse.fact_observacion_oferta', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.fact_observacion_oferta (
        observacion_oferta_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        
        -- Identidad y Origen
        proveedor_ingesta VARCHAR(50) NOT NULL,
        source_job_id VARCHAR(1000) NOT NULL,
        titulo_puesto VARCHAR(255) NOT NULL,
        
        -- Foreign Keys a Dimensiones
        rol_id INT NULL FOREIGN KEY REFERENCES warehouse.dim_rol(rol_id),
        empresa_id INT NOT NULL FOREIGN KEY REFERENCES warehouse.dim_empresa(empresa_id),
        ubicacion_id INT NULL FOREIGN KEY REFERENCES warehouse.dim_ubicacion(ubicacion_id),
        modalidad_id INT NULL FOREIGN KEY REFERENCES warehouse.dim_modalidad(modalidad_id),
        
        -- Fechas (Role-Playing Dimensions)
        fecha_captura_id INT NOT NULL FOREIGN KEY REFERENCES warehouse.dim_fecha(fecha_id),
        fecha_publicacion_id INT NULL FOREIGN KEY REFERENCES warehouse.dim_fecha(fecha_id),
        
        -- Atributos Desagregados
        plataforma_origen VARCHAR(100) NOT NULL DEFAULT 'Unknown',
        seniority VARCHAR(50) NULL,
        requisito_ingles VARCHAR(50) NULL,
        
        -- Trazabilidad y Metadatos
        search_query VARCHAR(500) NULL,
        descripcion_oferta VARCHAR(MAX) NULL,
        url_oferta VARCHAR(MAX) NULL,
        ingestion_timestamp_utc DATETIME2 NOT NULL,

        -- Restricción de Invariabilidad por Snapshot Multi-Fuente
        CONSTRAINT UQ_observacion_snapshot UNIQUE (
            proveedor_ingesta,
            source_job_id,
            fecha_captura_id
        )
    );
END
GO

-- -----------------------------------------------------------------------------
-- 3. TABLA PUENTE / RELACIÓN MUCHOS A MUCHOS (BRIDGE TABLE)
-- -----------------------------------------------------------------------------

IF OBJECT_ID('warehouse.rel_oferta_skill', 'U') IS NULL
BEGIN
    CREATE TABLE warehouse.rel_oferta_skill (
        observacion_oferta_id BIGINT NOT NULL,
        skill_id INT NOT NULL,
        PRIMARY KEY (observacion_oferta_id, skill_id),
        FOREIGN KEY (observacion_oferta_id) REFERENCES warehouse.fact_observacion_oferta(observacion_oferta_id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES warehouse.dim_skill(skill_id)
    );
END
GO

-- -----------------------------------------------------------------------------
-- 4. POBLADO INICIAL DE CATÁLOGOS ESTÁTICOS
-- -----------------------------------------------------------------------------

-- Modalidades Estándar
INSERT INTO warehouse.dim_modalidad (modalidad_trabajo)
SELECT m FROM (VALUES ('Remote'), ('Hybrid'), ('Onsite'), ('Unspecified')) AS temp(m)
WHERE NOT EXISTS (SELECT 1 FROM warehouse.dim_modalidad WHERE modalidad_trabajo = temp.m);
GO

-- Poblado de Dimensión Fecha Vectorizado (2024 - 2030)
IF NOT EXISTS (SELECT TOP 1 1 FROM warehouse.dim_fecha)
BEGIN
    DECLARE @StartDate DATE = '2024-01-01';
    DECLARE @EndDate   DATE = '2030-12-31';

    WITH N1(n) AS (
        SELECT 1 UNION ALL SELECT 1 UNION ALL SELECT 1 UNION ALL SELECT 1 UNION ALL 
        SELECT 1 UNION ALL SELECT 1 UNION ALL SELECT 1 UNION ALL SELECT 1 UNION ALL 
        SELECT 1 UNION ALL SELECT 1
    ),
    N2(n) AS (SELECT 1 FROM N1 a CROSS JOIN N1 b),
    N3(n) AS (SELECT 1 FROM N1 a CROSS JOIN N2 b),
    N4(n) AS (SELECT 1 FROM N2 a CROSS JOIN N2 b),
    Tally(N) AS (SELECT ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 FROM N4),
    Dates(Fecha) AS (
        SELECT DATEADD(DAY, N, @StartDate)
        FROM Tally
        WHERE DATEADD(DAY, N, @StartDate) <= @EndDate
    )
    INSERT INTO warehouse.dim_fecha (
        fecha_id,
        fecha,
        anio,
        mes,
        nombre_mes,
        trimestre,
        dia_semana
    )
    SELECT 
        CAST(CONVERT(VARCHAR(8), d.Fecha, 112) AS INT) AS fecha_id,
        d.Fecha AS fecha,
        YEAR(d.Fecha) AS anio,
        MONTH(d.Fecha) AS mes,
        DATENAME(MONTH, d.Fecha) AS nombre_mes,
        DATEPART(QUARTER, d.Fecha) AS trimestre,
        DATENAME(WEEKDAY, d.Fecha) AS dia_semana
    FROM Dates d;

    PRINT 'Dimensión Calendario [warehouse.dim_fecha] poblada exitosamente con 2,557 días.';
END
GO