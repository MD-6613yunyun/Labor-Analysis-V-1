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
    window.location = '/auth/log'
}
function showDropdown(btn){              
    dropdownContent = btn.nextElementSibling
    if (dropdownContent.style.display === "block") {
      dropdownContent.style.display = "none";
    } else {
      dropdownContent.style.display = "block";
    }
}



var imgCharData;
if (window.location.href.endsWith("/get-report")){
    dates = JSON.parse(localStorage.getItem('date'))
    fetch(`/get-graph-report/${dates[0]}/${dates[1]}/${dates[2]}/${dates[3]}`)
    .then(response => response.json())
    .then(result => {
        let caption = document.getElementsByClassName("for-graph-caption")[0].textContent
        function drawChart() {
            console.log(result)
            // Define the chart to be drawn.
            for (var idx = 1; idx < result.length; idx++) {
                result[idx] = result[idx].map((value, index) =>
                    (index === 0 || index === result[idx].length - 1) ? value : parseFloat(value)
                );
            }
            let haxisFontSize = 12
            if (result.length > 20){
            document.getElementById("chartContainer").children[0].style.width = `${(result.length - 1)*30}px`
                haxisFontSize = 8
        }
            
            var data = google.visualization.arrayToDataTable(result);
            var the_last_total = (result[0].length)-3
            // Set chart options
            var options = {
            title : 'Service Job Activites' + caption,
            bar : {
                columnWidth: '100%',
            },
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
                    fontSize: haxisFontSize // Adjust the x-axis tick labels font size
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
                highcontrast:true,
                textStyle: {
                    fontSize: 10, // Adjust the data label font size
                    bold: true,
                    italic: true,
                    // The color of the text.
                    color: '#a30b0b',
                    // The color of the text outline.
                    auraColor: '#fff',
                }
            },
            // Hover text (tooltip)
            tooltip: {
                highcontrast:true,
                textStyle: {
                    fontSize: 12, // Adjust the tooltip font size
                }
            },
            seriesType: 'bars',
            series: {[the_last_total]: {type: 'line'}}
            };
            // Instantiate and draw the chart.
            var chart = new google.visualization.ComboChart(document.getElementById('container'));
            // SET ROTATE TEXT
            google.visualization.events.addListener(chart, 'ready', function () {
                var observer = new MutationObserver(function () {
                  var labels = container.querySelectorAll('text[font-size="10"]');
                  Array.prototype.forEach.call(labels, function(label) {
                    if (label.getAttribute('text-anchor') === 'middle') {
                      label.setAttribute('transform', 'rotate(-60, ' + label.getAttribute('x') + ' ' + label.getAttribute('y') + ')');
                    }
                  });
                });
                observer.observe(container, {
                  childList: true,
                  subtree: true
                });
            });
            // DRAW
            chart.draw(data, options);
            document.getElementById('graph-image-container').innerHTML = '<img id="chart" src=' + chart.getImageURI() + '>';
            document.getElementById("download_link").setAttribute("href", chart.getImageURI())
        }
        google.charts.setOnLoadCallback(drawChart);        
    })
    .catch(err => console.log(err))

}

