$("#submit").on("click", function() {
    $("#result").hide(250);

    // example of accepted time string: 2023-06-21 00:31:22
    // .toISOString() ignores local time zone, which is needed for other things to work correctly
    // also, JS sucks and there's no good way to format a date into a string
    var tzoffset = (new Date()).getTimezoneOffset() * 60000; // timezone offset in milliseconds
    var time = (new Date(Date.now() - tzoffset)).toISOString().slice(0, -5).replace('T', ' ');

    // flags format: (flag, exploit_name, team_ip, time)
    var data = {"username": "WebAdmin", "flags": []};
    $.each($('#flags').val().split(/\n/), function(i, flag){
        flag = flag.trim();
        if(flag)
            data.flags.push({"flag": flag, "exploit_name": "<manual>", "team_ip": "10.60.0.1", "time": time});
    });

    if(data.flags.length > 0) {
        $.ajax({
            type: "POST",
            url: "/api/upload_flags",
            data: JSON.stringify(data),
            contentType: "application/json; charset=utf-8",
            success: function(response){
                $("#result")
                    .removeClass("alert-error")
                    .addClass("alert-info")
                    .text(response)
                    .show(250);
            },
            error: function(xhr, status, error){
                $("#result")
                    .removeClass("alert-info")
                    .addClass("alert-error")
                    .text(xhr.responseText)
                    .show(250);
            }
        });
    }
});