app.factory('PlaceSize', function($resource, $routeParams){
	return $resource('/api/placesize', {},{
		query: {
			method: 'GET',
			params: {
				format: 'json'
			},
			isArray: true
		}
	});
});
