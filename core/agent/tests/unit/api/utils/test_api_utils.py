"""API工具类单元测试模块."""

import re
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class MockAPIUtils:
    """模拟API工具类，用于测试."""

    @staticmethod
    def validate_request_data(data: Any) -> bool:
        """验证请求数据."""
        if not isinstance(data, dict):
            return False
        if not data:
            return False
        return True

    @staticmethod
    def format_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
        """格式化响应数据."""
        return {
            "status": "success" if status_code == 200 else "error",
            "status_code": status_code,
            "data": data,
            "timestamp": time.time(),
        }

    @staticmethod
    def sanitize_input(input_str: Any) -> str:
        """清理输入字符串."""
        if not isinstance(input_str, str):
            return ""
        # 移除危险字符
        dangerous_chars = ["<", ">", '"', "'", "&"]
        result = input_str
        for char in dangerous_chars:
            result = result.replace(char, "")
        return result.strip()

    @staticmethod
    def parse_pagination_params(params: Any) -> Dict[str, int]:
        """解析分页参数."""
        try:
            page = params.get("page", 1)
            size = params.get("size", 20)

            # 处理无穷大和特殊值
            if (
                not isinstance(page, (int, float))
                or page == float("inf")
                or page == float("-inf")
            ):
                page = 1
            if (
                not isinstance(size, (int, float))
                or size == float("inf")
                or size == float("-inf")
            ):
                size = 20

            page = int(page)
            size = int(size)
        except (ValueError, OverflowError):
            page = 1
            size = 20

        # 限制范围
        page = max(1, page)
        size = max(1, min(100, size))

        offset = (page - 1) * size

        return {"page": page, "size": size, "offset": offset, "limit": size}

    @staticmethod
    def generate_request_id() -> str:
        """生成请求ID."""
        return str(uuid.uuid4())

    @staticmethod
    def extract_user_info(headers: Dict[str, str]) -> Dict[str, Optional[str]]:
        """从头部提取用户信息."""
        user_info: Dict[str, Optional[str]] = {
            "user_id": None,
            "session_id": None,
            "client_type": None,
            "api_key": None,
        }

        # 提取用户ID
        if "X-User-ID" in headers:
            user_info["user_id"] = headers["X-User-ID"]

        # 提取会话ID
        if "X-Session-ID" in headers:
            user_info["session_id"] = headers["X-Session-ID"]

        # 提取客户端类型
        if "User-Agent" in headers:
            user_info["client_type"] = headers["User-Agent"]

        # 提取API密钥
        if "Authorization" in headers:
            auth_header = headers["Authorization"]
            if auth_header.startswith("Bearer "):
                user_info["api_key"] = auth_header[7:]

        return user_info


