const addItemButton = document.getElementById('add-button');
const tableBody = document.querySelector('#table tbody');
const tableTotalBody = document.querySelector('#table-total-body');
const searchButton = document.getElementById('search-button');

function populateTable(data) {
	let currentRow = null;

	// Clear the existing table rows
	tableBody.innerHTML = '';

	for (let index = 0; index < data.length; index++) {
		const item = data[index];
		const row = tableBody.insertRow();
		row.dataset.itemId = item.item_id;

		row.innerHTML = `
          <td class="item-number" id="item-${item.item_number}">${item.item_number}</td>
          <td contenteditable="true" class="item-date">${item.date}</td>
          <td contenteditable="true" class="item-name">${item.item_name}</td>
          <td contenteditable="true" class="cost-per-item">$ ${item.cost_per_item}</td>
          <td contenteditable="true" class="current-price">$ ${item.current_price}</td>
          <td contenteditable="true" class="number-of-items">${item.number_of_items}</td>
          <td class="total-cost">$ ${item.total_cost}</td>
          <td class="total-value">$ ${item.total_value}</td>
          <td class="total-return-dollar">$ ${item.total_return_dollar}</td>
          <td class="total-return-percent">${item.total_return_percent} %</td>
          <td contenteditable="true" class="item-link">${item.item_link}</td>
          <td contenteditable="true" class="action-data">
            <div class="action-buttons hidden">
              <button class="btn btn-success" id="edit-button">✅</button>
              <button class="btn btn-danger" id="delete-button">⛔</button>
            </div>
          </td>
      `;

		// Add an event listener to the edit button in each row
		const editButton = row.querySelector('#edit-button');
		editButton.addEventListener('click', function () {
			// retrieve the item id from the row
			const itemId = row.querySelector('.item-number').textContent;

			// removing $ and %
			function removeSymbols(text) {
				return text.replace(/[$,%]/g, '');
			}

			// Retrieve the corresponding item's data from the table cells
			const editedData = {
				date: row.querySelector('.item-date').textContent,
				item_name: row.querySelector('.item-name').textContent,
				cost_per_item: removeSymbols(
					row.querySelector('.cost-per-item').textContent
				),
				current_price: removeSymbols(
					row.querySelector('.current-price').textContent
				),
				number_of_items: row.querySelector('.number-of-items').textContent,
				total_cost: removeSymbols(row.querySelector('.total-cost').textContent),
				total_value: removeSymbols(
					row.querySelector('.total-value').textContent
				),
				total_return_dollar: removeSymbols(
					row.querySelector('.total-return-dollar').textContent
				),
				total_return_percent: removeSymbols(
					row.querySelector('.total-return-percent').textContent
				),
				item_link: row.querySelector('.item-link').textContent,
			};
			saveEditedData(itemId, editedData);
		});

		// Add event listener to the delete button in each row
		const deleteButton = row.querySelector('#delete-button');
		deleteButton.addEventListener('click', function () {
			// retrieve the item id from the row
			const itemId = row.querySelector('.item-number').textContent;
			deleteData(itemId);
		});

		// Add event listener to each cell
		const cells = row.querySelectorAll('td[contenteditable="true"]');
		for (let i = 0; i < cells.length; i++) {
			cells[i].addEventListener('mousedown', function () {
				// Hide buttons for the previous row
				if (currentRow !== null) {
					const buttonsToHide = currentRow.querySelectorAll('.action-buttons');
					for (let j = 0; j < buttonsToHide.length; j++) {
						buttonsToHide[j].classList.add('hidden');
					}
				}

				// Show buttons for the current row
				const buttonsToShow = row.querySelectorAll('.action-buttons');
				for (let j = 0; j < buttonsToShow.length; j++) {
					buttonsToShow[j].classList.remove('hidden');
				}

				// Update the current row
				currentRow = row;
			});
		}
	}
}

function populateTableTotals(data) {
	// Clear the existing table rows
	tableTotalBody.innerHTML = '';

	// Create row
	const row = tableTotalBody.insertRow();
	row.innerHTML = `
		<td class="total-total-items">${data.number_of_items}</td>
		<td class="total-total-cost">$ ${data.total_cost}</td>
		<td class="total-total-value">$ ${data.total_value}</td>
		<td class="total-total-return-$">$ ${data.total_return_dollar}</td>
		<td class="total-total-return-%">${data.total_return_percent} %</td>
	`;
}

