import re


def validate_and_extract_llm_content(content: str):
    """
    校验LLM生成内容并提取各部分内容：
    1. 验证Intent->Node->Reason的顺序
    2. 提取各部分内容并检查是否为空
    3. 允许内容中包含冒号等特殊字符

    返回:
        tuple: (is_valid, intent, node, reason)
        is_valid: 格式和内容是否有效
        intent: Intent部分内容（如有效）
        node: Node部分内容（如有效）
        reason: Reason部分内容（如有效）
    """
    # 清理输入内容：去除首尾空白，合并连续空白
    cleaned_content = re.sub(r"\s+", " ", content.strip())

    # 定义正则模式：按顺序匹配三个部分
    # 使用非贪婪匹配确保各部分不会跨行匹配
    pattern = r"Intent:\s*(?P<intent>.+?)\s*Node:\s*(?P<node>.+?)\s*Reason:\s*(?P<reason>.+)$"

    # 尝试匹配模式
    match = re.search(pattern, cleaned_content, re.DOTALL | re.IGNORECASE)

    if not match:
        # 匹配失败
        return False, None, None, None

    # 提取各部分内容
    intent_content = match.group("intent").strip()
    node_content = match.group("node").strip()
    reason_content = match.group("reason").strip()

    # 检查内容是否为空
    if not (intent_content and node_content and reason_content):
        return False, None, None, None

    # 所有检查通过
    return True, intent_content, node_content, reason_content


def compute_score(
    solution_str: str,
    ground_truth: str,
    std_format: float = 1.0,
    std_acc: float = 3.0,
):
    format_flag, intent, node, reason = validate_and_extract_llm_content(solution_str)
    if not format_flag:
        format_score = -std_format
        acc_score = -std_acc

        return {
            "score": acc_score + format_score,
            "acc": False,
            "pred": f"[❌Format]{solution_str}",
        }

    true_nodes = set()
    if isinstance(ground_truth, str):
        ground_truth = ground_truth.split(",")
    for i_node in ground_truth:
        true_nodes.add(i_node.strip().lower())

    if node.lower() in true_nodes:
        acc_score = std_acc
        acc = True
        pred = f"[✅Format✅Node]Intent: {intent}\nNode: {node}\nReason: {reason}"
    else:
        acc_score = -std_acc
        acc = False
        pred = f"[✅Format❌Node]Intent: {intent}\nNode: {node}\nReason: {reason}"

    format_score = std_format
    return {
        "score": acc_score + format_score,
        "acc": acc,
        "pred": pred,
    }


if __name__ == "__main__":
    from rich import print

    test_cases = [
        # 有效内容
        {"content": "Intent: 查询天气 Node: Node-3 Reason: 用户明确询问今日天气情况", "expected": (True, "查询天气", "Node-3", "用户明确询问今日天气情况")},
        # Intent内容为空
        {"content": "Intent:  Node: Node-1 Reason: 测试", "expected": (False, None, None, None)},
        # 顺序错误
        {"content": "Node: Node-1 Intent: 测试 Reason: 测试", "expected": (False, None, None, None)},
        # 缺少Reason部分
        {"content": "Intent: 测试 Node: Node-1", "expected": (False, None, None, None)},
        # 有多余内容
        {"content": "前置内容 Intent: 测试 Node: Node-1 Reason: 测试 后置内容", "expected": (True, "测试", "Node-1", "测试 后置内容")},
        # 内容中包含冒号
        {"content": "Intent: 需要:复杂内容 Node: Node:with:colon Reason: 包含:特殊字符", "expected": (True, "需要:复杂内容", "Node:with:colon", "包含:特殊字符")},
        # 多行内容
        {"content": "Intent: 多行\n内容测试 Node: Node-5\nReason: 换行\n处理", "expected": (True, "多行 内容测试", "Node-5", "换行 处理")},
        # 大小写混合
        {"content": "iNtEnT: 大小写测试 nOdE: Node-6 rEaSoN: 不区分大小写", "expected": (True, "大小写测试", "Node-6", "不区分大小写")},
    ]

    for i, test in enumerate(test_cases):
        result = validate_and_extract_llm_content(test["content"])
        if result != test["expected"]:
            print(f"测试 {i + 1} 失败: 输入=[green]{test['content']}[/green] 错误结果=[red]{result}[/red] 预期=[green]{test['expected']}[/green]")
            break
        else:
            print(f"测试 {i + 1} 通过: {result}")

    print("所有测试通过!")