class TestAPIUtils:  # pylint: disable=too-many-public-methods
    """API工具类测试."""

    def __init__(self) -> None:
        """初始化测试类."""
        self.api_utils = MockAPIUtils()

    def setup_method(self) -> None:
        """测试方法初始化."""
        # Reset API utils instance for each test
        self.api_utils = MockAPIUtils()

    def test_validate_request_data_valid(self) -> None:
        """测试有效请求数据验证."""
        valid_data_sets = [
            {"key": "value"},
            {"user": "test", "action": "create"},
            {"data": [1, 2, 3], "metadata": {"count": 3}},
            {"query": "中文查询", "params": {"language": "zh-CN"}},
        ]

        for data in valid_data_sets:
            result = self.api_utils.validate_request_data(data)
            assert result is True

    def test_validate_request_data_invalid(self) -> None:
        """测试无效请求数据验证."""
        invalid_data_sets: List[Any] = [None, {}, [], "", 123, "string_data"]

        for data in invalid_data_sets:
            result = self.api_utils.validate_request_data(data)
            assert result is False

    def test_format_response_success(self) -> None:
        """测试成功响应格式化."""
        test_data = {"result": "success", "message": "操作完成"}

        response = self.api_utils.format_response(test_data)

        assert response["status"] == "success"
        assert response["status_code"] == 200
        assert response["data"] == test_data
        assert "timestamp" in response
        assert isinstance(response["timestamp"], float)

    def test_format_response_error(self) -> None:
        """测试错误响应格式化."""
        error_data = {"error": "ValidationError", "details": "字段缺失"}

        response = self.api_utils.format_response(error_data, 400)

        assert response["status"] == "error"
        assert response["status_code"] == 400
        assert response["data"] == error_data

    def test_format_response_unicode_data(self) -> None:
        """测试Unicode数据响应格式化."""
        unicode_data = {
            "message": "中文消息🚀",
            "content": "特殊字符①②③",
            "data": ["中文", "English", "日本語"],
        }

        response = self.api_utils.format_response(unicode_data)

        assert response["status"] == "success"
        assert "🚀" in response["data"]["message"]
        assert "特殊字符①②③" in response["data"]["content"]

    def test_sanitize_input_clean_text(self) -> None:
        """测试清理干净文本."""
        clean_inputs = [
            "normal text",
            "中文文本",
            "text with numbers 123",
            "text_with_underscores",
        ]

        for input_text in clean_inputs:
            result = self.api_utils.sanitize_input(input_text)
            assert result == input_text

    def test_sanitize_input_dangerous_characters(self) -> None:
        """测试清理危险字符."""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            'SELECT * FROM users WHERE id = "1"',
            "text with & ampersand",
            "<div>html content</div>",
            "text with 'single quotes'",
        ]

        for input_text in dangerous_inputs:
            result = self.api_utils.sanitize_input(input_text)
            # 验证危险字符被移除
            assert "<" not in result
            assert ">" not in result
            assert '"' not in result
            assert "'" not in result
            assert "&" not in result

    def test_sanitize_input_invalid_types(self) -> None:
        """测试清理无效类型输入."""
        invalid_inputs: List[Any] = [None, 123, [], {}, True]

        for invalid_input in invalid_inputs:
            result = self.api_utils.sanitize_input(invalid_input)
            assert result == ""

    def test_sanitize_input_unicode_content(self) -> None:
        """测试清理Unicode内容."""
        unicode_inputs = [
            "中文内容🚀",
            "特殊字符①②③④⑤",
            "emoji测试😀😁😂🤣",
            "混合内容: English + 中文 + 🎉",
        ]

        for input_text in unicode_inputs:
            result = self.api_utils.sanitize_input(input_text)
            # Unicode字符应该保留
            assert len(result) > 0
            assert "中文" in result if "中文" in input_text else True

    def test_parse_pagination_params_valid(self) -> None:
        """测试解析有效分页参数."""
        valid_params_sets = [
            {"page": 1, "size": 20},
            {"page": 2, "size": 10},
            {"page": 5, "size": 50},
            {"page": "3", "size": "15"},  # 字符串数字
        ]

        for params in valid_params_sets:
            result = self.api_utils.parse_pagination_params(params)

            assert "page" in result
            assert "size" in result
            assert "offset" in result
            assert "limit" in result

            assert result["page"] >= 1
            assert result["size"] >= 1
            assert result["offset"] >= 0
            assert result["limit"] == result["size"]

    def test_parse_pagination_params_defaults(self) -> None:
        """测试解析默认分页参数."""
        empty_params: Dict[str, Any] = {}
        result = self.api_utils.parse_pagination_params(empty_params)

        assert result["page"] == 1
        assert result["size"] == 20
        assert result["offset"] == 0
        assert result["limit"] == 20

    def test_parse_pagination_params_boundary_values(self) -> None:
        """测试解析边界值分页参数."""
        boundary_params_sets = [
            {"page": 0, "size": 0},  # 最小值以下
            {"page": -1, "size": -5},  # 负数
            {"page": 1, "size": 200},  # 超过最大限制
            {"page": 1000, "size": 1},  # 极大页码
        ]

        for params in boundary_params_sets:
            result = self.api_utils.parse_pagination_params(params)

            # 验证边界限制
            assert result["page"] >= 1
            assert result["size"] >= 1
            assert result["size"] <= 100

    def test_generate_request_id_uniqueness(self) -> None:
        """测试生成请求ID唯一性."""
        request_ids = set()

        # 生成多个ID验证唯一性
        for _ in range(100):
            request_id = self.api_utils.generate_request_id()
            assert isinstance(request_id, str)
            assert len(request_id) > 0
            assert request_id not in request_ids
            request_ids.add(request_id)

    def test_generate_request_id_format(self) -> None:
        """测试生成请求ID格式."""
        request_id = self.api_utils.generate_request_id()

        # 验证UUID格式 (假设使用UUID4)
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(uuid_pattern, request_id, re.IGNORECASE)

    def test_extract_user_info_complete_headers(self) -> None:
        """测试提取完整用户信息."""
        complete_headers = {
            "X-User-ID": "user-123",
            "X-Session-ID": "session-456",
            "User-Agent": "TestClient/1.0",
            "Authorization": "Bearer sk-test-api-key-789",
        }

        user_info = self.api_utils.extract_user_info(complete_headers)

        assert user_info["user_id"] == "user-123"
        assert user_info["session_id"] == "session-456"
        assert user_info["client_type"] == "TestClient/1.0"
        assert user_info["api_key"] == "sk-test-api-key-789"

    def test_extract_user_info_partial_headers(self) -> None:
        """测试提取部分用户信息."""
        partial_headers = {"X-User-ID": "user-456", "Content-Type": "application/json"}

        user_info = self.api_utils.extract_user_info(partial_headers)

        assert user_info["user_id"] == "user-456"
        assert user_info["session_id"] is None
        assert user_info["client_type"] is None
        assert user_info["api_key"] is None

    def test_extract_user_info_empty_headers(self) -> None:
        """测试提取空头部用户信息."""
        empty_headers: Dict[str, str] = {}

        user_info = self.api_utils.extract_user_info(empty_headers)

        assert user_info["user_id"] is None
        assert user_info["session_id"] is None
        assert user_info["client_type"] is None
        assert user_info["api_key"] is None

    def test_extract_user_info_unicode_headers(self) -> None:
        """测试提取Unicode头部用户信息."""
        unicode_headers = {
            "X-User-ID": "中文用户_123",
            "X-Session-ID": "会话_456",
            "User-Agent": "中文客户端/1.0 🚀",
        }

        user_info = self.api_utils.extract_user_info(unicode_headers)

        assert user_info["user_id"] is not None
        assert "中文用户" in str(user_info["user_id"])
        assert user_info["session_id"] is not None
        assert "会话" in str(user_info["session_id"])
        assert user_info["client_type"] is not None
        assert "🚀" in str(user_info["client_type"])

    def test_extract_user_info_malformed_auth(self) -> None:
        """测试提取格式错误的认证信息."""
        malformed_headers = {
            "Authorization": "Basic username:password",  # 不是Bearer
            "X-User-ID": "user-789",
        }

        user_info = self.api_utils.extract_user_info(malformed_headers)

        assert user_info["user_id"] == "user-789"
        assert user_info["api_key"] is None  # Bearer格式不匹配

    def test_api_utils_performance(self) -> None:
        """测试API工具性能."""
        # 测试大量数据处理性能
        large_data = {"items": list(range(1000)), "metadata": {"count": 1000}}

        start_time = time.time()

        # 执行多个操作
        for _ in range(100):
            self.api_utils.validate_request_data(large_data)
            self.api_utils.format_response(large_data)
            self.api_utils.generate_request_id()

        end_time = time.time()
        execution_time = end_time - start_time

        # 验证性能合理（100次操作应该在1秒内完成）
        assert execution_time < 1.0

    def test_api_utils_concurrent_safety(self) -> None:
        """测试API工具并发安全性."""
        results: List[Dict[str, Any]] = []

        def concurrent_operations(thread_id: int) -> None:
            try:
                # 执行各种操作
                data = {"thread_id": thread_id, "data": f"thread_{thread_id}_data"}

                # 验证请求
                valid = self.api_utils.validate_request_data(data)

                # 格式化响应
                response = self.api_utils.format_response(data)

                # 生成ID
                request_id = self.api_utils.generate_request_id()

                # 解析分页
                pagination = self.api_utils.parse_pagination_params(
                    {"page": thread_id + 1}
                )

                results.append(
                    {
                        "thread_id": thread_id,
                        "valid": valid,
                        "response": response,
                        "request_id": request_id,
                        "pagination": pagination,
                    }
                )

            except (ValueError, TypeError, AttributeError) as e:
                results.append({"thread_id": thread_id, "error": str(e)})

        # 创建多个线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=concurrent_operations, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(results) == 10

        # 验证所有操作都成功
        successful_results = [r for r in results if "error" not in r]
        assert len(successful_results) == 10

        # 验证请求ID唯一性
        request_ids = [r["request_id"] for r in successful_results]
        assert len(set(request_ids)) == 10  # 所有ID应该唯一

    def test_api_utils_edge_cases(self) -> None:
        """测试API工具边界情况."""
        # 测试极大数据
        huge_data = {"content": "x" * 100000}
        assert self.api_utils.validate_request_data(huge_data) is True

        # 测试嵌套深度数据
        nested_data = {"level1": {"level2": {"level3": {"level4": "deep"}}}}
        assert self.api_utils.validate_request_data(nested_data) is True

        # 测试空字符串清理
        empty_result = self.api_utils.sanitize_input("   ")
        assert empty_result == ""

        # 测试极端分页参数
        extreme_pagination = self.api_utils.parse_pagination_params(
            {"page": float("inf"), "size": float("inf")}
        )
        assert isinstance(extreme_pagination["page"], int)
        assert isinstance(extreme_pagination["size"], int)
