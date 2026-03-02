"""
Pytest test suite for the GradCafe microservice application.
Uses mocks so no real DB, RabbitMQ, or network calls are made.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'web'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'worker'))

# ---------------------------------------------------------------------------
# Web / Flask tests
# ---------------------------------------------------------------------------

class TestAnalysis:
    """Tests for the /analysis endpoint."""

    @pytest.fixture
    def client(self):
        with patch('run.publish_task'):
            from run import create_app
            app = create_app()
            app.config['TESTING'] = True
            with app.test_client() as c:
                yield c

    def test_analysis_returns_200(self, client):
        """GET /analysis should return HTTP 200."""
        response = client.get('/analysis')
        assert response.status_code == 200

    def test_analysis_contains_buttons(self, client):
        """Page should include the required data-testid buttons."""
        response = client.get('/analysis')
        assert b'pull-data-btn' in response.data
        assert b'update-analysis-btn' in response.data


class TestPullData:
    """Tests for the /pull-data endpoint."""

    @pytest.fixture
    def client(self):
        with patch('run.publish_task') as mock_pub:
            from run import create_app
            app = create_app()
            app.config['TESTING'] = True
            with app.test_client() as c:
                c.mock_pub = mock_pub
                yield c

    def test_pull_data_returns_202(self, client):
        """POST /pull-data should return 202 when queued successfully."""
        response = client.post('/pull-data')
        assert response.status_code == 202
        assert response.get_json() == {'queued': True}

    def test_pull_data_calls_publish(self, client):
        """POST /pull-data should call publish_task with correct kind."""
        client.post('/pull-data')
        client.mock_pub.assert_called_once_with('scrape_new_data')

    def test_pull_data_503_on_error(self):
        """When publish_task raises, /pull-data should return 503."""
        with patch('run.publish_task', side_effect=RuntimeError('broker down')):
            from run import create_app
            app = create_app()
            app.config['TESTING'] = True
            with app.test_client() as c:
                response = c.post('/pull-data')
            assert response.status_code == 503


class TestUpdateAnalysis:
    """Tests for the /update-analysis endpoint."""

    @pytest.fixture
    def client(self):
        with patch('run.publish_task') as mock_pub:
            from run import create_app
            app = create_app()
            app.config['TESTING'] = True
            with app.test_client() as c:
                c.mock_pub = mock_pub
                yield c

    def test_update_analysis_returns_202(self, client):
        """POST /update-analysis should return 202 when queued successfully."""
        response = client.post('/update-analysis')
        assert response.status_code == 202
        assert response.get_json() == {'queued': True}

    def test_update_analysis_calls_publish(self, client):
        """POST /update-analysis should call publish_task with correct kind."""
        client.post('/update-analysis')
        client.mock_pub.assert_called_once_with('recompute_analytics')

    def test_update_analysis_503_on_error(self):
        """When publish_task raises, /update-analysis should return 503."""
        with patch('run.publish_task', side_effect=RuntimeError('broker down')):
            from run import create_app
            app = create_app()
            app.config['TESTING'] = True
            with app.test_client() as c:
                response = c.post('/update-analysis')
            assert response.status_code == 503


# ---------------------------------------------------------------------------
# Publisher tests
# ---------------------------------------------------------------------------

class TestPublisher:
    """Tests for publisher.py."""

    def test_open_channel_declares_exchange_and_queue(self):
        """_open_channel should declare exchange, queue, and binding."""
        with patch('publisher.pika') as mock_pika:
            mock_conn = MagicMock()
            mock_ch = MagicMock()
            mock_pika.BlockingConnection.return_value = mock_conn
            mock_conn.channel.return_value = mock_ch

            import publisher
            with patch.dict(os.environ, {'RABBITMQ_URL': 'amqp://guest:guest@localhost/'}):
                conn, ch = publisher._open_channel()

            mock_ch.exchange_declare.assert_called_once()
            mock_ch.queue_declare.assert_called_once()
            mock_ch.queue_bind.assert_called_once()

    def test_publish_task_sends_message(self):
        """publish_task should call basic_publish with delivery_mode=2."""
        with patch('publisher.pika') as mock_pika:
            mock_conn = MagicMock()
            mock_ch = MagicMock()
            mock_pika.BlockingConnection.return_value = mock_conn
            mock_conn.channel.return_value = mock_ch
            mock_pika.URLParameters = MagicMock()
            mock_pika.BasicProperties = MagicMock()

            import publisher
            with patch.dict(os.environ, {'RABBITMQ_URL': 'amqp://guest:guest@localhost/'}):
                publisher.publish_task('scrape_new_data', {'key': 'value'})

            mock_ch.basic_publish.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_publish_task_closes_connection_on_error(self):
        """publish_task should close connection even if basic_publish raises."""
        with patch('publisher.pika') as mock_pika:
            mock_conn = MagicMock()
            mock_ch = MagicMock()
            mock_ch.basic_publish.side_effect = RuntimeError('publish failed')
            mock_pika.BlockingConnection.return_value = mock_conn
            mock_conn.channel.return_value = mock_ch
            mock_pika.URLParameters = MagicMock()
            mock_pika.BasicProperties = MagicMock()

            import publisher
            with patch.dict(os.environ, {'RABBITMQ_URL': 'amqp://guest:guest@localhost/'}):
                with pytest.raises(RuntimeError):
                    publisher.publish_task('scrape_new_data')

            mock_conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# Consumer tests
# ---------------------------------------------------------------------------

class TestConsumer:
    """Tests for consumer.py handlers."""

    def test_handle_recompute_analytics(self):
        """handle_recompute_analytics should query and commit."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (42,)

        import consumer
        consumer.handle_recompute_analytics(mock_conn, {})

        mock_cur.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cur.close.assert_called_once()

    def test_on_message_unknown_kind_nacks(self):
        """Unknown task kind should nack without requeue."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 1

        import consumer
        body = json.dumps({'kind': 'unknown_task', 'payload': {}}).encode()
        consumer.on_message(mock_ch, mock_method, None, body)

        mock_ch.basic_nack.assert_called_once_with(1, requeue=False)

    def test_on_message_bad_json_nacks(self):
        """Malformed JSON should nack without requeue."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 2

        import consumer
        consumer.on_message(mock_ch, mock_method, None, b'not-json')

        mock_ch.basic_nack.assert_called_once_with(2, requeue=False)

    def test_on_message_acks_on_success(self):
        """Successful handler should ack the message."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 3
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (10,)

        import consumer
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        with patch('consumer.get_db', return_value=mock_conn):
            body = json.dumps({'kind': 'recompute_analytics', 'payload': {}}).encode()
            consumer.on_message(mock_ch, mock_method, None, body)

        mock_ch.basic_ack.assert_called_once_with(3)


# ---------------------------------------------------------------------------
# query_data tests (covers src/web/app/query_data.py)
# ---------------------------------------------------------------------------

class TestQueryData:
    """Tests for query_data helpers."""

    def test_clamp_limit_min(self):
        """Values below MIN_LIMIT should be clamped to 1."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'web'))
        from app.query_data import _clamp_limit
        assert _clamp_limit(0) == 1

    def test_clamp_limit_max(self):
        """Values above MAX_LIMIT should be clamped to 100."""
        from app.query_data import _clamp_limit
        assert _clamp_limit(999) == 100

    def test_clamp_limit_normal(self):
        """Values within range should pass through unchanged."""
        from app.query_data import _clamp_limit
        assert _clamp_limit(50) == 50

    def test_compute_analysis_returns_dict(self):
        """compute_analysis should return a dict with expected keys."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.side_effect = [(10,), ("55.00",)]

        with patch('app.query_data.get_connection', return_value=mock_conn):
            from app.query_data import compute_analysis
            result = compute_analysis()

        assert 'Fall 2026 Applicants' in result
        assert 'International %' in result

    def test_compute_analysis_handles_none(self):
        """compute_analysis should handle None DB results gracefully."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.side_effect = [(0,), (None,)]

        with patch('app.query_data.get_connection', return_value=mock_conn):
            from app.query_data import compute_analysis
            result = compute_analysis()

        assert result['International %'] == '0.00%'

    def test_query_applicants_no_filters(self):
        """query_applicants with no filters should return all rows."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = [('MIT', 'CS', 'PhD', 'Accepted', 'Fall 2026', 'International', '3.9', '2024-01-01')]

        with patch('app.query_data.get_connection', return_value=mock_conn):
            from app.query_data import query_applicants
            rows = query_applicants()

        assert len(rows) == 1

    def test_query_applicants_with_filters(self):
        """query_applicants with filters should execute filtered query."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchall.return_value = []

        with patch('app.query_data.get_connection', return_value=mock_conn):
            from app.query_data import query_applicants
            rows = query_applicants(university='MIT', decision='Accepted')

        assert rows == []
        mock_cur.execute.assert_called_once()