function exportTableToExcel() {
    let table = document.getElementById("report-table")
    if (!table){
        table = document.getElementById("pic-table");        
    }else{
        document.getElementById("download_link").click()
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

function addAnotherRow(td,for_check_in_out=false) {
    let previousRowofTable = td.parentElement.parentElement.previousElementSibling;
    if (for_check_in_out){
        const endTimeBtn = previousRowofTable.children[5].querySelector("button");
        const startTimeBtn = previousRowofTable.children[4].querySelector("button");
        setTimeInput(startTimeBtn);
        setTimeInput(endTimeBtn);
    }
    let no_error = true
    let inps = previousRowofTable.getElementsByClassName("inp");
    
    previousRowofTable.querySelectorAll("input.pic:not(.d-none)").forEach(pic => {
        if (pic.value.trim() == ""){
            no_error = false
        }
    })
    
    if (no_error) {
        for (let inp of inps) {
            if (inp.value.trim() == "") {
            no_error = false;
            break;
            }
        }
    }

    
    if (no_error & !td.classList.contains("disabled")) {
        // checking duplicates technicians in the same time
        if (for_check_in_out){
            let techId = previousRowofTable.getElementsByClassName("pic_id")[0].value
            console.log(techId)
            let startTime = previousRowofTable.children[4].children[0].value
            let endTime = previousRowofTable.children[5].children[0].value
            let dateValue = document.getElementsByClassName("date-error-input")[0].value;
            console.log(startTime)
            console.log(dateValue)
            const serverData = {
                job_date: dateValue,
                tech_id: techId,
                start_time: startTime,
                end_time: endTime
              };
              
            fetch('/import/keep-in-import/check-in-out-techs', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(serverData),
            })
            .then(response => response.json())
            .then(result => {
                no_error = true 
                if(result[0] == '0'){
                    let asking = confirm("Another Job was assigned to the technician. Assign another Job??")
                    no_error = asking ? true : false;
                }
                if (no_error){
                    let clonedRow = document.getElementById("willBeCloned").cloneNode(true);
                    clonedRow.classList.remove('d-none')
                    td.parentElement.parentElement.parentNode.insertBefore(clonedRow, td.parentElement.parentElement);  
                }

            })
            .catch(error => console.error('Error:', error));
        }else{
            let clonedRow = document.getElementById("willBeCloned").cloneNode(true);
            clonedRow.classList.remove('d-none')
            td.parentElement.parentElement.parentNode.insertBefore(clonedRow, td.parentElement.parentElement);            
        }
    }
}

function sumUpTotals(inp){
    console.log(inp.value)
    inp.value = inp.value.replace(/^0+/, '');
    console.log(inp.value)
    let all_amts = document.getElementsByClassName("amts")
    let total_txt = document.getElementsByClassName("total-amount")
    let total = 0.0
    for (amt of Array.from(all_amts).slice(1)){
        total += parseFloat(amt.value) || 0.0   
    }
    total_txt[0].value = total.toFixed(2)
    total_txt[1].children[0].value = total.toFixed(2)
}

function deleteJobRow(btn,for_check_in_out=false){
    console.log(btn.parentElement.parentElement.parentElement.children.length)
    if (btn.parentElement.parentElement.parentElement.children.length > 3){
        if(confirm("Are you sure you want to delete the data?")){
            btn.parentElement.parentElement.remove()
            if (for_check_in_out){
                let clickedBtn = document.getElementsByClassName("timeEndBtn")[1]
                setTimeInput(clickedBtn);                
            }
        }
    }else{
        alert("You must edit the data for the remaining first row rather than deleting that row..")
    }
}

function checkVehiclePlate(inp,what,for_check_in_out=false){
    let state = prefix = digit = plate = ''

    if (what == 'digit'){
        state = inp.previousElementSibling.previousElementSibling.value
        prefix = inp.previousElementSibling.value
        digit = inp.value
    }else{
    state = inp.previousElementSibling.value
    prefix = inp.value
    digit = inp.nextElementSibling.value 
        if (inp.value.trim() == 'UN' ){
            inp.nextElementSibling.setAttribute("type","text")        
        }else{
            inp.nextElementSibling.setAttribute("type","number")
        }    
    }
    if (prefix.length >=2 && digit.length == 4){
        plate = state.trim() + prefix.trim() + digit.trim()
        fetch(`/get-data/vehicle/${plate}`)
        .then(response => response.json() )
        .then(result => {
            console.log(result)
            if(result.length > 0 && result[0][result[0].length-1] == 't'){
                let lst = document.getElementsByClassName('list-group-vehicle-information')[0]
                lst.innerHTML = ""
                let i = 1
                for (data of result){
                    let class_name = ""
                    let disabled_text = "disabled"
                    if (i == result.length){
                        class_name = "class='table-dark'"
                        disabled_text = ""
                    }
                    let fun_name = for_check_in_out ? `autoFillVehicleInfo('${data[0]}','${data[6]}',for_check_in_out=true)` : `autoFillVehicleInfo('${data[0]}','${data[6]}',for_check_in_out=false)`; 
                    lst.innerHTML += `<tr ${class_name}>
                    <td><button type='button' ${disabled_text} data-bs-dismiss='modal' onclick="${fun_name}" style="font-size:5px;" class='btn btn-sm btn-info'>✔️</button></td>
                    <td>${data[0]}</td>
                    <td>${data[1]}</td>
                    <td>${data[2]}</td>
                    <td>${data[3]}</td>
                    <td>${data[4]}</td>
                    <td>${data[5]}</td>
                </tr>`
                i ++;
                }
                if (document.getElementById("changeOwner")){
                    let fun_name = for_check_in_out ? `autoFillVehicleInfo('${data[0]}',null,for_check_in_out=true)` : `autoFillVehicleInfo('${data[0]}',null,for_check_in_out=false)`; 
                    document.getElementById("changeOwner").setAttribute("onclick",fun_name)
                }
                document.getElementById("vehicleInformation").value = data[9]
                let modalClicker = document.getElementsByClassName("validateModal")
                modalClicker[0].click()
            }else if(result.length > 0 && result[0][result[0].length-1] == 'f'){
                document.getElementById("vehicleInformation").value = result[0][0]
                let allinputs = Array.from(document.getElementsByClassName("autoFillByVehicle"))
                if (allinputs.length > 4){
                    allinputs = [allinputs[3],allinputs[5],allinputs[6]]
                }
                console.log(allinputs)
                for (let idx in allinputs){
                    idx = Number(idx)
                    allinputs[idx].value = result[0][idx+1]
                    allinputs[idx].setAttribute("disabled", "")
                }
            }else{
                if (confirm("Would you like to create a new vehicle?")){
                    document.querySelectorAll(".autoFillByVehicle").forEach(val => {
                        val.disabled = false
                        val.value = ""
                        document.getElementById("vehicleInformation").value = "None"
                    })                    
                }else{
                    document.querySelectorAll(".each-input input").forEach(inp => {
                        inp.value = ""
                    })
                }
            }
        })
        .catch(err => console.log(err))
    }
}

function autoFillVehicleInfo(idd,cus_id,for_check_in_out=false) {
    let vari = ""
    if (cus_id){
        document.getElementById("customerInformation").value = cus_id
        vari = idd + '||' + cus_id
    }else{
        vari = idd
        document.getElementById("customerInformation").value = "None"
        fetch(`/get-data/change-owner/${idd}`)
        .then(response => console.log(response.status) )
        .catch(err => console.log(err))
    }
    fetch(`/get-data/vehicle/${vari}`)
    .then(response => response.json() )
    .then(result => {
        console.log(result)
        let values = cus_id ? [result[0][3],result[0][7],result[0][5],result[0][1],result[0][4],result[0][2],result[0][8]] : [result[0][1],result[0][2],result[0][8]]
        if (for_check_in_out){
            values = cus_id ? [result[0][1],result[0][2],result[0][8],result[0][0]] : [result[0][1],result[0][2],result[0][8]]
        }
        let classPlacer = cus_id ? 'autoFillByVehicle' : 'autoFillNewOwner'
        var i = 0;
        document.querySelectorAll(`.${classPlacer}`).forEach(val => {
            val.disabled = true;
            val.value = values[i]
            console.log(val)
            console.log(values[i])
            i ++;
        })
    })
    .catch(err => console.log(err))
}

function autoFillByCustomer(inp){
    let cus_name = inp.value.toUpperCase().trim()
    fetch(`/get-data/autofill-customer/${cus_name}`)
    .then(response => response.json())
    .then(result => {
        let customerHolders = document.querySelectorAll(".autoFillByVehicle")
        let cus_id_set = document.getElementById("customerInformation")
        if (result.length > 0){
            customerHolders[1].value = result[0][0]
            customerHolders[2].value = result[0][1]
            customerHolders[4].value = result[0][2]
            cus_id_set.value = result[0][3]
        }else{
            if (!confirm("Are you want to create a new customer ?")){
                inp.value = ""
            }
            customerHolders[1].value = customerHolders[2].value = customerHolders[4].value = ""
            cus_id_set.value = "None"
        }
    })
    .catch(err => console.log(err))
}

function checkAllServiceDatas(forWhat="not-approve") {
    let picRows = document.querySelectorAll('#table-body-of-pic tr:not(.d-none) .pic:not(.d-none),.form-area .upperPic');
    let allRows = document.querySelectorAll('.input-sec input:not([hidden]):not([disabled]):not(.not-required-input),#table-body-of-pic tr:not(.d-none) .inp');
    let promises = [];
    let notDNone = document.querySelectorAll("#table-body-of-pic tr:not(.d-none)")
    for (let i = 0;i < notDNone.length-1;i++){
        if (notDNone[i].querySelectorAll(".pic:not(.d-none)").length == 0){
            notDNone[i].style.border = '2px solid red';
            promises.push(Promise.resolve(false));
        }
    }

    // Validate allRows inputs
    for (let pic of allRows) {
        if (pic.value.trim() == "") {
            pic.setAttribute('style', 'border: 2px solid red;');
            promises.push(Promise.resolve(false));
        } else {
            promises.push(Promise.resolve(true));
        }
    }

    let model_name = document.getElementById("model")
    if (model_name.value.trim() != ""){
        promises.push(
            fetch(`/get-data/get-brand-model/${model_name.value}`)
            .then(response => response.json())
            .then(result => {
                if (result.length != 1) {
                    model_name.setAttribute('style', 'border: 2px solid red;');
                    return false;
                } else {
                    document.getElementById("brand_id").value = result[0][0]
                    document.getElementById("model_id").value = result[0][1]
                    return true;
                }
            })
            .catch(err => {
                console.log(err);
                return false;
            })
        );
    }
    
    shop_value = document.getElementsByClassName("specific-shop-id-in-form")[0].value
    date_value = document.getElementsByClassName("date-error-input")[0].value
    // Validate picRows inputs
    for (let pic of picRows) {
        if (pic.value.trim() == "" || shop_value.trim() == '0' || date_value.trim() == '') {
            pic.setAttribute('style', 'border: 2px solid red;');
            promises.push(Promise.resolve(false));
        }
    }

    Promise.all(promises).then(results => {
        let no_error = results.every(result => result);
        if (forWhat == 'approve'){
            document.querySelectorAll(".approve-data").forEach(inp => {
                inp.removeAttribute("disabled");
            })
        }
        if (no_error) {
            document.getElementById("service-data-input-form").submit();
        }
    });
}


let offsetLimit  = 81
function clickPagination(target,txt,shop_id=0){
    target_mapp = {"job":"job-data-changeable",
              "vehicles":"vehicle-data-changeable",
              "customers":"customer-data-changeable",
              "descriptions":"tree-data-changeable",
              "jobType":"tree-data-changeable",
              "technician":"tree-data-changeable",
              "psfuCall":`shop-psfu-${shop_id}-data-changeable`,}
    console.log(target)
    all_tr = document.getElementsByClassName(target_mapp[target])
    offsetLimit = target == 'psfuCall' ? 20 : 81
    let display_amt_holder = document.getElementById("paginate-amount")
    if (target == 'psfuCall'){
        display_amt_holder = document.getElementById(`${shop_id}-paginate-amount`)
    }
    if (txt == 'prev'){
        let displayAmt = display_amt_holder.textContent.trim().split("/")
        getTotal = displayAmt[1]
        last = displayAmt[0].split("-")[1]
        fst = Number(displayAmt[0].split("-")[0])
        let offset_var = target == 'psfuCall' ? `${fst-(offsetLimit+1)}~${shop_id}` : `${fst-(offsetLimit+1)}`
        if (fst != 1){
            fetch(`/offset-display/${target}/${offset_var}`)
            .then(response => response.json())
            .then(result => {
                display_amt_holder.textContent = `${fst-offsetLimit}-${fst-1} / ${getTotal}`
                replaceTableData(result,target)
            })
            .catch(err => console.log(err))
        }
        
    }else{
        let displayAmt = display_amt_holder.textContent.trim().split("/")
        getTotal = Number(displayAmt[1])
        last = Number(displayAmt[0].split("-")[1])
        let offset_var = target == 'psfuCall' ? `${last}~${shop_id}` : `${last}`
        if (last != getTotal){
            fetch(`/offset-display/${target}/${offset_var}`)
            .then(response => response.json())
            .then(result => { 
                if (target == 'job') {         
                    formattedDate = new Date(result[0][1]).toISOString().substr(0, 10);
                }
                if(last+(offsetLimit+1) > Number(getTotal)){
                    display_amt_holder.textContent = `${last+1}-${getTotal} / ${getTotal}`
                }else{
                    display_amt_holder.textContent = `${last+1}-${last+offsetLimit} / ${getTotal}`
                }
                replaceTableData(result,target)
            })
            .catch(err => console.log(err))
        }
    }
}

function replaceTableData(result,target) {
    let i = 0;
    for (i = 0; i < result.length; i++) {
        all_tr[i].classList.remove("d-none")
        if (target == 'job'){
            all_tr[i].setAttribute('onclick',`redirectToFormEdit('${result[i][4]},${result[i][result[i].length - 1]}','eachJob')`)
            tds = all_tr[i].getElementsByTagName('td');
            Array.from(tds).forEach((td, index) => {
            td.innerText = index === 1
            ? new Date(result[i][index]).toISOString().substr(0, 10)
            : result[i][index];
            });
        }
        else if(target == "descriptions" || target == "jobType" || target == "technician"){
            tds = all_tr[i].getElementsByTagName('td');
            tds[0].children[0].value = result[i][0]
            for (let ij=1;ij<tds.length-1;ij++) {
                tds[ij].textContent = result[i][ij]
            }
            tds[tds.length-1].setAttribute("onclick", `deleteLineDataFromViewForm('${result[i][0]}','${target}')`)
        }else if (target == "psfuCall"){
            tds = all_tr[i].getElementsByTagName('td');
            if (tds[0].classList.contains("line-through")){
                for(let tdd of tds){
                    tdd.classList.remove("line-through")
                }
            }
            tds[0].textContent = new Date(result[i][1]).toISOString().substr(0, 10)
            tds[1].textContent = result[i][0]
            tds[2].textContent = result[i][2]
            tds[3].textContent = result[i][3]
            tds[4].textContent = result[i][4]
            tds[6].children[1].value = ""
            tds[7].children[0].value = result[i][6]
            tds[8].children[0].setAttribute("onclick", `redirectToFormEdit('${result[i][5]}','eachJob')`)
        } else{
            all_tr[i].setAttribute('onclick',`redirectToFormEdit('${result[i][0]}','${target.slice(0,-1)}')`)
            tds = all_tr[i].getElementsByTagName('td');
            Array.from(tds).forEach((td, index) => { td.innerText = result[i][index+1]; });        
        }
    }
    for (i = i;i < all_tr.length;i++){
        all_tr[i].classList.add("d-none")        
    }
    // console.log(all_tr)
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
    document.getElementById("editOrSubmit").value = 'False'
    document.getElementById("column").value = col
    document.getElementsByClassName("search-bar")[0].parentElement.submit()
}


function redirectToFormEdit(dt,table){
    let column = document.getElementById('column')
    let table_column = {'eachJobs':'job_no','customer':'name','vehicle':'plate','check-in-out':'id','technician':'id','psfu-calls':'id'}
    column.value = table_column[table]
    if (column.nextElementSibling.classList.contains("rounded")){
        column.nextElementSibling.value = dt
    }else{
        column.nextElementSibling.nextElementSibling.value = dt            
    }
    document.getElementById('editOrSubmit').value = 'True'
    console.log(column.parentElement)
    column.parentElement.parentElement.submit()
}

function deleteAllServiceDatas(idd,db){
    let confirmAction = confirm("Are you sure want to delete the data?\nDeleting this form will remove all associated datas !!!");
    if (confirmAction){
        fetch(`/get-data/${db}/${idd}`)
        .then(response => response.text())
        .then(result => {
            if(result == 'failed'){
                document.getElementById('errorMessageDisplayer').textContent = "You can't delete this data as some data depends on this.."
                document.getElementsByClassName("errorModal")[0].click()
            }else{
                window.location.href = window.location.href
            }
        })
        .catch(err => console.log(err))
    }
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
        .then(response => response.text())
        .then(result => {
            if(result == 'failed'){
                document.getElementById('errorMessageDisplayer').textContent = "You can't delete this data as some data depends on this.."
                document.getElementsByClassName("errorModal")[0].click()
            }else{
                window.location.reload()
            }
        })
        .catch(err => console.log(err))
    }

}

