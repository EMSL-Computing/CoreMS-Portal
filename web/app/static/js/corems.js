
$(function(){
    onPageLoad();
});


function onPageLoad(){
    
    // All commands here
    
    let pathname = window.location.pathname;
    $('a[href="' + pathname + '"]').addClass('is-active');
    
    $('.left_nav li a').click(function(e) {
        window.location = $(this).attr('href');
        
        $('.left_nav li a').removeClass('is-active');
        $(this).addClass('is-active');
        e.preventDefault();
    })
    
    
    $('#gcms_process').on('submit', function(event) {

        event.preventDefault();

        let formData = new FormData($('#gcms_process')[0]);
        let preset_id = $('#gcmspresetsubmmit').val();
        let url = `${$(this).attr('action')}/${preset_id}`;
        
        if ( $( "#gcms_selected_reference_file :selected" ).text() == 'None'){
            alert("Please upload and select a reference file");
            return
        }

        $.ajax({
            
            type : 'POST',
            url : url,
            data : formData,
            processData : false,
            contentType : false,
            beforeSend: function(){
                
                

                //startModalSpin();
             },
            
        }).done(function() {
            
            //alert('Processing task has been successfully submitted, please check results tables for task status');
            //TODO: populate results table and add status (active, success, failed)
            switchToGcmsResult();
            location.reload();
            
                        
        }).fail(function() {
            stopModalSpin();
            alert('Ops something went wrong, please try again!');
            
        });

    })

    $('#ftms_process').on('submit', function(event) {

        event.preventDefault();

        let formData = new FormData($('#ftms_process')[0]);
        let preset_id = $('#ftmspresetsubmmit').val();
        let url = `${$(this).attr('action')}/${preset_id}`;
        
        $.ajax({
            
            type : 'POST',
            url : url,
            data : formData,
            processData : false,
            contentType : false,
            beforeSend: function(){
                
                //startModalSpin();   
             },
            
        }).done(function() {
            
            //alert('Processing task has been successfully submitted, please check results tables for task status');
            //TODO: populate results table and add status (active, success, failed)
            switchToFtmsResult();
            location.reload();
            
                        
        }).fail(function() {
            stopModalSpin();
            alert('Ops something went wrong, please try again!');
            
        });

    })
    
    //$('tr').click(function(){
        
    //    $(this).toggleClass('is-selected');
        //var table = $(this).parents('table').eq(0)
        //alert( table.rows('is-selected').data().length +' row(s) selected' );

    //} );
    //$('th').click(function(){
    //    var table = $(this).parents('table').eq(0)
    //    var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()))
    //    this.asc = !this.asc
    //    if (!this.asc){rows = rows.reverse()}
    //    for (var i = 0; i < rows.length; i++){table.append(rows[i])}
    //});

  };


function startModalSpin() {
    
    var pmodal = document.querySelector('#progress');  // assuming you have only 1
    var html = document.querySelector('html');
    pmodal.classList.add('is-active');
    html.classList.add('is-clipped');

    pmodal.querySelector('.modal-background').addEventListener('click', function(e) {
        e.preventDefault();
        pmodal.classList.remove('is-active');
        html.classList.remove('is-clipped');
        
        })
    pmodal.querySelector('.modal-close').addEventListener('click', function(e) {
        e.preventDefault();
        pmodal.classList.remove('is-active');
        html.classList.remove('is-clipped');
        
        })  
}

function stopModalSpin() {
    
    var html = document.querySelector('html');
    var pmodal = document.querySelector('#progress');
    pmodal.classList.remove('is-active');
    html.classList.remove('is-clipped');
}


function comparer(index) {
    return function(a, b) {
        var valA = getCellValue(a, index), valB = getCellValue(b, index)
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB)
    }
}
function getCellValue(row, index){ return $(row).children('td').eq(index).text() }