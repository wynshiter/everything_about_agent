/**
 * Agent Design Patterns Data
 * 设计模式数据配置
 */

const PATTERNS_DATA = {
    chaining: {
        id: 'chaining',
        key: 'chaining',
        chapter: 1,
        title: 'Prompt Chaining',
        subtitle: '提示链模式',
        level: 'basic',
        description: '将复杂任务分解为顺序执行的子任务，每个步骤的输出作为下一个步骤的输入。',
        tags: ['顺序执行', '任务分解', 'LCEL'],
        pptFile: '../practices/Agent_design/chapter1_chaining/Chapter1_Prompt_Chaining.pptx',
        docFile: '../practices/Agent_design/chapter1_chaining/index.md',
        codeFile: '../../src/agents/patterns/chaining.py',
        slides: [
            { title: '背景与动机', content: '顺序执行子任务' },
            { title: '核心概念', content: '任务分解、顺序执行' },
            { title: '实现方式', content: 'LCEL链式调用' }
        ],
        diagram: `flowchart TD
    A[用户输入] --> B[步骤1: 分析任务]
    B --> C[步骤2: 生成内容]
    C --> D[步骤3: 格式化输出]
    D --> E[最终结果]
    
    style A fill:#e3f2fd
    style E fill:#c8e6c9
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#fff3e0`,
        diagramSteps: [
            { title: '输入处理', desc: '接收用户输入并进行预处理' },
            { title: '步骤执行', desc: '按顺序执行每个处理步骤' },
            { title: '结果输出', desc: '返回最终处理结果' }
        ]
    },
    routing: {
        id: 'routing',
        key: 'routing',
        chapter: 2,
        title: 'Routing',
        subtitle: '路由模式',
        level: 'basic',
        description: '根据输入内容动态选择不同的处理路径，实现条件分支和决策。',
        tags: ['条件分支', '动态选择', 'RunnableBranch'],
        pptFile: '../practices/Agent_design/chapter2_routing/Chapter2_Routing.pptx',
        docFile: '../practices/Agent_design/chapter2_routing/index.md',
        codeFile: '../../src/agents/patterns/routing.py',
        slides: [
            { title: '背景与动机', content: '动态路径选择' },
            { title: '核心概念', content: '意图识别、路由分发' },
            { title: '实现方式', content: 'RunnableBranch' }
        ],
        diagram: `flowchart TD
    A[用户输入] --> B{意图分类}
    B -->|查询| C[查询处理分支]
    B -->|预订| D[预订处理分支]
    B -->|投诉| E[投诉处理分支]
    C --> F[返回结果]
    D --> F
    E --> F
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style F fill:#c8e6c9`,
        diagramSteps: [
            { title: '意图识别', desc: '分析用户输入判断意图类型' },
            { title: '路由分发', desc: '根据意图选择处理分支' },
            { title: '分支处理', desc: '执行对应分支的处理逻辑' }
        ]
    },
    parallelization: {
        id: 'parallelization',
        key: 'parallelization',
        chapter: 3,
        title: 'Parallelization',
        subtitle: '并行化模式',
        level: 'basic',
        description: '同时执行多个独立的子任务，减少总体执行时间，提高效率。',
        tags: ['并发执行', 'RunnableParallel', '异步'],
        pptFile: '../practices/Agent_design/chapter3_parallelization/Chapter3_并行化.pptx',
        docFile: '../practices/Agent_design/chapter3_parallelization/index.md',
        codeFile: '../../src/agents/patterns/parallelization.py',
        slides: [
            { title: '背景与动机', content: '顺序执行效率低' },
            { title: '核心概念', content: '独立任务并行' },
            { title: '实现方式', content: 'RunnableParallel' }
        ],
        diagram: `flowchart TD
    A[用户输入] --> B[任务分发]
    B --> C[分支1]
    B --> D[分支2]
    B --> E[分支3]
    C --> F[结果聚合]
    D --> F
    E --> F
    F --> G[最终结果]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style F fill:#fff3e0
    style G fill:#c8e6c9`,
        diagramSteps: [
            { title: '任务分发', desc: '将输入分发给多个并行分支' },
            { title: '并行执行', desc: '多个分支同时处理' },
            { title: '结果聚合', desc: '合并各分支结果' }
        ]
    },
    reflection: {
        id: 'reflection',
        key: 'reflection',
        chapter: 4,
        title: 'Reflection',
        subtitle: '反思模式',
        level: 'basic',
        description: 'Agent评估自己的输出并进行改进，通过迭代提高输出质量。',
        tags: ['自我评估', '迭代改进', '质量提升'],
        pptFile: '../practices/Agent_design/chapter4_reflection/Chapter4_反思.pptx',
        docFile: '../practices/Agent_design/chapter4_reflection/index.md',
        codeFile: '../../src/agents/patterns/reflection.py',
        slides: [
            { title: '背景与动机', content: '初始输出可能不完美' },
            { title: '核心概念', content: '评估-反馈-改进' },
            { title: 'Producer-Critic', content: '生成者-批评者模式' }
        ],
        diagram: `flowchart TD
    A[任务输入] --> B[生成输出]
    B --> C{评估检查}
    C -->|满意| D[返回结果]
    C -->|需改进| E[生成反馈]
    E --> F[改进输出]
    F --> C
    
    style A fill:#e3f2fd
    style D fill:#c8e6c9
    style C fill:#fff3e0`,
        diagramSteps: [
            { title: '生成输出', desc: 'Agent生成初始输出' },
            { title: '评估检查', desc: '评估输出质量' },
            { title: '迭代改进', desc: '根据反馈持续改进' }
        ]
    },
    tool_use: {
        id: 'tool_use',
        key: 'tool_use',
        chapter: 5,
        title: 'Tool Use',
        subtitle: '工具使用模式',
        level: 'intermediate',
        description: '扩展Agent能力，通过调用外部工具完成LLM无法直接执行的任务。',
        tags: ['工具调用', 'Function Calling', '能力扩展'],
        pptFile: '../practices/Agent_design/chapter5_tool_use/Chapter5_工具使用.pptx',
        docFile: '../practices/Agent_design/chapter5_tool_use/index.md',
        codeFile: '../../src/agents/patterns/tool_use.py',
        slides: [
            { title: '背景与动机', content: 'LLM能力有限' },
            { title: '核心概念', content: '工具定义、调用、执行' },
            { title: '实现方式', content: 'bind_tools' }
        ],
        diagram: `flowchart TD
    A[用户请求] --> B{需要工具?}
    B -->|是| C[选择工具]
    C --> D[执行工具]
    D --> E[处理结果]
    B -->|否| F[直接回答]
    E --> G[返回结果]
    F --> G
    
    style A fill:#e3f2fd
    style G fill:#c8e6c9
    style B fill:#fff3e0
    style C fill:#fce4ec
    style D fill:#fce4ec`,
        diagramSteps: [
            { title: '判断需求', desc: '分析是否需要工具支持' },
            { title: '工具选择', desc: '选择合适的工具' },
            { title: '执行返回', desc: '执行工具并返回结果' }
        ]
    },
    planning: {
        id: 'planning',
        key: 'planning',
        chapter: 6,
        title: 'Planning',
        subtitle: '规划模式',
        level: 'intermediate',
        description: '制定计划后再执行，提高复杂任务完成的可靠性和效率。',
        tags: ['任务规划', '步骤分解', '执行跟踪'],
        pptFile: '../practices/Agent_design/chapter6_planning/Chapter6_规划.pptx',
        docFile: '../practices/Agent_design/chapter6_planning/index.md',
        codeFile: '../../src/agents/patterns/planning.py',
        slides: [
            { title: '背景与动机', content: '复杂任务需要规划' },
            { title: '核心概念', content: '目标分解、计划制定' },
            { title: '实现方式', content: 'Plan-and-Execute' }
        ],
        diagram: `flowchart TD
    A[目标输入] --> B[制定计划]
    B --> C[步骤列表]
    C --> D[执行步骤1]
    D --> E[执行步骤2]
    E --> F[执行步骤N]
    F --> G[完成任务]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style G fill:#c8e6c9`,
        diagramSteps: [
            { title: '目标分析', desc: '理解最终目标' },
            { title: '计划制定', desc: '分解为具体步骤' },
            { title: '逐步执行', desc: '按计划执行每个步骤' }
        ]
    },
    multi_agent: {
        id: 'multi_agent',
        key: 'multi_agent',
        chapter: 7,
        title: 'Multi-Agent Collaboration',
        subtitle: '多Agent协作模式',
        level: 'intermediate',
        description: '多个Agent协作完成任务，各司其职，模拟团队协作。',
        tags: ['多Agent', '协作', '角色分工'],
        pptFile: '../practices/Agent_design/chapter7_multi_agent/Chapter7_多Agent协作.pptx',
        docFile: '../practices/Agent_design/chapter7_multi_agent/index.md',
        codeFile: '../../src/agents/patterns/multi_agent.py',
        slides: [
            { title: '背景与动机', content: '单一Agent能力有限' },
            { title: '核心概念', content: '角色定义、协作模式' },
            { title: '实现方式', content: 'SequentialAgent' }
        ],
        diagram: `flowchart TD
    A[任务输入] --> B[协调Agent]
    B --> C[Agent 1: 研究员]
    B --> D[Agent 2: 分析师]
    B --> E[Agent 3: 写作者]
    C --> F[结果整合]
    D --> F
    E --> F
    F --> G[最终输出]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style G fill:#c8e6c9`,
        diagramSteps: [
            { title: '任务分配', desc: '协调者分配任务' },
            { title: '并行处理', desc: '各Agent独立处理' },
            { title: '结果整合', desc: '合并各Agent结果' }
        ]
    },
    memory: {
        id: 'memory',
        key: 'memory',
        chapter: 8,
        title: 'Memory Management',
        subtitle: '记忆管理模式',
        level: 'intermediate',
        description: '管理Agent的记忆，支持多轮对话和长期学习。',
        tags: ['记忆管理', '上下文', '持久化'],
        pptFile: '../practices/Agent_design/chapter8_memory/Chapter8_记忆管理.pptx',
        docFile: '../practices/Agent_design/chapter8_memory/index.md',
        codeFile: '../../src/agents/patterns/memory.py',
        slides: [
            { title: '背景与动机', content: 'LLM无状态' },
            { title: '核心概念', content: '短期/长期记忆' },
            { title: '实现方式', content: 'ConversationBuffer' }
        ],
        diagram: `flowchart TD
    A[用户输入] --> B[检索记忆]
    B --> C[上下文构建]
    C --> D[生成响应]
    D --> E[更新记忆]
    E --> F[返回响应]
    
    style A fill:#e3f2fd
    style F fill:#c8e6c9
    style B fill:#fff3e0
    style E fill:#fff3e0`,
        diagramSteps: [
            { title: '记忆检索', desc: '从存储中检索相关记忆' },
            { title: '上下文构建', desc: '构建对话上下文' },
            { title: '记忆更新', desc: '保存新的对话记忆' }
        ]
    },
    rag: {
        id: 'rag',
        key: 'rag',
        chapter: 14,
        title: 'Knowledge Retrieval (RAG)',
        subtitle: '检索增强生成',
        level: 'intermediate',
        description: '通过检索外部知识库增强生成，提供准确、最新的信息。',
        tags: ['RAG', '向量检索', '知识库'],
        pptFile: '../practices/Agent_design/chapter14_rag/Chapter14_检索增强生成.pptx',
        docFile: '../practices/Agent_design/chapter14_rag/index.md',
        codeFile: '../../src/agents/patterns/rag.py',
        slides: [
            { title: '背景与动机', content: 'LLM知识有限' },
            { title: '核心概念', content: '检索-增强-生成' },
            { title: '实现方式', content: 'VectorStore + LLM' }
        ],
        diagram: `flowchart TD
    A[用户查询] --> B[向量化]
    B --> C[相似性检索]
    C --> D[获取文档]
    D --> E[构建Prompt]
    E --> F[LLM生成]
    F --> G[返回答案]
    
    H[(知识库)] --> C
    
    style A fill:#e3f2fd
    style G fill:#c8e6c9
    style H fill:#fce4ec`,
        diagramSteps: [
            { title: '查询向量化', desc: '将查询转换为向量' },
            { title: '相似性检索', desc: '从知识库检索相关文档' },
            { title: '增强生成', desc: '基于检索内容生成回答' }
        ]
    },
    guardrails: {
        id: 'guardrails',
        key: 'guardrails',
        chapter: 18,
        title: 'Guardrails & Safety',
        subtitle: '护栏与安全模式',
        level: 'advanced',
        description: '确保AI行为安全可控，防止有害输出和攻击。',
        tags: ['安全', '护栏', '内容过滤'],
        pptFile: '../practices/Agent_design/chapter18_guardrails/Chapter18_护栏_安全.pptx',
        docFile: '../practices/Agent_design/chapter18_guardrails/index.md',
        codeFile: '../../src/agents/patterns/guardrails.py',
        slides: [
            { title: '背景与动机', content: 'AI安全风险' },
            { title: '核心概念', content: '输入/输出验证' },
            { title: '实现方式', content: 'Guardrails框架' }
        ],
        diagram: `flowchart TD
    A[用户输入] --> B{输入验证}
    B -->|通过| C[LLM处理]
    B -->|拒绝| D[返回错误]
    C --> E{输出检查}
    E -->|安全| F[返回结果]
    E -->|敏感| G[过滤/修改]
    G --> F
    
    style A fill:#e3f2fd
    style F fill:#c8e6c9
    style B fill:#fff3e0
    style E fill:#fff3e0`,
        diagramSteps: [
            { title: '输入验证', desc: '检查用户输入是否安全' },
            { title: '处理生成', desc: 'LLM处理生成响应' },
            { title: '输出检查', desc: '过滤敏感内容' }
        ]
    }
};

