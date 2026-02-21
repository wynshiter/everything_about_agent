/**
 * Diagram Module
 * Mermaid流程图管理
 */

// 图表缩放和交互
let currentZoom = 1;

// 初始化图表
function initDiagramControls() {
    // 添加拖拽支持
    const wrapper = document.getElementById('mermaidWrapper');
    if (wrapper) {
        let isDragging = false;
        let startX, startY, scrollLeft, scrollTop;
        
        wrapper.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.pageX - wrapper.offsetLeft;
            startY = e.pageY - wrapper.offsetTop;
            scrollLeft = wrapper.scrollLeft;
            scrollTop = wrapper.scrollTop;
        });
        
        wrapper.addEventListener('mouseleave', () => {
            isDragging = false;
        });
        
        wrapper.addEventListener('mouseup', () => {
            isDragging = false;
        });
        
        wrapper.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - wrapper.offsetLeft;
            const y = e.pageY - wrapper.offsetTop;
            const walkX = (x - startX) * 2;
            const walkY = (y - startY) * 2;
            wrapper.scrollLeft = scrollLeft - walkX;
            wrapper.scrollTop = scrollTop - walkY;
        });
    }
}

// 图表类型定义
const DIAGRAM_TEMPLATES = {
    flowchart: (nodes) => `flowchart TD
    ${nodes.map((n, i) => `${String.fromCharCode(65 + i)}[${n.label}]`).join('\n    ')}
    ${nodes.slice(0, -1).map((n, i) => `${String.fromCharCode(65 + i)} --> ${String.fromCharCode(66 + i)}`).join('\n    ')}`,
    
    sequence: (actors) => `sequenceDiagram
    ${actors.map(a => `participant ${a}`).join('\n    ')}
    ${actors.slice(0, -1).map((a, i) => `${a}->>${actors[i + 1]}: 消息${i + 1}`).join('\n    ')}`,
    
    state: (states) => `stateDiagram-v2
    ${states.map((s, i) => `state${i + 1} : ${s}`).join('\n    ')}
    ${states.slice(0, -1).map((s, i) => `state${i + 1} --> state${i + 2}`).join('\n    ')}`
};

// 动态生成图表
function generateDiagram(type, data) {
    const template = DIAGRAM_TEMPLATES[type];
    if (!template) return '';
    
    return template(data);
}

// 导出图表为SVG
function exportDiagramAsSVG() {
    const svg = document.querySelector('#mermaidDiagram svg');
    if (!svg) return;
    
    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentPattern?.id || 'diagram'}.svg`;
    a.click();
    
    URL.revokeObjectURL(url);
}

// 图表高亮功能
function highlightNode(nodeId) {
    const nodes = document.querySelectorAll('#mermaidDiagram .node');
    nodes.forEach(node => {
        node.style.opacity = node.id === nodeId ? '1' : '0.5';
    });
}

function resetHighlight() {
    const nodes = document.querySelectorAll('#mermaidDiagram .node');
    nodes.forEach(node => {
        node.style.opacity = '1';
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initDiagramControls();
});
