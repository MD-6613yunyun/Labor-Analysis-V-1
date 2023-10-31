const workTime =[
    [
        ['2023-10-01T08:30', '2023-10-01T11:30'],
        ['2023-10-01T13:30', '2023-10-01T16:30']
    ],
    [
        ['2023-10-01T08:30', '2023-10-01T11:30'],
        ['2023-10-01T13:30', '2023-10-01T14:30']
    ],
]

const labels = [
    ['engine maintain', 'water pipe'],
    ['engine maintain', 'water pipe', 'fuel check', 'tier replace'],
    [],
    ['engine maintain', 'water pipe', 'fuel check', 'tier replace', 'fuel check', 'tier replace','fuel check', 'tier replace','engine maintain', 'water pipe', 'fuel check', 'tier replace', 'fuel check', 'tier replace','fuel check'],
]

const callBack = {
        label: function(context){
            return context.dataset.data[context.dataIndex]
        }
    }

// config 
const config = {
    type: 'bar',
    data: {
    datasets: [{
                    label: 'Working Hour',
                    barPercentage: 0.5,
                    backgroundColor: [
                        'rgba(233, 11, 12, 0.8)',
                    ]
                }
            ]
    },
    options: {
        indexAxis: 'y',
        plugins: {
            tooltip: {}
        },
        scales: {
            x:{
                type: 'time',
                time: {
                    unit: 'hour',
                    stepSize: 0.5,
                    displayFormats:{
                        hour: 'H:mm'
                    },
                },
                min: '2023-10-01T08:00', // Set the minimum time
                max: '2023-10-01T18:00',
                position: 'top',
            },
            y: {
                beginAtZero: true
            },
        },
    },
};

const dailyReportTable = document.getElementById("dailyReportTable");
const tableBodyChildrenCol = dailyReportTable.querySelector("tbody").children;

var i;
for(i = 0; i < tableBodyChildrenCol.length ;i++){
    const getCanvas = tableBodyChildrenCol[i].lastElementChild.querySelector('div').querySelector('canvas');
    getCanvas.width = 400;
    getCanvas.height = 150;
    const chartConfig = JSON.parse(JSON.stringify(config));
    chartConfig.data.labels = labels[i];
    chartConfig.data.datasets[0].data = workTime[i];
    chartConfig.options.plugins.tooltip.callbacks = callBack;
    console.log(chartConfig);
    const myChart = new Chart(getCanvas, chartConfig);
}
