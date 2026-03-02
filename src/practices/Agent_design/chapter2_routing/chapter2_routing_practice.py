import sys
import os

# 确保 src 在 Python 路径中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough
from src.utils.model_loader import model_loader
from loguru import logger


def practice_customer_service_router():
    """
    练习 1: Customer Service Router（客服路由）
    
    场景：根据用户查询类型（技术支持/账单/销售）将请求路由到不同的处理链
    
    实现逻辑：
    1. 使用意图分类器识别用户查询类型
    2. 根据分类结果，使用 RunnableBranch 路由到相应的专业处理链
    3. 每个专业链都有特定的提示词和处理逻辑
    """
    logger.info("--- Practice 1: Customer Service Router ---")
    
    # 1. 加载模型
    llm = model_loader.load_llm()
    logger.info(f"使用模型: {model_loader.active_model_id}")
    
    # 2. 定义意图分类器
    # 这个链用于识别用户查询的类型
    intent_classifier_prompt = ChatPromptTemplate.from_template(
        """请分析以下用户查询，判断其属于哪个类别。
        可选类别：技术支持(technical)、账单(billing)、销售(sales)
        
        用户查询: {query}
        
        请只回复一个类别词：technical、billing 或 sales"""
    )
    
    intent_classifier = intent_classifier_prompt | llm | StrOutputParser()
    
    # 3. 定义各专业处理链
    
    # 技术支持链 - 处理技术相关问题
    tech_support_prompt = ChatPromptTemplate.from_template(
        """你是一位技术支持专家。请专业地回答以下技术问题：
        
        用户问题: {query}
        
        请提供：
        1. 问题原因分析
        2. 具体的解决步骤
        3. 预防措施建议"""
    )
    tech_chain = tech_support_prompt | llm | StrOutputParser()
    
    # 账单链 - 处理账单相关问题
    billing_prompt = ChatPromptTemplate.from_template(
        """你是一位账单专员。请专业地回答以下账单问题：
        
        用户问题: {query}
        
        请提供：
        1. 账单状态说明
        2. 相关费用明细
        3. 支付方式和期限说明"""
    )
    billing_chain = billing_prompt | llm | StrOutputParser()
    
    # 销售链 - 处理销售和咨询问题
    sales_prompt = ChatPromptTemplate.from_template(
        """你是一位销售顾问。请热情地回答以下咨询：
        
        用户咨询: {query}
        
        请提供：
        1. 产品介绍和特点
        2. 价格和优惠信息
        3. 购买建议和后续步骤"""
    )
    sales_chain = sales_prompt | llm | StrOutputParser()
    
    # 默认链 - 当无法分类时使用
    default_prompt = ChatPromptTemplate.from_template(
        """你是客服代表。请礼貌地回复用户：
        
        用户消息: {query}
        
        请确认收到用户的请求，并表示会将问题转接到合适的部门。"""
    )
    default_chain = default_prompt | llm | StrOutputParser()
    
    # 4. 使用 RunnableBranch 构建路由逻辑
    # 定义条件函数
    def is_technical(x):
        return "technical" in x["intent"].lower()
    
    def is_billing(x):
        return "billing" in x["intent"].lower()
    
    def is_sales(x):
        return "sales" in x["intent"].lower()
    
    # 创建路由分支
    router = RunnableBranch(
        (is_technical, tech_chain),
        (is_billing, billing_chain),
        (is_sales, sales_chain),
        default_chain  # 默认情况
    )
    
    # 5. 定义完整的路由流程
    def classify_intent(data):
        """意图分类函数"""
        intent = intent_classifier.invoke({"query": data["query"]})
        logger.info(f"意图分类结果: {intent}")
        return {"query": data["query"], "intent": intent}
    
    # 构建完整链路：分类 -> 路由 -> 处理
    full_router_chain = (
        RunnableLambda(classify_intent)
        | router
    )
    
    # 6. 测试用例
    test_queries = [
        "我的电脑无法连接到WiFi，该怎么办？",  # 技术支持
        "为什么我这个月的账单多了50元？",      # 账单
        "你们最新的产品有什么功能？",          # 销售
    ]
    
    print("\n=== 客服路由系统测试 ===\n")
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"用户查询: {query}")
        print(f"{'='*60}")
        
        result = full_router_chain.invoke({"query": query})
        
        print(f"\n>>> 系统回复:\n{result}")
        print(f"{'='*60}\n")


