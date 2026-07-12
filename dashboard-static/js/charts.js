// Charts Management for SilhouetteMCP Dashboard

class DashboardCharts {
    constructor() {
        this.charts = {};
        this.chartData = {
            performance: {
                labels: [],
                data: []
            },
            resources: {
                cpu: [],
                memory: [],
                disk: []
            },
            monitoring: {
                labels: [],
                throughput: [],
                latency: [],
                errors: []
            }
        };
        this.maxDataPoints = 20;
    }

    // Initialize all charts
    init() {
        this.initPerformanceChart();
        this.initResourcesChart();
        this.initMonitoringChart();
    }

    // Performance Chart (Line Chart)
    initPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.chartData.performance.labels,
                datasets: [{
                    label: 'Tareas por Minuto',
                    data: this.chartData.performance.data,
                    borderColor: '#0066FF',
                    backgroundColor: 'rgba(0, 102, 255, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-primary').trim(),
                            font: { size: 12, weight: '600' }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#0066FF',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--border-color').trim()
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-secondary').trim()
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-secondary').trim()
                        }
                    }
                },
                animation: {
                    duration: 750
                }
            }
        });
    }

    // Resources Chart (Doughnut Chart)
    initResourcesChart() {
        const ctx = document.getElementById('resources-chart');
        if (!ctx) return;

        this.charts.resources = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['CPU', 'Memoria', 'Disco'],
                datasets: [{
                    data: [45, 30, 25],
                    backgroundColor: [
                        '#0066FF',
                        '#3B82F6',
                        '#60A5FA'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-primary').trim(),
                            font: { size: 12, weight: '600' },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Monitoring Chart (Multi-line Chart)
    initMonitoringChart() {
        const ctx = document.getElementById('monitoring-chart');
        if (!ctx) return;

        this.charts.monitoring = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.chartData.monitoring.labels,
                datasets: [
                    {
                        label: 'Throughput (req/s)',
                        data: this.chartData.monitoring.throughput,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        yAxisID: 'y',
                        tension: 0.4
                    },
                    {
                        label: 'Latencia (ms)',
                        data: this.chartData.monitoring.latency,
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.4
                    },
                    {
                        label: 'Errores',
                        data: this.chartData.monitoring.errors,
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        yAxisID: 'y',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-primary').trim(),
                            font: { size: 12, weight: '600' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--border-color').trim()
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-secondary').trim()
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-secondary').trim()
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement)
                                .getPropertyValue('--text-secondary').trim()
                        }
                    }
                }
            }
        });
    }

    // Update charts with new data
    updatePerformanceChart(value) {
        const now = new Date().toLocaleTimeString();
        
        this.chartData.performance.labels.push(now);
        this.chartData.performance.data.push(value);

        // Keep only last N points
        if (this.chartData.performance.labels.length > this.maxDataPoints) {
            this.chartData.performance.labels.shift();
            this.chartData.performance.data.shift();
        }

        if (this.charts.performance) {
            this.charts.performance.update('none'); // 60fps update
        }
    }

    updateResourcesChart(cpu, memory, disk) {
        if (this.charts.resources) {
            this.charts.resources.data.datasets[0].data = [cpu, memory, disk];
            this.charts.resources.update();
        }
    }

    updateMonitoringChart(throughput, latency, errors) {
        const now = new Date().toLocaleTimeString();
        
        this.chartData.monitoring.labels.push(now);
        this.chartData.monitoring.throughput.push(throughput);
        this.chartData.monitoring.latency.push(latency);
        this.chartData.monitoring.errors.push(errors);

        // Keep only last N points
        if (this.chartData.monitoring.labels.length > this.maxDataPoints) {
            this.chartData.monitoring.labels.shift();
            this.chartData.monitoring.throughput.shift();
            this.chartData.monitoring.latency.shift();
            this.chartData.monitoring.errors.shift();
        }

        if (this.charts.monitoring) {
            this.charts.monitoring.update('none'); // 60fps update
        }
    }

    // Destroy all charts
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }
}

// Export for use in app.js
window.dashboardCharts = new DashboardCharts();