function showBtnAndRemoveDisabled(btn){
    btn.nextElementSibling.classList.remove("d-none")
    document.querySelectorAll(".let-edit-user").forEach(inp => {
        inp.disabled = false
    })
    for (let delBtn of document.querySelectorAll(".disabled-for-delete")){
        delBtn.removeAttribute("disabled")
    }
    if (btn.classList.contains("for-check-in-out")){
        document.getElementById("approve-btn").classList.add("d-none")
    }
    btn.classList.add('d-none')
    approve_btn = document.getElementById("approve-input")
    if (approve_btn){
        approve_btn.setAttribute("disabled", "")
    }
}

var temp_datas_for_replace_input = []
function replaceInputFormInViewForm(tr){
    let inputType = ""
    let inputName = ""
    if(tr.children.length == 7){
        inputType = "number"
        inputName = ["rate","rate","rate","rate","rate"]
        optionList = ["","","","",""]
    }else{
        if (tr.id == 'technician'){ 
            inputName = ['tech','unit','shop']
            optionList = ['','unitListOptions','shopListOptions']
        }else{
            inputName = ["jobType"] 
            optionList = ['']           
        }
        inputType = "text" 
    }
    allTr = tr.getElementsByTagName('td')
    let inpArr = Array.from(allTr)
    let lastTdRow = inpArr[inpArr.length -1 ]
    inpArr[0].getElementsByTagName("input")[0].setAttribute("name","idd")
    if (tr.getElementsByClassName("trash-icon")[0].getAttribute('onclick')[0] != 'c'){
        if (temp_datas_for_replace_input.length == 0){
            inpArr[0].getElementsByTagName("input")[0].setAttribute("name","idd")
            for (let i=1;i < inpArr.length-1;i++){
                temp_datas_for_replace_input.push(inpArr[i].textContent)
                inpArr[i].innerHTML = `<input class="rate-inps" onkeyup="changeToUpperCaseInput(this)" list='${optionList[i-1]}' autocomplete='off' value="${inpArr[i].textContent}" type="${inputType}" min="0" max="100" name="${inputName[i-1]}">`        
            }
            lastTdRow.setAttribute("onclick","checkRateFormAndSumbit(this)")
            lastTdRow.innerHTML = `<i class="fa-solid fa-square-check"></i>`
            lastTdRow.classList.add('check-icon')
        }
    }else{
        inpArr[0].getElementsByTagName("input")[0].removeAttribute("name")
        for (let i=1;i < inpArr.length-1;i++){
            inpArr[i].innerHTML = temp_datas_for_replace_input[i-1]     
        }
        lastTdRow.setAttribute("onclick",`deleteLineDataFromViewForm('${inpArr[0].getElementsByTagName("input")[0].value}','pic')`)
        lastTdRow.innerHTML = `<i class="fa-solid fa-trash"></i>`
        lastTdRow.classList.remove('check-icon')
        temp_datas_for_replace_input = []
    }
    // console.log(document.getElementById("rate-form"))
    console.log(temp_datas_for_replace_input)
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
    let rateValues = inp.value.split(",")
    let picInputs = inp.parentElement.parentElement.getElementsByClassName("pic")
    let disabledIndex = findConsecutiveEndingZeroIndexes(rateValues)
    for (let idx in [0,1,2,3,4]){
        picInputs[idx].removeAttribute("disabled")
        if (disabledIndex.includes(Number(idx))){
            picInputs[idx].classList.add('d-none')              
        }else{
            picInputs[idx].classList.remove('d-none') 
        }
        picInputs[idx].value = ""
    }
}

