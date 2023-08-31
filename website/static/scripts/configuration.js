const listItems = document.querySelectorAll(".list-item");
listItems.forEach((listItem) => {
    listItem.addEventListener("click",function(e){
        const listsSection = document.querySelectorAll(".list-sec");
        const carList = document.getElementById("car-list"); 
        const amount = document.getElementById("amount");
        if(this.classList.contains("car-list")){
            listsSection.forEach((listSection) => {
                listSection.style.display = "none";
            })
            if(!this.classList.contains("active")){
                listItems.forEach((listItem) => {
                    listItem.classList.remove("active");
                })
                this.classList.add("active");
            }
            carList.style.display = "block";
        }
        if(this.classList.contains("amount")){
            listsSection.forEach((listSection) => {
                listSection.style.display = "none"
            })
            if(!this.classList.contains("active")){
                listItems.forEach((listItem) => {
                    listItem.classList.remove("active");
                })
                this.classList.add("active")
            }
            amount.style.display = "block"
        }
    })
})

