CREATE TABLE public.admins (
  id uuid NOT NULL,
  telegram_chat_id text NOT NULL,
  username text NOT NULL,
  CONSTRAINT admins_pkey PRIMARY KEY (id),
  CONSTRAINT admins_telegram_chat_id_key UNIQUE (telegram_chat_id)
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_admins_telegram_chat_id ON public.admins USING btree (telegram_chat_id) TABLESPACE pg_default;

CREATE TABLE public.faq_embeddings (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  question text NOT NULL,
  answer text NOT NULL,
  embedding vector(1536) NULL,  -- Ensure vector type is defined
  CONSTRAINT faq_embeddings_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_faq_embeddings_vector ON public.faq_embeddings USING ivfflat (embedding vector_cosine_ops) TABLESPACE pg_default;

CREATE TABLE public.issues (
  id uuid NOT NULL,
  telegram_chat_id text NOT NULL,
  username text NOT NULL,
  status text NOT NULL,
  CONSTRAINT issues_pkey PRIMARY KEY (id),
  CONSTRAINT issues_status_check CHECK (
    status = ANY (ARRAY['open'::text, 'manual'::text, 'closed'::text])
  )
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_issues_telegram_chat_id ON public.issues USING btree (telegram_chat_id) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_issues_status ON public.issues USING btree (status) TABLESPACE pg_default;

CREATE TABLE public.messages (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  issue_id uuid NOT NULL,
  from_user text NOT NULL,
  text text NOT NULL,
  timestamp bigint NOT NULL,
  CONSTRAINT messages_pkey PRIMARY KEY (id),
  CONSTRAINT messages_issue_id_fkey FOREIGN KEY (issue_id) REFERENCES issues (id) ON DELETE CASCADE
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_messages_issue_id ON public.messages USING btree (issue_id) TABLESPACE pg_default;

CREATE OR REPLACE FUNCTION match_faq_embeddings(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fe.id,
        fe.question,
        fe.answer,
        1 - (fe.embedding <=> query_embedding) AS similarity
    FROM
        faq_embeddings fe
    WHERE
        1 - (fe.embedding <=> query_embedding) > match_threshold
    ORDER BY
        fe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;