def practice_content_type_router():
    """
    练习 2: Content Type Router（内容类型路由）
    
    场景：根据用户输入内容类型（问题/比较/建议）路由到不同的处理策略
    
    实现逻辑：
    1. 分析用户输入的内容特征
    2. 使用 RunnableBranch 根据内容类型选择处理策略
    3. 每种类型采用不同的响应风格和处理深度
    """
    logger.info("--- Practice 2: Content Type Router ---")
    
    # 1. 加载模型
    llm = model_loader.load_llm()
    
    # 2. 定义内容类型分析器
    content_analyzer_prompt = ChatPromptTemplate.from_template(
        """请分析以下内容，判断用户需要什么类型的回复：
        
        用户内容: {content}
        
        类型选项：
        - question: 用户提出了一个需要解答的问题
        - comparison: 用户希望比较两个或多个事物
        - suggestion: 用户寻求建议或推荐
        - explanation: 用户希望了解某个概念或原理
        
        请只回复一个类型词：question、comparison、suggestion 或 explanation"""
    )
    
    content_analyzer = content_analyzer_prompt | llm | StrOutputParser()
    
    # 3. 定义各类型处理链
    
    # 问题回答链 - 直接回答用户问题
    question_handler_prompt = ChatPromptTemplate.from_template(
        """请直接回答用户的问题，保持简洁明了：
        
        用户问题: {content}
        
        回答要求：
        - 开门见山，先给出直接答案
        - 如有必要，提供简要解释
        - 控制在3-5句话内"""
    )
    question_chain = question_handler_prompt | llm | StrOutputParser()
    
    # 比较分析链 - 结构化比较多个事物
    comparison_handler_prompt = ChatPromptTemplate.from_template(
        """请对以下比较请求进行结构化分析：
        
        用户内容: {content}
        
        回答格式：
        - 概述：简要说明比较的对象
        - 对比表：列出关键差异（优缺点）
        - 建议：根据常见场景给出选择建议"""
    )
    comparison_chain = comparison_handler_prompt | llm | StrOutputParser()
    
    # 建议推荐链 - 提供个性化建议
    suggestion_handler_prompt = ChatPromptTemplate.from_template(
        """请针对以下请求提供专业建议：
        
        用户请求: {content}
        
        回答要求：
        - 给出2-3个具体可行的选项
        - 说明每个选项的适用场景
        - 提供决策参考因素"""
    )
    suggestion_chain = suggestion_handler_prompt | llm | StrOutputParser()
    
    # 原理解释链 - 深入浅出解释概念
    explanation_handler_prompt = ChatPromptTemplate.from_template(
        """请对以下内容进行深入浅出的解释：
        
        用户想了解: {content}
        
        解释结构：
        - 一句话定义（用通俗语言）
        - 核心原理说明
        - 实际例子或类比
        - 应用场景"""
    )
    explanation_chain = explanation_handler_prompt | llm | StrOutputParser()
    
    # 4. 定义条件函数
    def is_question(x):
        return "question" in x["content_type"].lower()
    
    def is_comparison(x):
        return "comparison" in x["content_type"].lower()
    
    def is_suggestion(x):
        return "suggestion" in x["content_type"].lower()
    
    def is_explanation(x):
        return "explanation" in x["content_type"].lower()
    
    # 5. 创建路由分支
    content_router = RunnableBranch(
        (is_question, question_chain),
        (is_comparison, comparison_chain),
        (is_suggestion, suggestion_chain),
        (is_explanation, explanation_chain),
        explanation_chain  # 默认使用解释链
    )
    
    # 6. 定义完整处理流程
    def analyze_content(data):
        """内容类型分析函数"""
        content_type = content_analyzer.invoke({"content": data["content"]})
        logger.info(f"内容类型分析结果: {content_type}")
        return {"content": data["content"], "content_type": content_type}
    
    # 构建完整链路
    content_processor = (
        RunnableLambda(analyze_content)
        | content_router
    )
    
    # 7. 测试用例
    test_contents = [
        "Python 和 JavaScript 哪个更适合做后端开发？",  # comparison
        "什么是机器学习？",                              # explanation
        "我应该学习什么编程语言？",                      # suggestion
        "量子计算的基本原理是什么？",                    # explanation
    ]
    
    print("\n=== 内容类型路由系统测试 ===\n")
    
    for content in test_contents:
        print(f"\n{'='*60}")
        print(f"用户内容: {content}")
        print(f"{'='*60}")
        
        result = content_processor.invoke({"content": content})
        
        print(f"\n>>> 系统回复:\n{result}")
        print(f"{'='*60}\n")


