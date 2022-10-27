let filterObject = {
    "product": [],
    "criteria":     [],
    "sortby": ""
}

const inputSelect = (inputName) => {
    let selectedItem = document.getElementById(`${inputName}-input`);

    let badgeBox = document.getElementById(`${inputName}-badgebox`);
    let applyAnchor = document.getElementById("apply");

    filterObject[`${inputName}`].push(selectedItem.value)
    applyAnchor.href = `/budget-report/?product_fitler=${filterObject.product.join("--")}&criteria_fitler=${filterObject.criteria.join("--")}&sortby=${filterObject.sortby}`

    let span = document.createElement("span");
    span.innerHTML = selectedItem.options[selectedItem.selectedIndex].textContent.trim();
//     set product id with product value
    span.id = selectedItem.value

    span.classList.add("select-badge");
    badgeBox.appendChild(span);

    selectedItem.remove(selectedItem.selectedIndex)

}

const sortSelect = (inputName) => {
    let selectedItem = document.getElementById(`${inputName}-input`);
    let applyAnchor = document.getElementById("apply");

    filterObject[`${inputName}`]  = selectedItem.value
    document.querySelector("#product-badgebox").onclick = function(e){
        if(e.srcElement.className == "select-badge"){
            filterObject.product = filterObject.product.filter(el => el !== e.target.id)
        }
       }

    if(document.location.href.endsWith("/budget-report/")){
        applyAnchor.href = `/budget-report/?product_fitler=${filterObject.product.join("--")}&criteria_fitler=${filterObject.criteria.join("--")}&sortby=${filterObject.sortby}`
    }else{
        let paramsArray = document.location.search.replace("?", "").split("&")
        console.log(paramsArray[0],paramsArray[1])
        applyAnchor.href = `/budget-report/?${paramsArray[0]}&${paramsArray[1]}&sortby=${filterObject.sortby}`
    }
}

const valueSet = () => {
    let paramsInput = document.getElementById("params");

    if(document.location.href.endsWith("/budget-report/")){
        paramsInput.value = `product_fitler=${filterObject.product.join("--")}&criteria_fitler=${filterObject.criteria.join("--")}&sortby=${filterObject.sortby}`
    }else{
        let paramsArray = document.location.search.replace("?", "").split("&")
        paramsInput.value = `${paramsArray[0]}&${paramsArray[1]}&sortby=${filterObject.sortby}`
    }
}

const valueSubmit = () => {
    let month_value = document.getElementById("month_value").value
    let month_input = document.getElementById("month_input").value;

    if(month_value == "" || month_value == null){
        alert("Please fill the value of month");
        return false
    }
    else if(month_input == "Select a month..." || month_input == null){
        alert("Please select a month");
        return false
    }
}


window.addEventListener("load", function(){
    document.querySelector("#product-badgebox").onclick = function(e){
        if(e.srcElement.className == "select-badge"){
            let option = document.createElement("option");
            option.innerHTML = e.target.innerText;

//          create option value and id with span value and id
            option.value = e.target.id
            option.id = e.target.id

            document.querySelector("#product-input").appendChild(option);
//          delete product form filterObject by the id
            filterObject.product = filterObject.product.filter(el => el !== e.target.id)
            console.log(filterObject.product)
            let applyAnchor = document.getElementById("apply");
            applyAnchor.href = `/budget-report/?product_fitler=${filterObject.product.join("--")}&criteria_fitler=${filterObject.criteria.join("--")}&sortby=${filterObject.sortby}`

            e.target.remove()
        }
    }

    document.querySelector("#criteria-badgebox").onclick = function(e){
        if(e.srcElement.className == "select-badge"){
            let option = document.createElement("option");
            option.innerHTML = e.target.innerText;
            option.value = e.target.innerText

            document.querySelector("#criteria-input").appendChild(option);

            filterObject['criteria'] = filterObject.criteria.filter(el => el !== e.target.innerText)

            let applyAnchor = document.getElementById("apply");
            applyAnchor.href = `/budget-report/?product_fitler=${filterObject.product.join("--")}&criteria_fitler=${filterObject.criteria.join("--")}&sortby=${filterObject.sortby}`

            e.target.remove()
        }
    }
})