function checkRegNumber(val,maxlength){
    val.value = val.value.toUpperCase()
    if (val.value.length > maxlength){
        val.value = val.value.slice(0,maxlength)
    }
}

function generateVehicleModel(inp){
    if (inp.value.trim() != ""){
        fetch(`/get-data/vehicle_model/${inp.value}`)
        .then(response => response.json())
        .then(result => {
            modelList = document.getElementById("modelListOptions")
            modelList.innerHTML = ""
            if(result.length != 0){
                result.forEach(data => {
                    modelList.innerHTML += `<option value="${data[0]}"></option>`
                })
            }else{
                modelList.innerHTML = `<option value="No Model Was Found"></option>`
            }
        })
        .catch(err => consoley.log(err))
    }else{
        inp.setAttribute('style', 'border: 2px solid red;');
    }
}

function showModelDropDownFromBrand(divv){
    let listHolder = divv.parentElement.nextElementSibling
    if (listHolder.classList.contains("toggle-box")){
        listHolder.classList.remove("toggle-box")
        divv.parentElement.classList.remove("active-maker")
        divv.children[0].classList.replace("fa-square-caret-down", "fa-square-caret-right")
    }else{
        listHolder.classList.add("toggle-box")
        divv.parentElement.classList.add("active-maker")
        divv.children[0].classList.replace("fa-square-caret-right", "fa-square-caret-down")       
    }
}

