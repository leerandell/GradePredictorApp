const toggleBtn = document.getElementById('toggle-btn');
const toggleBtnCollapsed = document.getElementById('toggle-btn-collapsed');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');

toggleBtn.addEventListener('click', () => {
    sidebar.classList.add('collapsed');
    toggleBtn.style.display = 'none';
    toggleBtnCollapsed.style.display = 'block';
});

toggleBtnCollapsed.addEventListener('click', () => {
    sidebar.classList.remove('collapsed');
    toggleBtnCollapsed.style.display = 'none';
    toggleBtn.style.display = 'block';
});

function updateSliderValue(sliderId, valueId) {
    const slider = document.getElementById(sliderId);
    const valueDisplay = document.getElementById(valueId);

    slider.addEventListener('input', () => {
        valueDisplay.textContent = slider.value;
    });
}

// Initialize sliders
updateSliderValue('financialSituation', 'financialSituationValue');
updateSliderValue('learningEnvironment', 'learningEnvironmentValue');

// Define pagination functions in the global scope
const rowsPerPage = 5;

function setupPagination(rows, pagination, displayPageFunc) {
    const totalPages = Math.ceil(rows.length / rowsPerPage);
    pagination.innerHTML = ''; // Clear existing pagination

    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.classList.add('page-item');
        if (i === 1) li.classList.add('active');

        const a = document.createElement('a');
        a.classList.add('page-link');
        a.href = '#';
        a.textContent = i;

        a.addEventListener('click', (e) => {
            e.preventDefault();
            displayPageFunc(i);
        });

        li.appendChild(a);
        pagination.appendChild(li);
    }

    displayPageFunc(1); // Display the first page initially
}

function displayPage1(page) {
    const tableBody1 = document.querySelector('#flush-collapseTwo tbody');
    const rows1 = tableBody1.getElementsByTagName('tr');
    for (let i = 0; i < rows1.length; i++) {
        rows1[i].style.display = 'none';
    }

    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    for (let i = start; i < end && i < rows1.length; i++) {
        rows1[i].style.display = '';
    }

    const paginationButtons = document.getElementById('pagination').getElementsByTagName('li');
    for (let i = 0; i < paginationButtons.length; i++) {
        paginationButtons[i].classList.remove('active');
    }
    paginationButtons[page - 1].classList.add('active');
}

function displayPage2(page) {
    const tableBody2 = document.querySelector('#panelsStayOpen-collapseTwo tbody');
    const rows2 = tableBody2.getElementsByTagName('tr');
    for (let i = 0; i < rows2.length; i++) {
        rows2[i].style.display = 'none';
    }

    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    for (let i = start; i < end && i < rows2.length; i++) {
        rows2[i].style.display = '';
    }

    const paginationButtons = document.getElementById('pagination-stored').getElementsByTagName('li');
    for (let i = 0; i < paginationButtons.length; i++) {
        paginationButtons[i].classList.remove('active');
    }
    paginationButtons[page - 1].classList.add('active');
}

// Handle the prediction form submission
document.getElementById('prediction-form').addEventListener('submit', function (e) {
    e.preventDefault();  // Prevent the default form submission

    const daysPresent = parseFloat(document.querySelector('input[name="days_present"]').value);
    const schoolDays = parseFloat(document.querySelector('input[name="school_days"]').value);
    const previousGrades = parseFloat(document.querySelector('input[name="previous_grades"]').value);
    const financialSituation = parseFloat(document.querySelector('input[name="financial_situation"]').value);
    const learningEnvironment = parseFloat(document.querySelector('input[name="learning_environment"]').value);

    // Frontend validation
    if (isNaN(daysPresent) || isNaN(schoolDays) || isNaN(previousGrades)) {
        alert('Please fill in all fields.');
        return;
    }

    // Days present should not be negative
    if (daysPresent < 0) {
        alert('Days present cannot be negative.');
        return;
    }

    // Days present should not exceed school days
    if (daysPresent > schoolDays) {
        alert('Days present cannot exceed school days.');
        return;
    }

    // Construct the data payload
    const data = {
        days_present: daysPresent,
        school_days: schoolDays,
        attendance: (daysPresent / schoolDays) * 100,
        previous_grades: previousGrades,
        financial_situation: financialSituation,
        learning_environment: learningEnvironment
    };

    // Send the data to the server
    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            throw new Error(result.error);
        }

        // Update the tables with new data
        const firstAccordionTable = document.querySelector('#flush-collapseTwo tbody');
        const newRowInputs = document.createElement('tr');
        newRowInputs.innerHTML = `
            <td>${result.student_id}</td>
            <td>${data.attendance.toFixed(2)}</td>
            <td>${previousGrades}</td>
            <td>${financialSituation}</td>
            <td>${learningEnvironment}</td>
            <td>${result.prediction.toFixed(2)}</td>
            <td>${result.remarks}</td>
        `;
        firstAccordionTable.appendChild(newRowInputs);

        const secondAccordionTable = document.querySelector('#panelsStayOpen-collapseTwo tbody');
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>${result.student_id}</td>
            <td>${result.prediction.toFixed(2)}</td>
            <td>${result.remarks}</td>
        `;
        secondAccordionTable.appendChild(newRow);

        // Call the pagination setup for both tables
        const rows1 = firstAccordionTable.getElementsByTagName('tr');
        const rows2 = secondAccordionTable.getElementsByTagName('tr');
        const pagination1 = document.getElementById('pagination');
        const pagination2 = document.getElementById('pagination-stored');

        setupPagination(rows1, pagination1, displayPage1);
        setupPagination(rows2, pagination2, displayPage2);

        document.getElementById('prediction-result').textContent = 'Predicted Grade: ' + result.prediction.toFixed(2);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Prediction failed: ' + error.message);
    });
});

// Initialize pagination after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    const tableBody1 = document.getElementById('csv-data-body');
    const rows1 = tableBody1.getElementsByTagName('tr');
    const pagination1 = document.getElementById('pagination');
    
    const tableBody2 = document.getElementById('stored-predictions-body');
    const rows2 = tableBody2.getElementsByTagName('tr');
    const pagination2 = document.getElementById('pagination-stored');

    // Initialize pagination for both tables
    setupPagination(rows1, pagination1, displayPage1);
    setupPagination(rows2, pagination2, displayPage2);
});
