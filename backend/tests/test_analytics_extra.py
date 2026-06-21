from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import analytics_service


class TestAnalyticsServiceExtra:
    @pytest.mark.asyncio
    async def test_log_recommendation_skips_when_no_db(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = ""
        with patch("app.services.analytics_service.get_settings", return_value=mock_settings):
            await analytics_service.log_recommendation("rules", "transport", 10.0, 1)

    @pytest.mark.asyncio
    async def test_log_recommendation_success(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = False
        with (
            patch("app.services.analytics_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", return_value=mock_pool),
        ):
            await analytics_service.log_recommendation("rules", "transport", 10.0, 1)
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_recommendation_exception(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        with (
            patch("app.services.analytics_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", side_effect=Exception("DB fail")),
        ):
            await analytics_service.log_recommendation("rules", "transport", 10.0, 1)

    @pytest.mark.asyncio
    async def test_query_top_categories_no_db(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = ""
        with patch("app.services.analytics_service.get_settings", return_value=mock_settings):
            res = await analytics_service.query_top_categories()
            assert res == []

    @pytest.mark.asyncio
    async def test_query_top_categories_success(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = False
        mock_conn.fetch.return_value = [{"top_category": "home", "count": 5}]
        with (
            patch("app.services.analytics_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", return_value=mock_pool),
        ):
            res = await analytics_service.query_top_categories()
            assert len(res) == 1
            assert res[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_query_top_categories_exception(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        with (
            patch("app.services.analytics_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", side_effect=Exception("err")),
        ):
            res = await analytics_service.query_top_categories()
            assert res == []

    @pytest.mark.asyncio
    async def test_query_avg_footprint_no_db(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = ""
        with patch("app.services.analytics_service.get_settings", return_value=mock_settings):
            res = await analytics_service.query_avg_footprint_by_diet()
            assert res == []

    @pytest.mark.asyncio
    async def test_query_avg_footprint_success(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = False
        mock_conn.fetch.return_value = [{"diet_type": "vegan", "avg_kg": 1500, "count": 2}]
        with (
            patch("app.services.analytics_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", return_value=mock_pool),
        ):
            res = await analytics_service.query_avg_footprint_by_diet()
            assert len(res) == 1
            assert res[0]["diet_type"] == "vegan"

    @pytest.mark.asyncio
    async def test_query_avg_footprint_exception(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        with (
            patch("app.services.analytics_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", side_effect=Exception("err")),
        ):
            res = await analytics_service.query_avg_footprint_by_diet()
            assert res == []
