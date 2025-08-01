import json

import pytest

from main import *


class TestValidateDate():

    def test_valid_date(self):
        assert validate_date("2025-07-30") == "2025-07-30"

    def test_invalid_format_short(self):
        with pytest.raises(SystemExit) as e:
            validate_date("2025-7-3")
        assert str(e.value) == "Дата должна быть в формате YYYY-MM-DD"

    def test_invalid_format_10_symbols(self):
        with pytest.raises(SystemExit) as e:
            validate_date("2025070300")
        assert str(e.value) == "Несуществующая дата либо неверный формат. Верный формат - YYYY-MM-DD"

    def test_invalid_format_inversion(self):
        with pytest.raises(SystemExit) as e:
            validate_date("30-07-2025")
        assert str(e.value) == "Несуществующая дата либо неверный формат. Верный формат - YYYY-MM-DD"

    def test_nonexistent_date(self):
        with pytest.raises(SystemExit) as e:
            validate_date("2025-02-30")
        assert str(e.value) == "Несуществующая дата либо неверный формат. Верный формат - YYYY-MM-DD"


class TestCreateCounter():
    
    def setUp(self, tmp_path, example_logs: list):
        file_names = []

        for ind, log in enumerate(example_logs):
            file = tmp_path / f"{ind}.log"
            with open(file, "w", encoding="utf-8") as f:
                for line in log:
                    f.write(json.dumps(line) + "\n")
            file_names.append(str(file))
        return file_names

    def test_counter_no_filter_date(self, tmp_path):
        ex1 = [
            {"@timestamp": "2025-06-22T10:00:00", "url": "/api/context/...", "response_time": 0.1},
            {"@timestamp": "2025-06-22T10:01:00", "url": "/api/context/...", "response_time": 0.2},
            {"@timestamp": "2025-06-22T10:02:00", "url": "/api/homeworks/...", "response_time": 0.05}
        ]

        log_files = self.setUp(tmp_path, [ex1,])
        result = create_counter_with_and_without_filter_date(log_files)

        assert result["/api/context/..."][0] == 2
        assert result["/api/homeworks/..."][0] == 1
        assert result["/api/homeworks/..."][1] == 0.05

    def test_counter_with_filter_date(self, tmp_path):
        ex1 = [
            {"@timestamp": "2025-07-29T23:59:59", "url": "/api/context/...", "response_time": 0.3},
            {"@timestamp": "2025-07-30T10:00:00", "url": "/api/context/...", "response_time": 0.1},
            {"@timestamp": "2025-07-30T10:01:00", "url": "/api/context/...", "response_time": 0.2}
        ]

        log_files = self.setUp(tmp_path, [ex1,])
        result = create_counter_with_and_without_filter_date(log_files, 
                                                             filter_date="2025-07-30")

        assert result["/api/context/..."][0] == 2

    def test_counter_missing_fields(self, tmp_path):
        ex1 = [
            {"@timestamp": "2025-06-22T13:57:32+00:00", "url": "/api/context/..."},
            {"@timestamp": "2025-06-22T13:57:32+00:00", "response_time": 0.02},
            {"@timestamp": "2025-06-22T13:57:32+00:00", "url": "/api/context/...", "response_time": 0.1}
        ]

        log_files = self.setUp(tmp_path, [ex1,])
        result = create_counter_with_and_without_filter_date(log_files)

        assert result["/api/context/..."][0] == 1
        assert result["/api/context/..."][1] == 0.1

    def test_counter_many_files(self, tmp_path):
        ex1 = [
            {"@timestamp": "2025-06-22T10:00:00", "url": "/api/context/...", "response_time": 0.1},
            {"@timestamp": "2025-06-22T10:01:00", "url": "/api/context/...", "response_time": 0.2},
            {"@timestamp": "2025-06-22T10:02:00", "url": "/api/homeworks/...", "response_time": 0.05}
        ]

        ex2 = [
            {"@timestamp": "2025-06-22T10:00:00", "url": "/api/context/...", "response_time": 0.1},
            {"@timestamp": "2025-06-22T10:01:00", "url": "/api/context/...", "response_time": 0.2},
            {"@timestamp": "2025-06-22T10:02:00", "url": "/api/homeworks/...", "response_time": 0.05}
        ]

        log_files = self.setUp(tmp_path, [ex1, ex2])
        result = create_counter_with_and_without_filter_date(log_files)

        assert result["/api/context/..."][0] == 4

    def test_one_file_doesnt_exist(self, caplog):
        log_files = ["non_existent_file.log", ]

        with pytest.raises(SystemExit) as e:
            create_counter_with_and_without_filter_date(log_files)
    
        assert str(e.value) == "Данные для отчета отсутствуют"

    def test_two_files_one_doesnt_exist(self, tmp_path, caplog):
        ex1 = [
            {"@timestamp": "2025-06-22T10:00:00", "url": "/api/context/...", "response_time": 0.1},
            {"@timestamp": "2025-06-22T10:01:00", "url": "/api/context/...", "response_time": 0.2},
            {"@timestamp": "2025-06-22T10:02:00", "url": "/api/homeworks/...", "response_time": 0.05}
        ]

        log_files = self.setUp(tmp_path, [ex1,])
        log_files += ["non_existent_file.log"]

        with caplog.at_level("ERROR"):
            result = create_counter_with_and_without_filter_date(log_files)

        assert result is not None
        assert any("Файл не найден" in msg for msg in caplog.text.splitlines())

    def test_json_decode_error(self, tmp_path, caplog):
        file_path = tmp_path / "bad_log.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('{"@timestamp": "2025-06-22T10:00:00", "url": "/api/context/...", "response_time": 0.1}\n')
            f.write('{"@timestamp": \n')

        with caplog.at_level("ERROR"):
            result = create_counter_with_and_without_filter_date([str(file_path)])

        assert result["/api/context/..."][0] == 1
        assert any("JSONDecodeError" in msg for msg in caplog.text.splitlines())

    def test_empty_counter(self, tmp_path):
        ex1 = []

        log_files = self.setUp(tmp_path, [ex1,])

        with pytest.raises(SystemExit) as e:
            create_counter_with_and_without_filter_date(log_files)
        assert str(e.value) == "Данные для отчета отсутствуют"


class TestCalculateAvgResponseTime():

    def test_avg_response_time_basic(self):
        counter = {
            "/api/context/...": [2, 0.6, 0],
        }

        result = calculate_avg_response_time(counter)

        assert result[0] == ["/api/context/...", 2, 0.3]

    def test_avg_response_time_zero_count(self):
        counter = {
            "/api/context/...": [1, 0, 0]
        }

        result = calculate_avg_response_time(counter)

        assert result[0] == ["/api/context/...", 1, 0]
 
