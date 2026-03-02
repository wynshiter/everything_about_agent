import sys
import os

# Ensure src is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from src.utils.model_loader import model_loader
from loguru import logger


def practice_multi_aspect_analysis():
    """
    练习 1: Multi-Aspect Analysis (多维度文本分析)
    场景: 并行分析文本的情感、主题、关键词
    演示: 使用 RunnableParallel 同时执行多个独立的分析任务
    """
    logger.info("--- Practice 1: Multi-Aspect Analysis ---")
    
    # 1. 加载模型
    llm = model_loader.load_llm()
    logger.info(f"Using model: {model_loader.active_model_id}")
    
    # 2. 定义各个分析维度的 Prompt
    
    # 情感分析 Prompt
    prompt_sentiment = ChatPromptTemplate.from_template(
        """分析以下文本的情感倾向。
请输出：1) 整体情感（正面/负面/中性）2) 情感强度（1-10分）3) 主要情感词汇

文本：{text}

情感分析："""
    )
    
    # 主题分析 Prompt
    prompt_topic = ChatPromptTemplate.from_template(
        """分析以下文本的主要主题。
请输出：1) 主要主题 2) 次要主题 3) 主题之间的关联

文本：{text}

主题分析："""
    )
    
    # 关键词提取 Prompt
    prompt_keywords = ChatPromptTemplate.from_template(
        """从以下文本中提取关键词。
请输出：1) 5个核心关键词 2) 每个关键词的重要性评分（1-10）3) 关键词的简要解释

文本：{text}

关键词提取："""
    )
    
    # 3. 构建各个独立的 Chain
    sentiment_chain = prompt_sentiment | llm | StrOutputParser()
    topic_chain = prompt_topic | llm | StrOutputParser()
    keywords_chain = prompt_keywords | llm | StrOutputParser()
    
    # 4. 使用 RunnableParallel 构建并行处理链
    # RunnablePassthrough 用于保留原始输入
    parallel_analysis = RunnableParallel({
        "sentiment": sentiment_chain,
        "topic": topic_chain,
        "keywords": keywords_chain,
        "original_text": RunnablePassthrough()  # 保留原始输入
    })
    
    # 5. 综合报告生成 Chain
    prompt_report = ChatPromptTemplate.from_template(
        """基于以下多维度分析结果，生成一份综合分析报告：

【原始文本】
{original_text}

【情感分析】
{sentiment}

【主题分析】
{topic}

【关键词提取】
{keywords}

请生成一份结构化的综合分析报告，总结关键发现和建议。"""
    )
    
    report_chain = prompt_report | llm | StrOutputParser()
    
    # 6. 组合完整流程：并行分析 -> 综合报告
    full_chain = parallel_analysis | report_chain
    
    # 7. 执行分析
    sample_text = """
    人工智能正在深刻改变我们的生活方式。从智能手机助手到自动驾驶汽车，
    AI技术无处不在。虽然有人担心AI会取代人类工作，但更多人认为AI将创造新的就业机会
    并提高生产效率。关键在于我们如何适应这一变革，通过教育和培训来提升技能。
    未来，人机协作将成为主流模式，我们需要以开放的心态拥抱这项技术。
    """
    
    logger.info(f"Input Text: {sample_text[:100]}...")
    
    # 执行并行分析并获取结果
    parallel_results = parallel_analysis.invoke({"text": sample_text})
    
    print("\n" + "=" * 60)
    print("   并行分析结果")
    print("=" * 60)
    
    print(f"\n【情感分析】\n{parallel_results['sentiment']}")
    print(f"\n【主题分析】\n{parallel_results['topic']}")
    print(f"\n【关键词提取】\n{parallel_results['keywords']}")
    
    # 生成综合报告
    final_report = full_chain.invoke({"text": sample_text})
    
    print(f"\n【综合分析报告】\n{final_report}")
    print("=" * 60 + "\n")


