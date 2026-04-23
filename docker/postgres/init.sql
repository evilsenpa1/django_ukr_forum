-- docker/postgres/init.sql

-- Создаем расширение pg_trgm (trigram)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Создаем расширение unaccent (опционально, для поиска без учета диакритики)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Проверяем что установилось
\dx