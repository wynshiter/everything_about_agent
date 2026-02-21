/**
 * Chat Module
 * 实时聊天验证功能
 */

// 聊天状态
let chatHistory = [];

// 发送消息
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 添加用户消息
    addMessage('user', message);
    input.value = '';
    
    // 模拟AI响应
    setTimeout(() => {
        const response = generateResponse(message);
        addMessage('assistant', response);
    }, 500);
}

// 添加消息到聊天区域
function addMessage(role, content) {
    const container = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'assistant' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content"><p>${content}</p></div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    // 保存历史
    chatHistory.push({ role, content });
}

// 生成响应（模拟AI回答）
function generateResponse(question) {
    if (!currentPattern) {
        return '请先选择一个设计模式进行学习。';
    }
    
    const q = question.toLowerCase();
    
    // 基于关键词生成响应
    if (q.includes('概念') || q.includes('是什么') || q.includes('介绍')) {
        return `${currentPattern.subtitle}是Agent设计中的重要模式。${currentPattern.description}`;
    }
    
    if (q.includes('场景') || q.includes('应用') || q.includes('什么时候')) {
        const scenarios = [
            '信息收集与研究场景',
            '数据处理与分析场景',
            '多API调用场景',
            '内容生成场景',
            '验证与检查场景'
        ];
        return `${currentPattern.title}适用于以下场景：\n${scenarios.map((s, i) => `${i + 1}. ${s}`).join('\n')}`;
    }
    
    if (q.includes('代码') || q.includes('实现') || q.includes('如何')) {
        return `${currentPattern.title}可以使用LangChain的${currentPattern.tags?.[0] || '相关组件'}来实现。建议查看代码示例了解具体实现细节。`;
    }
    
    if (q.includes('对比') || q.includes('区别') || q.includes('优劣')) {
        return `${currentPattern.title}与其他模式的主要区别在于其处理任务的${currentPattern.level === 'basic' ? '基础方式' : currentPattern.level === 'intermediate' ? '进阶特性' : '高级能力'}。具体对比请查看PPT中的对比分析部分。`;
    }
    
    if (q.includes('优势') || q.includes('优点') || q.includes('好处')) {
        return `${currentPattern.title}的主要优势：\n1. 提高效率\n2. 降低复杂度\n3. 提升可靠性\n详细内容请查看PPT总结部分。`;
    }
    
    if (q.includes('注意') || q.includes('局限') || q.includes('缺点')) {
        return `使用${currentPattern.title}时需要注意：\n1. 适用场景的边界\n2. 资源消耗考量\n3. 与其他模式的配合`;
    }
    
    // 默认响应
    return `感谢您的问题！关于${currentPattern.title}，建议从以下几个角度理解：\n1. 核心概念和原理\n2. 适用场景和案例\n3. 代码实现方式\n您可以点击左侧的快速提问按钮获取更多信息。`;
}

// 快速提问
function sendQuickPrompt(type) {
    const prompts = {
        '概念': `请介绍一下${currentPattern?.title || '这个模式'}的核心概念`,
        '场景': `${currentPattern?.title || '这个模式'}有哪些典型应用场景？`,
        '代码': `${currentPattern?.title || '这个模式'}的代码实现要点是什么？`,
        '对比': `${currentPattern?.title || '这个模式'}与其他模式有什么区别？`
    };
    
    const input = document.getElementById('chatInput');
    input.value = prompts[type];
    sendMessage();
}

// 键盘事件
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});