def practice_document_processing():
    """
    练习 2: Document Processing (文档并行处理)
    场景: 并行执行摘要提取、问题生成、关键词提取
    演示: 使用 RunnableParallel 对同一文档进行多维度处理
    """
    logger.info("--- Practice 2: Document Processing ---")
    
    # 1. 加载模型
    llm = model_loader.load_llm()
    logger.info(f"Using model: {model_loader.active_model_id}")
    
    # 2. 定义各个处理任务的 Prompt
    
    # 摘要提取 Prompt
    prompt_summary = ChatPromptTemplate.from_template(
        """请为以下文档生成简洁的摘要。
要求：
1. 摘要长度不超过原文的30%
2. 包含文档的核心观点和主要结论
3. 使用简洁清晰的语言

文档内容：
{document}

摘要："""
    )
    
    # 问题生成 Prompt
    prompt_questions = ChatPromptTemplate.from_template(
        """基于以下文档内容，生成有助于理解文档的问答对。
要求：
1. 生成3-5个高质量问题
2. 问题应涵盖文档的不同方面
3. 每个问题附带简要答案

文档内容：
{document}

问答对："""
    )
    
    # 关键词提取 Prompt
    prompt_keywords = ChatPromptTemplate.from_template(
        """从以下文档中提取关键术语和概念。
要求：
1. 提取5-8个关键词或短语
2. 按重要性排序
3. 标注每个关键词的类别（如：技术/概念/人物等）

文档内容：
{document}

关键词："""
    )
    
    # 行动项提取 Prompt
    prompt_actions = ChatPromptTemplate.from_template(
        """从以下文档中提取行动项或建议。
要求：
1. 列出文档中提到的所有行动建议
2. 标注每个行动项的优先级（高/中/低）
3. 如有时间要求，一并标注

文档内容：
{document}

行动项："""
    )
    
    # 3. 构建各个独立的 Chain
    summary_chain = prompt_summary | llm | StrOutputParser()
    questions_chain = prompt_questions | llm | StrOutputParser()
    keywords_chain = prompt_keywords | llm | StrOutputParser()
    actions_chain = prompt_actions | llm | StrOutputParser()
    
    # 4. 使用 RunnableParallel 构建并行处理链
    parallel_processing = RunnableParallel({
        "summary": summary_chain,
        "questions": questions_chain,
        "keywords": keywords_chain,
        "actions": actions_chain,
        "document": RunnablePassthrough()  # 保留原始文档
    })
    
    # 5. 文档处理结果汇总 Chain
    prompt_consolidate = ChatPromptTemplate.from_template(
        """请将以下文档处理结果整合为一份结构化报告：

# 文档处理报告

## 1. 内容摘要
{summary}

## 2. 核心关键词
{keywords}

## 3. 关键问答
{questions}

## 4. 行动建议
{actions}

请确保报告结构清晰，便于快速理解文档要点。"""
    )
    
    consolidate_chain = prompt_consolidate | llm | StrOutputParser()
    
    # 6. 组合完整流程
    full_chain = parallel_processing | consolidate_chain
    
    # 7. 执行文档处理
    sample_document = """
    # 远程工作最佳实践指南

    ## 概述
    随着数字化转型的深入，远程工作已成为现代企业的重要工作模式。
    本指南旨在帮助团队和个人更好地适应远程工作环境，提高工作效率。

    ## 关键建议

    ### 1. 建立固定的工作时间
    尽管远程工作提供了灵活性，但建立规律的工作时间有助于保持工作效率
    和工作生活平衡。建议每天设定核心工作时段，并与团队成员同步。

    ### 2. 打造专属工作空间
    在家中设置一个专门的工作区域，有助于进入工作状态。
    确保工作空间安静、光线充足，并配备必要的办公设备。

    ### 3. 保持有效沟通
    使用即时通讯工具（如Slack、Teams）保持日常联系。
    定期进行视频会议，确保团队协作顺畅。
    重要：每周至少进行一次团队同步会议。

    ### 4. 注重身心健康
    长时间居家工作容易导致久坐和社交隔离。
    建议每工作1小时休息5-10分钟，定期进行体育锻炼。
    优先级：高 - 团队成员应在月底前制定个人健康计划。

    ### 5. 设定清晰的任务目标
    使用项目管理工具（如Jira、Trello）跟踪任务进度。
    每日开始时列出当日待办事项，结束时回顾完成情况。

    ## 结论
    成功的远程工作需要自律、沟通和正确的工具支持。
    管理层应为团队提供必要的资源和支持，定期评估远程工作政策的效果。
    预期在未来6个月内，远程工作效率将提升20%以上。
    """
    
    logger.info(f"Processing document of length: {len(sample_document)} characters")
    
    # 执行并行处理并获取各个结果
    processing_results = parallel_processing.invoke({"document": sample_document})
    
    print("\n" + "=" * 60)
    print("   文档并行处理结果")
    print("=" * 60)
    
    print(f"\n【摘要提取】\n{processing_results['summary']}")
    print(f"\n【问题生成】\n{processing_results['questions']}")
    print(f"\n【关键词提取】\n{processing_results['keywords']}")
    print(f"\n【行动项提取】\n{processing_results['actions']}")
    
    # 生成综合报告
    final_report = full_chain.invoke({"document": sample_document})
    
    print(f"\n【综合处理报告】\n{final_report}")
    print("=" * 60 + "\n")


