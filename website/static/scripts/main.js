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
    document.cookie = 'pg-username' + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = 'user_roles' + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location = '/auth/log'
}
if (window.location.href.includes("/auth")){
    document.cookie = 'pg-username' + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = 'user_roles' + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
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
        function drawChart() {
            // Define the chart to be drawn.
            for (var idx = 1; idx < result.length; idx++) {
                result[idx] = result[idx].map((value, index) =>
                    (index === 0 || index === result[idx].length - 1) ? value : parseFloat(value)
                );
            }
            if (result.length > 20){
            document.getElementById("chartContainer").children[0].style.width = `${(result.length - 1)*30}px`
            }
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
                    fontSize: 10 // Adjust the data label font size
                }
            },
            // Hover text (tooltip)
            tooltip: {
                highcontrast:true,
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
            // SET ROTATE TEXT
            google.visualization.events.addListener(chart, 'ready', function () {
                var observer = new MutationObserver(function () {
                  var labels = container.getElementsByTagName('text');
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

function addAnotherRow(td) {
    let no_error = true
    let inps = td.parentElement.previousElementSibling.getElementsByClassName("inp");
    
    td.parentElement.previousElementSibling.querySelectorAll("input.pic:not(.d-none)").forEach(pic => {
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
      let clonedRow = document.getElementById("willBeCloned").cloneNode(true);
      clonedRow.classList.remove('d-none')
      td.parentElement.parentNode.insertBefore(clonedRow, td.parentElement);
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

function deleteJobRow(btn,bool){
    if (bool && btn.parentElement.parentElement.children.length > 3 && !btn.classList.contains("disabled")){
        if(confirm("Are you sure want to delete the data?")){
            btn.parentElement.remove()        
        }
    }
}

function checkVehiclePlate(inp,what){
    let state = prefix = digit = plate = ''
    state = inp.previousElementSibling.value
    prefix = inp.value
    digit = inp.nextElementSibling.value
    if (what == 'digit'){
        state = inp.previousElementSibling.previousElementSibling.value
        prefix = inp.previousElementSibling.value
        digit = inp.value
    }
    if (prefix.length >=2 && digit.length == 4){
        plate = state.trim() + prefix.trim() + digit.trim()
        fetch(`/get-data/vehicle/${plate}`)
        .then(response => response.json() )
        .then(result => {
            console.log(result)
            if(result.length > 0){
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
                    lst.innerHTML += `<tr ${class_name}>
                    <td><button type='button' ${disabled_text} data-bs-dismiss='modal' onclick="autoFillVehicleInfo('${data[0]}','${data[6]}')" style="font-size:5px;" class='btn btn-sm btn-info'>✔️</button></td>
                    <td>${data[0]}</td>
                    <td>${data[1]}</td>
                    <td>${data[2]}</td>
                    <td>${data[3]}</td>
                    <td>${data[4]}</td>
                    <td>${data[5]}</td>
                </tr>`
                i ++;
                }
                document.getElementById("changeOwner").setAttribute("onclick",`autoFillVehicleInfo('${data[0]}',null)`)
                document.getElementById("vehicleInformation").value = data[9]
                let modalClicker = document.getElementsByClassName("validateModal")
                modalClicker[0].click()
            }else{
                document.querySelectorAll(".autoFillByVehicle").forEach(val => {
                    val.disabled = false
                    val.value = ""
                    document.getElementById("vehicleInformation").value = "None"
                })
            }
        })
        .catch(err => console.log(err))

    }
}

function autoFillVehicleInfo(idd,cus_id){
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
        let values = cus_id ? [result[0][3],result[0][7],result[0][5],result[0][1],result[0][4],result[0][2],result[0][8]] : [result[0][1],result[0][2],result[0][8]]
        let classPlacer = cus_id ? 'autoFillByVehicle' : 'autoFillNewOwner'
        var i = 0;
        document.querySelectorAll(`.${classPlacer}`).forEach(val => {
            val.disabled = true;
            val.value = values[i]
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

function checkAllServiceDatas() {
    let picRows = document.querySelectorAll('#table-body-of-pic tr:not(.d-none) .pic:not(.d-none),.form-area .upperPic');
    let allRows = document.querySelectorAll('.input-sec input:not([hidden]):not([disabled]),#table-body-of-pic tr:not(.d-none) .inp');
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
    // Validate picRows inputs
    for (let pic of picRows) {
        if (pic.value.trim() == "") {
            pic.setAttribute('style', 'border: 2px solid red;');
            promises.push(Promise.resolve(false));
        } else {
            shop_value = document.getElementById("temp_shop_id").textContent
            console.log(shop_value)
            promises.push(
                fetch(`/get-data/check-technician/${pic.value}|${shop_value}`)
                .then(response => response.json())
                .then(result => {
                    if (result.length != 1) {
                        pic.setAttribute('style', 'border: 2px solid red;');
                        return false;
                    } else {
                        return true;
                    }
                })
                .catch(err => {
                    console.log(err);
                    return false;
                })
            );
        }
    }

    Promise.all(promises).then(results => {
        let no_error = results.every(result => result);

        if (no_error) {
            document.getElementById("service-data-input-form").submit();
        }
    });
}


offsetLimit  = 81
function clickPagination(target,txt){
    target_mapp = {"job":"job-data-changeable",
              "vehicles":"vehicle-data-changeable",
              "customers":"customer-data-changeable"}
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
                replaceTableData(result,target)
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
                if (target == 'job') {         
                    formattedDate = new Date(result[0][1]).toISOString().substr(0, 10);
                }
                if(last+82 > Number(getTotal)){
                    display_amt_holder.textContent = `${last+1}-${getTotal} / ${getTotal}`
                }else{
                    display_amt_holder.textContent = `${last+1}-${last+81} / ${getTotal}`
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
        if (target == 'job'){
            all_tr[i].setAttribute('onclick',`redirectToFormEdit('${result[i][4]}','eachJob')`)
            tds = all_tr[i].getElementsByTagName('td');
            Array.from(tds).forEach((td, index) => {
            td.innerText = index === 1
            ? new Date(result[i][index]).toISOString().substr(0, 10)
            : result[i][index];
            });
        } else{
            all_tr[i].setAttribute('onclick',`redirectToFormEdit('${result[i][0]}','${target.slice(0,-1)}')`)
            tds = all_tr[i].getElementsByTagName('td');
            Array.from(tds).forEach((td, index) => { td.innerText = result[i][index+1]; });        
        }
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
    let table_column = {'eachJobs':'job_no','customer':'name','vehicle':'plate'}
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
    for (let delBtn of  document.querySelectorAll(".disabled-for-delete")){
        delBtn.classList.remove("disabled")
    }
    btn.classList.add('d-none')
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

function showAssociatedShopAndTechnician(inp){
    document.getElementById("temp_shop_id").textContent = inp.value
    fetch(`/get-data/show-technician-shop/${inp.value}`)
    .then(response => response.json())
    .then(result => {
        document.getElementById("shop").value = inp.value
        let techDataList =  document.getElementById("datalistOptions")
        techDataList.innerHTML = ""
        result.forEach(tech => {
            techDataList.innerHTML += `<option value="${tech[0]}"/>`
        })
    })
    .catch(err => console.log(err))
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
        value = div.previousElementSibling.children[1].textContent.split("(")[0]
        div.previousElementSibling.innerHTML = `<input type="text" id="brand" onkeyup="insertDataDb(this,'${value}')" required value='${value}'>`
        div.previousElementSibling.children[0].focus()
        div.classList.remove("fa-square-pen")
    }else if (typ == 'model'){
        value = div.textContent.trim()
        div.innerHTML = `<input type="text" id="model" onkeyup="insertDataDb(this,'${value}')" required value="${value}">`
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
    console.log(tick.value)
    fetch(`/get-data/removeCall/${tick.value}`)
    .then(response => {
        if (response.status == 200){
            tick.disabled = true;
        }
    })
    .catch(err => console.log(err))
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