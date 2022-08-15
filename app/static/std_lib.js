/* Some shared function */

function get_asset_list_std(type, target) {
  var http = new XMLHttpRequest();
  http.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById(target).innerHTML = this.responseText;
      document.getElementById(target).style.visibility = "visible";
    }
  };
  data = '{"action": "' + type + '", "asset": "", "options": ""}'
  http.open('POST', 'get_asset_list', true);
  http.setRequestHeader('content-type', 'application/json;charset=UTF-8');
  http.send(JSON.stringify(data));
}

function get_asset_select(select_target, select_id) {
    var http = new XMLHttpRequest();
    http.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
        select = '<select name="' + select_id + '" id="' + select_id + '">' +  this.responseText + '</select>'
        document.getElementById(select_target).innerHTML = select;
        document.getElementById(select_target).style.visibility = "visible";
      }
    };
    data = '{"action": "options", "asset": "", "options": ""}'
    http.open('POST', 'get_asset_list', true);
    http.setRequestHeader('content-type', 'application/json;charset=UTF-8');
    http.send(JSON.stringify(data));
}

// Quick and simple export target #table_id into a csv
function convert_table_to_csv(table_id, separator = ',') {
    // Select rows from table_id
    var rows = document.querySelectorAll('table#' + table_id + ' tr');
    // Construct csv
    var csv = [];
    for (var i = 0; i < rows.length; i++) {
        var row = [], cols = rows[i].querySelectorAll('td, th');
        for (var j = 0; j < cols.length; j++) {
            // Clean innertext to remove multiple spaces and jumpline (break csv)
            var data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ')
            // Escape double-quote with double-double-quote (see https://stackoverflow.com/questions/17808511/properly-escape-a-double-quote-in-csv)
            data = data.replace(/"/g, '""');
            // Push escaped string
            row.push('"' + data + '"');
        }
        csv.push(row.join(separator));
    }
    return csv_string = csv.join('\n');

  }

  function download_tables(csv_string) {
    // Download it
    var filename = 'export_' + new Date().toLocaleDateString() + '.csv';
    var link = document.createElement('a');
    link.style.display = 'none';
    link.setAttribute('target', '_blank');
    link.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv_string));
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}