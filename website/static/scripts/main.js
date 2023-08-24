function checkUsernameForget(btn){
    let name = btn.previousElementSibling.previousElementSibling.children[1]
    let pwd = btn.previousElementSibling.children[1]
    fetch(`auth/checkforget/${name.value}/${pwd.value}`)
    .then(response => response.json())
    .then(result => 
        {
        forgetPwd = document.getElementById('forget-pwd')
        if (result[0]){
            console.log('success')
            btn.previousElementSibling.previousElementSibling.style.display = "none"
            btn.previousElementSibling.style.display = "none"
            btn.style.display = "none"
            btn.nextElementSibling.style.display = ""
            btn.nextElementSibling.nextElementSibling.style.display = ""
            btn.nextElementSibling.nextElementSibling.nextElementSibling.style.display = ""
            forgetPwd.textContent = ""
        }else{
            forgetPwd.textContent = 'Unmatched Username And Email..'
        }
        })
    .catch(err => console.log(err))
}

function signOut(){
    document.cookie = 'username' + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location = '/auth/log'
}
if (window.location.href.includes("/auth")){
    document.cookie = 'username' + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}
function showDropdown(btn){              
    dropdownContent = btn.nextElementSibling
    if (dropdownContent.style.display === "block") {
      dropdownContent.style.display = "none";
    } else {
      dropdownContent.style.display = "block";
    }
}




if (window.location.href.endsWith("/get-report")){
    dates = JSON.parse(localStorage.getItem('date'))
    fetch(`/get-graph-report/${dates[0]}/${dates[1]}`)
    .then(response => response.json())
    .then(result => {
        function drawChart() {
            // Define the chart to be drawn.
            for (var idx = 1; idx < result.length; idx++) {
                result[idx] = result[idx].map((value, index) =>
                    (index === 0 || index === result[idx].length - 1) ? value : parseFloat(value)
                );
            }
            console.log(result)
            var data = google.visualization.arrayToDataTable(result);
            var the_last_total = (result[0].length)-3
            // Set chart options
            var options = {
            title : 'Service Job Activites',
            chartArea : {
                left : 100,
                right : 150
            },
            vAxis: {
                title: 'Amount',
                titleTextStyle: {
                        fontSize: 13, // Adjust the x-axis label font size
                        padding : 0
                    },
                textStyle: {
                        fontSize: 12, // Adjust the x-axis tick labels font size
                        padding : 0
                    }
            },
            hAxis: {
                title: 'Technicians',
                titleTextStyle: {
                    fontSize: 13 // Adjust the x-axis label font size
                },
                textStyle: {
                    fontSize: 12 // Adjust the x-axis tick labels font size
                }
            },
            legend: {
                position: 'top', 
                alignment: 'start',
                textStyle: {
                    fontSize: 13 // Adjust the legend font size
                }
            },
            annotations: {
                textStyle: {
                    fontSize: 13 // Adjust the data label font size
                }
            },
            // Hover text (tooltip)
            tooltip: {
                textStyle: {
                    fontSize: 12 // Adjust the tooltip font size
                }
            },
            bar: {
                groupWidth: '100%' // Adjust the value to set the desired bar width
            },
            seriesType: 'bars',
            series: {[the_last_total]: {type: 'line'}}
            };
            console.log(options.series)
            // Instantiate and draw the chart.
            var chart = new google.visualization.ComboChart(document.getElementById('container'));
            chart.draw(data, options);
        }
        google.charts.setOnLoadCallback(drawChart);        
    })
    .catch(err => console.log(err))

    var chartContainer = document.getElementById('chartContainer');
    chartContainer.addEventListener('scroll', function () {
        var scrollLeft = chartContainer.scrollLeft;
        chartWrapper.style.width = 1200 + scrollLeft + 'px';
    });
}

