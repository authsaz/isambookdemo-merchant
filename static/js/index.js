String.prototype.format = function() {
    var formatted = this;
    var keys = Object.keys(arguments[0]);
    for (var i = 0; i < keys.length; i++) {
        var regexp = new RegExp('\\{'+keys[i] +'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[0][keys[i]] );
    }
    return formatted;
};

$.oauthpopup = function(options)
{
    options.windowName = options.windowName ||  'ConnectWithOAuth'; // should not include space for IE
    options.windowOptions = options.windowOptions || 'location=0,status=0,width=800,height=600';
    options.callback = options.callback || function(){ window.location.reload(); };
    var that = this;
    that._oauthWindow = window.open(options.path, options.windowName, options.windowOptions);
    that._oauthInterval = window.setInterval(function(){
        if (that._oauthWindow.closed) {
            window.clearInterval(that._oauthInterval);
            options.callback();
        }
    }, 1000);
};

function popitup(url,windowName) {
    $("#detail-data").text("");
       newwindow=window.open(url,windowName,'height=600,width=800');
	   interval = window.setInterval(function(){
			if (newwindow.closed) {
				window.clearInterval(interval);
				//window.location.reload();
                if($("#detail-data").text()!=""){
                    $('#myModal').modal('show');
                }
			}
		}, 1000);
       if (window.focus) {newwindow.focus()}
       return false;
     }

     function handle_popup_data( data){
         console.log(data);
         
         $("#detail-data").text(JSON.stringify(data) );
     }

    $("#btn_accounts").click(function() {
        $.ajax({
            type: "POST",
            url: "/get_accounts",
			data: $("#form_accounts").serialize(),
            success: function(msg) { 
			   if("status" in msg && msg["status"] == "auth-need"){
                   var url = msg["url"].format({"policy":msg["policy"],"token":msg["token"],
                            "target":msg["target"]})
				   popitup( url);
			   }else{
                   handle_popup_data(msg);
                   $('#myModal').modal('show');
               }
            },
            error: function() {
                $('#fail').modal('show');
            }
        });
    });

    
    $("#btn_balance").click(function() {
        $.ajax({
            type: "POST",
            url: "/balance",
			data: $("#form_balance").serialize(),
            success: function(msg) { 
			   if("status" in msg && msg["status"] == "auth-need"){
                   var url = msg["url"].format({"policy":msg["policy"],"token":msg["token"],
                            "target":msg["target"]})
				   popitup( url);
			   }else{
                   handle_popup_data(msg);
                   $('#myModal').modal('show');
               }
            },
            error: function() {
                $('#fail').modal('show');
            }
        });
    });
    
    

    $("#btn_transfer").click(function() {
        $.ajax({
            type: "POST",
            data: $("#form_transfer").serialize(),
            url: "/transfer",
            success: function(msg) {
                if("status" in msg && msg["status"] == "auth-need"){
                   var url = msg["url"].format({"policy":msg["policy"],"token":msg["token"],
                            "target":msg["target"]})
				   popitup( url);
			   }else{
                   handle_popup_data(msg);
                   $('#myModal').modal('show');
               }
            },
            error: function() {
                $('#fail').modal('show');
            }
        });
        return false;
    });


    $("#btn_logout").click(function() {
        $.ajax({
            type: "POST",
            url: "/logout",
            success: function(msg) {
               window.location.reload();
            },
            error: function() {
                $('#fail').modal('show');
            }
        });
    });
	
	$("#btn_refresh").click(function() {
        $.ajax({
            type: "POST",
            url: "/refresh_token",
            success: function(msg) {
               window.location.reload();
            },
            error: function() {
                $('#fail').modal('show');
            }
        });
    });


    $("#btn_me").click(function() {
        $.ajax({
            type: "POST",
            url: "/me",
            success: me_callback,
            error: me_callback
        });
    });


function me_callback(msg){
     console.log(msg);
     msg = msg.substring(0,200);
     $("#more_info").text(msg);
}


function HandleMMFAResult(result) {
    alert("result of popup is: " + result);
}