def practice_parallel_comparison():
    """
    练习 3: Parallel Comparison (并行比较分析)
    场景: 对同一主题从不同角度并行生成内容，然后进行比较
    演示: 展示并行生成和后续比较的高级用法
    """
    logger.info("--- Practice 3: Parallel Comparison ---")
    
    # 1. 加载模型
    llm = model_loader.load_llm()
    logger.info(f"Using model: {model_loader.active_model_id}")
    
    # 2. 定义不同角度的生成 Prompt
    
    # 乐观角度
    prompt_optimistic = ChatPromptTemplate.from_template(
        """从乐观和支持的角度，写一篇关于"{topic}"的短文。
强调积极的方面、机遇和好处。篇幅控制在150字左右。"""
    )
    
    # 批判角度
    prompt_critical = ChatPromptTemplate.from_template(
        """从批判和审慎的角度，写一篇关于"{topic}"的短文。
强调潜在的风险、挑战和需要注意的问题。篇幅控制在150字左右。"""
    )
    
    # 中立角度
    prompt_neutral = ChatPromptTemplate.from_template(
        """从中立和客观的角度，写一篇关于"{topic}"的短文。
平衡地呈现事实，不偏不倚。篇幅控制在150字左右。"""
    )
    
    # 3. 构建各个 Chain
    optimistic_chain = prompt_optimistic | llm | StrOutputParser()
    critical_chain = prompt_critical | llm | StrOutputParser()
    neutral_chain = prompt_neutral | llm | StrOutputParser()
    
    # 4. 并行生成不同角度的内容
    parallel_generation = RunnableParallel({
        "optimistic_view": optimistic_chain,
        "critical_view": critical_chain,
        "neutral_view": neutral_chain,
        "topic": RunnablePassthrough()
    })
    
    # 5. 比较分析 Chain
    prompt_comparison = ChatPromptTemplate.from_template(
        """基于以下关于"{topic}"的不同观点，进行全面比较分析：

【乐观观点】
{optimistic_view}

【批判观点】
{critical_view}

【中立观点】
{neutral_view}

请提供：
1. 各观点的核心差异
2. 每种观点的合理性和局限性
3. 综合后的平衡观点
4. 对该主题的总体建议"""
    )
    
    comparison_chain = prompt_comparison | llm | StrOutputParser()
    
    # 6. 组合完整流程
    full_chain = parallel_generation | comparison_chain
    
    # 7. 执行分析
    topic = "人工智能在医疗诊断中的应用"
    logger.info(f"Analyzing topic from multiple perspectives: {topic}")
    
    # 获取各个角度的内容
    perspectives = parallel_generation.invoke({"topic": topic})
    
    print("\n" + "=" * 60)
    print("   多视角并行分析与比较")
    print("=" * 60)
    
    print(f"\n【乐观观点】\n{perspectives['optimistic_view']}")
    print(f"\n【批判观点】\n{perspectives['critical_view']}")
    print(f"\n【中立观点】\n{perspectives['neutral_view']}")
    
    # 生成比较分析
    comparison_result = full_chain.invoke({"topic": topic})
    
    print(f"\n【综合比较分析】\n{comparison_result}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("=" * 60)
    print("   Chapter 3: Parallelization (并行化模式) - Practice Code")
    print("=" * 60)
    
    # 练习 1: 多维度文本分析
    practice_multi_aspect_analysis()
    
    # 练习 2: 文档并行处理
    practice_document_processing()
    
    # 练习 3: 多视角并行比较
    practice_parallel_comparison()
    
    print("\n" + "=" * 60)
    print("   All practices completed!")
    print("=" * 60)