function changeToUpperCaseInput(inp){
    inp.value = inp.value.toUpperCase()
}

function regexForPicRate(inp){
    inp.value = inp.value.replace(/[^0-9,]/g, '');
}

function showAssociatedShopAndTechnician(){
    let date_value = document.getElementsByClassName("date-error-input")[0].value
    let shop_value = document.getElementsByClassName("specific-shop-id-in-form")[0]
    let picRows = document.querySelectorAll('#table-body-of-pic tr:not(.d-none) .pic:not(.d-none),.form-area .upperPic')
    if (date_value.trim() == ""){
        alert("Please choose  date to get real time information of technicians..")
        shop_value.value = "0"
    }else if(date_value.trim() != "" && shop_value.value.trim() != "0" && shop_value.value.trim() != ""){
        fetch(`/get-data/show-technician-shop/${shop_value.value}~~${date_value}`)
        .then(response => response.json())
        .then(result => {
            if (document.getElementsByClassName("date-error-input")[0].classList.contains("for-tech-leaves")){
                let techSelectList = document.getElementById("availableList")
                techSelectList.innerHTML = ""
                result.forEach(tech => {
                    techSelectList.innerHTML += `<div><span>${tech[0]}</span><input value="${tech[1]}" type="checkbox"></div>`
                })
                document.getElementById("selectedList").querySelectorAll("div").forEach(divv => {
                    if (divv.getAttribute("hidden") == null){
                        divv.remove()
                    }
                })
            }else{
                document.getElementById("shop").value = shop_value.value
                let techDataList =  document.getElementById("datalistOptions")
                techDataList.innerHTML = ""
                result.forEach(tech => {
                    techDataList.innerHTML += `<option value="${tech[0]}" data-id="${tech[1]}"/>`
                })
                for (let eachRow of picRows){
                    eachRow.value = ""
                    // Manually trigger the onchange event
                    eachRow.dispatchEvent(new Event('change'));
                }
            }
        })
        .catch(err => console.log(err))
    }
}

function customerVehicleSubmit(){
    let vehicle = document.getElementById("brandListOptions")
    if (vehicle){
        let model_name = document.getElementById("model")
        if (model_name.value.trim() != ""){
            fetch(`/get-data/get-brand-model/${model_name.value}`)
            .then(response => response.json())
            .then(result => {
                console.log(result)
                if (result.length != 1) {
                    model_name.setAttribute('style', 'border: 2px solid red;');
                } else {
                    document.getElementById("brand_id").value = result[0][0]
                    document.getElementById("model_id").value = result[0][1]
                    document.getElementById("service-data-input-form").submit()
                }
            })
            .catch(err => {console.log(err);})
        }else{
            model_name.setAttribute('style', 'border: 2px solid red;');
        }
    }else{
        document.getElementById("service-data-input-form").submit()
    }
}