function refresh_data() {
	// Call the populateTable function
	fetch('/get_data')
		.then((response) => response.json())
		.then((data) => {
			// Call the function to populate the table with the received data
			populateTable(data);
		})
		.catch((error) => {
			updateAlertContent('Error fetching data:', error);
		});

	// Call the populateTableTotal function
	fetch('/get_totals')
		.then((response) => response.json())
		.then((data) => {
			populateTableTotals(data);
		})
		.catch((error) => {
			updateAlertContent('Error fetching totals:', error);
		});
}

searchButton.addEventListener('click', function () {
	// Retrieve the search query from the search box
	const searchQuery = document.getElementById('search-box').value;

	// Send an AJAX request to the Flask route
	fetch('/search', {
		method: 'POST',
		body: new URLSearchParams({ search_query: searchQuery }),
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded',
		},
	})
		.then((response) => response.json())
		.then((result) => {
			// Update the table with the filtered data
			populateTable(result.data);

			// Update the totals table with the new totals
			populateTableTotals(result.totals);
		})
		.catch((error) => {
			console.error('Error:', error);
		});
});

function saveEditedData(itemId, editedData) {
	fetch(`/edit_item/${itemId}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(editedData),
	})
		.then((response) => response.json())
		.then((data) => {
			// Handle the response from the server, e.g., show an alert
			if (data.message) {
				// show message
				updateAlertContent(data.message);
				// refresh data
				refresh_data();
			} else {
				updateAlertContent(data.error);
			}
		})
		.catch((error) => {
			console.error('Error:', error);
		});
}

function deleteData(itemId) {
	fetch(`/delete_item/${itemId}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
	})
		.then((response) => {
			if (response.ok) {
				return response.json(); // Parse the response JSON
			} else {
				throw new Error('Error deleting item');
			}
		})
		.then((data) => {
			if (data.message) {
				updateAlertContent(data.message); // Show success message
				const rowToDelete = document.getElementById(`item-${itemId}`);
				// update tables
				refresh_data();
			}
		})
		.catch((error) => {
			console.error('Error:', error);
			updateAlertContent('An error occurred while deleting the item'); // Show error message
		});
}

if (window.location.pathname === '/') {
	refresh_data();
}

addItemButton.addEventListener('click', function () {
	// Create a new empty row
	const newRow = tableBody.insertRow(0);

	// Populate row
	newRow.innerHTML = `
	<td class="item-number"></td>
	<td contenteditable="true" class="item-date">REQUIRED</td>
	<td contenteditable="true" class="item-name"></td>
	<td contenteditable="true" class="cost-per-item">REQUIRED</td>
	<td contenteditable="true" class="current-price"></td>
	<td contenteditable="true" class="number-of-items">REQUIRED</td>
	<td class="total-cost"></td>
	<td class="total-value"></td>
	<td class="total-return-dollar"></td>
	<td class="total-return-percent"></td>
	<td contenteditable="true" class="item-link">REQUIRED</td>
	<td class="action-data">
			<div class="action-buttons">
					<button class="btn btn-success"  id="save-button" onclick="saveNewItem(this)">💾</button>
					<button class="btn btn-danger"  id="cancel-button" onclick="cancelNewItem(this)">❌</button>
			</div>
	</td>
`;
});

function saveNewItem(button) {
	// Get the row containing the new item data
	const newRow = button.closest('tr');

	// Create an object to store the new item's data
	const newItemData = {
		date: newRow.querySelector('.item-date').textContent,
		cost_per_item: newRow.querySelector('.cost-per-item').textContent,
		number_of_items: newRow.querySelector('.number-of-items').textContent,
		item_link: newRow.querySelector('.item-link').textContent,
	};

	// Check if item_name has content before adding it to newItemData
	const item_name = newRow.querySelector('.item-name').textContent.trim();
	if (item_name !== '') {
		newItemData.item_name = item_name;
	}

	// Check if current_price has content before adding it to newItemData
	const current_price = newRow
		.querySelector('.current-price')
		.textContent.trim();
	if (current_price !== '') {
		newItemData.current_price = current_price;
	}

	// Send the data to your Flask server via a POST request
	fetch('/add_item', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(newItemData),
	})
		.then((response) => response.json())
		.then((data) => {
			// Handle the response from the server, e.g., show an alert
			if (data.message) {
				// remove the row
				const newRow = button.closest('tr');
				newRow.remove();
				// refresh data
				refresh_data();
				// show message
				updateAlertContent(data.message);
			} else {
				updateAlertContent(data.error);
			}
		})
		.catch((error) => {
			console.error('Error:', error);
		});
}

function cancelNewItem(button) {
	// Get the row containing the "Cancel" button and delete it
	const newRow = button.closest('tr');
	newRow.remove();
}

function updateAlertContent(message) {
	const alertPlaceholder = document.querySelector('.custom-alert');
	alertPlaceholder.innerHTML = message;
}
