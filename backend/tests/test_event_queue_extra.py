from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import event_queue_service


class TestEventQueueExtra:
    @pytest.mark.asyncio
    async def test_process_pending_events_no_db(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = ""
        with patch("app.services.event_queue_service.get_settings", return_value=mock_settings):
            res = await event_queue_service.process_pending_events()
            assert res == 0

    @pytest.mark.asyncio
    async def test_process_pending_events_exception_pool(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        with (
            patch("app.services.event_queue_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", side_effect=Exception("DB down")),
        ):
            res = await event_queue_service.process_pending_events()
            assert res == 0

    @pytest.mark.asyncio
    async def test_process_pending_events_success(self):
        mock_settings = MagicMock()
        mock_settings.SUPABASE_DB_URL = "postgresql://test"
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = False

        mock_conn.fetch.return_value = [
            {"id": 1, "event_type": "insight_request", "payload": {}},
            {"id": 2, "event_type": "insight_request", "payload": {}}
        ]

        call_count = 0
        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("inner failure")

        mock_conn.execute.side_effect = mock_execute

        with (
            patch("app.services.event_queue_service.get_settings", return_value=mock_settings),
            patch("app.services.supabase_service._get_pool", return_value=mock_pool),
        ):
            res = await event_queue_service.process_pending_events()
            assert res == 1
