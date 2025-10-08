export const dashboardMetrics = {
    revenue: {
        value: '$128,450',
        change: 12.6,
        trend: [8200, 9600, 10200, 11800, 12400, 13750, 14200, 15200, 15800, 16600, 17200, 18400]
    },
    orders: {
        value: '1,482',
        change: 4.1,
        trend: [96, 102, 110, 108, 124, 130, 126, 142, 154, 166, 158, 172]
    },
    retention: {
        value: '87%',
        change: 2.4,
        trend: [74, 76, 78, 79, 81, 82, 83, 84, 85, 86, 87, 88]
    },
    activeUsers: {
        value: '12,985',
        change: -1.8,
        trend: [11240, 11600, 11950, 12110, 12400, 12890, 13200, 13150, 12980, 12860, 12910, 12985]
    }
};

export const salesData = {
    categories: ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'],
    revenueByChannel: {
        online: [8200, 8600, 9200, 9800, 11200, 11800, 12400, 13400, 14200, 15100, 15800, 16950],
        retail: [6200, 6400, 6800, 7300, 7800, 8100, 8700, 9100, 9500, 9900, 10300, 10800]
    },
    topProducts: [
        { name: 'AI Analytics Suite', revenue: 28400, growth: 18.4, status: 'Yükselişte' },
        { name: 'Automation Toolkit', revenue: 22680, growth: 11.2, status: 'Stabil' },
        { name: 'Predictive CRM', revenue: 19870, growth: -2.6, status: 'İyileştirme' },
        { name: 'Insight Dashboard', revenue: 15440, growth: 8.3, status: 'Yükselişte' }
    ],
    pipeline: [
        { stage: 'Potansiyel', value: 146 },
        { stage: 'İlk Temas', value: 108 },
        { stage: 'Demo', value: 78 },
        { stage: 'Teklif', value: 44 },
        { stage: 'Kapanan', value: 26 }
    ]
};

export const usersData = {
    activity: {
        dailyActive: [420, 460, 510, 550, 580, 610, 640],
        newSignups: [56, 68, 72, 80, 74, 86, 92]
    },
    segments: [
        { label: 'Kurumsal', value: 34 },
        { label: 'KOBİ', value: 41 },
        { label: 'Startup', value: 18 },
        { label: 'Bireysel', value: 7 }
    ],
    retention: [
        { month: '1. Ay', rate: 92 },
        { month: '2. Ay', rate: 88 },
        { month: '3. Ay', rate: 84 },
        { month: '4. Ay', rate: 81 },
        { month: '5. Ay', rate: 79 },
        { month: '6. Ay', rate: 76 }
    ],
    supportTickets: [
        { id: '#9842', user: 'Elif Demir', priority: 'Yüksek', topic: 'Faturalandırma', status: 'Açık', updatedAt: '5 dk önce' },
        { id: '#9834', user: 'Mert Yılmaz', priority: 'Orta', topic: 'Entegrasyon', status: 'Yanıtlandı', updatedAt: '20 dk önce' },
        { id: '#9821', user: 'Eda Kaya', priority: 'Yüksek', topic: 'Performans', status: 'İşlemde', updatedAt: '42 dk önce' },
        { id: '#9816', user: 'Burak Şen', priority: 'Düşük', topic: 'Eğitim', status: 'Kapandı', updatedAt: '1 saat önce' }
    ]
};

export const reportsData = {
    kpis: [
        { label: 'Yıllık Büyüme', value: '36%', change: 5.4 },
        { label: 'Net Gelir', value: '$864K', change: 3.8 },
        { label: 'Dönüşüm Oranı', value: '4.2%', change: 0.6 },
        { label: 'Müşteri Başına Gelir', value: '$256', change: 1.4 }
    ],
    quarterlyPerformance: {
        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
        revenue: [210000, 238000, 264000, 298000],
        expenses: [142000, 151000, 169000, 182000]
    },
    forecast: {
        labels: ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran'],
        projection: [72000, 74500, 77200, 80400, 83600, 86200],
        target: [70000, 73000, 76000, 79000, 82000, 85000]
    }
};
