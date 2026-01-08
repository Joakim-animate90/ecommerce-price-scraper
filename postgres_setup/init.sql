-- PostgreSQL Database Initialization Script
-- E-commerce Price Scraper Database Schema

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- ============================================================================
-- MAIN LAPTOPS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS laptops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Platform and identification
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('jumia', 'masoko', 'phoneplace', 'laptopclinic')),
    product_name VARCHAR(500) NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(200),
    
    -- Pricing information
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    original_price DECIMAL(10, 2) CHECK (original_price >= 0),
    currency VARCHAR(3) DEFAULT 'KES',
    
    -- URLs and media
    url TEXT NOT NULL,
    image_url TEXT,
    
    -- Specifications
    processor VARCHAR(200),
    ram VARCHAR(50),
    storage VARCHAR(100),
    screen_size VARCHAR(50),
    graphics VARCHAR(200),
    operating_system VARCHAR(100),
    
    -- Product status
    condition VARCHAR(50),
    availability VARCHAR(100),
    
    -- Additional specifications as JSON
    specs JSONB,
    
    -- Timestamps
    scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_platform_url UNIQUE (platform, url)
);

-- ============================================================================
-- PRICE HISTORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    laptop_id UUID NOT NULL REFERENCES laptops(id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    currency VARCHAR(3) DEFAULT 'KES',
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for efficient time-series queries
    CONSTRAINT fk_laptop FOREIGN KEY (laptop_id) REFERENCES laptops(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary search indexes
CREATE INDEX IF NOT EXISTS idx_laptops_platform ON laptops(platform);
CREATE INDEX IF NOT EXISTS idx_laptops_brand ON laptops(brand);
CREATE INDEX IF NOT EXISTS idx_laptops_price ON laptops(price);
CREATE INDEX IF NOT EXISTS idx_laptops_scraped_at ON laptops(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_laptops_updated_at ON laptops(updated_at DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_laptops_platform_price ON laptops(platform, price);
CREATE INDEX IF NOT EXISTS idx_laptops_brand_price ON laptops(brand, price);

-- Full-text search index on product names
CREATE INDEX IF NOT EXISTS idx_laptops_product_name_trgm ON laptops USING gin(product_name gin_trgm_ops);

-- JSONB index for specs queries
CREATE INDEX IF NOT EXISTS idx_laptops_specs ON laptops USING gin(specs);

-- Price history indexes
CREATE INDEX IF NOT EXISTS idx_price_history_laptop_id ON price_history(laptop_id);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_laptop_recorded ON price_history(laptop_id, recorded_at DESC);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on laptops table
DROP TRIGGER IF EXISTS update_laptops_updated_at ON laptops;
CREATE TRIGGER update_laptops_updated_at
    BEFORE UPDATE ON laptops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Latest prices per platform
CREATE OR REPLACE VIEW latest_prices_by_platform AS
SELECT 
    platform,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price
FROM laptops
GROUP BY platform;

-- View: Price comparison across platforms for similar products
CREATE OR REPLACE VIEW price_comparison AS
SELECT 
    l1.product_name,
    l1.brand,
    l1.platform as platform_1,
    l1.price as price_1,
    l2.platform as platform_2,
    l2.price as price_2,
    ABS(l1.price - l2.price) as price_difference,
    ROUND(((l1.price - l2.price) / NULLIF(l2.price, 0)) * 100, 2) as price_diff_percentage
FROM laptops l1
JOIN laptops l2 ON 
    l1.brand = l2.brand 
    AND l1.platform < l2.platform
    AND similarity(l1.product_name, l2.product_name) > 0.6
WHERE l1.price IS NOT NULL AND l2.price IS NOT NULL;

-- View: Recent price changes
CREATE OR REPLACE VIEW recent_price_changes AS
SELECT 
    l.id,
    l.platform,
    l.product_name,
    l.brand,
    l.price as current_price,
    ph.price as previous_price,
    (l.price - ph.price) as price_change,
    ROUND(((l.price - ph.price) / NULLIF(ph.price, 0)) * 100, 2) as price_change_percentage,
    ph.recorded_at as previous_price_date,
    l.updated_at as current_price_date
FROM laptops l
JOIN price_history ph ON l.id = ph.laptop_id
WHERE ph.recorded_at = (
    SELECT MAX(recorded_at)
    FROM price_history
    WHERE laptop_id = l.id AND recorded_at < l.updated_at
)
AND l.price != ph.price;

-- View: Top deals (biggest discounts)
CREATE OR REPLACE VIEW top_deals AS
SELECT 
    platform,
    product_name,
    brand,
    original_price,
    price as current_price,
    (original_price - price) as discount_amount,
    ROUND(((original_price - price) / NULLIF(original_price, 0)) * 100, 2) as discount_percentage,
    url,
    updated_at
FROM laptops
WHERE original_price IS NOT NULL 
    AND price IS NOT NULL 
    AND original_price > price
ORDER BY discount_percentage DESC;

-- ============================================================================
-- INITIAL DATA QUALITY CHECKS
-- ============================================================================

-- Check for products with unusual prices
CREATE OR REPLACE VIEW data_quality_price_outliers AS
SELECT 
    id,
    platform,
    product_name,
    price,
    'Price below minimum threshold' as issue
FROM laptops
WHERE price < 15000
UNION ALL
SELECT 
    id,
    platform,
    product_name,
    price,
    'Price above maximum threshold' as issue
FROM laptops
WHERE price > 500000;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions to scraper user (will be created in Dockerfile)
-- These will execute after user creation
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'scraper_user') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO scraper_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO scraper_user;
        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO scraper_user;
    END IF;
END $$;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE laptops IS 'Main table storing laptop product information from various e-commerce platforms';
COMMENT ON TABLE price_history IS 'Historical price tracking for trend analysis';

COMMENT ON COLUMN laptops.platform IS 'E-commerce platform source (jumia, masoko, phoneplace, laptopclinic)';
COMMENT ON COLUMN laptops.specs IS 'Additional specifications stored as JSON for flexibility';
COMMENT ON COLUMN laptops.scraped_at IS 'Timestamp when the product was first scraped';
COMMENT ON COLUMN laptops.updated_at IS 'Timestamp of the last update to this product';

COMMENT ON VIEW latest_prices_by_platform IS 'Aggregate statistics of prices per platform';
COMMENT ON VIEW price_comparison IS 'Cross-platform price comparison for similar products';
COMMENT ON VIEW recent_price_changes IS 'Products with recent price changes';
COMMENT ON VIEW top_deals IS 'Products with the highest discounts';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully';
    RAISE NOTICE 'Tables created: laptops, price_history';
    RAISE NOTICE 'Indexes created for optimal query performance';
    RAISE NOTICE 'Views created for analytics and reporting';
END $$;
