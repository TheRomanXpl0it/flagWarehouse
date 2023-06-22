let mins;
let secs;
let exploitFilter;
let flaggedTeams;
let intervalID;

let chDoughnut = new Chart($('#chDoughnut'), {
    type: 'doughnut',
    data: {
        labels: ['Accepted', 'Queued', 'Expired', 'Error'],
        datasets: [{
            data: [],
            borderWidth: 0,
            backgroundColor: [theme.success, theme.info, theme.warning, theme.danger]
        }]
    },
    options: {
        aspectRatio: 1.5,
        responsive: true,
        cutoutPercentage: 50,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 20
                }
            },
            labels: {
                pointStyle: 'circle',
                usePointStyle: true
            }
        }
    }
});

let barsOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false,
            position: 'top',
            labels: {
                boxWidth: 20
            }
        }
    }
};


let chBarsExploits = new Chart($('#chBarsExploits'), {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Accepted',
            backgroundColor: theme.success,
            barPercentage: 0.4,
            categoryPercentage: 0.8,
            data: []
        }, {
            label: 'Error',
            backgroundColor: theme.danger,
            barPercentage: 0.4,
            categoryPercentage: 0.8,
            data: []
        }]
    },
    options: barsOptions
});

let chBarsTeams = new Chart($('#chBarsTeams'), {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Accepted',
            backgroundColor: theme.success,
            barPercentage: 0.4,
            categoryPercentage: 0.8,
            data: []
        }, {
            label: 'Error',
            backgroundColor: theme.danger,
            barPercentage: 0.4,
            categoryPercentage: 0.8,
            data: []
        }]
    },
    options: barsOptions
});

let updateAll = function () {
    $.ajax({
        url: '/index/chart_data',
        method: 'get',
        data: {
            mins: mins,
            exploitFilter: exploitFilter
        },
        dataType: 'json',
        success: function (response) {
            // Doughnut
            chDoughnut.data.datasets[0].data[0] = response.doughnutStatus.accepted;
            chDoughnut.data.datasets[0].data[1] = response.doughnutStatus.queued;
            chDoughnut.data.datasets[0].data[2] = response.doughnutStatus.expired;
            chDoughnut.data.datasets[0].data[3] = response.doughnutStatus.error;
            chDoughnut.update();


            // EXPLOITS
            // Remove old objects and labels
            chBarsExploits.data.labels = chBarsExploits.data.labels.filter(function (label) {
                for (let i = 0; i < response.barsExploit.length; i++) {
                    if (response.barsExploit[i].name === label) {
                        return true;
                    }
                }
                return false;
            });
            chBarsExploits.data.datasets.forEach(function (dataset) {
                dataset.data = dataset.data.filter(function (obj) {
                    for (let i = 0; i < response.barsExploit.length; i++) {
                        if (response.barsExploit[i].name === obj.x) {
                            return true;
                        }
                    }
                    return false;
                });
            });

            // Update and add new objects, labels and menu options
            for (let i = 0; i < response.barsExploit.length; i++) {
                let item = response.barsExploit[i];
                if (chBarsExploits.data.labels.includes(item.name)) {
                    let idxAccepted = chBarsExploits.data.datasets[0].data.findIndex(obj => {
                        return obj.x === item.name;
                    });
                    let idxError = chBarsExploits.data.datasets[1].data.findIndex(obj => {
                        return obj.x === item.name;
                    });
                    chBarsExploits.data.datasets[0].data[idxAccepted].y = item.accepted;
                    chBarsExploits.data.datasets[1].data[idxError].y = item.error;
                } else {
                    chBarsExploits.data.labels.splice(i, 0, item.name);
                    let acceptedObj = {x: item.name, y: item.accepted}
                    let errorObj = {x: item.name, y: item.error}
                    chBarsExploits.data.datasets[0].data.splice(i, 0, acceptedObj);
                    chBarsExploits.data.datasets[1].data.splice(i, 0, errorObj);
                }
                // Remove invalid exploits menu options and add new ones
                // "validExploit" is a temporary class to test that an exploit still exists, just in case
                let selector = $(`.exploitSelectOption[value="${response.barsExploit[i].name}"`);
                if(selector.length)
                    selector.addClass("validExploit");
                else
                $('#exploitSelect').append(`<option value="${item.name}" class="exploitSelectOption validExploit">${item.name}</option>`);
            }
            chBarsExploits.update();
            $(".exploitSelectOption:not(.validExploit)").remove();
            $(".exploitSelectOption").removeClass("validExploit");


            // TEAMS
            // Remove old objects and labels
            chBarsTeams.data.labels = chBarsTeams.data.labels.filter(function (label) {
                for (let i = 0; i < response.barsTeams.length; i++) {
                    if (response.barsTeams[i].name === label) {
                        return true;
                    }
                }
                return false;
            });
            chBarsTeams.data.datasets.forEach(function (dataset) {
                dataset.data = dataset.data.filter(function (obj) {
                    for (let i = 0; i < response.barsTeams.length; i++) {
                        if (response.barsTeams[i].name === obj.x) {
                            return true;
                        }
                    }
                    return false;
                });
            });

            // Update and add new objects and labels
            flaggedTeams = [];
            for (let i = 0; i < response.barsTeams.length; i++) {
                let item = response.barsTeams[i];
                flaggedTeams.push(item.name);
                if (chBarsTeams.data.labels.includes(item.name)) {
                    let idxAccepted = chBarsTeams.data.datasets[0].data.findIndex(obj => {
                        return obj.x === item.name;
                    });
                    let idxError = chBarsTeams.data.datasets[1].data.findIndex(obj => {
                        return obj.x === item.name;
                    });
                    chBarsTeams.data.datasets[0].data[idxAccepted].y = item.accepted;
                    chBarsTeams.data.datasets[1].data[idxError].y = item.error;
                } else {
                    chBarsTeams.data.labels.splice(i, 0, item.name);
                    let acceptedObj = {x: item.name, y: item.accepted}
                    let errorObj = {x: item.name, y: item.error}
                    chBarsTeams.data.datasets[0].data.splice(i, 0, acceptedObj);
                    chBarsTeams.data.datasets[1].data.splice(i, 0, errorObj);
                }
            }
            chBarsTeams.update();
        }
    });
};

