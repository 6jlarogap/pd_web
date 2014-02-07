app.factory('Log', function($resource,$routeParams){
	return $resource('/api/log', {}, {
		place_log: {
			method: 'GET',
			params: {
				format: 'json',
				type:'place'
			},
			isArray: true
		},
	});
});