def practice_advanced_routing_with_fallback():
    """
    练习 3: 高级路由 - 带置信度和Fallback机制
    
    场景：实现更智能的路由，当分类置信度低时，使用组合策略
    """
    logger.info("--- Practice 3: Advanced Routing with Fallback ---")
    
    # 1. 加载模型
    llm = model_loader.load_llm()
    
    # 2. 定义带置信度的分类器
    confidence_classifier_prompt = ChatPromptTemplate.from_template(
        """请分析用户查询并分类，同时给出置信度（0-100）。
        
        用户查询: {query}
        可选类别： urgent（紧急）、normal（普通）、complex（复杂）
        
        回复格式：
        类别: <category>
        置信度: <confidence>"""
    )
    
    classifier_chain = confidence_classifier_prompt | llm | StrOutputParser()
    
    # 3. 定义不同优先级的处理链
    urgent_prompt = ChatPromptTemplate.from_template(
        "【紧急处理】用户紧急请求: {query}\n请立即提供解决方案，优先确保用户安全或关键问题解决。"
    )
    urgent_chain = urgent_prompt | llm | StrOutputParser()
    
    normal_prompt = ChatPromptTemplate.from_template(
        "【标准处理】用户一般请求: {query}\n提供标准、清晰的回复。"
    )
    normal_chain = normal_prompt | llm | StrOutputParser()
    
    complex_prompt = ChatPromptTemplate.from_template(
        "【复杂处理】用户复杂请求: {query}\n需要深入分析，提供详细的步骤和资源建议。"
    )
    complex_chain = complex_prompt | llm | StrOutputParser()
    
    # 4. 定义解析和处理函数
    def parse_classification(data):
        """解析分类结果和置信度"""
        raw_result = classifier_chain.invoke({"query": data["query"]})
        logger.info(f"原始分类结果: {raw_result}")
        
        # 简单解析逻辑
        category = "normal"  # 默认
        confidence = 50
        
        if "urgent" in raw_result.lower():
            category = "urgent"
        elif "complex" in raw_result.lower():
            category = "complex"
        
        # 提取置信度数值
        for line in raw_result.split('\n'):
            if '置信度' in line or 'confidence' in line.lower():
                try:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        confidence = int(numbers[0])
                except:
                    pass
        
        logger.info(f"解析结果 - 类别: {category}, 置信度: {confidence}")
        return {
            "query": data["query"],
            "category": category,
            "confidence": confidence
        }
    
    def route_with_fallback(data):
        """基于置信度的路由决策"""
        if data["confidence"] < 60:
            logger.warning(f"置信度较低 ({data['confidence']}%)，使用综合处理策略")
            # 低置信度时，使用复杂链提供更全面的回复
            return complex_chain.invoke({"query": data["query"]})
        
        # 正常路由
        if data["category"] == "urgent":
            return urgent_chain.invoke({"query": data["query"]})
        elif data["category"] == "complex":
            return complex_chain.invoke({"query": data["query"]})
        else:
            return normal_chain.invoke({"query": data["query"]})
    
    # 5. 构建完整链路
    advanced_router = (
        RunnableLambda(parse_classification)
        | RunnableLambda(route_with_fallback)
    )
    
    # 6. 测试
    test_queries = [
        "我的服务器宕机了，所有业务都中断了！",  # urgent
        "请帮我分析一下数据结构的复杂度",       # complex/normal
        "你好",                                 # normal (low confidence expected)
    ]
    
    print("\n=== 高级路由系统测试（带置信度判断）===\n")
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"用户查询: {query}")
        print(f"{'='*60}")
        
        result = advanced_router.invoke({"query": query})
        
        print(f"\n>>> 系统回复:\n{result}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("="*60)
    print("   Chapter 2: Routing (路由模式) - 练习代码")
    print("="*60)
    print("\n路由模式核心概念：")
    print("1. 意图分类器 - 识别用户意图类型")
    print("2. 条件路由 - 根据分类结果路由到不同处理链")
    print("3. 使用 RunnableBranch 实现条件分支")
    print("="*60)
    
    # 运行所有练习
    try:
        practice_customer_service_router()
    except Exception as e:
        logger.error(f"练习 1 执行失败: {e}")
        print(f"练习 1 执行失败: {e}")
    
    print("\n" + "="*60 + "\n")
    
    try:
        practice_content_type_router()
    except Exception as e:
        logger.error(f"练习 2 执行失败: {e}")
        print(f"练习 2 执行失败: {e}")
    
    print("\n" + "="*60 + "\n")
    
    try:
        practice_advanced_routing_with_fallback()
    except Exception as e:
        logger.error(f"练习 3 执行失败: {e}")
        print(f"练习 3 执行失败: {e}")
    
    print("\n" + "="*60)
    print("   所有练习执行完毕")
    print("="*60)
