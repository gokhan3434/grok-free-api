import { dashboardMetrics, salesData, usersData, reportsData } from './data.js';

const chartInstances = {};

const colors = {
    primary: '#38bdf8',
    secondary: '#818cf8',
    tertiary: '#34d399',
    muted: 'rgba(148, 163, 184, 0.35)'
};

function qs(selector) {
    return document.querySelector(selector);
}

function qsa(selector) {
    return Array.from(document.querySelectorAll(selector));
}

function setActiveNav(pathname) {
    const links = qsa('.nav-links a');
    links.forEach(link => {
        const isActive = link.getAttribute('href').includes(pathname);
        link.classList.toggle('active', isActive);
    });
}

function renderMetricCards() {
    const metricElements = qsa('[data-metric]');
    metricElements.forEach(card => {
        const key = card.dataset.metric;
        const metric = dashboardMetrics[key];
        if (!metric) return;

        const valueEl = card.querySelector('.metric-value');
        const changeEl = card.querySelector('.metric-change span.value');
        const badgeEl = card.querySelector('.metric-change span.badge');

        if (valueEl) {
            valueEl.textContent = metric.value;
        }

        if (changeEl) {
            changeEl.textContent = `${metric.change > 0 ? '+' : ''}${metric.change}%`;
        }

        if (badgeEl) {
            badgeEl.textContent = metric.change > 0 ? 'Artış' : 'Düşüş';
        }

        const changeWrapper = card.querySelector('.metric-change');
        changeWrapper?.classList.toggle('negative', metric.change < 0);

        const ctx = card.querySelector('canvas');
        if (ctx) {
            createSparkline(ctx, metric.trend, metric.change < 0 ? colors.secondary : colors.primary);
        }
    });
}

function createSparkline(canvas, data, color) {
    const id =
        canvas.dataset.chartId || (window.crypto?.randomUUID?.() ?? `chart-${Math.random().toString(16).slice(2)}`);
    canvas.dataset.chartId = id;
    if (chartInstances[id]) {
        chartInstances[id].destroy();
    }

    chartInstances[id] = new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.map((_, index) => index + 1),
            datasets: [
                {
                    data,
                    borderColor: color,
                    borderWidth: 2,
                    fill: true,
                    backgroundColor: `${color}33`,
                    pointRadius: 0,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

function renderDashboard() {
    const revenueCanvas = qs('#revenueChart');
    if (!revenueCanvas) return;

    new Chart(revenueCanvas, {
        type: 'line',
        data: {
            labels: salesData.categories,
            datasets: [
                {
                    label: 'Online Gelir',
                    data: salesData.revenueByChannel.online,
                    borderColor: colors.primary,
                    backgroundColor: `${colors.primary}33`,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Mağaza Geliri',
                    data: salesData.revenueByChannel.retail,
                    borderColor: colors.secondary,
                    backgroundColor: `${colors.secondary}33`,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#e2e8f0'
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                }
            }
        }
    });

    const conversionCanvas = qs('#conversionChart');
    new Chart(conversionCanvas, {
        type: 'bar',
        data: {
            labels: ['Organik', 'Reklam', 'Referans', 'Etkinlik'],
            datasets: [
                {
                    label: 'Dönüşüm',
                    data: [4.6, 5.1, 3.8, 6.2],
                    backgroundColor: [colors.primary, colors.secondary, colors.primary, colors.tertiary],
                    borderRadius: 8,
                    maxBarThickness: 36
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { display: false }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                }
            }
        }
    });

    const tableBody = qs('#topCustomers tbody');
    const customers = [
        { name: 'NovaTech', plan: 'Kurumsal', mrr: '$9,800', activity: '1 saat önce', status: 'Aktif' },
        { name: 'DataFlow', plan: 'KOBİ', mrr: '$4,600', activity: '18 dk önce', status: 'Aktif' },
        { name: 'Visionary Labs', plan: 'Startup', mrr: '$2,950', activity: '26 dk önce', status: 'İşlemde' },
        { name: 'QuantumSoft', plan: 'Kurumsal', mrr: '$11,200', activity: '2 saat önce', status: 'Risk' }
    ];

    if (tableBody) {
        tableBody.innerHTML = customers
            .map(
                customer => `
                <tr>
                    <td>${customer.name}</td>
                    <td>${customer.plan}</td>
                    <td>${customer.mrr}</td>
                    <td>${customer.activity}</td>
                    <td>
                        <span class="status-badge ${
                            customer.status === 'Aktif' ? 'success' : customer.status === 'Risk' ? 'danger' : 'warning'
                        }">${customer.status}</span>
                    </td>
                </tr>
            `
            )
            .join('');
    }
}

function renderSalesPage() {
    const revenueBreakdownCanvas = qs('#channelBreakdown');
    if (!revenueBreakdownCanvas) return;

    new Chart(revenueBreakdownCanvas, {
        type: 'bar',
        data: {
            labels: salesData.categories,
            datasets: [
                {
                    label: 'Online',
                    data: salesData.revenueByChannel.online,
                    backgroundColor: `${colors.primary}aa`
                },
                {
                    label: 'Mağaza',
                    data: salesData.revenueByChannel.retail,
                    backgroundColor: `${colors.secondary}aa`
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { display: false }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.08)' }
                }
            }
        }
    });

    const pipelineCanvas = qs('#pipelineChart');
    new Chart(pipelineCanvas, {
        type: 'bar',
        data: {
            labels: salesData.pipeline.map(item => item.stage),
            datasets: [
                {
                    label: 'Fırsat Adedi',
                    data: salesData.pipeline.map(item => item.value),
                    backgroundColor: salesData.pipeline.map((_, index) => `rgba(56, 189, 248, ${1 - index * 0.15})`),
                    borderRadius: 12,
                    barThickness: 24
                }
            ]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.08)' }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { display: false }
                }
            }
        }
    });

    const productsBody = qs('#topProducts tbody');
    if (productsBody) {
        productsBody.innerHTML = salesData.topProducts
            .map(product => `
                <tr>
                    <td>${product.name}</td>
                    <td>${product.revenue.toLocaleString('tr-TR', { style: 'currency', currency: 'USD' })}</td>
                    <td>
                        <span class="metric-change ${product.growth < 0 ? 'negative' : ''}">
                            <span class="badge">${product.growth < 0 ? 'Düşüş' : 'Artış'}</span>
                            <span class="value">${product.growth}%</span>
                        </span>
                    </td>
                    <td>${product.status}</td>
                </tr>
            `)
            .join('');
    }
}