let showTeamsInfo = function() {
    let missingTeams = [];
    let exploitableTeams = numberOfTeams - 1;
    for (let i = 1; i <= numberOfTeams; i++) {
        if (i == myTeam)
            continue;
        let team = teamFormat.replace("{}", i);
        if (!flaggedTeams.includes(team))
            missingTeams.push(team);
    }

    if (exploitFilter)
        $('#teamsDetailsModal .modal-title').text(`Details (${exploitFilter})`);
    else
        $('#teamsDetailsModal .modal-title').text('Details (all exploits)');

    if (!missingTeams.length) {
        $('#teamsDetailsModal .modal-body').text(`You're attacking all ${exploitableTeams} teams. Very good!`);
    } else {
        let output = `You're attacking ${flaggedTeams.length} out of ${exploitableTeams} teams.<br /><br />These teams aren't vulnerable: <ul><li>`;
        output += missingTeams.join('</li><li>')
        output += '</li></ul>Pwn them, bitch!';
        $('#teamsDetailsModal .modal-body').html(output);
    }
    
    $('#teamsDetailsModal').modal('show');
}

window.onload = function () {
    mins = $('#minsSelect').val();
    secs = $('#autorefreshSelect').val();
    exploitFilter = '';
    updateAll();
    intervalID = setInterval(updateAll, secs * 1000);
};

$('#minsSelect').on('change', function () {
    mins = $('#minsSelect').val();
    updateAll();
})

$('#autorefreshSelect').on('change', function () {
    secs = $('#autorefreshSelect').val();
    updateAll();
    clearInterval(intervalID);
    intervalID = setInterval(updateAll, secs * 1000);
})

$('#exploitSelect').on('change', function () {
    exploitFilter = $('#exploitSelect').val();
    updateAll();
})