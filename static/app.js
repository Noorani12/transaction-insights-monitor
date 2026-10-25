
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const riskFilter = document.getElementById("riskFilter");
const table = document.getElementById("transactionTable");
const emptyMessage = document.getElementById("emptyMessage");

function filterTransactions() {
    const query = searchInput.value.trim().toLowerCase();
    const selectedStatus = statusFilter.value;
    const selectedRisk = riskFilter.value;

    const rows = table.querySelectorAll("tbody tr");
    let visibleCount = 0;

    rows.forEach((row) => {
        const merchantCell = row.cells[1];

        // Ignore the placeholder row when the database is empty.
        if (!merchantCell) {
            row.hidden = true;
            return;
        }

        const merchant = merchantCell.textContent.toLowerCase();

        const matchesSearch = merchant.includes(query);
        const matchesStatus =
            !selectedStatus || row.dataset.status === selectedStatus;
        const matchesRisk =
            !selectedRisk || row.dataset.risk === selectedRisk;

        const visible =
            matchesSearch && matchesStatus && matchesRisk;

        row.hidden = !visible;

        if (visible) {
            visibleCount++;
        }
    });

    emptyMessage.hidden = visibleCount > 0;
}

searchInput.addEventListener("input", filterTransactions);
statusFilter.addEventListener("change", filterTransactions);
riskFilter.addEventListener("change", filterTransactions);

const chartDataElement = document.getElementById("chart-data");

if (chartDataElement && window.Chart) {
    const chartData = JSON.parse(chartDataElement.textContent);

    const chartPixelRatio = 2;

    new Chart(document.getElementById("statusChart"), {
        type: "doughnut",
        data: {
            labels: chartData.statusLabels,
            datasets: [{
                data: chartData.statusValues,
                backgroundColor: ["#22a06b", "#f0ad3d", "#e05252"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            devicePixelRatio: chartPixelRatio,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });

    new Chart(document.getElementById("dailyChart"), {
        type: "bar",
        data: {
            labels: chartData.dailyLabels,
            datasets: [{
                label: "Transaction value (₹)",
                data: chartData.dailyValues,
                backgroundColor: "#4263eb",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            devicePixelRatio: chartPixelRatio,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
