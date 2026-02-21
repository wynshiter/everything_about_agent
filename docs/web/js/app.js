/**
 * Main Application Logic
 * 主应用逻辑
 */

// 当前状态
let currentPattern = null;
let currentSlide = 0;
let totalSlides = 9;

// 初始化首页
function initHomePage() {
    renderPatternCards();
    setupEventListeners();
}

// 初始化详情页
function initPatternPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const patternId = urlParams.get('pattern') || 'chaining';
    
    loadPattern(patternId);
    setupTabNavigation();
    initMermaid();
}

// 渲染模式卡片
function renderPatternCards() {
    const grid = document.getElementById('patternsGrid');
    if (!grid) return;
    
    const chapters = getAllChapters();
    grid.innerHTML = chapters.map(ch => {
        const data = getPatternData(ch.id);
        return `
            <div class="pattern-card fade-in" data-pattern="${ch.id}" data-level="${ch.level}">
                <div class="card-header ${ch.level}">
                    <span class="card-badge">${getLevelText(ch.level)}</span>
                    <div class="card-chapter">Chapter ${ch.chapter}</div>
                    <h3 class="card-title">${ch.title}</h3>
                    <p class="card-subtitle">${ch.subtitle}</p>
                </div>
                <div class="card-body">
                    <p class="card-description">${data ? data.description : '正在完善...'}</p>
                    <div class="card-tags">
                        ${(data?.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                    <div class="card-footer">
                        <div class="card-stats">
                            <span class="stat"><i class="fas fa-file-powerpoint"></i> 9页</span>
                            <span class="stat"><i class="fas fa-code"></i> 2示例</span>
                        </div>
                        <a href="pattern.html?pattern=${ch.id}" class="card-link">
                            开始学习 <i class="fas fa-arrow-right"></i>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 获取难度文本
function getLevelText(level) {
    const map = {
        'basic': '基础',
        'intermediate': '进阶',
        'advanced': '高级'
    };
    return map[level] || level;
}

// 设置事件监听
function setupEventListeners() {
    // 筛选按钮
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.dataset.filter;
            filterCards(filter);
        });
    });
    
    // 搜索框
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            searchCards(query);
        });
    }
    
    // 卡片点击
    document.querySelectorAll('.pattern-card').forEach(card => {
        card.addEventListener('click', function() {
            const patternId = this.dataset.pattern;
            window.location.href = `pattern.html?pattern=${patternId}`;
        });
    });
}

// 筛选卡片
function filterCards(level) {
    const cards = document.querySelectorAll('.pattern-card');
    cards.forEach(card => {
        if (level === 'all' || card.dataset.level === level) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// 搜索卡片
function searchCards(query) {
    const results = searchPatterns(query);
    const cards = document.querySelectorAll('.pattern-card');
    
    cards.forEach(card => {
        const patternId = card.dataset.pattern;
        if (query === '' || results.some(r => r.id === patternId)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// 加载模式详情
function loadPattern(patternId) {
    currentPattern = getPatternData(patternId);
    if (!currentPattern) {
        console.error('Pattern not found:', patternId);
        return;
    }
    
    // 更新页面标题和内容
    document.title = `${currentPattern.title} - Agent Design Patterns`;
    document.getElementById('patternTitle').textContent = currentPattern.title;
    document.getElementById('patternSubtitle').textContent = currentPattern.subtitle;
    document.getElementById('patternDescription').textContent = currentPattern.description;
    document.getElementById('patternLevel').textContent = getLevelText(currentPattern.level);
    document.getElementById('patternLevel').className = `pattern-badge ${currentPattern.level}`;
    document.getElementById('currentPatternName').textContent = currentPattern.title;
    document.getElementById('breadcrumbPattern').textContent = currentPattern.subtitle;
    
    // 设置资源链接
    if (currentPattern.docFile) {
        document.getElementById('docLink').href = currentPattern.docFile;
    }
    if (currentPattern.codeFile) {
        document.getElementById('codeLink').href = currentPattern.codeFile;
    }
    
    // 初始化PPT
    initPPTViewer();
    
    // 初始化流程图
    initDiagram();
}

// 设置标签导航
function setupTabNavigation() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // 更新按钮状态
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 切换内容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// 初始化PPT查看器
function initPPTViewer() {
    if (!currentPattern) return;
    
    totalSlides = currentPattern.slides?.length || 9;
    document.getElementById('totalSlides').textContent = totalSlides;
    currentSlide = 0;
    
    renderThumbnails();
    showSlide(0);
}

// 渲染缩略图
function renderThumbnails() {
    const container = document.getElementById('pptThumbnails');
    if (!container || !currentPattern.slides) return;
    
    container.innerHTML = currentPattern.slides.map((slide, index) => `
        <div class="thumbnail ${index === 0 ? 'active' : ''}" onclick="goToSlide(${index})">
            <div class="thumbnail-content">第${index + 1}页</div>
        </div>
    `).join('');
}

// 显示幻灯片
function showSlide(index) {
    if (!currentPattern || !currentPattern.slides) return;
    
    currentSlide = index;
    document.getElementById('currentSlide').textContent = index + 1;
    
    const slideData = currentPattern.slides[index];
    const slideEl = document.getElementById('pptSlide');
    
    if (slideData) {
        slideEl.innerHTML = `
            <div class="slide-content" style="padding: 40px; height: 100%; display: flex; flex-direction: column;">
                <h2 style="color: #1e293b; font-size: 24px; margin-bottom: 20px;">${slideData.title}</h2>
                <p style="color: #475569; font-size: 16px;">${slideData.content}</p>
            </div>
        `;
    }
    
    // 更新缩略图高亮
    document.querySelectorAll('.thumbnail').forEach((thumb, i) => {
        thumb.classList.toggle('active', i === index);
    });
}

// 幻灯片导航
function prevSlide() {
    if (currentSlide > 0) {
        showSlide(currentSlide - 1);
    }
}

function nextSlide() {
    if (currentSlide < totalSlides - 1) {
        showSlide(currentSlide + 1);
    }
}

function goToSlide(index) {
    showSlide(index);
}

// 全屏切换
function toggleFullscreen() {
    const container = document.getElementById('pptSlideContainer');
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        container.requestFullscreen();
    }
}

// 下载PPT
function downloadPPT() {
    if (currentPattern && currentPattern.pptFile) {
        window.open(currentPattern.pptFile, '_blank');
    }
}

// 分享
function sharePattern() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        alert('链接已复制到剪贴板');
    });
}

// 初始化Mermaid
function initMermaid() {
    mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        themeVariables: {
            primaryColor: '#3b82f6',
            primaryTextColor: '#fff',
            primaryBorderColor: '#2563eb',
            lineColor: '#64748b',
            secondaryColor: '#f1f5f9',
            tertiaryColor: '#e2e8f0'
        }
    });
}

// 初始化流程图
function initDiagram() {
    if (!currentPattern || !currentPattern.diagram) return;
    
    const diagramEl = document.getElementById('mermaidDiagram');
    diagramEl.textContent = currentPattern.diagram;
    
    mermaid.run({
        nodes: [diagramEl]
    }).then(() => {
        renderDiagramSteps();
    });
}

// 渲染流程图步骤说明
function renderDiagramSteps() {
    if (!currentPattern || !currentPattern.diagramSteps) return;
    
    const container = document.getElementById('explanationSteps');
    container.innerHTML = currentPattern.diagramSteps.map((step, index) => `
        <div class="step-item">
            <div class="step-number">${index + 1}</div>
            <div class="step-content">
                <h4>${step.title}</h4>
                <p>${step.desc}</p>
            </div>
        </div>
    `).join('');
}

// 流程图缩放
let diagramZoom = 1;

function zoomDiagram(direction) {
    if (direction === 'in') {
        diagramZoom = Math.min(diagramZoom + 0.1, 2);
    } else {
        diagramZoom = Math.max(diagramZoom - 0.1, 0.5);
    }
    
    const wrapper = document.getElementById('mermaidWrapper');
    wrapper.style.transform = `scale(${diagramZoom})`;
}

function resetDiagram() {
    diagramZoom = 1;
    const wrapper = document.getElementById('mermaidWrapper');
    wrapper.style.transform = 'scale(1)';
}

// 移动端菜单
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('active');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('patternsGrid')) {
        initHomePage();
    }
});
