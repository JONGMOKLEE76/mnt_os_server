document.addEventListener('DOMContentLoaded', () => {
    const tableSelect = document.getElementById('table-select');
    const tableHead = document.getElementById('table-head');
    const tableBody = document.getElementById('table-body');
    const pagination = document.getElementById('pagination');
    const addBtn = document.getElementById('add-btn');
    const modal = document.getElementById('master-modal');
    const modalTitle = document.getElementById('modal-title');
    const masterForm = document.getElementById('master-form');
    const formFields = document.getElementById('form-fields');
    const closeBtns = document.querySelectorAll('.close-modal');

    let currentTable = tableSelect.value;
    let currentPage = 1;
    let columns = [];
    let pkColumn = '';

    // Load Data
    async function loadData(page = 1) {
        currentPage = page;
        try {
            const response = await fetch(`/api/master-data/${currentTable}?page=${page}`);
            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            columns = data.columns;
            renderTable(data);
            renderPagination(data);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    function renderTable(data) {
        // Render Headers
        tableHead.innerHTML = `
            <tr>
                ${data.columns.map(col => `<th>${col}</th>`).join('')}
                <th>Actions</th>
            </tr>
        `;

        // Render Rows
        tableBody.innerHTML = data.items.map(item => `
            <tr>
                ${data.columns.map(col => `<td>${item[col] || ''}</td>`).join('')}
                <td>
                    <button class="action-btn approve edit-btn" data-id="${item[data.columns[0]]}">Edit</button>
                    <button class="action-btn reject delete-btn" data-id="${item[data.columns[0]]}">Delete</button>
                </td>
            </tr>
        `).join('');

        // Add Event Listeners
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', () => openModal('edit', btn.dataset.id));
        });
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => deleteItem(btn.dataset.id));
        });
    }

    function renderPagination(data) {
        let html = '';
        for (let i = 1; i <= data.total_pages; i++) {
            html += `<button class="page-btn ${i === data.page ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        pagination.innerHTML = html;

        document.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => loadData(parseInt(btn.dataset.page)));
        });
    }

    // Modal Logic
    function openModal(mode, id = null) {
        modalTitle.innerText = mode === 'edit' ? 'Edit Data' : 'Add New Data';
        modal.style.display = 'flex';

        // Generate Form Fields
        formFields.innerHTML = columns.map(col => `
            <div class="form-group">
                <label class="form-label">${col}</label>
                <input type="text" name="${col}" class="form-input" ${mode === 'edit' && col === columns[0] ? 'readonly' : ''}>
            </div>
        `).join('');

        if (mode === 'edit') {
            // Fetch item data and populate form
            const row = Array.from(tableBody.rows).find(r => r.cells[0].innerText === id);
            if (row) {
                columns.forEach((col, index) => {
                    masterForm.elements[col].value = row.cells[index].innerText;
                });
            }
            masterForm.dataset.mode = 'edit';
            masterForm.dataset.id = id;
        } else {
            masterForm.reset();
            masterForm.dataset.mode = 'add';
        }
    }

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => modal.style.display = 'none');
    });

    window.onclick = (event) => {
        if (event.target === modal) modal.style.display = 'none';
    };

    // Form Submission
    masterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(masterForm);
        const data = Object.fromEntries(formData.entries());
        const mode = masterForm.dataset.mode;
        const id = masterForm.dataset.id;

        const url = mode === 'edit' ? `/api/master-data/${currentTable}/${id}` : `/api/master-data/${currentTable}`;
        const method = mode === 'edit' ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (result.error) {
                alert(result.error);
            } else {
                modal.style.display = 'none';
                loadData(currentPage);
            }
        } catch (error) {
            console.error('Error saving data:', error);
        }
    });

    // Delete Logic
    async function deleteItem(id) {
        if (!confirm('Are you sure you want to delete this item?')) return;

        try {
            const response = await fetch(`/api/master-data/${currentTable}/${id}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (result.error) {
                alert(result.error);
            } else {
                loadData(currentPage);
            }
        } catch (error) {
            console.error('Error deleting data:', error);
        }
    }

    // Initial Load
    tableSelect.addEventListener('change', () => {
        currentTable = tableSelect.value;
        loadData(1);
    });

    addBtn.addEventListener('click', () => openModal('add'));

    loadData();
});
