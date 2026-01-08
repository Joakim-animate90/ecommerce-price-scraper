"""
Integration tests for database operations.
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime


@pytest.fixture(scope="module")
def db_connection():
    """Create a test database connection."""
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "test_ecommerce_prices"),
        user=os.getenv("POSTGRES_USER", "test_user"),
        password=os.getenv("POSTGRES_PASSWORD", "test_password"),
    )

    yield conn

    # Cleanup
    conn.close()


@pytest.fixture
def clean_database(db_connection):
    """Clean database before each test."""
    cursor = db_connection.cursor()
    cursor.execute("TRUNCATE TABLE laptops, price_history CASCADE")
    db_connection.commit()
    cursor.close()

    yield

    # Cleanup after test
    cursor = db_connection.cursor()
    cursor.execute("TRUNCATE TABLE laptops, price_history CASCADE")
    db_connection.commit()
    cursor.close()


@pytest.mark.integration
class TestDatabaseSchema:
    """Test database schema and constraints."""

    def test_laptops_table_exists(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'laptops'
            )
        """
        )
        exists = cursor.fetchone()[0]
        assert exists is True
        cursor.close()

    def test_price_history_table_exists(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'price_history'
            )
        """
        )
        exists = cursor.fetchone()[0]
        assert exists is True
        cursor.close()

    def test_insert_laptop(self, db_connection, clean_database):
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            INSERT INTO laptops (
                platform, product_name, brand, price, url, scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """,
            (
                "jumia",
                "Dell Inspiron 15",
                "Dell",
                75000,
                "https://jumia.co.ke/test",
                datetime.now(),
                datetime.now(),
            ),
        )

        result = cursor.fetchone()
        db_connection.commit()
        cursor.close()

        assert result["id"] is not None

    def test_unique_platform_url_constraint(self, db_connection, clean_database):
        cursor = db_connection.cursor()

        # Insert first laptop
        cursor.execute(
            """
            INSERT INTO laptops (
                platform, product_name, price, url, scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                "jumia",
                "Dell Inspiron 15",
                75000,
                "https://jumia.co.ke/test",
                datetime.now(),
                datetime.now(),
            ),
        )
        db_connection.commit()

        # Try to insert duplicate
        with pytest.raises(psycopg2.IntegrityError):
            cursor.execute(
                """
                INSERT INTO laptops (
                    platform, product_name, price, url, scraped_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    "jumia",
                    "Dell Inspiron 15",
                    75000,
                    "https://jumia.co.ke/test",  # Same platform + URL
                    datetime.now(),
                    datetime.now(),
                ),
            )
            db_connection.commit()

        db_connection.rollback()
        cursor.close()

    def test_price_history_tracking(self, db_connection, clean_database):
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)

        # Insert laptop
        cursor.execute(
            """
            INSERT INTO laptops (
                platform, product_name, price, url, scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """,
            (
                "jumia",
                "Dell Inspiron 15",
                75000,
                "https://jumia.co.ke/test",
                datetime.now(),
                datetime.now(),
            ),
        )

        laptop_result = cursor.fetchone()
        laptop_id = laptop_result["id"]

        # Insert price history
        cursor.execute(
            """
            INSERT INTO price_history (laptop_id, price, currency, recorded_at)
            VALUES (%s, %s, %s, %s)
        """,
            (laptop_id, 75000, "KES", datetime.now()),
        )

        db_connection.commit()

        # Verify price history
        cursor.execute(
            """
            SELECT COUNT(*) as count FROM price_history WHERE laptop_id = %s
        """,
            (laptop_id,),
        )

        result = cursor.fetchone()
        assert result["count"] == 1

        cursor.close()


@pytest.mark.integration
class TestDatabaseViews:
    """Test database views."""

    def test_latest_prices_by_platform_view(self, db_connection, clean_database):
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)

        # Insert test data
        cursor.execute(
            """
            INSERT INTO laptops (platform, product_name, price, url, scraped_at, updated_at)
            VALUES 
                ('jumia', 'Laptop 1', 75000, 'https://jumia.co.ke/1', NOW(), NOW()),
                ('jumia', 'Laptop 2', 80000, 'https://jumia.co.ke/2', NOW(), NOW()),
                ('masoko', 'Laptop 3', 70000, 'https://masoko.com/3', NOW(), NOW())
        """
        )
        db_connection.commit()

        # Query view
        cursor.execute("SELECT * FROM latest_prices_by_platform ORDER BY platform")
        results = cursor.fetchall()

        assert len(results) >= 2
        assert results[0]["platform"] == "jumia"
        assert results[0]["product_count"] == 2

        cursor.close()
