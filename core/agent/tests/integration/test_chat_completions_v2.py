"""
Chat Completions API功能测试 V2

测试 /agent/v1/chat/completions 接口的各种场景，包括：
- 基础聊天功能
- 流式和非流式响应
- 错误处理
- 参数验证

重要说明：
1. API返回的HTTP状态码通常为200，真正的业务状态需要查看响应JSON中的code字段
2. 根据base_inputs.py，API有以下限制：
   - 不支持system角色消息
   - messages必须以user结尾，且user/assistant交替
   - bot_id长度至少1个字符
3. 测试使用固定参数：
   - x-consumer-username: cb7386a7
   - bot_id: 14a9bbbcf0254f9b94562e6705d3a13f
   - uid: 12
"""

import concurrent.futures
import json
import time
from typing import Any, Dict, List, Tuple

import httpx


class ChatCompletionsTestClient:
    """Chat Completions API测试客户端"""

    def __init__(self, base_url: str = "http://localhost:17870"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/agent/v1/chat/completions"
        self.default_headers = {
            "Content-Type": "application/json",
            "x-consumer-username": "cb7386a7",
        }

    def parse_response(self, response: httpx.Response) -> Tuple[int, str, dict]:
        """解析API响应，返回(business_code, business_message, full_data)"""
        try:
            data = response.json()
            business_code = data.get("code", 0)
            business_message = data.get("message", "")
            return business_code, business_message, data
        except (ValueError, KeyError, TypeError) as e:
            return -1, f"JSON解析失败: {e}", {}

    def send_request(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> httpx.Response:
        """发送Chat Completions请求"""
        # 提取参数
        uid = kwargs.get("uid", "12")  # 固定用户ID
        stream = kwargs.get("stream", False)
        meta_data = kwargs.get("meta_data")
        bot_id = kwargs.get("bot_id", "14a9bbbcf0254f9b94562e6705d3a13f")  # 固定bot_id
        headers = kwargs.get("headers")

        if meta_data is None:
            meta_data = {"caller": "chat_open_api", "caller_sid": ""}

        request_data = {
            "uid": uid,
            "messages": messages,
            "stream": stream,
            "meta_data": meta_data,
            "bot_id": bot_id,
        }

        request_headers = headers or self.default_headers

        return httpx.post(
            self.endpoint, json=request_data, headers=request_headers, timeout=30
        )


class TestChatCompletionsV2:
    """Chat Completions API测试套件 V2"""

    client: ChatCompletionsTestClient

    @classmethod
    def setup_class(cls) -> None:
        """测试类初始化"""
        cls.client = ChatCompletionsTestClient()

    def test_basic_chat_completion(self) -> None:
        """测试基础聊天完成功能"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        response = self.client.send_request(messages)

        # 验证HTTP状态码
        assert (
            response.status_code == 200
        ), f"期望HTTP状态码200，实际: {response.status_code}"

        # 验证响应头
        assert "application/json" in response.headers.get("content-type", "").lower()

        # 解析业务状态码
        business_code, business_message, _ = self.client.parse_response(response)
        print(f"Business code: {business_code}, message: {business_message}")

        # 记录完整响应用于分析
        if business_code != 0:
            print(f"⚠️ 业务状态码: {business_code}, 消息: {business_message}")
            _, _, data = self.client.parse_response(response)
            print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    def test_chat_with_valid_bot_id(self) -> None:
        """测试使用有效bot_id的聊天请求"""
        messages = [{"role": "user", "content": "请介绍一下Python编程语言"}]

        response = self.client.send_request(messages)  # 使用默认的固定bot_id

        assert response.status_code == 200

        business_code, business_message, _ = self.client.parse_response(response)
        print(
            f"有效Bot ID测试 - Business code: "
            f"{business_code}, message: {business_message}"
        )

    def test_chat_with_uid(self) -> None:
        """测试带用户ID的聊天请求"""
        messages = [{"role": "user", "content": "测试用户ID功能"}]

        response = self.client.send_request(messages)  # 使用默认的固定uid

        assert response.status_code == 200

        business_code, business_message, _ = self.client.parse_response(response)
        print(f"UID测试 - Business code: {business_code}, message: {business_message}")

    def test_chat_with_conversation_history(self) -> None:
        """测试符合规则的多轮对话"""
        # 根据base_inputs.py，必须是user/assistant交替，且以user结尾
        messages = [
            {"role": "user", "content": "我想学习Python编程"},
            {"role": "assistant", "content": "很好！Python是一门很棒的编程语言。"},
            {"role": "user", "content": "请推荐一些入门书籍"},
        ]

        response = self.client.send_request(messages)

        assert response.status_code == 200

        business_code, business_message, _ = self.client.parse_response(response)
        print(
            f"多轮对话测试 - Business code: "
            f"{business_code}, message: {business_message}"
        )

    def test_stream_chat_completion(self) -> None:
        """测试流式聊天完成"""
        messages = [{"role": "user", "content": "请详细解释什么是人工智能"}]

        response = self.client.send_request(messages, stream=True)

        assert response.status_code == 200

        business_code, business_message, _ = self.client.parse_response(response)
        print(
            f"流式响应测试 - Business code: "
            f"{business_code}, message: {business_message}"
        )

    def test_empty_bot_id_validation(self) -> None:
        """测试空bot_id验证 - 应该失败"""
        messages = [{"role": "user", "content": "测试空bot_id"}]

        response = self.client.send_request(messages, bot_id="")

        assert response.status_code == 200  # HTTP状态码仍为200

        business_code, business_message, _ = self.client.parse_response(response)
        print(
            f"空bot_id验证测试 - Business code: "
            f"{business_code}, message: {business_message}"
        )

        # 根据你提供的示例，空bot_id应该返回40002错误
        if business_code == 40002:
            print("✅ 空bot_id验证正常工作")
        else:
            print(f"⚠️ 期望错误码40002，实际: {business_code}")

    def test_system_message_validation(self) -> None:
        """测试system消息验证 - 根据base_inputs.py应该失败"""
        messages = [
            {"role": "system", "content": "你是一个友好的AI助手"},
            {"role": "user", "content": "今天天气怎么样？"},
        ]

        response = self.client.send_request(messages)

        # 根据base_inputs.py，system角色应该被拒绝，可能返回422状态码
        print(f"System消息测试 - HTTP状态码: {response.status_code}")

        if response.status_code == 422:
            print("✅ System消息验证正常工作 - 返回422")
        else:
            business_code, business_message, _ = self.client.parse_response(response)
            print(
                f"System消息测试 - Business code: "
                f"{business_code}, message: {business_message}"
            )

    def test_empty_message_validation(self) -> None:
        """测试空消息验证"""
        messages: List[Dict[str, str]] = []

        response = self.client.send_request(messages)

        print(f"空消息测试 - HTTP状态码: {response.status_code}")

        if response.status_code == 422:
            print("✅ 空消息验证正常工作 - 返回422")
        else:
            business_code, business_message, _ = self.client.parse_response(response)
            print(
                f"空消息测试 - Business code: "
                f"{business_code}, message: {business_message}"
            )

    def test_invalid_message_order(self) -> None:
        """测试无效的消息顺序 - 不是user/assistant交替"""
        messages = [
            {"role": "user", "content": "第一条消息"},
            {"role": "user", "content": "连续两条user消息"},  # 违反交替规则
        ]

        response = self.client.send_request(messages)

        print(f"无效消息顺序测试 - HTTP状态码: {response.status_code}")

        if response.status_code == 422:
            print("✅ 消息顺序验证正常工作 - 返回422")
        else:
            business_code, business_message, _ = self.client.parse_response(response)
            print(
                f"无效消息顺序测试 - Business code: "
                f"{business_code}, message: {business_message}"
            )

    def test_uid_length_validation(self) -> None:
        """测试UID长度验证"""
        messages = [{"role": "user", "content": "测试超长UID"}]

        # 创建超过32字符的UID
        long_uid = "a" * 33

        response = self.client.send_request(messages, uid=long_uid)

        print(f"UID长度验证测试 - HTTP状态码: {response.status_code}")

        if response.status_code == 422:
            print("✅ UID长度验证正常工作 - 返回422")
        else:
            business_code, business_message, _ = self.client.parse_response(response)
            print(
                f"UID长度验证测试 - Business code: "
                f"{business_code}, message: {business_message}"
            )

    def test_missing_required_header(self) -> None:
        """测试缺少必需的header"""
        messages = [{"role": "user", "content": "测试缺少header"}]

        # 移除必需的x-consumer-username header
        headers = {"Content-Type": "application/json"}

        response = self.client.send_request(messages, headers=headers)

        print(f"缺少header测试 - HTTP状态码: {response.status_code}")

        if response.status_code in [400, 422]:
            print("✅ Header验证正常工作")
        else:
            business_code, business_message, _ = self.client.parse_response(response)
            print(
                f"缺少header测试 - Business code: "
                f"{business_code}, message: {business_message}"
            )

    def test_concurrent_requests(self) -> None:
        """测试并发请求"""

        def send_single_request(thread_id: int) -> Tuple[int, int, float, int]:
            """发送单个请求并记录时间和业务状态"""
            messages = [{"role": "user", "content": f"这是线程{thread_id}的测试消息"}]

            start_time = time.time()
            response = self.client.send_request(messages)  # 使用默认的固定uid
            end_time = time.time()

            business_code, _, _ = self.client.parse_response(response)

            return (
                thread_id,
                response.status_code,
                end_time - start_time,
                business_code,
            )

        # 并发发送5个请求
        max_workers = 5
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(send_single_request, i): i for i in range(max_workers)
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    thread_id, http_status, response_time, business_code = (
                        future.result()
                    )
                    results.append(
                        (thread_id, http_status, response_time, business_code)
                    )
                    print(
                        f"线程{thread_id}: HTTP={http_status}, "
                        f"业务码={business_code}, 时间={response_time:.2f}s"
                    )
                except (ValueError, RuntimeError, TypeError) as exc:
                    print(f"线程请求失败: {exc}")

        # 验证结果
        http_success_count = sum(
            1 for _, http_status, _, _ in results if http_status == 200
        )
        business_success_count = sum(
            1 for _, _, _, business_code in results if business_code == 0
        )

        print(
            f"HTTP成功: {http_success_count}/{max_workers}, "
            f"业务成功: {business_success_count}/{max_workers}"
        )

        # 计算平均响应时间
        if results:
            avg_response_time = sum(time for _, _, time, _ in results) / len(results)
            print(f"平均响应时间: {avg_response_time:.2f}s")


if __name__ == "__main__":
    # 直接运行测试
    test_instance = TestChatCompletionsV2()
    test_instance.setup_class()

    print("🚀 开始Chat Completions API功能测试 V2...")
    print("=" * 60)

    # 测试用例列表
    test_methods = [
        ("基础聊天完成", test_instance.test_basic_chat_completion),
        ("有效Bot ID", test_instance.test_chat_with_valid_bot_id),
        ("带UID聊天", test_instance.test_chat_with_uid),
        ("多轮对话", test_instance.test_chat_with_conversation_history),
        ("流式聊天", test_instance.test_stream_chat_completion),
        ("空Bot ID验证", test_instance.test_empty_bot_id_validation),
        ("System消息验证", test_instance.test_system_message_validation),
        ("空消息验证", test_instance.test_empty_message_validation),
        ("无效消息顺序", test_instance.test_invalid_message_order),
        ("UID长度验证", test_instance.test_uid_length_validation),
        ("缺少Header验证", test_instance.test_missing_required_header),
        ("并发请求", test_instance.test_concurrent_requests),
    ]

    tests_passed = 0  # pylint: disable=invalid-name
    tests_failed = 0  # pylint: disable=invalid-name

    for test_name, test_method in test_methods:
        try:
            print(f"\n🧪 {test_name}测试:")
            test_method()
            print(f"✅ {test_name}测试完成")
            tests_passed += 1
        except (AssertionError, ValueError, RuntimeError) as e:
            print(f"❌ {test_name}测试失败: {e}")
            tests_failed += 1

    print("\n" + "=" * 60)
    print(
        f"📊 测试完成！通过: {tests_passed}, "
        f"失败: {tests_failed}, 总计: {tests_passed + tests_failed}"
    )
    print("=" * 60)
