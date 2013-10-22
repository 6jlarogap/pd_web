$(function(){
	$.ajaxSetup({
    	headers: { 'X-CSRFToken': getCookie('csrftoken') || csrf }
	});
});


app.config(["$httpProvider", function($httpProvider) {
	var csrfToken = getCookie('csrftoken') || csrfToken;
    $httpProvider.defaults.headers.common['X-CSRFToken'] = csrfToken; 
    //$httpProvider.defaults.headers.post['X-CSRF-Token'] = csrfToken;
    //$httpProvider.defaults.headers.put['X-CSRF-Token'] = csrfToken;
    //$httpProvider.defaults.headers.patch['X-CSRF-Token'] = csrfToken;
    //$httpProvider.defaults.headers['delete']['X-CSRF-Token'] = csrfToken;
}])

.config(['$httpProvider', function($httpProvider) {
	/* HTTP Interceptor*/
	$httpProvider.responseInterceptors.push(['$q', function($q) {
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
						alert('Объект не найден');
			            break;
					case 400:
						// var key = keys(a)[0]
						var error = '';
						for(var i in response.data){
							if(i) error += '{0}: {1}\n'.format(i, response.data[i]);
						}
			            alert(error);
			            break;
					case 500:
						alert('Ошибка обработки');
			            break;
					default:
						alert('Ошибка выполнения');
			            break;
				}
				return $q.reject(response);
			});
		}
	}]);
}]);

