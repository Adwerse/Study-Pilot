CREATE EXTENSION IF NOT EXISTS vector;

-- Keep vector(1536) in sync with Settings.EMBEDDING_DIMENSIONS and
-- .env.example EMBEDDING_DIMENSIONS. The runtime service validates dimensions
-- before inserting embeddings.

CREATE TABLE IF NOT EXISTS documents (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	title text NOT NULL,
	filename text NOT NULL,
	content_type text NOT NULL,
	size_bytes bigint NOT NULL,
	source_type varchar(20) NOT NULL DEFAULT 'upload',
	status varchar(20) NOT NULL DEFAULT 'processing',
	error_message text,
	chunks_count integer NOT NULL DEFAULT 0,
	tags jsonb,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT ck_documents_source_type CHECK (source_type IN ('upload', 'telegram', 'manual')),
	CONSTRAINT ck_documents_status CHECK (status IN ('processing', 'ready', 'failed'))
);

CREATE TABLE IF NOT EXISTS document_chunks (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	chunk_index integer NOT NULL,
	content text NOT NULL,
	token_count integer,
	metadata jsonb,
	embedding vector(1536) NOT NULL,
	created_at timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT ux_document_chunks_document_index UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS ix_documents_user_created_at
	ON documents(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_documents_user_status_created_at
	ON documents(user_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id
	ON document_chunks(document_id);

CREATE INDEX IF NOT EXISTS ix_document_chunks_user_document
	ON document_chunks(user_id, document_id);

CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_cosine
	ON document_chunks USING ivfflat (embedding vector_cosine_ops)
	WITH (lists = 100);