# ---------------------------------------------------------------------------
# handle_scrape_new_data tests
# ---------------------------------------------------------------------------

class TestHandleScrapeNewData:
    """Tests for the scrape_new_data handler."""

    def test_handle_scrape_new_data_inserts_rows(self):
        """handle_scrape_new_data should insert rows and update watermark."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None  # no watermark yet

        fake_rows = [{
            'university': 'MIT', 'program': 'CS', 'degree': 'PhD',
            'decision': 'Accepted', 'season': 'Fall 2026',
            'applicant_status': 'International', 'gpa': '3.9',
            'added_on': '2026-01-01', 'result_id': 'test-999', 'page_scraped': 1
        }]

        import consumer
        with patch('consumer.get_db', return_value=mock_conn):
            with patch('etl.incremental_scraper.scrape_data', return_value=fake_rows):
                consumer.handle_scrape_new_data(mock_conn, {})

        mock_conn.commit.assert_called_once()

    def test_handle_scrape_new_data_with_watermark(self):
        """handle_scrape_new_data should read existing watermark."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = ('2025-01-01',)

        fake_rows = []

        import consumer
        with patch('etl.incremental_scraper.scrape_data', return_value=fake_rows):
            consumer.handle_scrape_new_data(mock_conn, {})

        mock_conn.commit.assert_called_once()

    def test_on_message_nacks_on_handler_error(self):
        """Handler exception should cause nack without requeue."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 99
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = RuntimeError('db error')

        import consumer
        with patch('consumer.get_db', return_value=mock_conn):
            body = json.dumps({'kind': 'recompute_analytics', 'payload': {}}).encode()
            consumer.on_message(mock_ch, mock_method, None, body)

        mock_ch.basic_nack.assert_called_once_with(99, requeue=False)


# ---------------------------------------------------------------------------
# incremental_scraper tests
# ---------------------------------------------------------------------------

class TestIncrementalScraper:
    """Tests for the GradCafe scraper."""

    def test_extract_decision_parts_season(self):
        """Should extract season from decision parts."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'worker'))
        from etl.incremental_scraper import _extract_decision_parts
        season, status, gpa = _extract_decision_parts(['Decision', 'Fall 2026'])
        assert season == 'Fall 2026'

    def test_extract_decision_parts_status(self):
        """Should extract applicant status from decision parts."""
        from etl.incremental_scraper import _extract_decision_parts
        season, status, gpa = _extract_decision_parts(['Decision', 'International'])
        assert status == 'International'

    def test_extract_decision_parts_gpa(self):
        """Should extract GPA from decision parts."""
        from etl.incremental_scraper import _extract_decision_parts
        season, status, gpa = _extract_decision_parts(['Decision', 'GPA 3.9'])
        assert gpa == '3.9'

    def test_extract_decision_parts_empty(self):
        """Should handle empty parts gracefully."""
        from etl.incremental_scraper import _extract_decision_parts
        season, status, gpa = _extract_decision_parts(['Decision'])
        assert season == ''
        assert status == ''
        assert gpa == ''

    def test_scraper_init(self):
        """GradCafeScraper should initialize with correct base_url."""
        from etl.incremental_scraper import GradCafeScraper
        scraper = GradCafeScraper()
        assert 'thegradcafe.com' in scraper.base_url

    def test_scrape_data_returns_list(self):
        """scrape_data should return a list."""
        mock_response = MagicMock()
        mock_response.content = b'<html><body><table></table></body></html>'
        mock_response.raise_for_status = MagicMock()

        with patch('requests.get', return_value=mock_response):
            from etl.incremental_scraper import scrape_data
            result = scrape_data()
        assert isinstance(result, list)

    def test_scraper_handles_request_error(self):
        """scrape_data should raise on network errors."""
        with patch('requests.get', side_effect=Exception('network error')):
            from etl.incremental_scraper import scrape_data
            with pytest.raises(Exception):
                scrape_data()


