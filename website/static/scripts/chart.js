// Monthly report start
monthsummaryData = [
    [
        ['Date', 'Work Hour', { role: 'annotation' }, 'Idle Hour', { role: 'annotation' }],
        ['11/11/2023', 7, 'Label 1', 3, 'Label 2'],
        // Add labels for each column
        ['11/12/2023', 6, 'Label 3', 4, 'Label 4'],
        ['11/13/2023', 8, 'Label 5', 2, 'Label 6'],
        // Add more data as needed
    ]
];
var monthsumoptions = {
    height: 350,
    chart: {
        title: 'Daily Summary',
    },
    hAxis: {
        title: "Dates",
        ticks: [1, 2, 3, 4, 5, 6, 7, 8],
        minValue: 0,
        maxValue: 8
    },
    vAxis: {
        title: "Hours",
        ticks: [1, 2, 3, 4, 5, 6, 7, 8],
        minValue: 0,
        maxValue: 8
    },
    // Add annotations to display labels
    annotations: {
        textStyle: {
            fontSize: 12,
        },
    },
};

// Monthly report end

// start drawing graph
const currentURL = window.location.href;
console.log(currentURL)
if(currentURL.endsWith("/in-out")){
    google.charts.load('current', {packages:['bar']});
}

google.charts.setOnLoadCallback(drawChart); 

function drawChart(){
    let dailyReportTable;
    if(currentURL.endsWith("/in-out")){
        dailyReportTable = document.getElementById("monthlyReportSum");
    }
    let tableBodyChildrenCol;
    if(currentURL.endsWith("/in-out")){
        tableBodyChildrenCol = dailyReportTable.querySelector("tbody").querySelectorAll("tr:nth-child(odd)");
    }

    var i;
    for(i = 0; i < tableBodyChildrenCol.length; i++){
        
        var container = tableBodyChildrenCol[i].lastElementChild.querySelector("div");

        if(currentURL.endsWith("/in-out")){
            var chart = new google.charts.Bar(container);
            container.style.width = "900px";
            container.style.overflow = "auto";
            container.style.margin = "0 auto";
        }

        
        if(currentURL.endsWith("/in-out")){
            console.log(monthsummaryData[i].length);
            if(monthsummaryData[i].length > 9){
                monthsumoptions.width = monthsummaryData[i].length * 100;
                console.log(monthsumoptions.width);
            }else{
                monthsumoptions.width = 900;
                console.log(monthsumoptions.width);
            }
            var options = monthsumoptions;
        }
        
        if(currentURL.endsWith("/in-out")){
            var data = google.visualization.arrayToDataTable(monthsummaryData[i]);

            // Add annotations for the first and third columns
            data.setColumnProperty(2, 'role', 'annotation');
            data.setColumnProperty(4, 'role', 'annotation');
            
            var view = new google.visualization.DataView(data);
            view.setColumns([0, 1, 2, 3, 4]);
            
            chart.draw(view, google.charts.Bar.convertOptions(options));
        }
    }
}
