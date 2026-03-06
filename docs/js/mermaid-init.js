// Mermaid 初始化脚本
document.addEventListener('DOMContentLoaded', function() {
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            },
            sequence: {
                useMaxWidth: true
            },
            gantt: {
                useMaxWidth: true
            }
        });
        console.log('[Mermaid] Initialized successfully');
    } else {
        console.warn('[Mermaid] Library not loaded');
    }
});