function showTagInInputForm(btn){
    const listsSection = document.querySelectorAll(".list-sec");
    const carList = document.getElementById("car-list"); 
    const amount = document.getElementById("car-add");
    const listItems = document.querySelectorAll(".list-item")
    const addCarBtn = document.getElementsByClassName("showHiddenCar")[0]
    if(btn.classList.contains("car-list")){
        listsSection.forEach((listSection) => {
            listSection.style.display = "none";
        })
        if(!btn.classList.contains("active")){
            listItems.forEach((listItem) => {
                listItem.classList.remove("active");
            })
            btn.classList.add("active");
        }
        carList.style.display = "block";
        addCarBtn.classList.remove("d-none")
    }
    if(btn.classList.contains("car-add")){
        listsSection.forEach((listSection) => {
            listSection.style.display = "none"
        })
        if(!btn.classList.contains("active")){
            listItems.forEach((listItem) => {
                listItem.classList.remove("active");
            })
            btn.classList.add("active")
        }
        console.log(amount)
        amount.style.display = "block"
        addCarBtn.classList.add("d-none")
    }
}

function showHiddenCarAddInputForm(){
    let sthInBtn = document.getElementsByClassName('showHiddenCar')[0]
    let hiddenInput = document.getElementById('add-input-cars-add-box')
    if (sthInBtn.textContent == '+'){
        hiddenInput.classList.remove('d-none')
        sthInBtn.textContent = '-'
    }else{
        hiddenInput.classList.add('d-none')
        sthInBtn.textContent = '+'
    }
}

function submitInsideForm(){
    let prefixBox = document.getElementById("regPrefix")
    let digitBox = document.getElementById("regDigits")
    let regState = document.getElementById("regState")
    let errMgsHolder = document.getElementsByClassName("error-mgs-for-car-add")[0]
    let customer_id = document.getElementById("customerId")
    if (prefixBox.value.trim() == "" || digitBox.value.trim() == ""){
        prefixBox.setAttribute("style","border:2px solid red;")
        digitBox.setAttribute("style","border:2px solid red;")
    }else{
        let plate = regState.value + prefixBox.value.trim() + digitBox.value.trim()
        console.log(plate)
        fetch(`/get-data/check-vehicle/${plate}`)
        .then(response => response.json())
        .then(result => {
            if (result.length == 0){
                errMgsHolder.classList.remove("d-none")
                errMgsHolder.innerHTML = `Vehicle ${plate} is not registered in our system..`
            }else{
                fetch(`/get-data/ownership/${result[0][0]}||${customer_id.value}`)
                .then(response => {
                    if (response.status == 200){
                        window.location.reload()
                    }
                })
                .catch(err => errMgsHolder.innerHTML = err)
            }
            console.log(result)
        })
        .catch(err => errMgsHolder.innerHTML = err)
    }
}

function showInputBrand(div,typ){
    if (typ == 'brand'){
        if (div.classList.contains('fa-square-pen')){
            div.previousElementSibling.children[0].classList.add("d-none")
            div.previousElementSibling.children[1].classList.add("d-none")
            div.previousElementSibling.children[2].classList.remove("d-none")
            div.classList.replace("fa-square-pen","fa-square-check")
        }else{
            div.previousElementSibling.children[0].classList.remove("d-none")
            div.previousElementSibling.children[1].classList.remove("d-none")
            div.previousElementSibling.children[2].classList.add("d-none")
            div.classList.replace("fa-square-check","fa-square-pen")
        }
    }else if (typ == 'model'){
        value = div.textContent.trim()
        if(div.innerHTML.startsWith('<input')){
            div.innerHTML = div.children[0].value
        }else{
            div.innerHTML = `<input type="text" id="model" onkeyup="insertDataDb(this,'${value}')" required value="${value}">`
        }
    }
}

function insertDataDb(inp,data){
    if(event.keyCode == '13'){
        console.log(data,data.length)
        fetch(`/get-data/${inp.id}/${inp.value.trim()}~${data}`)
        .then(response => {
            if (response.status == 200){
                window.location.reload()
            }})
        .catch(err => console.log(err))
    }
}

function showHiddenInputBrand(){
    btnText = document.getElementsByClassName("showHiddenInputBrandClicker")[0]
    let hiddenInp = document.getElementById("hidden-maker-box")
    if (hiddenInp.classList.contains("d-none")){
        hiddenInp.classList.remove("d-none")
        btnText.textContent = 'Discard'
    }else{
        btnText.textContent = 'Create'
        hiddenInp.classList.add("d-none")
    }
}

function tickThePsfuCall(tick){
    let wholeTr = tick.parentElement.parentElement
    console.log(wholeTr)
    let status_id = wholeTr.querySelector("#status_id").value.trim()
    if (status_id == ''){
        alert("Please select PSFU status..")
        tick.checked = false;
    }else{
        if(confirm("Are you sure want to close this call?")){
            console.log(tick.value)
            fetch(`/get-data/postPsfuCall/${wholeTr.querySelector("#psfu_id").value}||${status_id}||${wholeTr.querySelector("#remark").value}`)
            .then(response => {
                if (response.status == 200){
                    const tableData = tick.parentElement.parentElement.children;
                    for(let i = 0; i < tableData.length; i++){
                        tableData[i].classList.toggle("line-through");
                    };
                    tick.disabled = true;
                }
            })
            .catch(err => console.log(err))
        }else{
            tick.checked = false;
        }
    }
}

function checkRegisteredUser(idd,what){
    fetch(`/get-data/checkRegisteredUsers/${idd}|${what}`)
    .then(response => {
        if(response.status = 200){
            window.location.reload()
        }
    })
    .catch(err => console.log(err))
}

function stopPropagation(event) {
    event.stopPropagation();
}

function goBackToPreviousLocation(){
    window.history.back()
}

// check Min and hour

function checkMin(inp){
    const regex = /^\d{0,2}$/;
    if(regex.test(inp.value)){
        if(parseInt(inp.value) > 59 || parseInt(inp.value) < 0){
        inp.value = 0
    }
    }else{
        inp.value = 0
    }
}

