 
$(function(){
    
    $("#searchFtmsResultsTable").on("keyup", function() {
        let value = $(this).val().toLowerCase();
        $("#ftmsResultsTable tr").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });

    $("#searchFtmsDataTable").on("keyup", function() {
        let value = $(this).val().toLowerCase();
        $("#ftmsDataTable tr").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
    
 });

