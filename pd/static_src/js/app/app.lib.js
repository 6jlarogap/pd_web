
function default_display_response_error(result){
    return;
    /*if(result.data.__all__ && result.data.__all__.length){
        var error = result.data.__all__[0] || 'Ошибка при добавлении' ;
        noty({text: error, type:'error', layout:'topRight'});
    }*/
}

if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}


function getCookie(name) {
    var cookie = document.cookie || " ",
        search = name + "=",
        setStr = null,
        offset = 0,
        end = 0;
    if (cookie.length > 0) {
        offset = cookie.indexOf(search);
        if (offset != -1) {
            offset += search.length;
            end = cookie.indexOf(";", offset)
            if (end == -1) {
                end = cookie.length;
            }
            setStr = unescape(cookie.substring(offset, end));
        }
    }
    return setStr;
}


function date2time(val){
    if(typeof(val)=='string' && val[2]==':'){
        return val
    }else if(!val || !val.getHours ){
        return '00:00';
    }
	var h = val.getHours().toString(),
		m = val.getMinutes().toString();
     if(h.length==1){
        h = '0'+h;
     }
     if(m.length==1){
        m = '0'+m;
     }
	return h+':'+m;
};

function caretakerShow(caretaker, caretakers) {
	if (caretaker) {
		for (i = 0; i < caretakers.length; i++) {
			if (caretakers[i].id == caretaker) {
				return caretakers[i].fio;
			}
		}
	} else {
		return "не назначен";
	}
	return "не задан"
};
