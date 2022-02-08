$(function(){
    
    $('#ftmsupload').on('submit', function(event) {

        event.preventDefault();

        let formData = new FormData($('form')[0]);

        $.ajax({
            xhr : function() {
                var xhr = new window.XMLHttpRequest();
                    
                xhr.upload.addEventListener('progress', function(e) {

                    if (e.lengthComputable) {

                        console.log('Bytes Loaded: ' + e.loaded);
                        console.log('Total Size: ' + e.total);
                        console.log('Percentage Uploaded: ' + (e.loaded / e.total));

                        var percent = Math.round((e.loaded / e.total) * 100);
                        
                        $('#progressBar').attr('data-label', percent +'% Complete');
                        $('#valueprogress').css('width', percent + '%');
                    }

                });

                return xhr;
            },
            type : 'POST',
            url : $(this).attr('action'),
            data : formData,
            processData : false,
            contentType : false,
            
            
        }).done(function() {
            alert('All files were uploaded!');
            $('#progressBar').attr('data-label', 0 +'% Complete');
            $('#valueprogress').css('width', 0 + '%');
            
            //TODO: reload data table and process list to avoid reload
            // call to update on load
            switchToFtmsData(); 
            updateFtmsDataList();
            
            
            //alert('test');
            
            //location.reload();
            
            
            
        }).fail(function(data) {
            alert(data.responseText);
            $('#progressBar').attr('data-label', 0 +'% Complete');
            $('#valueprogress').css('width', 0 + '%');
        });

    });
});