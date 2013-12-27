$(function(){
	$.ajaxSetup({
    	headers: { 'X-CSRFToken': getCookie('csrftoken') || csrf }
	});
});

$.noty.defaults = {
    layout: 'top',
    theme: 'defaultTheme',
    type: 'alert',
    text: '',
    dismissQueue: true, // If you want to use queue feature set this true
    template: '<div class="noty_message"><span class="noty_text"></span><div class="noty_close">X</div>X</div>',
    animation: {
        open: {height: 'toggle'},
        close: {height: 'toggle'},
        easing: 'swing',
        speed: 500 // opening & closing animation speed
    },
    timeout: 2500, // delay for closing event. Set false for sticky notifications
    force: false, // adds notification to the beginning of queue when set to true
    modal: false,
    maxVisible: 5, // you can set max visible notification for dismissQueue true option
    closeWith: ['click', 'hover'], // ['click', 'button', 'hover']
    callback: {
        onShow: function() {},
        afterShow: function() {},
        onClose: function() {},
        afterClose: function() {}
    },
    buttons: false // an array of buttons
};


app.config(["$httpProvider", function($httpProvider) {
	var csrfToken = getCookie('csrftoken') || csrfToken;
    $httpProvider.defaults.headers.common['X-CSRFToken'] = csrfToken;
    $httpProvider.defaults.headers.common['HTTP_X_CSRFTOKEN'] = csrfToken;
    //$httpProvider.defaults.headers.post['X-CSRF-Token'] = csrfToken;
    //$httpProvider.defaults.headers.put['X-CSRF-Token'] = csrfToken;
    //$httpProvider.defaults.headers.patch['X-CSRF-Token'] = csrfToken;
    //$httpProvider.defaults.headers['delete']['X-CSRF-Token'] = csrfToken;
}])

.config(['$httpProvider', function($httpProvider) {
	/* HTTP Interceptor*/
	$httpProvider.responseInterceptors.push(['$q', '$location' function($q, $location) {
		return function(promise) {
			return promise.then(function(response) { // The HTTP request was successful.
				// response.status >= 200 && response.status <= 299
				// The http request was completed successfully.
				//response.data.extra = 'Interceptor strikes back';
				//console.info(response.config.url)
				return response; 
			}, function(response) { // The HTTP request was not successful.
				switch (response.status) {
					case 401:
			            $location.path('/login');
			            break;
					case 404:
						//console.log(response);
						//noty({text: 'Объект не найден', timeout:false, type:'warning', layout:'topRight'});
						$location.path('/manage/404?title=Объект не найден');
			            break;
					case 400:
						var error = '';
						for(var i in response.data){
							if(i){ 
								var error = '{0}: {1}\n'.format(i, response.data[i]);
			            		noty({text: error, timeout:false, type:'warning', layout:'topRight'});
			            	}
						}
			            break;
					case 500:
						noty({text: 'Ошибка обработки', type:'warning', layout:'topRight'});
			            $location.path('/manage/500');
			            break;
					default:
						noty({text: 'Ошибка выполнения', type:'warning', layout:'topRight'});
			            break;
				}
				return $q.reject(response);
			});
		}
	}]);
}]);