function checkHour(inp){
    const regex = /^\d{0,2}$/;
    if(regex.test(inp.value)){
        if(parseInt(inp.value) > 23 || parseInt(inp.value) < 0){
            inp.value = 0
        }
        if(parseInt(inp.value) > 12){
            inp.nextElementSibling.nextElementSibling.value = "pm"
            inp.value = parseInt(inp.value) - 12
        }
    }else{
        inp.value = 0
    }
}

// Start Time End Time function

function calculatDuration(setBtn){
    let startTime , endTime , duration , startPlace ;
    if (setBtn.classList.contains('timeEndBtn')){
        endTime = setBtn.previousElementSibling
        startTime = setBtn.parentElement.previousElementSibling.children[0]
        duration = setBtn.parentElement.nextElementSibling
        startPlace = setBtn.parentElement.previousElementSibling
    }else{
        startTime = setBtn.previousElementSibling
        endTime = setBtn.parentElement.nextElementSibling.children[0]
        duration = setBtn.parentElement.nextElementSibling.nextElementSibling  
        startPlace = setBtn.parentElement 
    }
    if (startTime.value && endTime.value){
        const [h1, m1] = endTime.value.split(':').map(Number);
        const [h2, m2] = startTime.value.split(':').map(Number);
        const diffMinutes = (h1 * 60 + m1) - (h2 * 60 + m2);
        if (diffMinutes < 0){
            alert("Start time must be greater than end time...")
            startPlace.querySelectorAll("input").forEach(inp => {
                inp.value = ""
            })
        }else{
            const diffHours = Math.floor(diffMinutes / 60);
            const diffMinutesRemaining = diffMinutes % 60;
            const diffResult = String(diffHours).padStart(2,'0') + ':' + String(diffMinutesRemaining).padStart(2,'0')
            duration.children[0].textContent = diffResult
            duration.children[1].value = diffResult
            sumAllDurations()
        }
    }
}

function sumAllDurations(){
    let totalHours = totalMins = 0;
    Array.from(document.querySelectorAll(".durationForJob")).slice(1).forEach(inp => {
        const [h1, m1] = inp.value.split(':').map(Number)
        totalHours += h1
        totalMins += m1
    })
    document.getElementById("duration").textContent = String(totalHours).padStart(2, '0') + ':' + String(totalMins).padStart(2, '0')
}

function setTimeInput(startBtn){
    // getting elements
    const hourInpElement = startBtn.nextElementSibling;
    const minInpElement = startBtn.nextElementSibling.nextElementSibling;
    let ampmchooser = startBtn.nextElementSibling.nextElementSibling.nextElementSibling;
    const currentDate = new Date();
    const currentHour = currentDate.getHours(); 
    const currentMin = currentDate.getMinutes();

    console.log(hourInpElement.value,hourInpElement.value.length)
    if (hourInpElement.value == "" || (parseInt(hourInpElement.value) == 0 && minInpElement.value.trim() == "")) {
        if(currentHour > 12){
            ampmchooser.value = "pm"
            hourInpElement.value = currentHour - 12;
        }else{
            ampmchooser.value = currentHour < 12 ? "am" : "pm"
            hourInpElement.value = currentHour;
        } 
    }
    
    if (hourInpElement.value == "12"){
        ampmchooser.value = "pm"       
    }else if(hourInpElement.value == "0"){
        ampmchooser.value = "am"
    }

    if (minInpElement.value == "" || (parseInt(minInpElement.value) == 0 && hourInpElement.value.trim() == "")){
        minInpElement.value = currentMin;
    }

    startBtn.previousElementSibling.value = ampmchooser.value == "pm" & hourInpElement.value != "12"
    ? `${String(parseInt(hourInpElement.value) + 12).padStart(2, '0')}:${String(minInpElement.value).padStart(2, '0')}`
    : `${String(hourInpElement.value).padStart(2, '0')}:${String(minInpElement.value).padStart(2, '0')}`;
  
    console.log(startBtn.previousElementSibling.value)

    calculatDuration(startBtn)
}

function CheckIdFromOneToOne(inp){
    let inpVal = inp.value
    let is_valid = '00'
    console.log(inp.list.getElementsByTagName('option'))
    for (let opt of inp.list.getElementsByTagName('option')){
        if (inpVal == opt.value){
            is_valid = opt.getAttribute('data-id')
            inp.nextElementSibling.value = is_valid
            break;
        }
    }
    if (is_valid == '00'){
        inp.value = ""
        inp.nextElementSibling.value = "-1"
    }
    console.log(inp.nextElementSibling.value)
}

// technician transfer form

//Techanician Nav Change Function
function navChange(btn){
    const changeShop = document.getElementById("changeShop");
    const shopHistory = document.getElementById("shopHistory");
    const leaveForm = document.getElementById("leaveForm");
    console.log(btn,btn.nextElementSibling);
    if(btn.classList.contains("shopHistoryNav")){
        if(shopHistory.classList.contains("d-none")){
            shopHistory.classList.remove("d-none");
            btn.classList.add("active");
            btn.nextElementSibling.classList.remove("active");
            btn.nextElementSibling.nextElementSibling.classList.remove("active");
            changeShop.classList.add("d-none");
            leaveForm.classList.add("d-none");
        }
    }else if(btn.classList.contains("changeShopNav")){
        if(changeShop.classList.contains("d-none")){
            changeShop.classList.remove("d-none");
            btn.classList.add("active");
            btn.previousElementSibling.classList.remove("active");
            btn.nextElementSibling.classList.remove("active");
            shopHistory.classList.add("d-none");
            leaveForm.classList.add("d-none");
        }
    }else if(btn.classList.contains("leaveFormNav")){
        if(leaveForm.classList.contains("d-none")){
            leaveForm.classList.remove("d-none");
            btn.classList.add("active");
            btn.previousElementSibling.classList.remove("active");
            btn.previousElementSibling.previousElementSibling.classList.remove("active");
            changeShop.classList.add("d-none");
            shopHistory.classList.add("d-none");
        }
    }
}