// 章节列表（用于首页展示）
const CHAPTERS_LIST = [
    { id: 'chaining', chapter: 1, title: 'Prompt Chaining', subtitle: '提示链模式', level: 'basic' },
    { id: 'routing', chapter: 2, title: 'Routing', subtitle: '路由模式', level: 'basic' },
    { id: 'parallelization', chapter: 3, title: 'Parallelization', subtitle: '并行化模式', level: 'basic' },
    { id: 'reflection', chapter: 4, title: 'Reflection', subtitle: '反思模式', level: 'basic' },
    { id: 'tool_use', chapter: 5, title: 'Tool Use', subtitle: '工具使用模式', level: 'intermediate' },
    { id: 'planning', chapter: 6, title: 'Planning', subtitle: '规划模式', level: 'intermediate' },
    { id: 'multi_agent', chapter: 7, title: 'Multi-Agent', subtitle: '多Agent协作模式', level: 'intermediate' },
    { id: 'memory', chapter: 8, title: 'Memory', subtitle: '记忆管理模式', level: 'intermediate' },
    { id: 'learning', chapter: 9, title: 'Learning', subtitle: '学习与适应模式', level: 'intermediate' },
    { id: 'mcp', chapter: 10, title: 'MCP', subtitle: '模型上下文协议', level: 'intermediate' },
    { id: 'goal_setting', chapter: 11, title: 'Goal Setting', subtitle: '目标设定与监控', level: 'intermediate' },
    { id: 'exception_handling', chapter: 12, title: 'Exception Handling', subtitle: '异常处理与恢复', level: 'intermediate' },
    { id: 'human_in_loop', chapter: 13, title: 'Human-in-Loop', subtitle: '人机协作模式', level: 'intermediate' },
    { id: 'rag', chapter: 14, title: 'RAG', subtitle: '检索增强生成', level: 'intermediate' },
    { id: 'a2a', chapter: 15, title: 'A2A', subtitle: 'Agent间通信', level: 'intermediate' },
    { id: 'reasoning', chapter: 17, title: 'Reasoning', subtitle: '推理技术', level: 'advanced' },
    { id: 'guardrails', chapter: 18, title: 'Guardrails', subtitle: '护栏与安全模式', level: 'advanced' },
    { id: 'evaluation', chapter: 19, title: 'Evaluation', subtitle: '评估与监控', level: 'advanced' },
    { id: 'prioritization', chapter: 20, title: 'Prioritization', subtitle: '优先级管理', level: 'advanced' },
    { id: 'exploration', chapter: 21, title: 'Exploration', subtitle: '探索与发现', level: 'advanced' }
];

// 获取模式数据
function getPatternData(patternId) {
    return PATTERNS_DATA[patternId] || null;
}

// 获取所有章节
function getAllChapters() {
    return CHAPTERS_LIST;
}

// 根据难度筛选
function filterByLevel(level) {
    if (level === 'all') return CHAPTERS_LIST;
    return CHAPTERS_LIST.filter(ch => ch.level === level);
}

// 搜索模式
function searchPatterns(query) {
    const q = query.toLowerCase();
    return CHAPTERS_LIST.filter(ch => 
        ch.title.toLowerCase().includes(q) || 
        ch.subtitle.toLowerCase().includes(q)
    );
}
