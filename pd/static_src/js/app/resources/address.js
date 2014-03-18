app.factory('Address', function($resource,$routeParams){
	return $resource('/api/geo/location/:addressID', {
		addressID : '@id'
	}, {
		update : {
			method : 'PUT'
		}
	});
});
