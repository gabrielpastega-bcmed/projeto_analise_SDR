-- ============================================
-- Migration: Create octadesk_analysis_results table
-- Purpose: Store LLM analysis results in PostgreSQL instead of BigQuery
-- ============================================

-- ============================================
-- Table: octadesk_analysis_results
-- Purpose: Store chat analysis from Gemini LLM
-- ============================================

CREATE TABLE IF NOT EXISTS octadesk_analysis_results (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Chat Identification
    chat_id VARCHAR(255) UNIQUE NOT NULL,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- ============================================
    -- CX (Customer Experience) Metrics
    -- ============================================
    cx_sentiment VARCHAR(50),                    -- positivo, neutro, negativo
    cx_humanization_score INTEGER CHECK (cx_humanization_score BETWEEN 1 AND 5),
    cx_nps_prediction INTEGER CHECK (cx_nps_prediction BETWEEN 0 AND 10),
    cx_resolution_status VARCHAR(50),            -- resolvido, não_resolvido, pendente
    cx_personalization_used BOOLEAN,
    cx_satisfaction_comment TEXT,
    
    -- ============================================
    -- Product Metrics
    -- ============================================
    product_names TEXT[],                        -- Array de produtos mencionados
    product_interest_level VARCHAR(50),          -- alto, médio, baixo
    product_technical_questions BOOLEAN,
    product_price_discussed BOOLEAN,
    product_competitor_mentioned BOOLEAN,
    product_comparison_requested BOOLEAN,
    
    -- ============================================
    -- Sales Metrics
    -- ============================================
    sales_stage VARCHAR(50),                     -- prospecção, qualificação, proposta, negociação, fechamento
    sales_objections_handled BOOLEAN,
    sales_objections_list TEXT[],                -- Array de objeções identificadas
    sales_urgency_level VARCHAR(50),             -- alto, médio, baixo
    sales_converted BOOLEAN,
    sales_next_steps TEXT,
    
    -- ============================================
    -- QA (Quality Assurance) Metrics
    -- ============================================
    qa_script_followed BOOLEAN,
    qa_required_info_collected BOOLEAN,
    qa_response_time_adequate BOOLEAN,
    qa_professionalism_score INTEGER CHECK (qa_professionalism_score BETWEEN 1 AND 5),
    qa_compliance_issues TEXT[],                 -- Array de problemas de compliance
    qa_recommendations TEXT,
    
    -- ============================================
    -- Performance & Metadata
    -- ============================================
    processing_time_ms INTEGER,
    model_version VARCHAR(50) DEFAULT 'gemini-2.5-flash',
    api_cost_usd DECIMAL(10, 6),
    cache_hit BOOLEAN DEFAULT FALSE,
    
    -- ============================================
    -- Raw Data (for debugging/reprocessing)
    -- ============================================
    raw_transcript TEXT,
    full_response JSONB,                         -- Complete LLM response
    
    -- ============================================
    -- Audit
    -- ============================================
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Time-based queries (dashboard filters)
CREATE INDEX IF NOT EXISTS idx_analysis_analyzed_at 
    ON octadesk_analysis_results(analyzed_at DESC);

-- Chat lookup
CREATE INDEX IF NOT EXISTS idx_analysis_chat_id 
    ON octadesk_analysis_results(chat_id);

-- CX metrics (common filters)
CREATE INDEX IF NOT EXISTS idx_analysis_sentiment 
    ON octadesk_analysis_results(cx_sentiment);

CREATE INDEX IF NOT EXISTS idx_analysis_nps 
    ON octadesk_analysis_results(cx_nps_prediction);

-- Sales metrics (conversion analysis)
CREATE INDEX IF NOT EXISTS idx_analysis_converted 
    ON octadesk_analysis_results(sales_converted);

CREATE INDEX IF NOT EXISTS idx_analysis_sales_stage 
    ON octadesk_analysis_results(sales_stage);

-- Product analysis
CREATE INDEX IF NOT EXISTS idx_analysis_products 
    ON octadesk_analysis_results USING GIN(product_names);

-- Full-text search on transcript
CREATE INDEX IF NOT EXISTS idx_analysis_transcript_search 
    ON octadesk_analysis_results USING GIN(to_tsvector('portuguese', raw_transcript));

-- JSONB queries on full response
CREATE INDEX IF NOT EXISTS idx_analysis_jsonb 
    ON octadesk_analysis_results USING GIN(full_response);

-- ============================================
-- Trigger: Update timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_analysis_updated_at 
    BEFORE UPDATE ON octadesk_analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Comments for Documentation
-- ============================================

COMMENT ON TABLE octadesk_analysis_results IS 
    'Stores qualitative analysis results from Gemini LLM for Octadesk chats';

COMMENT ON COLUMN octadesk_analysis_results.chat_id IS 
    'Unique identifier from Octadesk chat';

COMMENT ON COLUMN octadesk_analysis_results.cx_humanization_score IS 
    '1=robotic, 5=very humanized';

COMMENT ON COLUMN octadesk_analysis_results.cx_nps_prediction IS 
    'Predicted Net Promoter Score (0-10)';

COMMENT ON COLUMN octadesk_analysis_results.full_response IS 
    'Complete JSON response from Gemini API for debugging';

-- ============================================
-- Grant Permissions (adjust as needed)
-- ============================================

-- Grant to application user
-- GRANT SELECT, INSERT, UPDATE ON octadesk_analysis_results TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE octadesk_analysis_results_id_seq TO your_app_user;