function renderUsersPage() {
    const activityCanvas = qs('#userActivityChart');
    if (!activityCanvas) return;

    new Chart(activityCanvas, {
        type: 'line',
        data: {
            labels: ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'],
            datasets: [
                {
                    label: 'Günlük Aktif Kullanıcı',
                    data: usersData.activity.dailyActive,
                    borderColor: colors.primary,
                    backgroundColor: `${colors.primary}33`,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Yeni Kayıt',
                    data: usersData.activity.newSignups,
                    borderColor: colors.secondary,
                    backgroundColor: `${colors.secondary}33`,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.08)' }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.08)' }
                }
            }
        }
    });

    const segmentsCanvas = qs('#segmentChart');
    new Chart(segmentsCanvas, {
        type: 'doughnut',
        data: {
            labels: usersData.segments.map(segment => segment.label),
            datasets: [
                {
                    data: usersData.segments.map(segment => segment.value),
                    backgroundColor: [
                        `${colors.primary}cc`,
                        `${colors.secondary}cc`,
                        `${colors.tertiary}cc`,
                        `${colors.primary}77`
                    ],
                    borderWidth: 0
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            }
        }
    });

    const retentionBody = qs('#retentionTable tbody');
    if (retentionBody) {
        retentionBody.innerHTML = usersData.retention
            .map(record => `
                <tr>
                    <td>${record.month}</td>
                    <td>${record.rate}%</td>
                    <td>
                        <div class="progress">
                            <div class="progress-bar" style="width:${record.rate}%"></div>
                        </div>
                    </td>
                </tr>
            `)
            .join('');
    }

    const ticketBody = qs('#supportTickets tbody');
    if (ticketBody) {
        ticketBody.innerHTML = usersData.supportTickets
            .map(ticket => `
                <tr>
                    <td>${ticket.id}</td>
                    <td>${ticket.user}</td>
                    <td>${ticket.priority}</td>
                    <td>${ticket.topic}</td>
                    <td>${ticket.status}</td>
                    <td>${ticket.updatedAt}</td>
                </tr>
            `)
            .join('');
    }
}

function renderReportsPage() {
    const kpiContainer = qs('#reportKpis');
    if (!kpiContainer) return;

    kpiContainer.innerHTML = reportsData.kpis
        .map(
            kpi => `
            <div class="card">
                <h3>${kpi.label}</h3>
                <p class="metric-value">${kpi.value}</p>
                <p class="metric-change ${kpi.change < 0 ? 'negative' : ''}">
                    <span class="badge">${kpi.change < 0 ? 'Düşüş' : 'Artış'}</span>
                    <span class="value">${kpi.change > 0 ? '+' : ''}${kpi.change}%</span>
                </p>
            </div>
        `
        )
        .join('');

    const quarterlyCanvas = qs('#quarterlyChart');
    new Chart(quarterlyCanvas, {
        type: 'bar',
        data: {
            labels: reportsData.quarterlyPerformance.labels,
            datasets: [
                {
                    label: 'Gelir',
                    data: reportsData.quarterlyPerformance.revenue,
                    backgroundColor: `${colors.primary}aa`,
                    borderRadius: 10
                },
                {
                    label: 'Gider',
                    data: reportsData.quarterlyPerformance.expenses,
                    backgroundColor: `${colors.secondary}aa`,
                    borderRadius: 10
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { display: false }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                }
            }
        }
    });

    const forecastCanvas = qs('#forecastChart');
    new Chart(forecastCanvas, {
        type: 'line',
        data: {
            labels: reportsData.forecast.labels,
            datasets: [
                {
                    label: 'Projeksiyon',
                    data: reportsData.forecast.projection,
                    borderColor: colors.primary,
                    backgroundColor: `${colors.primary}33`,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Hedef',
                    data: reportsData.forecast.target,
                    borderColor: colors.secondary,
                    backgroundColor: `${colors.secondary}33`,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                x: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.08)' }
                },
                y: {
                    ticks: { color: colors.muted },
                    grid: { color: 'rgba(148, 163, 184, 0.08)' }
                }
            }
        }
    });
}

function decorateProgressBars() {
    qsa('.progress').forEach(progress => {
        if (!progress.querySelector('.progress-bar')) {
            const value = Number(progress.dataset.value || 0);
            const bar = document.createElement('div');
            bar.className = 'progress-bar';
            bar.style.width = `${value}%`;
            progress.appendChild(bar);
        }
    });
}

function init() {
    const pathname = window.location.pathname.split('/').pop() || 'index.html';
    setActiveNav(pathname);
    renderMetricCards();
    decorateProgressBars();
    renderDashboard();
    renderSalesPage();
    renderUsersPage();
    renderReportsPage();
}

document.addEventListener('DOMContentLoaded', init);
