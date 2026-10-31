CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    original_name TEXT NOT NULL,
    size INTEGER NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_type TEXT NOT NULL
);

DO $$
BEGIN
    IF to_regclass('public.documents') IS NOT NULL THEN
        INSERT INTO images (filename, original_name, size, upload_time, file_type)
        SELECT stored_name, original_name, size_bytes, uploaded_at, extension
        FROM documents
        WHERE NOT EXISTS (
            SELECT 1 FROM images WHERE images.filename = documents.stored_name
        );
    END IF;
END $$;
