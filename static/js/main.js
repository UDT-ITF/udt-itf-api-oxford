

var version = 1;
$('#switchAPIs').change(e => {
    if ($('#switchAPIs').is(':checked')) {
        $('#lblAPIName').html('Text Fragment API Playground')
        e.preventDefault();
        $('#textAPIs').load('/text_fragment_api', (e) => {
            $('.info-box').load('/text_fragment_api #divInfo', (e)=>{
                $('.info-box').html($(e).html())
            })
            var script = document.createElement('script');
            script.src=`/static/js/text-fragment-api.js?t=${++version}`;
            script.type = 'module';
            $('#textAPIs').append(script);
        })
    } else {
        $('#lblAPIName').html('Text Info API Playground')
        $('#textAPIs').load('/text_info_api', (e)=>{
            $('.info-box').load('/text_info_api #divInfo', (e)=>{
                $('.info-box').html($(e).html())
            })

            var script = document.createElement('script');
            script.src=`/static/js/text-info-api.js?t=${++version}`;
            script.type = 'module';
            $('#textAPIs').append(script);
        })
        $('.word-density').hide()
    }
})


// On page load
$(document).ready((e) => {
    $('#textAPIs').load('/text_fragment_api', (e) => {
        var script = document.createElement('script');
        script.src=`/static/js/text-fragment-api.js?t=${++version}`;
        script.type = 'module';
        //if we're adding a new script we need to wait for it to finish loading before
        //triggering the DOMContentLoaded event
        $('#textAPIs').append(script);
    })
})