function changeTabOver(btn, idd){
    const visibleObject = document.getElementById(idd);
    const allTabs = document.querySelectorAll('.eachTab')
    const tabLists = document.querySelectorAll(".tab-list");
    allTabs.forEach((allTab) => {
            allTab.classList.add("d-none")
    })
    tabLists.forEach((tabList) => {
            tabList.classList.remove("active");
    })
    btn.classList.add('active')
    console.log(visibleObject)
    visibleObject.classList.remove('d-none')
}

// techanician edit btn function
function showTechnicianInput(btn){
    const techanicianDetailCard = document.getElementById("techanichianDetailCard");
    const hiddeninput = techanicianDetailCard.querySelectorAll("input");
    const currentValue = techanicianDetailCard.querySelectorAll("span");

    if(btn.innerText == "Edit"){
        btn.classList.add("d-none");
        btn.nextElementSibling.classList.remove("d-none");
        btn.nextElementSibling.nextElementSibling.setAttribute("onclick","removeTechnicianInput(this)")
        btn.nextElementSibling.nextElementSibling.children[0].setAttribute("onclick", "return false;")
        currentValue[0].hidden = true;
        hiddeninput[0].value = currentValue[0].innerText;
        hiddeninput[0].classList.remove("d-none");
    }
}

function removeTechnicianInput(btn){
    const techanicianDetailCard = document.getElementById("techanichianDetailCard");
    const hiddeninput = techanicianDetailCard.querySelectorAll("input");
    const currentValue = techanicianDetailCard.querySelectorAll("span");
    btn.previousElementSibling.previousElementSibling.classList.remove("d-none");
    btn.previousElementSibling.classList.add("d-none");
    btn.children[0].removeAttribute("onclick");
    currentValue[0].hidden = false;
    hiddeninput[0].classList.add("d-none");

}

// leavees 


function gotoform(clickedTab){
    const leaveForm = document.getElementById("leaveForm");
    clickedTab.parentElement.style.display = "none";
    leaveForm.style.display = "grid";
    if(clickedTab.innerText == "Leave"){
        leaveForm.children[1].children[2].style.display = "none";
    }else{
        leaveForm.children[0].children[4].style.display = "none";
        leaveForm.children[0].children[4].removeAttribute("required")

        leaveForm.children[1].children[0].style.display = "none";

        leaveForm.children[1].children[1].style.display = "none";
        leaveForm.children[1].children[1].removeAttribute("required")

        document.getElementById("shopListInModal").classList.remove("d-none")
    }
}

function addToList(){
    let shopAvailableList = document.getElementById("shopListInModal")
    const availableList = shopAvailableList.classList.contains("d-none") ?  document.getElementById('availableList') : shopAvailableList;
    const selectedList = document.getElementById("selectedList");

    let i;
    for(i = 0; i < availableList.children.length; i++){
        if(availableList.children[i].querySelector("input").checked == true && !availableList.children[i].hidden){
            availableList.children[i].hidden = true;
            let theName = availableList.children[i].querySelector("span").innerText;
            let clonedDiv = selectedList.querySelector("div[hidden]").cloneNode(true);
            clonedDiv.removeAttribute("hidden");
            clonedDiv.querySelector("span").innerText = theName;  
            clonedDiv.querySelector("input").value = availableList.children[i].querySelector("input").value
            selectedList.append(clonedDiv);
        }
    }
    document.getElementById("multipleSelectModal").querySelector("input[type='search']").value = ""
    let y;
    for(y = 0; y < availableList.children.length; y++){
        if(!availableList.children[y].hidden){
            availableList.children[y].style.display = "";
        }
    }    
    document.getElementById("modalCloseBtn").click();
}

function deleteParentDiv(btn){
    let shopAvailableList = document.getElementById("shopListInModal")
    const availableList = shopAvailableList.classList.contains("d-none") ?  document.getElementById('availableList') : shopAvailableList;
    console.log(availableList)
    for(i = 0; i < availableList.children.length; i++){
        if(btn.previousElementSibling.previousElementSibling.innerText == availableList.children[i].querySelector("span").innerText && availableList.children[i].hidden == true){
            availableList.children[i].removeAttribute("hidden");
            availableList.children[i].querySelector("input").checked = false;
        }
    }
    btn.parentElement.remove();
}

// search feature of modal box
function searchavailableList(inp){
    const availableList = document.getElementById('availableList');
    if(inp.value.length > 0){
        let x;
        for(x = 0; x < availableList.children.length; x++){
            let eachlistText = availableList.children[x].querySelector("span").innerText;
            if(!eachlistText.trim().toUpperCase().includes(inp.value.toUpperCase())){
                availableList.children[x].style.display = "none";
            }else{
                availableList.children[x].style.display = "";
            }
        }
    }else{
        let y;
        for(y = 0; y < availableList.children.length; y++){
            if(!availableList.children[y].hidden){
                availableList.children[y].style.display = "";
            }
        }
    }
}

// leave report dropdown feature
function droppingFilter(btn){
    const dropdown = document.getElementsByClassName("filter_dropdown");
    let i;
    for(i = 0 ; i < dropdown.length; i++){
        dropdown[i].style.display = "none";
    }
    
    if(btn.nextElementSibling.style.display == "none"){
        btn.nextElementSibling.style.display = "";
    }else if(btn.nextElementSibling.style.display = ""){
        btn.nextElementSibling.style.display = "none";
    }
}


// window.addEventListener("click", function(e){
//     const dropdown = document.getElementsByClassName("filter_dropdown");
//     if(!e.target.classList.contains("filter_btn")){
//         let i;
//         for(i = 0 ; i < dropdown.length; i++){
//             dropdown[i].style.display = "none";
//         }
//     }
// })