function exportTableToExcel() {
    let table = document.getElementById("report-table")
    if (!table){
        table = document.getElementById("pic-table");        
    }

    headerRows = table.querySelectorAll('tr.d-none')
    headerRows.forEach(row=>{
        row.classList.remove('d-none')
    })

    const wb = XLSX.utils.table_to_book(table, { sheet: "SheetJS" });
    const wbout = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    const blob = new Blob([wbout], { type: "application/octet-stream" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "Export-Data.xlsx";
    a.click();
    URL.revokeObjectURL(url);

    headerRows.forEach(row=>{
        row.classList.add('d-none')
    })
}

function addAnotherRow(td) {
    let no_error = true
    let pics = td.parentElement.previousElementSibling.querySelectorAll("input.pic:not(.d-none)");
    let inps = td.parentElement.previousElementSibling.getElementsByClassName("inp");
    
    for (let pic of pics) {
        if (isNaN(pic.value.split("|")[1])) {
            no_error = false;
            break;
        }
    }
    
    if (no_error) {
        for (let inp of inps) {
            if (inp.value.trim() == "") {
            no_error = false;
            console.log(inp.value)
            break;
            }
        }
    }

    if (no_error) {
      let clonedRow = document.getElementById("willBeCloned").cloneNode(true);
      clonedRow.classList.remove('d-none')
      td.parentElement.parentNode.insertBefore(clonedRow, td.parentElement);
    }
}

function sumUpTotals(){
    let all_amts = document.getElementsByClassName("amts")
    let total_txt = document.getElementsByClassName("total-amount")
    let total = 0.0
    for (amt of Array.from(all_amts).slice(1)){
        total += parseFloat(amt.value) || 0.0   
    }
    total_txt[0].value = total.toFixed(2)
    total_txt[1].innerText = total.toFixed(2)
}

function deleteJobRow(btn,bool){
    if (bool && btn.parentElement.parentElement.children.length > 3){
        btn.parentElement.remove()        
    }
}

function chooseRegistartionNo(){
    let plate = document.getElementById("vehiclePlate").value.trim()
    if (plate.length != 0){
        fetch(`/get-data/vehicle/${plate.trim()}`)
        .then(response => response.json() )
        .then(result => {
            if (result.length != 0){
                let changeDatas = document.getElementsByClassName("vehicle-datas")
                document.getElementById("vehicleInformation").value = result[0][0]
                var i = 1;
                for (let changeData of changeDatas){
                    changeData.value = result[0][i]
                    changeData.focus()
                    i += 1;
                }
            }
        })
        .catch(err => console.log(err))
    }
}

function checkAllServiceDatas(){
    let plate = document.getElementById("vehiclePlate").value.trim()
    let picRows = document.querySelectorAll('#table-body-of-pic tr:not(.d-none) .pic:not(.d-none),.form-area .upperPic');
    let no_error = true;
    console.log(picRows)
    picRows.forEach(pic=>{
        userVals = pic.value.split("|")
        if (userVals.length != 2 || isNaN(userVals[1])){
            pic.setAttribute('style','border: 2px solid red;')
            no_error = false;
        }else{
            pic.removeAttribute('style')
        }
    })
    if (plate.length != 0){
        fetch(`/get-data/vehicle/${plate}`)
        .then(response => response.json() )
        .then(result => {
            if (result.length == 0){
                let modalClicker = document.getElementsByClassName("validateModal")
                document.getElementById("vehicleInformation").value = -100
                liItems = document.getElementsByClassName("list-group-vehicle-information")[0].querySelectorAll("li")
                let changeDatas = document.getElementsByClassName("vehicle-datas")
                liItems[0].innerText = plate
                liItems[1].innerText = changeDatas[0].value
                liItems[2].innerText = changeDatas[1].value
                liItems[3].innerText = changeDatas[2].value
                modalClicker[0].click()
            }else if(no_error){
                console.log("nani")
                let submitBtn = document.getElementsByClassName("service-data-submit")[0]
                submitBtn.click()
            }
        })
        .catch(err => console.log(err))
    }
}


offsetLimit  = 81
function clickPagination(target,txt){
    target_mapp = {"job":"job-data-changeable",
                  "dty":"duty-query-changeable",
              "machine":"machine-list-changeable",
              "expense":"expense-list-changeable"}
    all_tr = document.getElementsByClassName(target_mapp[target])
    let display_amt_holder = document.getElementById("paginate-amount")
    if (txt == 'prev'){
        let displayAmt = display_amt_holder.textContent.trim().split("/")
        getTotal = displayAmt[1]
        last = displayAmt[0].split("-")[1]
        fst = Number(displayAmt[0].split("-")[0])
        if (fst != 1){
            fetch(`/offset-display/${target}/${fst-82}`)
            .then(response => response.json())
            .then(result => {
                display_amt_holder.textContent = `${fst-81}-${fst-1} / ${getTotal}`
                replaceTableData(result)
            })
            .catch(err => console.log(err))
        }
        
    }else{
        let displayAmt = display_amt_holder.textContent.trim().split("/")
        getTotal = Number(displayAmt[1])
        last = Number(displayAmt[0].split("-")[1])
        if (last != getTotal){
            fetch(`/offset-display/${target}/${last}`)
            .then(response => response.json())
            .then(result => {
                formattedDate = new Date(result[0][1]).toISOString().substr(0, 10);
                if(last+82 > Number(getTotal)){
                    display_amt_holder.textContent = `${last+1}-${getTotal} / ${getTotal}`
                }else{
                    display_amt_holder.textContent = `${last+1}-${last+81} / ${getTotal}`
                }
                replaceTableData(result)
            })
            .catch(err => console.log(err))
        }
    }
}

function replaceTableData(result) {
    let i = 0;
    for (i = 0; i < result.length; i++) {
      tds = all_tr[i].getElementsByTagName('td');
      Array.from(tds).forEach((td, index) => {
        td.innerText = index === 1
        ? new Date(result[i][index]).toISOString().substr(0, 10)
        : result[i][index];
      });
    }
}

function typeSthInDropdown(inp){
    let val = inp.value
    let pTags = document.getElementsByClassName("dropdownFormClicker")
    if (val.trim() != ""){
        inp.nextElementSibling.nextElementSibling.classList.remove("d-none")
        for (let pTag of pTags){
            pTag.textContent = val
        }
    }else{
        inp.nextElementSibling.nextElementSibling.classList.add("d-none")
    }
}


function addValForTable(col){
    document.getElementById("column").value = col
    document.getElementsByClassName("search-bar")[0].parentElement.submit()
}


function redirectToFormEdit(dt,table){
    let column = document.getElementById('column')
    if (table == 'eachJob'){
        column.value = 'job_no'
        if (column.nextElementSibling.classList.length == 1){
            column.nextElementSibling.nextElementSibling.value = dt
        }else{
            column.nextElementSibling.value = dt     
        }
        document.getElementById('editOrSubmit').value = 'True'
        column.parentElement.parentElement.submit()
    }
}

function deleteAllServiceDatas(idd,db){
    console.log("nani",db,idd)
    fetch(`/get-data/${db}/${idd}`)
    .then(result => {
        if (result.status == 200){
            window.location.href = window.location.href
        }
    })
    .catch(err => console.log(err))
}

function checkRateFormAndSumbit(btn){
    if (btn.parentElement.children.length == 7){
        let total = 0.0
        let rateInps = btn.parentElement.querySelectorAll('.rate-inps')
        let error = false;
        rateInps.forEach(function(inp){
            total += Number(inp.value)
            if(inp.value.trim() == ""){
                error = true;
            }
        })
        if (total != 100 || error){
            console.log(total)
            for (let inp of rateInps){
                console.log(inp)
                inp.setAttribute("style","border: 1px solid red;")
            }
        }else{
            console.log(total)
            for (let inp of rateInps){
                console.log(inp)
                inp.removeAttribute("style")
            }
            document.getElementById("rate-form").submit()
        }
    }else{
        document.getElementById("rate-form").submit()
    }

}

function deleteLineDataFromViewForm(idd,db){
    let confirmAction = confirm("Are you sure want to delete the data?");
    if (confirmAction) {
        fetch(`/get-data/${db}/${idd}`)
        .then(response => {window.location.href = window.location.href})
        .catch(err => console.log(err))
    }

}


function replaceInputFormInViewForm(idd,tr){
    let inputType = ""
    let inputName = ""
    if(tr.children.length == 7){
        inputType = "number"
        inputName = "rate"
    }else{
        if (tr.id == 'technician'){ 
            inputName = "tech"
        }else{
            inputName = "jobType"            
        }
        inputType = "text" 
    }
    allTr = tr.getElementsByTagName('td')
    let inpArr = Array.from(allTr)
    let lastTdRow = inpArr[inpArr.length -1 ]
    inpArr[0].getElementsByTagName("input")[0].setAttribute("name","idd")
    if (tr.getElementsByClassName("trash-icon")[0].getAttribute('onclick')[0] != 'c'){
        inpArr[0].getElementsByTagName("input")[0].setAttribute("name","idd")
        for (let i=1;i < inpArr.length-1;i++){
            inpArr[i].innerHTML = `<input class="rate-inps" value="${inpArr[i].textContent}" type="${inputType}" min="0" max="100" name="${inputName}">`        
        }
        lastTdRow.setAttribute("onclick","checkRateFormAndSumbit(this)")
        lastTdRow.innerHTML = `<i class="fa-solid fa-square-check"></i>`
        lastTdRow.classList.add('check-icon')
    }else{
        inpArr[0].getElementsByTagName("input")[0].removeAttribute("name")
        for (let i=1;i < inpArr.length-1;i++){
            inpArr[i].innerHTML = inpArr[i].getElementsByTagName("input")[0].value      
        }
        lastTdRow.setAttribute("onclick",`deleteLineDataFromViewForm('${inpArr[0].getElementsByTagName("input")[0].value}','pic')`)
        lastTdRow.innerHTML = `<i class="fa-solid fa-trash"></i>`
        lastTdRow.classList.remove('check-icon')
    }
    // console.log(document.getElementById("rate-form"))
}

function findConsecutiveEndingZeroIndexes(arr) {
    let result = [];
    for (let i = arr.length - 1; i >= 0; i--) {
        if (arr[i] === '0') {
            result.unshift(i);
        }
    }
    return result
}
  

function storeValueFromListToHiddenInput(inp){
    inpValues = inp.value.split("|")
    rateValues = inpValues[0].trim().split(",")
    if (rateValues.length == 5 && inpValues.length == 2){
        let picInputs = inp.parentElement.parentElement.getElementsByClassName("pic")
        let disabledIndex = findConsecutiveEndingZeroIndexes(rateValues)
        console.log(disabledIndex)
        console.log(picInputs)
        for (let idx in [0,1,2,3,4]){
            if (disabledIndex.includes(Number(idx))){
                picInputs[idx].classList.add('d-none')              
            }else{
                picInputs[idx].classList.remove('d-none') 
            }
            picInputs[idx].value = ""
        }
        inp.value = inpValues[0].trim()
        inp.nextElementSibling.value = inpValues[0].trim()
    }
}