app.factory('Phone', function($resource,$routeParams){
	return $resource('/static/js/app/phones.json');
});