# ---------------------------------------------------------------------------
# consumer main() test
# ---------------------------------------------------------------------------

class TestConsumerMain:
    """Tests for consumer main() function."""

    def test_main_starts_consuming(self):
        """main() should declare entities and start consuming."""
        with patch('consumer.pika') as mock_pika:
            mock_conn = MagicMock()
            mock_ch = MagicMock()
            mock_pika.BlockingConnection.return_value = mock_conn
            mock_conn.channel.return_value = mock_ch
            mock_pika.URLParameters = MagicMock()
            mock_ch.start_consuming.side_effect = KeyboardInterrupt

            import consumer
            with patch.dict(os.environ, {'RABBITMQ_URL': 'amqp://guest:guest@localhost/'}):
                try:
                    consumer.main()
                except KeyboardInterrupt:
                    pass

            mock_ch.basic_qos.assert_called_once_with(prefetch_count=1)
            mock_ch.start_consuming.assert_called_once()

    def test_parse_row_valid(self):
        """_parse_row should parse a valid HTML row correctly."""
        from bs4 import BeautifulSoup
        from etl.incremental_scraper import GradCafeScraper
        html = '''<tr>
            <td>MIT</td>
            <td>Computer Science\nPhD</td>
            <td>2026-01-01</td>
            <td>Accepted|Fall 2026|International|GPA 3.9</td>
        </tr>'''
        row = BeautifulSoup(html, 'html.parser').find('tr')
        result = GradCafeScraper._parse_row(row, 1)
        assert result['university'] == 'MIT'
        assert result['degree'] == 'PhD'
        assert result['page_scraped'] == 1

    def test_parse_row_too_few_cells(self):
        """_parse_row should return empty dict for rows with < 4 cells."""
        from bs4 import BeautifulSoup
        from etl.incremental_scraper import GradCafeScraper
        html = '<tr><td>MIT</td><td>CS</td></tr>'
        row = BeautifulSoup(html, 'html.parser').find('tr')
        result = GradCafeScraper._parse_row(row, 1)
        assert result == {}

    def test_parse_row_with_result_id(self):
        """_parse_row should extract result_id from href."""
        from bs4 import BeautifulSoup
        from etl.incremental_scraper import GradCafeScraper
        html = '''<tr>
            <td>Stanford</td>
            <td>ML\nMS</td>
            <td>2026-02-01</td>
            <td>Rejected<a href="/result/12345">See More</a></td>
        </tr>'''
        row = BeautifulSoup(html, 'html.parser').find('tr')
        result = GradCafeScraper._parse_row(row, 2)
        assert result['result_id'] == '12345'


class TestCreateAppConfig:
    """Test create_app with config injection."""

    def test_create_app_with_config(self):
        """create_app should accept and apply a config dict."""
        with patch('run.publish_task'):
            from run import create_app
            app = create_app(config={'TESTING': True, 'CUSTOM': 'val'})
            assert app.config['CUSTOM'] == 'val'


class TestGetDb:
    """Test get_db connection helper."""

    def test_get_db_calls_connect(self):
        """get_db should call psycopg.connect with DATABASE_URL."""
        import consumer
        with patch('consumer.psycopg') as mock_psycopg:
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}):
                consumer.get_db()
            mock_psycopg.connect.assert_called_once_with('postgresql://test')


class TestWebDb:
    """Test web app db connection helper."""

    def test_get_connection_calls_connect(self):
        """get_connection should call psycopg.connect with DATABASE_URL."""
        with patch('app.db.psycopg') as mock_psycopg:
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}):
                from app.db import get_connection
                get_connection()
            mock_psycopg.connect.assert_called_once_with('postgresql://test')
