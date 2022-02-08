$(function(){
    
    $("#searchGcmsResultsTable").on("keyup", function() {
        let value = $(this).val().toLowerCase();
        $("#gcmsResultsTable tr").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });

    $("#searchGcmsDataTable").on("keyup", function() {
        let value = $(this).val().toLowerCase();
        $("#gcmsDataTable tr").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
    
 });