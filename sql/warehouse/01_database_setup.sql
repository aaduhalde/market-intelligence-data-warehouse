-- =============================================================================
-- MARKET INTELLIGENCE DATA PLATFORM
-- File: 01_database_setup.sql
-- Phase: Architecture & Base Setup
-- Target Engine: Azure SQL Database / SQL Server 2019+
-- =============================================================================
-- -----------------------------------------------------------------------------
-- 1. ESQUEMAS LÓGICOS DE ARQUITECTURA
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'staging')
    EXEC('CREATE SCHEMA staging AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'warehouse')
    EXEC('CREATE SCHEMA warehouse AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'analytics')
    EXEC('CREATE SCHEMA analytics AUTHORIZATION dbo;');
GO

-- -----------------------------------------------------------------------------
-- 2. TABLA LANDING/STAGING (Carga incremental desde Python)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('staging.stg_observacion_oferta', 'U') IS NOT NULL
    DROP TABLE staging.stg_observacion_oferta;
GO

CREATE TABLE staging.stg_observacion_oferta (
    stg_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    
    -- Datos de Origen y Empresa
    proveedor_ingesta VARCHAR(50) NOT NULL,
    source_job_id VARCHAR(1000) NOT NULL,
    titulo_puesto VARCHAR(255) NOT NULL,
    nombre_empresa VARCHAR(255) NOT NULL,
    nombre_empresa_raw VARCHAR(255) NOT NULL,
    
    -- Ubicación y Modalidad
    ubicacion_raw VARCHAR(255) NOT NULL,
    ciudad VARCHAR(100) NULL,
    pais VARCHAR(100) NULL,
    market_tier VARCHAR(50) NOT NULL DEFAULT 'Unclassified',
    modalidad_trabajo VARCHAR(50) NOT NULL,
    
    -- Taxonomía y Atributos
    nombre_rol VARCHAR(150) NULL,
    familia_rol VARCHAR(50) NULL,
    seniority VARCHAR(50) NULL,
    requisito_ingles VARCHAR(50) NULL,
    
    -- Fechas
    fecha_captura DATE NOT NULL,
    fecha_captura_id INT NOT NULL,
    fecha_publicacion DATE NULL,
    fecha_publicacion_id INT NULL,
    
    -- Metadatos
    plataforma_origen VARCHAR(100) NOT NULL DEFAULT 'Unknown',
    search_query VARCHAR(500) NULL,
    descripcion_oferta VARCHAR(MAX) NULL,
    url_oferta VARCHAR(MAX) NULL,
    skills_array VARCHAR(MAX) NULL,
    ingestion_timestamp_utc DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);
GO